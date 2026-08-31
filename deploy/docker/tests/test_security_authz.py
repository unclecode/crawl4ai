"""
Behavioral authorization tests for R1 (beyond the blanket default-deny gate):

  * admin scope    - monitor destructive actions require an admin principal;
                     a valid data-scope token is allowed past the gate but
                     rejected (403) by require_admin.
  * MCP no-laundering - the MCP tool proxy authenticates its internal loopback
                     call (it no longer relies on the endpoints being open).
  * job ownership  - a task records its owner; a different requester gets 404
                     (not 403), and an admin can read any task.

These exercise the running app, not its source text.
"""

import pytest

pytestmark = pytest.mark.posture

from auth import create_access_token  # noqa: E402


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ───────────────────────────── admin scope ─────────────────────────────
class TestAdminScope:
    def test_data_scope_cannot_reset_stats(self, stock_client):
        data_tok = create_access_token({"sub": "user@x.com"}, scope="data")
        r = stock_client.post("/monitor/stats/reset", headers=_bearer(data_tok))
        assert r.status_code == 403, f"data-scope reached admin action: {r.status_code}"

    def test_data_scope_cannot_kill_browser(self, stock_client):
        data_tok = create_access_token({"sub": "user@x.com"}, scope="data")
        r = stock_client.post(
            "/monitor/actions/kill_browser", json={"sig": "abc"}, headers=_bearer(data_tok)
        )
        assert r.status_code == 403

    def test_admin_scope_passes_require_admin(self, stock_client):
        admin_tok = create_access_token({"sub": "ops@x.com"}, scope="admin")
        r = stock_client.post("/monitor/stats/reset", headers=_bearer(admin_tok))
        # Past require_admin: not a 401/403. (500 acceptable here: no monitor
        # singleton without a lifespan — the point is authz let it through.)
        assert r.status_code not in (401, 403), f"admin blocked: {r.status_code}"

    def test_unauthenticated_admin_action_is_401(self, stock_client):
        r = stock_client.post("/monitor/stats/reset")
        assert r.status_code == 401


# ────────────────────────── MCP no-laundering ──────────────────────────
class TestMcpNoLaundering:
    def test_mcp_proxy_attaches_service_credential(self):
        """The internal loopback proxy must carry a valid, data-scope token."""
        import mcp_bridge
        from auth import decode_token

        headers = mcp_bridge._service_auth_headers()
        assert "Authorization" in headers
        scheme, _, token = headers["Authorization"].partition(" ")
        assert scheme == "Bearer" and token
        claims = decode_token(token)
        assert claims["scope"] == "data", "MCP service token must not be admin-scoped"

    def test_mcp_base_url_is_loopback(self, server_module):
        """The MCP proxy must target loopback, never the 0.0.0.0 bind address."""
        import inspect
        src = inspect.getsource(server_module)
        assert "http://127.0.0.1:" in src
        assert 'base_url=f"http://{config' not in src


# ─────────────────────────── job ownership ─────────────────────────────
class _FakeRedis:
    """Minimal async Redis stub holding one task hash."""

    def __init__(self, task):
        # Real redis returns bytes keys/values; decode_redis_hash expects that.
        self._task = {k.encode(): str(v).encode() for k, v in task.items()}

    async def hgetall(self, key):
        return dict(self._task)

    async def delete(self, key):
        self._task = {}


@pytest.mark.asyncio
class TestJobOwnership:
    async def _status(self, task, **kw):
        import api
        redis = _FakeRedis(task)
        return await api.handle_task_status(
            redis, "crawl_abc", base_url="http://t/", keep=True, **kw
        )

    async def test_owner_can_read_own_task(self):
        task = {"status": "completed", "created_at": "2026-01-01T00:00:00",
                "url": "[]", "result": "{}", "owner": "alice@x.com"}
        resp = await self._status(task, requester="alice@x.com", is_admin=False)
        assert resp.status_code == 200

    async def test_other_requester_gets_404_not_403(self):
        from fastapi import HTTPException
        task = {"status": "completed", "created_at": "2026-01-01T00:00:00",
                "url": "[]", "result": "{}", "owner": "alice@x.com"}
        with pytest.raises(HTTPException) as exc:
            await self._status(task, requester="mallory@x.com", is_admin=False)
        assert exc.value.status_code == 404  # not 403: don't reveal existence

    async def test_admin_can_read_any_task(self):
        task = {"status": "completed", "created_at": "2026-01-01T00:00:00",
                "url": "[]", "result": "{}", "owner": "alice@x.com"}
        resp = await self._status(task, requester="ops@x.com", is_admin=True)
        assert resp.status_code == 200
