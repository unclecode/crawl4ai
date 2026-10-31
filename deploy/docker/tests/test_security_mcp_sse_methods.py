"""
Regression test for issue #2120: a POST to the MCP SSE endpoint must be
rejected fast (405), not silently upgraded into an SSE connection.

`/mcp/sse` is mounted as a raw ASGI Route with a class-based endpoint
(`_MCPSseApp`). Starlette only defaults `methods` to `["GET"]` for
function/method endpoints; a class-based endpoint with no explicit
`methods=` matches *every* HTTP verb. Clients that probe an MCP endpoint
with a POST (e.g. attempting the Streamable HTTP transport before falling
back to legacy SSE) were routed straight into the SSE handshake instead of
getting a 405, and the request just hung until the client's own timeout —
matching the "connect via MCP from LM Studio" timeout report.

The client call runs in a daemon thread with a hard wall-clock bound: on
the buggy code the request never returns, so awaiting it inline (or via a
non-daemon executor, whose shutdown() joins the thread) would hang the test
suite forever instead of failing.
"""

import threading

import pytest

pytestmark = pytest.mark.cve

from auth import create_access_token


def test_post_to_mcp_sse_is_rejected_fast(stock_client):
    # Authenticate past the AuthGateMiddleware gate so the request actually
    # reaches routing — an unauthenticated POST would get a fast 401 from the
    # gate regardless of the route's `methods`, which would not exercise the
    # bug this test guards against.
    token = create_access_token({"sub": "user@x.com"}, scope="data")

    result = {}

    def _post():
        result["response"] = stock_client.post(
            "/mcp/sse",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            headers={"Authorization": f"Bearer {token}"},
        )

    thread = threading.Thread(target=_post, daemon=True)
    thread.start()
    thread.join(timeout=5)

    if thread.is_alive():
        pytest.fail(
            "POST /mcp/sse did not return within 5s — it was routed into "
            "the SSE handshake instead of being rejected with 405, so the "
            "connection hangs until the client's own timeout."
        )

    response = result["response"]
    assert response.status_code == 405, (
        f"POST /mcp/sse returned {response.status_code}; expected 405 "
        "(only GET should reach the SSE handshake)."
    )
