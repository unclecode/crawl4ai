# deploy/docker/mcp_bridge.py

import importlib.metadata
import inspect, json, re, anyio, logging
from contextlib import suppress
from typing import Any, Callable, Dict, List, Optional, Tuple
import httpx

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.routing import Route, Mount

import mcp.types as t
from mcp.server.lowlevel.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

logger = logging.getLogger(__name__)

# ── version detection ─────────────────────────────────────────
_TRANSPORTS_AVAILABLE: Dict[str, Any] = {}


def _detect_transports():
    """Detect available MCP transports based on installed SDK version."""
    try:
        ver = importlib.metadata.version("mcp")
    except importlib.metadata.PackageNotFoundError:
        logger.error("MCP SDK not installed")
        return

    _TRANSPORTS_AVAILABLE["version"] = ver

    # SSE: available in all supported versions
    try:
        from mcp.server.sse import SseServerTransport  # noqa: F401
        _TRANSPORTS_AVAILABLE["sse"] = True
    except ImportError:
        _TRANSPORTS_AVAILABLE["sse"] = False

    # StreamableHTTP: available in >=1.20.0
    try:
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager  # noqa: F401
        _TRANSPORTS_AVAILABLE["streamable_http"] = True
    except ImportError:
        _TRANSPORTS_AVAILABLE["streamable_http"] = False

    logger.info(
        f"MCP SDK v{ver} — transports: "
        f"sse={'yes' if _TRANSPORTS_AVAILABLE.get('sse') else 'no'}, "
        f"streamable_http={'yes' if _TRANSPORTS_AVAILABLE.get('streamable_http') else 'no'}"
    )


_detect_transports()

# ── opt‑in decorators ───────────────────────────────────────────
def mcp_resource(name: Optional[str] = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "resource", name
        return fn
    return deco

def mcp_template(name: Optional[str] = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "template", name
        return fn
    return deco

def mcp_tool(name: Optional[str] = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "tool", name
        return fn
    return deco

# ── HTTP‑proxy helper for FastAPI endpoints ─────────────────────
def _make_http_proxy(base_url: str, route, *, timeout: Optional[float] = None):
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

        async with httpx.AsyncClient(timeout=timeout) as client:
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
            except httpx.TimeoutException:
                raise HTTPException(504, "upstream request timed out")
    return proxy


# ── transport attachment helpers ──────────────────────────────
def _attach_sse(app: FastAPI, mcp_server: Server, init_opts, base: str):
    """Mount SSE transport as raw ASGI routes (no middleware wrapping)."""
    from mcp.server.sse import SseServerTransport

    sse = SseServerTransport(f"{base}/messages/")

    async def _mcp_sse_handler(scope, receive, send):
        """Raw ASGI handler for SSE — avoids Starlette middleware conflict."""
        async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
            await mcp_server.run(read_stream, write_stream, init_opts)

    # Mount as raw ASGI routes (no middleware wrapping)
    app.routes.append(Route(f"{base}/sse", endpoint=_mcp_sse_handler))
    app.routes.append(Mount(f"{base}/messages", app=sse.handle_post_message))

    logger.info(f"MCP SSE endpoints: GET {base}/sse, POST {base}/messages/")


def _attach_streamable_http(app: FastAPI, mcp_server: Server, init_opts, base: str):
    """Mount StreamableHTTP transport as a single raw ASGI route."""
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        stateless=True,
    )

    async def _streamable_handler(scope, receive, send):
        await session_manager.handle_request(scope, receive, send)

    # Single unified route handles GET, POST, DELETE
    app.routes.append(
        Route(f"{base}/mcp", endpoint=_streamable_handler, methods=["GET", "POST", "DELETE"])
    )

    logger.info(f"MCP StreamableHTTP endpoint: {base}/mcp")


# ── main entry point ────────────────────────────────────────────
def attach_mcp(
    app: FastAPI,
    *,                          # keyword‑only
    base_url: str,              # eg. "http://127.0.0.1:8020"
    mcp_config: Optional[Dict] = None,
) -> None:
    """Call once after all routes are declared to expose WS+SSE MCP endpoints."""
    if mcp_config is None:
        mcp_config = {}

    if not mcp_config.get("enabled", True):
        logger.info("MCP disabled by config")
        return

    base = mcp_config.get("base_path", "/mcp")
    server_name = mcp_config.get("server_name") or app.title or "FastAPI-MCP"
    timeout = mcp_config.get("timeout")
    mcp = Server(server_name)

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

        if kind == "tool":
            proxy = _make_http_proxy(base_url, route, timeout=timeout)
            tools[key] = (proxy, fn)
            continue
        if kind == "resource":
            resources[key] = fn
        if kind == "template":
            templates[key] = fn

    # helpers for JSON‑Schema
    def _schema(model: Optional[type] = None) -> dict:
        return {"type": "object"} if model is None else model.model_json_schema()

    def _body_model(fn: Callable) -> Optional[type]:
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
    async def _call_tool(name: str, arguments: Optional[Dict] = None) -> List[t.TextContent]:
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

    # ── WebSocket transport (always on, works correctly) ──────
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

    # ── HTTP transport selection ──────────────────────────────
    transport = mcp_config.get("transport", "auto")

    if transport == "auto":
        if _TRANSPORTS_AVAILABLE.get("streamable_http"):
            transport = "streamable_http"
        elif _TRANSPORTS_AVAILABLE.get("sse"):
            transport = "sse"
        else:
            raise RuntimeError(
                f"No supported MCP transport found "
                f"(MCP SDK v{_TRANSPORTS_AVAILABLE.get('version', '?')})"
            )

    if transport == "streamable_http":
        if not _TRANSPORTS_AVAILABLE.get("streamable_http"):
            raise RuntimeError(
                f"transport='streamable_http' requires MCP SDK >=1.20.0 "
                f"(installed: {_TRANSPORTS_AVAILABLE.get('version', '?')})"
            )
        _attach_streamable_http(app, mcp, init_opts, base)
    elif transport == "sse":
        if not _TRANSPORTS_AVAILABLE.get("sse"):
            raise RuntimeError(
                f"transport='sse' requires MCP SDK with SSE support "
                f"(installed: {_TRANSPORTS_AVAILABLE.get('version', '?')})"
            )
        _attach_sse(app, mcp, init_opts, base)
    else:
        raise ValueError(
            f"Unknown MCP transport: {transport!r}. "
            f"Use 'auto', 'sse', or 'streamable_http'."
        )

    logger.info(f"MCP transport: {transport} at {base}")

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
