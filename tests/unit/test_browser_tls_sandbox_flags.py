"""TLS verification and Chromium sandbox launch flags.

ignore_https_errors=False must really verify certificates. A launch flag like
--ignore-certificate-errors turns verification off for the whole browser, so
the context option would have no effect. The end-to-end tests crawl a local
HTTPS server with a self-signed certificate on every launch path.

CRAWL4AI_CHROMIUM_SANDBOX=true must run Chromium with its sandbox on.
"""

import asyncio
import http.server
import secrets
import ssl
import subprocess
import threading

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.browser_manager import BrowserManager, ManagedBrowser

CERT_FLAGS = ("--ignore-certificate-errors", "--ignore-certificate-errors-spki-list")


def _has_cert_flag(args):
    return any(a.split("=", 1)[0] in CERT_FLAGS for a in args)


# ── launch flag construction (no browser) ──────────────────────────────


@pytest.mark.parametrize("ignore", [True, False])
def test_build_browser_args_has_no_cert_flag(ignore):
    bc = BrowserConfig(headless=True, ignore_https_errors=ignore)
    assert not _has_cert_flag(BrowserManager(browser_config=bc)._build_browser_args()["args"])


@pytest.mark.parametrize("ignore", [True, False])
def test_build_browser_flags_has_no_cert_flag(ignore):
    bc = BrowserConfig(headless=True, ignore_https_errors=ignore)
    assert not _has_cert_flag(ManagedBrowser.build_browser_flags(bc))


@pytest.mark.parametrize("ignore", [True, False])
def test_managed_subprocess_cert_flag_follows_config(ignore, monkeypatch):
    """The CDP default context has no ignore_https_errors option, so the
    subprocess launch carries the flag only when the config asks for it."""
    bc = BrowserConfig(headless=True, ignore_https_errors=ignore)
    mb = ManagedBrowser(browser_type="chromium", headless=True, browser_config=bc)

    async def fake_path():
        return "chromium"

    monkeypatch.setattr(mb, "_get_browser_path", fake_path)
    args = asyncio.run(mb._get_browser_args())
    assert _has_cert_flag(args) is ignore


def test_sandbox_off_by_default(monkeypatch):
    monkeypatch.delenv("CRAWL4AI_CHROMIUM_SANDBOX", raising=False)
    bc = BrowserConfig(headless=True)
    launch = BrowserManager(browser_config=bc)._build_browser_args()
    assert "--no-sandbox" in launch["args"]
    assert not launch.get("chromium_sandbox")
    assert "--no-sandbox" in ManagedBrowser.build_browser_flags(bc)


def test_sandbox_requested_by_env(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_CHROMIUM_SANDBOX", "true")
    bc = BrowserConfig(headless=True, extra_args=["--no-sandbox", "--disable-gpu"])
    launch = BrowserManager(browser_config=bc)._build_browser_args()
    assert "--no-sandbox" not in launch["args"]
    assert "--disable-gpu" in launch["args"]
    assert launch["chromium_sandbox"] is True
    assert "--no-sandbox" not in ManagedBrowser.build_browser_flags(bc)


# ── end to end: self-signed HTTPS origin ───────────────────────────────


@pytest.fixture(scope="module")
def self_signed_origin(tmp_path_factory):
    work = tmp_path_factory.mktemp("tls")
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
         "-subj", "/CN=localhost", "-keyout", str(work / "k.pem"), "-out", str(work / "c.pem")],
        check=True, capture_output=True,
    )
    marker = "tls-marker-" + secrets.token_hex(6)
    # Padding keeps the page above the anti-bot near-empty threshold.
    filler = "<p>" + "Plain test content. " * 100 + "</p>"
    (work / "index.html").write_text(
        f"<html><head><title>tls</title></head><body><p>{marker}</p>{filler}</body></html>"
    )

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(work / "c.pem"), str(work / "k.pem"))

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(work), **k)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"https://localhost:{srv.server_address[1]}/", marker
    srv.shutdown()


async def _crawl(url, **browser_kwargs):
    bc = BrowserConfig(headless=True, verbose=False, **browser_kwargs)
    async with AsyncWebCrawler(config=bc) as crawler:
        r = await crawler.arun(url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
    return r.html or ""


LAUNCH_MODES = {
    "playwright_launch": {},
    "managed_cdp": {"use_managed_browser": True},
    "persistent_context": {"use_persistent_context": True},
}


@pytest.mark.parametrize("mode", list(LAUNCH_MODES))
def test_tls_verified_when_ignore_https_errors_false(self_signed_origin, mode):
    url, marker = self_signed_origin
    html = asyncio.run(_crawl(url, ignore_https_errors=False, **LAUNCH_MODES[mode]))
    assert marker not in html, "untrusted certificate accepted with ignore_https_errors=False"


@pytest.mark.parametrize("mode", list(LAUNCH_MODES))
def test_insecure_tls_when_ignore_https_errors_true(self_signed_origin, mode):
    url, marker = self_signed_origin
    html = asyncio.run(_crawl(url, ignore_https_errors=True, **LAUNCH_MODES[mode]))
    assert marker in html, "ignore_https_errors=True no longer reaches a self-signed origin"
