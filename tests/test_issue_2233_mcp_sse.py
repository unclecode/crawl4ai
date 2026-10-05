"""
Tests for issue #2233 — MCP SSE rejects concurrent requests during initialize.

Clients that POST initialize plus tools/call in the same burst hit
ServerSession before the handshake finishes and get -32602
("Received request before initialization was complete").

The WebSocket transport already gates on init_done; SSE must do the same
in mcp_bridge (not by patching the upstream MCP SDK race).
"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


BRIDGE = Path("deploy/docker/mcp_bridge.py")


def _bridge_source() -> str:
    return BRIDGE.read_text()


def _sse_app_source() -> str:
    source = _bridge_source()
    start = source.index("class _MCPSseApp")
    end = source.index("app.routes.append", start)
    return source[start:end]


class TestSSEInitGateInBridge:
    """Source-level checks that SSE uses the same init_done latch as WS."""

    def test_sse_calls_init_gate_helper(self):
        body = _sse_app_source()
        assert "_run_with_init_gate" in body
        assert "mcp.run" in body

    def test_init_gate_helper_mirrors_ws_latch(self):
        source = _bridge_source()
        assert "async def _run_with_init_gate" in source
        assert "init_done = anyio.Event()" in source
        assert "await init_done.wait()" in source
        assert "init_done.set()" in source
        # first inbound frame is forwarded before the wait (initialize)
        helper = source[source.index("async def _run_with_init_gate") :]
        wait_at = helper.index("await init_done.wait()")
        send_at = helper.index("await c2s_send.send(first)")
        assert send_at < wait_at

    def test_callable_class_pattern_preserved(self):
        """#1850: Route must still receive a class instance, not a function."""
        source = _bridge_source()
        assert "class _MCPSseApp" in source
        assert "async def __call__(self, scope, receive, send)" in source
        assert "_MCPSseApp()" in source


def _load_bridge_with_mocks():
    """Import mcp_bridge without Docker/MCP runtime deps."""
    mods = [
        "mcp",
        "mcp.types",
        "mcp.server",
        "mcp.server.sse",
        "mcp.server.lowlevel",
        "mcp.server.lowlevel.server",
        "mcp.server.models",
        "fastapi",
        "fastapi.responses",
        "starlette",
        "starlette.routing",
        "httpx",
        "pydantic",
        "auth",
    ]
    saved = {name: sys.modules.get(name) for name in mods}
    for name in mods:
        sys.modules.setdefault(name, MagicMock())

    # pydantic.BaseModel / TypeAdapter and FastAPI are only needed at
    # attach_mcp() time; module import just binds names.
    spec = importlib.util.spec_from_file_location("mcp_bridge_2233", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        for name, prev in saved.items():
            if prev is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = prev
    return module


class TestRunWithInitGate:
    """Behavioral test of the bridge latch (no live MCP server)."""

    def test_later_messages_wait_until_initialize_result(self):
        anyio = pytest.importorskip("anyio")
        bridge = _load_bridge_with_mocks()

        async def body():
            inbound_send, inbound_recv = anyio.create_memory_object_stream(100)
            outbound_send, outbound_recv = anyio.create_memory_object_stream(100)
            seen: list = []
            released = anyio.Event()

            async def fake_run(read, write, _opts):
                first = await read.receive()
                seen.append(first)
                # initialize is in flight — extra frames must not appear yet
                with anyio.move_on_after(0.05) as scope:
                    extra = await read.receive()
                assert scope.cancel_called, extra if not scope.cancel_called else None
                await write.send("initialize-result")
                released.set()
                async for msg in read:
                    seen.append(msg)
                await write.aclose()

            async def client():
                await inbound_send.send("initialize")
                await inbound_send.send("tools/call-1")
                await inbound_send.send("tools/call-2")
                await inbound_send.aclose()

            async with anyio.create_task_group() as tg:
                tg.start_soon(
                    bridge._run_with_init_gate,
                    fake_run,
                    inbound_recv,
                    outbound_send,
                    None,
                )
                tg.start_soon(client)
                result = await outbound_recv.receive()
                assert result == "initialize-result"
                await released.wait()

            assert seen[0] == "initialize"
            assert seen[1:] == ["tools/call-1", "tools/call-2"]

        anyio.run(body)
