"""API callers never share a pooled browser context.

Report 2026-10 (docker-shared-browser-context, arpe1618): the pool and the
BrowserManager context cache were keyed by config only, so two callers with
the same (often empty) config ran in one Chromium context and saw each other's
cookies, storage and service workers.

The fix sets crawl4ai.browser_manager.browser_context_partition to the
caller's JWT sub in AuthGateMiddleware, carries it into queued jobs and MCP
loopback calls, and keys the context cache by it. These tests attack each of
those links, then run the real server end to end.
"""

import asyncio
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DOCKER_DIR.parents[1]
if str(DOCKER_DIR) not in sys.path:
    sys.path.insert(0, str(DOCKER_DIR))

from crawl4ai.browser_manager import browser_context_partition  # noqa: E402


# ── auth gate: the partition is the authenticated sub, per request ─────────


def _gate(recorded, delay=0.0):
    from auth_gate import AuthGateMiddleware

    async def app(scope, receive, send):
        await asyncio.sleep(delay)  # let concurrent requests interleave
        recorded.append((scope["path"], browser_context_partition.get()))
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    return AuthGateMiddleware(app, token_provider=lambda: "op-static-token-0123456789")


async def _call(gate, path, token=None, extra_headers=()):
    headers = [(k.encode(), v.encode()) for k, v in extra_headers]
    if token:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    scope = {"type": "http", "path": path, "headers": headers, "query_string": b""}
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        sent.append(msg)

    await gate(scope, receive, send)
    return sent[0]["status"]


def _jwt(sub, **extra):
    from auth import create_access_token

    data = {"sub": sub} if sub is not None else {}
    data.update(extra)
    return create_access_token(data)


def test_gate_sets_the_callers_sub_and_resets_it():
    rec = []
    gate = _gate(rec)

    async def run():
        await _call(gate, "/crawl", _jwt("alice@example.com"))
        await _call(gate, "/crawl", _jwt("mallory@example.com"))
        await _call(gate, "/crawl", "op-static-token-0123456789")
        return browser_context_partition.get()

    after = asyncio.run(run())
    assert [p for _, p in rec] == ["alice@example.com", "mallory@example.com", "operator"]
    assert after is None  # nothing leaks out of the request


def test_concurrent_requests_keep_their_own_partition():
    rec = []
    gate = _gate(rec, delay=0.01)
    subs = [f"user{i}@example.com" for i in range(30)]

    async def run():
        await asyncio.gather(*(_call(gate, f"/crawl/{s}", _jwt(s)) for s in subs))

    asyncio.run(run())
    assert len(rec) == len(subs)
    for path, partition in rec:
        assert path == f"/crawl/{partition}"


def test_caller_cannot_choose_the_partition_with_headers_or_claims():
    rec = []
    gate = _gate(rec)
    forged = [("x-partition", "victim@example.com"), ("x-forwarded-user", "victim@example.com")]

    async def run():
        # Extra claims ride along in the JWT, but only sub is used.
        await _call(gate, "/crawl", _jwt("mallory@example.com", partition="victim@example.com"), forged)

    asyncio.run(run())
    assert rec == [("/crawl", "mallory@example.com")]


def test_token_without_sub_gets_a_fresh_partition_each_time():
    rec = []
    gate = _gate(rec)

    async def run():
        await _call(gate, "/crawl", _jwt(None))
        await _call(gate, "/crawl", _jwt(None))

    asyncio.run(run())
    (_, a), (_, b) = rec
    assert a and b and a != b
    assert a.startswith("anonymous-") and b.startswith("anonymous-")


def test_rejected_and_forged_tokens_never_reach_the_app():
    rec = []
    gate = _gate(rec)
    import jwt as pyjwt

    forged = pyjwt.encode({"sub": "victim@example.com", "scope": "data"}, "x" * 40, algorithm="HS256")

    async def run():
        return [await _call(gate, "/crawl"), await _call(gate, "/crawl", forged)]

    assert asyncio.run(run()) == [401, 401]
    assert rec == []


# ── work queue: a job runs in the submitting caller's partition ───────────


def test_queued_jobs_run_in_the_submitters_partition():
    from work_queue import WorkQueue

    seen = []

    def job(tag):
        async def run():
            seen.append((tag, browser_context_partition.get()))
            # A job that sets the var must not leak it into the next job.
            browser_context_partition.set("set-inside-job")
        return run

    async def run():
        q = WorkQueue(workers=1)
        await q.start()  # worker created with no partition, like server boot
        try:
            for tag, sub in [("a1", "alice"), ("m1", "mallory"), ("a2", "alice"), ("n", None)]:
                token = browser_context_partition.set(sub)
                try:
                    q.submit(job(tag), sub)
                finally:
                    browser_context_partition.reset(token)
            await q._q.join()
        finally:
            await q.stop()

    asyncio.run(run())
    assert seen == [("a1", "alice"), ("m1", "mallory"), ("a2", "alice"), ("n", None)]


def test_enqueue_job_carries_the_partition_through_api():
    import api
    import work_queue

    seen = []

    async def factory():
        seen.append(browser_context_partition.get())

    async def run():
        q = work_queue.WorkQueue(workers=1)
        await q.start()
        work_queue.set_job_queue(q)
        try:
            token = browser_context_partition.set("alice@example.com")
            try:
                api._enqueue_job(None, factory, principal="alice@example.com")
            finally:
                browser_context_partition.reset(token)
            await q._q.join()
        finally:
            work_queue.set_job_queue(None)
            await q.stop()

    asyncio.run(run())
    assert seen == ["alice@example.com"]


# ── MCP: the loopback call carries the MCP caller, not one shared sub ──────


def test_mcp_loopback_token_carries_the_caller():
    from auth import decode_token
    from mcp_bridge import _service_auth_headers

    def sub_for(partition):
        token = browser_context_partition.set(partition)
        try:
            bearer = _service_auth_headers()["Authorization"].split(" ", 1)[1]
        finally:
            browser_context_partition.reset(token)
        return decode_token(bearer)

    alice, mallory = sub_for("alice@example.com"), sub_for("mallory@example.com")
    assert alice["sub"] == "alice@example.com" and alice["scope"] == "data"
    assert mallory["sub"] == "mallory@example.com"
    assert sub_for(None)["sub"] == "mcp-service"
    # The caller's admin rights are not carried: the loopback token is data scope.
    assert sub_for("operator")["scope"] == "data"


# ── request body: no way into a shared or managed context ─────────────────


@pytest.mark.parametrize("mode", ["builtin", "docker", "custom", "Builtin", " dedicated", "", None, 1])
def test_untrusted_browser_mode_other_than_dedicated_is_refused(mode):
    from crawl4ai.async_configs import BrowserConfig, Provenance, UntrustedConfigError

    with pytest.raises(UntrustedConfigError):
        BrowserConfig.load(
            {"type": "BrowserConfig", "params": {"browser_mode": mode}},
            provenance=Provenance.UNTRUSTED,
        )


def test_untrusted_body_cannot_reach_managed_or_persistent_mode():
    from crawl4ai.async_configs import (
        BrowserConfig, CrawlerRunConfig, Provenance, UntrustedConfigError,
    )

    for field, value in (("user_data_dir", "/tmp/x"), ("cdp_url", "http://127.0.0.1:9222")):
        with pytest.raises(UntrustedConfigError):
            BrowserConfig.load({"type": "BrowserConfig", "params": {field: value}},
                               provenance=Provenance.UNTRUSTED)

    bc = BrowserConfig.load(
        {"type": "BrowserConfig", "params": {
            "browser_mode": "dedicated", "use_managed_browser": True,
            "use_persistent_context": True, "create_isolated_context": False,
        }},
        provenance=Provenance.UNTRUSTED,
    )
    assert bc.use_managed_browser is False
    assert bc.use_persistent_context is False
    assert not bc.cdp_url

    rc = CrawlerRunConfig.load(
        {"type": "CrawlerRunConfig", "params": {
            "_partition": "victim", "partition": "victim",
            "browser_context_partition": "victim",
        }},
        provenance=Provenance.UNTRUSTED,
    )
    assert not any(hasattr(rc, f) for f in ("_partition", "partition", "browser_context_partition"))


# ── end to end: the real server, two JWTs, one pooled browser ─────────────

_FILL = "<p>" + "This page exists to test browser context isolation. " * 20 + "</p>"


class _Site(BaseHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        if path == "/set":
            self.send_header("Set-Cookie", f"secret={params.get('v', '')}; Path=/")
            body = f"<html><body><p>set</p>{_FILL}<script>localStorage.setItem('secret','{params.get('v', '')}')</script></body></html>"
        else:
            body = (f"<html><body><p>COOKIE[{self.headers.get('Cookie') or ''}]</p><p id=l></p>{_FILL}"
                    "<script>document.getElementById('l').textContent='LS['+(localStorage.getItem('secret')||'')+']'</script></body></html>")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _redis_up():
    try:
        with socket.create_connection(("127.0.0.1", 6379), timeout=1):
            return True
    except OSError:
        return False


_SERVER = """
import sys
sys.path[:0] = [{root!r}, {docker!r}]
import crawler_pool
crawler_pool.MEM_LIMIT = 101  # a busy dev machine must not refuse the browser
import uvicorn, server
uvicorn.run(server.app, host="127.0.0.1", port={port}, log_level="warning")
"""


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    if not _redis_up():
        pytest.skip("needs Redis on 127.0.0.1:6379")
    site = ThreadingHTTPServer(("127.0.0.1", 0), _Site)
    threading.Thread(target=site.serve_forever, daemon=True).start()

    secret = "e2e-context-partition-" + "k" * 32
    port = _free_port()
    env = dict(os.environ, SECRET_KEY=secret, CRAWL4AI_ALLOW_INTERNAL_URLS="true",
               PYTHONPATH=str(REPO_ROOT),
               CRAWL4AI_ARTIFACT_DIR=str(tmp_path_factory.mktemp("artifacts")))
    proc = subprocess.Popen(
        [sys.executable, "-c", _SERVER.format(root=str(REPO_ROOT), docker=str(DOCKER_DIR), port=port)],
        cwd=str(DOCKER_DIR), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    import httpx

    base = f"http://127.0.0.1:{port}"
    for _ in range(120):
        try:
            if httpx.get(f"{base}/health", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            pass
        if proc.poll() is not None:
            pytest.fail("server exited:\n" + proc.stdout.read().decode(errors="replace")[-3000:])
        time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("server did not start")

    import jwt as pyjwt

    def token(sub):
        exp = int(time.time()) + 600
        return pyjwt.encode({"sub": sub, "scope": "data", "exp": exp}, secret, algorithm="HS256")

    yield {"base": base, "site": f"http://127.0.0.1:{site.server_port}", "token": token}
    proc.terminate()
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    site.shutdown()


def _crawl(live, sub, path):
    import httpx

    r = httpx.post(
        f"{live['base']}/crawl",
        headers={"Authorization": f"Bearer {live['token'](sub)}"},
        json={"urls": [f"{live['site']}{path}"],
              "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "bypass"}}},
        timeout=120,
    )
    assert r.status_code == 200, r.text[:500]
    res = r.json()["results"][0]
    assert res["success"], res.get("error_message")
    return res["html"]


def _crawl_job(live, sub, path):
    import httpx

    h = {"Authorization": f"Bearer {live['token'](sub)}"}
    r = httpx.post(f"{live['base']}/crawl/job", headers=h, timeout=30, json={
        "urls": [f"{live['site']}{path}"],
        "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "bypass"}}})
    assert r.status_code == 202, r.text[:500]
    task_id = r.json()["task_id"]
    for _ in range(240):
        s = httpx.get(f"{live['base']}/crawl/job/{task_id}", headers=h, timeout=30).json()
        if s["status"] in ("completed", "failed"):
            assert s["status"] == "completed", s
            return s["result"]["results"][0]["html"]
        time.sleep(0.5)
    pytest.fail("job did not finish")


def test_e2e_crawl_does_not_carry_another_callers_state(live):
    _crawl(live, "alice@example.com", "/set?v=ALICE-E2E")
    own = _crawl(live, "alice@example.com", "/echo")
    other = _crawl(live, "mallory@example.com", "/echo")
    assert "secret=ALICE-E2E" in own and "LS[ALICE-E2E]" in own  # probe works
    assert "ALICE-E2E" not in other


def test_e2e_job_queue_does_not_carry_another_callers_state(live):
    _crawl_job(live, "alice2@example.com", "/set?v=ALICE-JOB")
    own = _crawl_job(live, "alice2@example.com", "/echo")
    other = _crawl_job(live, "mallory2@example.com", "/echo")
    sync_other = _crawl(live, "mallory2@example.com", "/echo")
    assert "secret=ALICE-JOB" in own
    assert "ALICE-JOB" not in other and "ALICE-JOB" not in sync_other


def test_e2e_concurrent_callers_stay_apart(live):
    from concurrent.futures import ThreadPoolExecutor

    subs = [f"c{i}@example.com" for i in range(6)]
    with ThreadPoolExecutor(len(subs)) as ex:
        list(ex.map(lambda i: _crawl(live, subs[i], f"/set?v=C{i}X"), range(len(subs))))
        pages = list(ex.map(lambda s: _crawl(live, s, "/echo"), subs))
    for i, html in enumerate(pages):
        assert f"secret=C{i}X" in html
        assert not any(f"C{j}X" in html for j in range(len(subs)) if j != i)
