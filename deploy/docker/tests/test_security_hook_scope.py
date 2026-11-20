"""Declarative hooks apply only to the request that sent them.

Report 2026-11 (docker-hook-retention): _attach_declarative_hooks() called
set_hook() on the pooled, shared crawler strategy and nothing removed the
hooks, so a later caller's crawl, sent with no hooks, still ran the earlier
caller's set_headers / add_cookies and carried their Authorization header and
session cookie to whatever URL the later caller chose.

Real server in a subprocess with CRAWL4AI_HOOKS_ENABLED=true, real Chromium,
two JWT callers, a local site that echoes the Authorization and Cookie headers.
Needs Redis on 127.0.0.1:6379 (skipped otherwise).
"""

import os
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DOCKER_DIR.parents[1]
_FILL = "<p>" + "This page exists to test that hooks stay with their request. " * 20 + "</p>"


class _Site(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (f"<html><body><p>AUTH[{self.headers.get('Authorization') or ''}]</p>"
                f"<p>COOKIE[{self.headers.get('Cookie') or ''}]</p>{_FILL}</body></html>")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
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

    secret = "e2e-hook-scope-" + "k" * 32
    port = _free_port()
    env = dict(os.environ, SECRET_KEY=secret, CRAWL4AI_ALLOW_INTERNAL_URLS="true",
               CRAWL4AI_HOOKS_ENABLED="true", PYTHONPATH=str(REPO_ROOT),
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


def _hooks(secret):
    return {"hooks": [
        {"action": "set_headers", "params": {"headers": {"Authorization": f"Bearer {secret}"}}},
        {"action": "add_cookies", "params": {"cookies": [
            {"name": "session", "value": secret, "domain": "127.0.0.1", "secure": False}]}},
    ]}


def _body(live, path, hooks=None):
    body = {"urls": [f"{live['site']}{path}"],
            "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "bypass"}}}
    if hooks:
        body["hooks"] = hooks
    return body


def _crawl(live, sub, path, hooks=None):
    import httpx

    r = httpx.post(f"{live['base']}/crawl", json=_body(live, path, hooks), timeout=120,
                   headers={"Authorization": f"Bearer {live['token'](sub)}"})
    assert r.status_code == 200, r.text[:500]
    res = r.json()["results"][0]
    assert res["success"], res.get("error_message")
    return res["html"]


def _crawl_stream(live, sub, path, hooks=None):
    import json

    import httpx

    html = ""
    with httpx.stream("POST", f"{live['base']}/crawl/stream", json=_body(live, path, hooks), timeout=120,
                      headers={"Authorization": f"Bearer {live['token'](sub)}"}) as r:
        assert r.status_code == 200, r.read()[:500]
        for line in r.iter_lines():
            if line.strip():
                item = json.loads(line)
                html += item.get("html") or ""
    return html


def test_later_caller_does_not_run_earlier_callers_hooks(live):
    own = _crawl(live, "alice@example.com", "/alice", _hooks("ALICE-SYNC"))
    other = _crawl(live, "mallory@example.com", "/mallory")
    assert "AUTH[Bearer ALICE-SYNC]" in own and "session=ALICE-SYNC" in own  # probe works
    assert "ALICE-SYNC" not in other


def test_hookless_request_after_a_hooked_one_runs_no_hooks(live):
    _crawl(live, "carol@example.com", "/one", _hooks("CAROL-AGAIN"))
    again = _crawl(live, "carol2@example.com", "/two")
    assert "CAROL-AGAIN" not in again


def test_stream_does_not_carry_hooks(live):
    own = _crawl_stream(live, "alice3@example.com", "/alice", _hooks("ALICE-STREAM"))
    other = _crawl_stream(live, "mallory3@example.com", "/mallory")
    sync_other = _crawl(live, "mallory3@example.com", "/mallory-sync")
    assert "AUTH[Bearer ALICE-STREAM]" in own
    assert "ALICE-STREAM" not in other and "ALICE-STREAM" not in sync_other


def test_concurrent_callers_keep_their_own_hooks(live):
    def run(i):
        if i % 2:
            return i, _crawl(live, f"hooked{i}@example.com", f"/h{i}", _hooks(f"SECRET-{i}"))
        return i, _crawl(live, f"plain{i}@example.com", f"/p{i}")

    with ThreadPoolExecutor(6) as pool:
        results = dict(pool.map(run, range(6)))
    for i, html in results.items():
        if i % 2:
            assert f"AUTH[Bearer SECRET-{i}]" in html
            assert all(f"SECRET-{j}" not in html for j in results if j != i)
        else:
            assert "SECRET-" not in html
