"""BrowserConfig.service_workers: validation, round-trips, trust boundary, and
real-browser behaviour through both context-creation paths.

Browser tests serve a page from a local HTTP server on 127.0.0.1. localhost is a
secure context, so navigator.serviceWorker is available there.
"""

import asyncio
import http.server
import sys
import threading
from pathlib import Path

import pytest

from crawl4ai import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import Provenance, UntrustedConfigError
from crawl4ai.browser_manager import BrowserManager

ROOT = Path(__file__).resolve().parents[2]
DOCKER_DIR = ROOT / "deploy" / "docker"

PAGE = b"<!doctype html><html><body>sw test</body></html>"
SW_JS = b"self.addEventListener('install', () => self.skipWaiting());"
# With service_workers="block", register() still resolves but creates no
# registration, so count registrations rather than checking the promise.
REGISTER_JS = (
    "navigator.serviceWorker.register('/sw.js')"
    ".then(() => navigator.serviceWorker.getRegistrations())"
    ".then(r => 'registrations:' + r.length, e => 'rejected:' + e.name)"
)


# ── config surface ──────────────────────────────────────────────────────────

def test_default_is_allow():
    assert BrowserConfig().service_workers == "allow"


@pytest.mark.parametrize("value", ["allow", "block"])
def test_valid_values_accepted(value):
    assert BrowserConfig(service_workers=value).service_workers == value


@pytest.mark.parametrize("value", ["", "deny", "BLOCK", None, True])
def test_invalid_values_refused(value):
    with pytest.raises(ValueError, match="service_workers"):
        BrowserConfig(service_workers=value)


def test_to_dict_and_clone_round_trip():
    cfg = BrowserConfig(service_workers="block")
    assert cfg.to_dict()["service_workers"] == "block"
    assert BrowserConfig.from_kwargs(cfg.to_dict()).service_workers == "block"
    assert cfg.clone().service_workers == "block"
    assert cfg.clone(service_workers="allow").service_workers == "allow"


def test_load_from_untrusted_request_keeps_block():
    cfg = BrowserConfig.load(
        {"service_workers": "block"}, provenance=Provenance.UNTRUSTED
    )
    assert cfg.service_workers == "block"


@pytest.mark.parametrize("value", ["deny", "", None])
def test_invalid_untrusted_value_is_a_400_error(value):
    """Docker maps UntrustedConfigError to HTTP 400; a plain ValueError is a 500."""
    with pytest.raises(UntrustedConfigError):
        BrowserConfig.load({"service_workers": value}, provenance=Provenance.UNTRUSTED)


def test_pool_signature_separates_service_workers():
    """The Docker pool keys browsers by sha1(to_dict()). Differing values must
    not share a pooled browser."""
    import json

    allow = json.dumps(BrowserConfig(service_workers="allow").to_dict(), sort_keys=True)
    block = json.dumps(BrowserConfig(service_workers="block").to_dict(), sort_keys=True)
    assert allow != block

    sys.path.insert(0, str(DOCKER_DIR))
    try:
        pool = pytest.importorskip("crawler_pool", reason="docker server deps not installed")
        assert pool._sig(BrowserConfig(service_workers="allow")) != pool._sig(
            BrowserConfig(service_workers="block")
        )
    finally:
        sys.path.remove(str(DOCKER_DIR))


# ── explicit gap: managed / CDP browsers reject "block" ─────────────────────

@pytest.mark.parametrize(
    "kwargs",
    [
        {"cdp_url": "http://127.0.0.1:9", "browser_mode": "custom"},
        {"browser_mode": "builtin", "use_managed_browser": True},
        {"use_managed_browser": True},
    ],
)
def test_block_refused_for_managed_or_cdp_browsers(kwargs):
    async def run():
        manager = BrowserManager(
            browser_config=BrowserConfig(service_workers="block", **kwargs)
        )
        with pytest.raises(ValueError, match="service_workers='block'"):
            await manager.start()
        await manager.close()

    asyncio.run(run())


# ── real browser: both context-creation paths ───────────────────────────────

@pytest.fixture
def page_url():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()


class _QuietHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body, ctype = (SW_JS, "text/javascript") if self.path == "/sw.js" else (PAGE, "text/html")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


async def _register_in(page, url):
    await page.goto(url)
    return await page.evaluate(REGISTER_JS)


def _run_get_page(config, url):
    """Crawl path: BrowserManager.get_page(). Covers a dedicated browser or,
    with use_persistent_context=True, the launch_persistent_context path."""
    async def run():
        manager = BrowserManager(browser_config=config)
        await manager.start()
        try:
            page, _ = await manager.get_page(CrawlerRunConfig())
            return await _register_in(page, url)
        finally:
            await manager.close()

    return asyncio.run(run())


def _run_create_context(config, url):
    """new_context path: create_browser_context() called directly."""
    async def run():
        manager = BrowserManager(browser_config=config)
        await manager.start()
        try:
            context = await manager.create_browser_context()
            try:
                page = await context.new_page()
                return await _register_in(page, url)
            finally:
                await context.close()
        finally:
            await manager.close()

    return asyncio.run(run())


@pytest.mark.parametrize("runner", [_run_get_page, _run_create_context])
def test_allow_registers_and_block_rejects(runner, page_url):
    assert runner(BrowserConfig(headless=True, service_workers="allow"), page_url) == "registrations:1"
    assert runner(BrowserConfig(headless=True, service_workers="block"), page_url) == "registrations:0"


def test_persistent_context_honours_block(tmp_path, page_url):
    allow = BrowserConfig(
        headless=True,
        use_persistent_context=True,
        user_data_dir=str(tmp_path / "allow"),
        service_workers="allow",
    )
    block = BrowserConfig(
        headless=True,
        use_persistent_context=True,
        user_data_dir=str(tmp_path / "block"),
        service_workers="block",
    )
    assert _run_get_page(allow, page_url) == "registrations:1"
    assert _run_get_page(block, page_url) == "registrations:0"


def _free_port():
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.mark.parametrize(
    "service_workers, expected",
    [("allow", "registrations:1"), ("block", "registrations:0")],
)
def test_isolated_cdp_contexts_honour_service_workers(service_workers, expected, page_url):
    """A real Chromium with a debugging port: create_isolated_context makes
    contexts here, so the option applies and the start() check lets it through."""
    from playwright.async_api import async_playwright
    from crawl4ai.async_logger import AsyncLogger

    port = _free_port()

    async def run():
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, args=[f"--remote-debugging-port={port}"]
            )
            manager = BrowserManager(
                browser_config=BrowserConfig(
                    cdp_url=f"http://127.0.0.1:{port}",
                    browser_mode="custom",
                    create_isolated_context=True,
                    cdp_cleanup_on_close=True,
                    service_workers=service_workers,
                ),
                logger=AsyncLogger(verbose=False),
            )
            try:
                await manager.start()
                page, _ = await manager.get_page(CrawlerRunConfig())
                return await _register_in(page, page_url)
            finally:
                await manager.close()
                await browser.close()

    assert asyncio.run(run()) == expected


def test_block_refused_in_undetected_mode():
    async def run():
        manager = BrowserManager(
            browser_config=BrowserConfig(headless=True, service_workers="block"),
            use_undetected=True,
        )
        with pytest.raises(ValueError, match="undetected"):
            await manager.start()
        await manager.close()

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["builtin", "docker"])
def test_untrusted_block_with_managed_browser_mode_is_a_400_error(mode):
    """Start() refuses this combination; untrusted input must fail as 400, not
    as a ValueError during browser start (HTTP 500)."""
    with pytest.raises(UntrustedConfigError):
        BrowserConfig.load(
            {"browser_mode": mode, "service_workers": "block"},
            provenance=Provenance.UNTRUSTED,
        )


def test_untrusted_allow_with_managed_browser_mode_is_fine():
    cfg = BrowserConfig.load(
        {"browser_mode": "builtin", "service_workers": "allow"},
        provenance=Provenance.UNTRUSTED,
    )
    assert cfg.service_workers == "allow"


def test_untrusted_block_in_dedicated_mode_is_fine():
    cfg = BrowserConfig.load(
        {"browser_mode": "dedicated", "service_workers": "block"},
        provenance=Provenance.UNTRUSTED,
    )
    assert cfg.service_workers == "block"


def test_create_profile_refuses_block(tmp_path):
    from crawl4ai.browser_profiler import BrowserProfiler

    async def run():
        with pytest.raises(ValueError, match="create_profile"):
            await BrowserProfiler().create_profile(
                profile_name="sw-test",
                browser_config=BrowserConfig(service_workers="block"),
            )

    asyncio.run(run())


def test_untrusted_default_block_with_builtin_is_a_400_error():
    """A class-level set_defaults() override must count, not just the request."""
    BrowserConfig.set_defaults(service_workers="block")
    try:
        with pytest.raises(UntrustedConfigError):
            BrowserConfig.load({"browser_mode": "builtin"}, provenance=Provenance.UNTRUSTED)
    finally:
        BrowserConfig.reset_defaults("service_workers")


def test_untrusted_isolated_default_allows_builtin_block():
    """A trusted create_isolated_context default makes builtin + block work, so
    the untrusted gate must not refuse it."""
    BrowserConfig.set_defaults(create_isolated_context=True)
    try:
        cfg = BrowserConfig.load(
            {"browser_mode": "builtin", "service_workers": "block"},
            provenance=Provenance.UNTRUSTED,
        )
        assert cfg.service_workers == "block"
    finally:
        BrowserConfig.reset_defaults("create_isolated_context")


def test_create_profile_refuses_inherited_block():
    from crawl4ai.browser_profiler import BrowserProfiler

    BrowserConfig.set_defaults(service_workers="block")
    try:
        async def run():
            with pytest.raises(ValueError, match="create_profile"):
                await BrowserProfiler().create_profile(profile_name="sw-test-inherited")

        asyncio.run(run())
    finally:
        BrowserConfig.reset_defaults("service_workers")


def test_standalone_browser_refuses_inherited_block(tmp_path):
    from crawl4ai.browser_profiler import BrowserProfiler

    BrowserConfig.set_defaults(service_workers="block")
    try:
        async def run():
            with pytest.raises(ValueError, match="standalone browser"):
                await BrowserProfiler().launch_standalone_browser(
                    user_data_dir=str(tmp_path / "standalone"),
                    debugging_port=_free_port(),
                )

        asyncio.run(run())
    finally:
        BrowserConfig.reset_defaults("service_workers")


def test_mixed_backend_cached_connection_refuses_block(page_url):
    """A Patchright connection in the shared CDP cache must not serve a Playwright
    manager that asks for "block". Real acquire() path, real Chromium."""
    from playwright.async_api import async_playwright
    from crawl4ai.async_logger import AsyncLogger
    from crawl4ai.browser_manager import _CDPConnectionCache

    port = _free_port()
    url = f"http://127.0.0.1:{port}"

    def config(service_workers):
        return BrowserConfig(
            cdp_url=url,
            browser_mode="custom",
            cache_cdp_connection=True,
            create_isolated_context=True,
            service_workers=service_workers,
        )

    async def run():
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, args=[f"--remote-debugging-port={port}"]
            )
            try:
                # Another (undetected) manager caches a Patchright connection.
                await _CDPConnectionCache.acquire(url, use_undetected=True)
                try:
                    blocked = BrowserManager(
                        browser_config=config("block"), logger=AsyncLogger(verbose=False)
                    )
                    with pytest.raises(ValueError, match="undetected mode"):
                        await blocked.start()

                    # The refused manager released its reference: the cached
                    # connection is still held by the first acquire only.
                    _, _, count = _CDPConnectionCache._cache[url]
                    assert count == 1

                    # "allow" shares that connection as upstream does.
                    allowed = BrowserManager(
                        browser_config=config("allow"), logger=AsyncLogger(verbose=False)
                    )
                    await allowed.start()
                    await allowed.close()
                finally:
                    await _CDPConnectionCache.close_all()
            finally:
                await browser.close()

    asyncio.run(run())
