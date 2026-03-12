"""
Tests for #1678: MCP WebSocket SessionMessage wrapping.

The mcp SDK >=1.18.0 expects SessionMessage wrappers around JSONRPCMessage.
The WebSocket transport must wrap incoming messages and unwrap outgoing ones.
"""

import pytest
from pydantic import TypeAdapter
from mcp.types import JSONRPCMessage
from mcp.shared.message import SessionMessage


@pytest.fixture
def adapter():
    return TypeAdapter(JSONRPCMessage)


# ── import / availability ─────────────────────────────────────


def test_session_message_importable():
    """SessionMessage must be importable from mcp.shared.message."""
    assert SessionMessage is not None


def test_session_message_has_message_attr():
    """SessionMessage instances must expose a .message attribute."""
    adapter = TypeAdapter(JSONRPCMessage)
    raw = {"jsonrpc": "2.0", "method": "ping", "id": 1}
    msg = SessionMessage(message=adapter.validate_python(raw))
    assert hasattr(msg, "message")


# ── wrapping (client → server) ────────────────────────────────


def test_wrap_initialize_request(adapter):
    """'initialize' request should be wrappable in SessionMessage."""
    raw = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1,
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "0.1"}},
    }
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)
    assert isinstance(session_msg, SessionMessage)
    assert session_msg.message is json_msg


def test_wrap_notification(adapter):
    """Notifications (no id) should be wrappable."""
    raw = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)
    assert session_msg.message is json_msg


def test_wrap_tool_call(adapter):
    """Tool call requests should be wrappable."""
    raw = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 42,
        "params": {"name": "md", "arguments": {"url": "https://example.com"}},
    }
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)
    assert session_msg.message is json_msg


def test_wrap_preserves_jsonrpc_fields(adapter):
    """Wrapping should not alter the original JSONRPCMessage content."""
    raw = {"jsonrpc": "2.0", "method": "resources/list", "id": 7}
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)
    dumped = session_msg.message.model_dump()
    assert dumped["jsonrpc"] == "2.0"


def test_wrap_multiple_messages_independent(adapter):
    """Each message gets its own SessionMessage wrapper."""
    msgs = [
        {"jsonrpc": "2.0", "method": "ping", "id": i}
        for i in range(5)
    ]
    wrapped = [SessionMessage(message=adapter.validate_python(m)) for m in msgs]
    assert len(set(id(w) for w in wrapped)) == 5  # all distinct objects


# ── unwrapping (server → client) ──────────────────────────────


def test_unwrap_session_message(adapter):
    """Unwrapping SessionMessage should yield the original JSONRPCMessage."""
    raw = {"jsonrpc": "2.0", "method": "ping", "id": 2}
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)

    # Simulate srv_to_ws unwrap logic
    unwrapped = session_msg.message if isinstance(session_msg, SessionMessage) else session_msg
    assert unwrapped is json_msg


def test_unwrap_serializable(adapter):
    """Unwrapped message should be JSON-serializable via model_dump."""
    raw = {"jsonrpc": "2.0", "result": {"tools": []}, "id": 3}
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)
    unwrapped = session_msg.message if isinstance(session_msg, SessionMessage) else session_msg
    dumped = unwrapped.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["jsonrpc"] == "2.0"


def test_passthrough_raw_jsonrpc(adapter):
    """If msg is already a raw JSONRPCMessage (backward compat), passthrough works."""
    raw = {"jsonrpc": "2.0", "method": "test", "id": 3}
    json_msg = adapter.validate_python(raw)

    result = json_msg.message if isinstance(json_msg, SessionMessage) else json_msg
    assert result is json_msg


# ── round-trip ────────────────────────────────────────────────


def test_round_trip_wrap_unwrap(adapter):
    """Wrap then unwrap should return the original message."""
    raw = {"jsonrpc": "2.0", "method": "tools/list", "id": 10}
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)
    unwrapped = session_msg.message
    assert unwrapped is json_msg
    assert unwrapped.model_dump() == json_msg.model_dump()


def test_round_trip_preserves_params(adapter):
    """Complex params survive wrap/unwrap."""
    raw = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 99,
        "params": {
            "name": "md",
            "arguments": {"url": "https://example.com", "f": "llm", "q": "summarize"},
        },
    }
    json_msg = adapter.validate_python(raw)
    session_msg = SessionMessage(message=json_msg)
    dumped = session_msg.message.model_dump()
    assert dumped["params"]["name"] == "md"
    assert dumped["params"]["arguments"]["url"] == "https://example.com"
