"""Monitor records end with their request, and monitor reads are admin-only.

Report 2026-11 (docker-monitor-active-leak): handle_crawl_request() started a
monitor record before validating the request, and its HTTPException and
timeout exits never ended it. Every rejected /crawl (e.g. 400 "URL blocked")
stayed in MonitorStats.active_requests forever.

Found while triaging it: every /monitor read (and /monitor/ws) was open to any
data-scope token and listed other callers' crawl URLs and error text. Reads now
need admin scope, like the monitor actions already did.

TestClient, no browser or Redis: the monitor gets an in-memory Redis stand-in.
"""

import asyncio

import pytest

from auth import create_access_token  # noqa: E402


def _bearer(scope="data") -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'}, scope=scope)}"}


class _NoRedis:
    async def set(self, *a, **kw):
        pass

    async def get(self, *a, **kw):
        return None


@pytest.fixture
def monitor(server_module, monkeypatch):
    import monitor as monitor_module

    stats = monitor_module.MonitorStats(_NoRedis())
    monkeypatch.setattr(monitor_module, "monitor_stats", stats)
    return stats


def test_blocked_crawl_does_not_stay_active(stock_client, monitor):
    for _ in range(5):
        r = stock_client.post("/crawl", headers=_bearer(), json={"urls": ["http://127.0.0.1/"]})
        assert r.status_code == 400, r.text
    assert monitor.active_requests == {}
    assert len(monitor.completed_requests) == 5
    assert {c["status_code"] for c in monitor.completed_requests} == {400}


def test_timed_out_crawl_does_not_stay_active(server_module, monitor, monkeypatch):
    import api

    async def too_slow(*a, **kw):
        raise asyncio.TimeoutError

    monkeypatch.setattr(api.asyncio, "wait_for", too_slow)

    class _Crawler:
        async def arun_many(self, *a, **kw):
            return []

        async def arun(self, *a, **kw):
            return []

    async def fake_get_crawler(cfg):
        return _Crawler()

    async def fake_release(c):
        pass

    import crawler_pool
    monkeypatch.setattr(crawler_pool, "get_crawler", fake_get_crawler)
    monkeypatch.setattr(crawler_pool, "release_crawler", fake_release)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as e:
        asyncio.run(api.handle_crawl_request(
            urls=["https://example.com"], browser_config={}, crawler_config={},
            config=server_module.config))
    assert e.value.status_code == 504
    assert monitor.active_requests == {}


@pytest.mark.parametrize("path", [
    "/monitor/requests", "/monitor/browsers", "/monitor/endpoints/stats",
    "/monitor/timeline", "/monitor/logs/janitor", "/monitor/logs/errors",
])
def test_monitor_reads_need_admin(stock_client, monitor, path):
    assert stock_client.get(path, headers=_bearer("data")).status_code == 403
    assert stock_client.get(path, headers=_bearer("admin")).status_code == 200


def test_monitor_health_stays_open_to_data_tokens(stock_client, monitor):
    assert stock_client.get("/monitor/health", headers=_bearer("data")).status_code != 403


def test_monitor_websocket_needs_admin(stock_client, monitor):
    from starlette.websockets import WebSocketDisconnect

    token = create_access_token({"sub": "u@x.com"}, scope="data")
    with pytest.raises(WebSocketDisconnect) as e:
        with stock_client.websocket_connect(f"/monitor/ws?token={token}") as ws:
            ws.receive_json()
    assert e.value.code == 4403
