# deploy/docker/mcp_bridge.py

from __future__ import annotations
import inspect, json, re, anyio
from contextlib import suppress
from typing import Any, Callable, Dict, List, Tuple
import httpx

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Request
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from mcp.server.sse import SseServerTransport

import mcp.types as t
from mcp.server.lowlevel.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

# ── opt‑in decorators ───────────────────────────────────────────
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

# ── HTTP‑proxy helper for FastAPI endpoints ─────────────────────
def _make_http_proxy(base_url: str, route):
    method = list(route.methods - {"HEAD", "OPTIONS"})[0]
    async def proxy(**kwargs):
        # replace `/items/{id}` style params first
        path = route.path
        for k, v in list(kwargs.items()):
            placeholder = "{" + k + "}"
            if placeholder in path:
                path = path.replace(placeholder, str(v))
                kwargs.pop(k)
        url = base_url.rstrip("/") + path

        async with httpx.AsyncClient() as client:
            try:
                r = (
                    await client.get(url, params=kwargs)
                    if method == "GET"
                    else await client.request(method, url, json=kwargs)
                )
                r.raise_for_status()
                return r.text if method == "GET" else r.json()
            except httpx.HTTPStatusError as e:
                # surface FastAPI error details instead of plain 500
                raise HTTPException(e.response.status_code, e.response.text)
    return proxy

# ── main entry point ────────────────────────────────────────────
def attach_mcp(
    app: FastAPI,
    *,                          # keyword‑only
    base: str = "/mcp",
    name: str | None = None,
    base_url: str,              # eg. "http://127.0.0.1:8020"
) -> None:
    """Call once after all routes are declared to expose WS+SSE MCP endpoints."""
    server_name = name or app.title or "FastAPI-MCP"
    mcp = Server(server_name)

    # tools: Dict[str, Callable] = {}
    tools: Dict[str, Tuple[Callable, Callable]] = {}
    resources: Dict[str, Callable] = {}
    templates: Dict[str, Callable] = {}

    # register decorated FastAPI routes
    for route in app.routes:
        fn = getattr(route, "endpoint", None)
        kind = getattr(fn, "__mcp_kind__", None)
        if not kind:
            continue

        key = fn.__mcp_name__ or re.sub(r"[/{}}]", "_", route.path).strip("_")

        # if kind == "tool":
        #     tools[key] = _make_http_proxy(base_url, route)
        if kind == "tool":
            proxy = _make_http_proxy(base_url, route)
            tools[key] = (proxy, fn)
            continue
        if kind == "resource":
            resources[key] = fn
        if kind == "template":
            templates[key] = fn

    # helpers for JSON‑Schema
    def _schema(model: type[BaseModel] | None) -> dict:
        return {"type": "object"} if model is None else model.model_json_schema()

    def _body_model(fn: Callable) -> type[BaseModel] | None:
        for p in inspect.signature(fn).parameters.values():
            a = p.annotation
            if inspect.isclass(a) and issubclass(a, BaseModel):
                return a
        return None

    # MCP handlers
    @mcp.list_tools()
    async def _list_tools() -> List[t.Tool]:
        out = []
        for k, (proxy, orig_fn) in tools.items():
            desc   = getattr(orig_fn, "__mcp_description__", None) or inspect.getdoc(orig_fn) or ""
            schema = getattr(orig_fn, "__mcp_schema__", None) or _schema(_body_model(orig_fn))
            out.append(
                t.Tool(name=k, description=desc, inputSchema=schema)
            )
        return out
             

    @mcp.call_tool()
    async def _call_tool(name: str, arguments: Dict | None) -> List[t.TextContent]:
        if name not in tools:
            raise HTTPException(404, "tool not found")
        
        proxy, _ = tools[name]
        try:
            res = await proxy(**(arguments or {}))
        except HTTPException as exc:
            # map server‑side errors into MCP "text/error" payloads
            err = {"error": exc.status_code, "detail": exc.detail}
            return [t.TextContent(type = "text", text=json.dumps(err))]
        return [t.TextContent(type = "text", text=json.dumps(res, default=str))]

    @mcp.list_resources()
    async def _list_resources() -> List[t.Resource]:
        return [
            t.Resource(name=k, description=inspect.getdoc(f) or "", mime_type="application/json")
            for k, f in resources.items()
        ]

    @mcp.read_resource()
    async def _read_resource(name: str) -> List[t.TextContent]:
        if name not in resources:
            raise HTTPException(404, "resource not found")
        res = resources[name]()
        return [t.TextContent(type = "text", text=json.dumps(res, default=str))]

    @mcp.list_resource_templates()
    async def _list_templates() -> List[t.ResourceTemplate]:
        return [
            t.ResourceTemplate(
                name=k,
                description=inspect.getdoc(f) or "",
                parameters={
                    p: {"type": "string"} for p in _path_params(app, f)
                },
            )
            for k, f in templates.items()
        ]

    init_opts = InitializationOptions(
        server_name=server_name,
        server_version="0.1.0",
        capabilities=mcp.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    # ── WebSocket transport ────────────────────────────────────
    @app.websocket_route(f"{base}/ws")
    async def _ws(ws: WebSocket):
        await ws.accept()
        c2s_send, c2s_recv = anyio.create_memory_object_stream(100)
        s2c_send, s2c_recv = anyio.create_memory_object_stream(100)

        from pydantic import TypeAdapter
        from mcp.types import JSONRPCMessage
        adapter = TypeAdapter(JSONRPCMessage)

        init_done = anyio.Event()

        async def srv_to_ws():
            first = True 
            try:
                async for msg in s2c_recv:
                    await ws.send_json(msg.model_dump())
                    if first:
                        init_done.set()
                        first = False
            finally:
                # make sure cleanup survives TaskGroup cancellation
                with anyio.CancelScope(shield=True):
                    with suppress(RuntimeError):       # idempotent close
                        await ws.close()

        async def ws_to_srv():
            try:
                # 1st frame is always "initialize"
                first = adapter.validate_python(await ws.receive_json())
                await c2s_send.send(first)
                await init_done.wait()          # block until server ready
                while True:
                    data = await ws.receive_json()
                    await c2s_send.send(adapter.validate_python(data))
            except WebSocketDisconnect:
                await c2s_send.aclose()

        async with anyio.create_task_group() as tg:
            tg.start_soon(mcp.run, c2s_recv, s2c_send, init_opts)
            tg.start_soon(ws_to_srv)
            tg.start_soon(srv_to_ws)

    # ── SSE transport (official) ─────────────────────────────
    sse = SseServerTransport(f"{base}/messages/")

    @app.get(f"{base}/sse")
    async def _mcp_sse(request: Request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send  # starlette ASGI primitives
        ) as (read_stream, write_stream):
            await mcp.run(read_stream, write_stream, init_opts)

    # client → server frames are POSTed here
    app.mount(f"{base}/messages", app=sse.handle_post_message)

    # ── schema endpoint ───────────────────────────────────────
    @app.get(f"{base}/schema")
    async def _schema_endpoint():
        return JSONResponse({
            "tools": [x.model_dump() for x in await _list_tools()],
            "resources": [x.model_dump() for x in await _list_resources()],
            "resource_templates": [x.model_dump() for x in await _list_templates()],
        })


# ── helpers ────────────────────────────────────────────────────
def _route_name(path: str) -> str:
    return re.sub(r"[/{}}]", "_", path).strip("_")

def _path_params(app: FastAPI, fn: Callable) -> List[str]:
    for r in app.routes:
        if r.endpoint is fn:
            return list(r.param_convertors.keys())
    return []
