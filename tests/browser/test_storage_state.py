"""Regression tests for BrowserConfig.storage_state across browser modes.

Prevents:
1. TypeError when passing storage_state to Playwright launch_persistent_context()
   (use_persistent_context=True) and subsequent AttributeError when get_page()
   calls create_browser_context() while self.browser is None.
2. clone_runtime_state() unpacking Playwright localStorage dicts as ("name", "value")
   and passing two positional args to page.evaluate(), raising TypeError.
3. Redundant context.storage_state(path=None) no-op IPC call in setup_context().
4. Unexpanded leading '~' in file-based storage_state paths.
"""

import asyncio
import http.server
import json
import os
import socket
import socketserver
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.browser_manager import (
    BrowserManager,
    _apply_storage_state_to_context,
    _normalize_local_storage_entries,
    _resolve_storage_state,
    clone_runtime_state,
)


# ── Unit tests (no browser required) ─────────────────────────────────────────


def test_resolve_storage_state_expands_tilde_and_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert _resolve_storage_state("~/state.json") == str(tmp_path / "state.json")
    assert _resolve_storage_state(tmp_path / "state.json") == str(tmp_path / "state.json")
    d = {"cookies": [], "origins": []}
    assert _resolve_storage_state(d) is d
    assert _resolve_storage_state(None) is None


def test_normalize_local_storage_entries_handles_dicts_and_tuples():
    raw = [
        {"name": "jwt", "value": "tok_123"},
        ("workspace", "eng"),
        {"bad": "entry"},
        "ignored",
    ]
    assert _normalize_local_storage_entries(raw) == [
        ["jwt", "tok_123"],
        ["workspace", "eng"],
    ]


@pytest.mark.asyncio
async def test_clone_runtime_state_preserves_dict_local_storage_and_single_evaluate_arg():
    """Playwright storage_state() returns origins[].localStorage as [{name, value}]."""
    src = AsyncMock()
    src.cookies.return_value = [
        {"name": "sid", "value": "abc", "domain": "127.0.0.1", "path": "/"}
    ]
    src.storage_state.return_value = {
        "cookies": [],
        "origins": [
            {
                "origin": "https://app.example.com",
                "localStorage": [
                    {"name": "jwt_token", "value": "eyJ_real"},
                    {"name": "theme", "value": "dark"},
                ],
            },
            {
                "origin": "file:///etc/passwd",
                "localStorage": [{"name": "bad", "value": "ignored"}],
            },
        ],
    }

    evaluated = []

    class FakePage:
        def __init__(self):
            self.closed = False
            self.routed = []
            self.unrouted = []
            self.gotos = []

        async def route(self, url, handler):
            self.routed.append(url)

        async def unroute(self, url, handler):
            self.unrouted.append(url)

        async def goto(self, url, wait_until=None):
            self.gotos.append((url, wait_until))

        async def evaluate(self, expression, arg=None):
            # Enforces Playwright Python's single-arg signature (never 2 positional args).
            evaluated.append((expression, arg))

        async def close(self):
            self.closed = True

    fake_page = FakePage()
    dst = AsyncMock()
    dst.new_page.return_value = fake_page

    result = await clone_runtime_state(src, dst)
    assert result is dst
    dst.add_cookies.assert_awaited_once()
    assert fake_page.closed is True
    # Only https://app.example.com was hydrated (file:// skipped).
    assert fake_page.routed == ["https://app.example.com/__crawl4ai_storage_init__"]
    assert fake_page.unrouted == ["https://app.example.com/__crawl4ai_storage_init__"]
    assert len(evaluated) == 1
    _, arg = evaluated[0]
    assert arg == [
        "https://app.example.com",
        [["jwt_token", "eyJ_real"], ["theme", "dark"]],
    ]


@pytest.mark.asyncio
async def test_setup_context_does_not_call_noop_storage_state_read():
    cfg = BrowserConfig(headless=True, storage_state={"cookies": [], "origins": []})
    mgr = BrowserManager(browser_config=cfg)
    ctx = AsyncMock()
    await mgr.setup_context(ctx)
    ctx.storage_state.assert_not_called()


# ── Loopback live Playwright integration tests ───────────────────────────────


class _AuthEchoHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        cookie_hdr = self.headers.get("Cookie", "")
        mutate_js = (
            "localStorage.setItem('jwt_token', 'eyJ_mutated_by_page');"
            if self.path == "/mutate"
            else ""
        )
        html = f"""<!doctype html>
<html>
<head><title>Auth Echo</title></head>
<body>
  <p id="c">COOKIE:{cookie_hdr}</p>
  <p id="ls">LS:PENDING</p>
  <script>
    {mutate_js}
    document.getElementById('ls').textContent =
      'LS:' + (localStorage.getItem('jwt_token') || 'MISSING') +
      '|WS:' + (localStorage.getItem('workspace') || 'MISSING');
  </script>
</body>
</html>
"""
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture(scope="module")
def auth_echo_server():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), _AuthEchoHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def _sample_state(origin: str) -> dict:
    return {
        "cookies": [
            {
                "name": "sid",
                "value": "httponly_cookie_val",
                "domain": "127.0.0.1",
                "path": "/",
                "expires": 1999999999,
                "httpOnly": True,
                "secure": False,
                "sameSite": "Lax",
            }
        ],
        "origins": [
            {
                "origin": origin,
                "localStorage": [
                    {"name": "jwt_token", "value": "eyJ_initial_jwt"},
                    {"name": "workspace", "value": "acme-eng"},
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_dedicated_storage_state_expands_tilde_path(auth_echo_server, tmp_path, monkeypatch):
    state_file = tmp_path / "forked-state.json"
    state_file.write_text(json.dumps(_sample_state(auth_echo_server)), encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))

    cfg = BrowserConfig(headless=True, verbose=False, storage_state="~/forked-state.json")
    async with AsyncWebCrawler(config=cfg) as crawler:
        res = await crawler.arun(
            url=f"{auth_echo_server}/check",
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
    assert res.success, res.error_message
    md = res.markdown.raw_markdown
    assert "COOKIE:sid=httponly_cookie_val" in md
    assert "LS:eyJ_initial_jwt|WS:acme-eng" in md


@pytest.mark.asyncio
async def test_persistent_context_with_storage_state_hydrates_once_without_crashing(
    auth_echo_server, tmp_path
):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(_sample_state(auth_echo_server)), encoding="utf-8")
    profile_dir = tmp_path / "persistent-profile"

    cfg = BrowserConfig(
        headless=True,
        verbose=False,
        use_persistent_context=True,
        user_data_dir=str(profile_dir),
        storage_state=str(state_file),
    )
    async with AsyncWebCrawler(config=cfg) as crawler:
        res1 = await crawler.arun(
            url=f"{auth_echo_server}/check",
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        assert res1.success, res1.error_message
        assert "COOKIE:sid=httponly_cookie_val" in res1.markdown.raw_markdown
        assert "LS:eyJ_initial_jwt|WS:acme-eng" in res1.markdown.raw_markdown

        # Mutate localStorage via page JS, then crawl again — storage_state must
        # NOT be re-applied and clobber the runtime mutation.
        res2 = await crawler.arun(
            url=f"{auth_echo_server}/mutate",
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        assert res2.success, res2.error_message
        assert "LS:eyJ_mutated_by_page|WS:acme-eng" in res2.markdown.raw_markdown

        res3 = await crawler.arun(
            url=f"{auth_echo_server}/check",
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        assert res3.success, res3.error_message
        assert "LS:eyJ_mutated_by_page|WS:acme-eng" in res3.markdown.raw_markdown


@pytest.mark.asyncio
async def test_cdp_url_with_storage_state_hydrates_cookies_and_local_storage(
    auth_echo_server, tmp_path
):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        exec_path = p.chromium.executable_path
        if not os.path.exists(exec_path):
            # Walk up to ms-playwright cache root to locate headless shell on macOS/Linux
            cache_root = Path(
                os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or ""
            )
            if not cache_root.is_dir():
                for parent in Path(exec_path).parents:
                    if parent.name == "ms-playwright":
                        cache_root = parent
                        break
            shells = (
                sorted(cache_root.glob("chromium_headless_shell-*/**/chrome-headless-shell"))
                if cache_root.is_dir()
                else []
            )
            if not shells:
                pytest.skip("No Playwright Chromium binary installed for CDP test")
            exec_path = str(shells[-1])

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    cdp_port = sock.getsockname()[1]
    sock.close()

    state_file = tmp_path / "cdp-state.json"
    state_file.write_text(json.dumps(_sample_state(auth_echo_server)), encoding="utf-8")
    user_data = tmp_path / "cdp-ud"

    proc = subprocess.Popen(
        [
            exec_path,
            f"--remote-debugging-port={cdp_port}",
            f"--user-data-dir={user_data}",
            "--no-first-run",
            "--headless",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json/version", timeout=0.5)
                break
            except Exception:
                time.sleep(0.1)

        cfg = BrowserConfig(
            headless=True,
            verbose=False,
            cdp_url=f"http://127.0.0.1:{cdp_port}",
            storage_state=str(state_file),
        )
        async with AsyncWebCrawler(config=cfg) as crawler:
            res = await crawler.arun(
                url=f"{auth_echo_server}/check",
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
            )
            assert res.success, res.error_message
            assert "COOKIE:sid=httponly_cookie_val" in res.markdown.raw_markdown
            assert "LS:eyJ_initial_jwt|WS:acme-eng" in res.markdown.raw_markdown
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
