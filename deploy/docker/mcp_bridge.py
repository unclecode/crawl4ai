from __future__ import annotations
import inspect, json, re
from typing import Any, Callable
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

def mcp_resource(name: str | None = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "resource", name
        return fn
    return deco

def mcp_template(name: str | None = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "template", name
        return fn
    return deco

def mcp_tool(name: str | None = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "tool", name
        return fn
    return deco

def _service_auth_headers() -> dict:
    from auth import create_access_token
    token = create_access_token({"sub": "mcp-service"}, scope="data")
    return {"Authorization": f"Bearer {token}"}


def _make_http_proxy(base_url: str, route, *, timeout: float | None = None):
    method = list(route.methods - {"HEAD", "OPTIONS"})[0]
    async def proxy(**kwargs):
        path = route.path
        for k, v in list(kwargs.items()):
            placeholder = "{" + k + "}"
            if placeholder in path:
                path = path.replace(placeholder, str(v))
                kwargs.pop(k)
        url = base_url.rstrip("/") + path

        headers = _service_auth_headers()
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                r = (
                    await client.get(url, params=kwargs, headers=headers)
                    if method == "GET"
                    else await client.request(method, url, json=kwargs, headers=headers)
                )
                r.raise_for_status()
                return r.text if method == "GET" else r.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(e.response.status_code, e.response.text)
            except httpx.TimeoutException:
                raise HTTPException(504, "upstream request timed out")
    return proxy


def _schema(model: type[BaseModel] | None) -> dict:
    return {"type": "object"} if model is None else model.model_json_schema()


def _body_model(fn: Callable) -> type[BaseModel] | None:
    for p in inspect.signature(fn).parameters.values():
        a = p.annotation
        if inspect.isclass(a) and issubclass(a, BaseModel):
            return a
    return None


def _make_tool_wrapper(
    name: str,
    proxy_fn: Callable,
    model: type[BaseModel] | None,
) -> Callable:
    """Create a properly-typed async wrapper for MCP tool registration.

    Uses the Pydantic model's fields to build the function signature so the
    MCP SDK generates the correct JSON input schema automatically.
    """
    if model is None:
        async def wrapper() -> str:
            try:
                res = await proxy_fn()
            except HTTPException as exc:
                return json.dumps({"error": exc.status_code, "detail": exc.detail}, ensure_ascii=False)
            return json.dumps(res, default=str, ensure_ascii=False)
        wrapper.__name__ = name
        return wrapper

    fields = model.model_fields
    params: list[inspect.Parameter] = []
    for field_name, field in fields.items():
        annotation = field.annotation if field.annotation is not inspect.Parameter.empty else str
        if field.is_required():
            params.append(inspect.Parameter(field_name, inspect.Parameter.KEYWORD_ONLY, annotation=annotation))
        else:
            params.append(inspect.Parameter(field_name, inspect.Parameter.KEYWORD_ONLY, default=field.default, annotation=annotation))

    sig = inspect.Signature(params, return_annotation=str)

    async def wrapper(**kwargs) -> str:
        try:
            res = await proxy_fn(**kwargs)
        except HTTPException as exc:
            return json.dumps({"error": exc.status_code, "detail": exc.detail}, ensure_ascii=False)
        return json.dumps(res, default=str, ensure_ascii=False)

    wrapper.__name__ = name
    wrapper.__signature__ = sig
    return wrapper


def attach_mcp(
    app: FastAPI,
    *,
    base: str = "/mcp",
    name: str | None = None,
    base_url: str,
    timeout: float | None = None,
) -> FastMCP:
    """Mount the Streamable-HTTP MCP transport on a FastAPI app.

    Call once after all routes are declared.  Registers every endpoint
    decorated with ``@mcp_tool`` as an MCP tool and exposes a single
    ``POST {base}`` Streamable-HTTP endpoint (replaces the deprecated SSE
    transport).
    """
    server_name = name or app.title or "FastAPI-MCP"
    mcp = FastMCP(
        server_name,
        streamable_http_path=base,
        json_response=True,
    )

    # Collect decorated routes
    tools: dict[str, tuple[Callable, Callable]] = {}

    for route in app.routes:
        fn = getattr(route, "endpoint", None)
        kind = getattr(fn, "__mcp_kind__", None)
        if not kind:
            continue
        key = fn.__mcp_name__ or re.sub(r"[/{}}]", "_", route.path).strip("_")
        if kind == "tool":
            proxy = _make_http_proxy(base_url, route, timeout=timeout)
            tools[key] = (proxy, fn)

    # Register tools on FastMCP
    for k, (proxy, orig_fn) in tools.items():
        desc = getattr(orig_fn, "__mcp_description__", None) or inspect.getdoc(orig_fn) or ""
        model = _body_model(orig_fn)
        wrapper = _make_tool_wrapper(k, proxy, model)
        mcp.add_tool(wrapper, name=k, description=desc)

    # Build the Streamable-HTTP ASGI app and wire its route into the outer app
    mcp_starlette = mcp.streamable_http_app()
    for route in mcp_starlette.routes:
        app.routes.append(route)

    # Expose the MCP instance so the parent lifespan can manage the session
    app.state._mcp_instance = mcp

    # ── schema endpoint (informational, not required by Streamable-HTTP) ──
    @app.get(f"{base}/schema")
    async def _schema_endpoint():
        tools_list = []
        for k, (proxy, orig_fn) in tools.items():
            desc = getattr(orig_fn, "__mcp_description__", None) or inspect.getdoc(orig_fn) or ""
            model = _body_model(orig_fn)
            tools_list.append({
                "name": k,
                "description": desc,
                "inputSchema": _schema(model),
            })
        return JSONResponse({"tools": tools_list})

    return mcp
