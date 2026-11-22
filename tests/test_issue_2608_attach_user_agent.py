"""Issue #2608: attaching via cdp_url rewrites the browser's UA/sec-ch-ua.

Two fixes, both covered here:
1. In attach mode (a caller-supplied cdp_url) the default User-Agent and the
   generated sec-ch-ua must not be pushed onto the existing browser's
   contexts unless user_agent was set explicitly.
2. generate_client_hints must derive its brands from the UA it is given:
   a HeadlessChrome (Chrome for Testing) UA gets no "Google Chrome" brand,
   and the GREASE brand follows Chromium's major-version rules.
"""

import html
import json
import re
import socket
import threading
from contextlib import asynccontextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.user_agent_generator import (
    DEFAULT_USER_AGENT,
    UAGen,
    UserAgentGenerator,
)

HEADLESS_158_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) HeadlessChrome/158.0.0.0 Safari/537.36"
)
BRANDED_152_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)
EDGE_153_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0"
)
FIREFOX_UA = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
SAFARI_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15"
)
CDP_URL = "http://127.0.0.1:9222"


# --- generate_client_hints ---------------------------------------------------

def test_headless_chrome_has_no_google_chrome_brand():
    # What Chrome for Testing 158 actually sends on the wire.
    assert UAGen.generate_client_hints(HEADLESS_158_UA) == (
        '"Not.A/Brand";v="24", "Chromium";v="158"'
    )


def test_branded_chrome_158_matches_real_chrome():
    # What branded Google Chrome 158 actually sends on the wire.
    assert UAGen.generate_client_hints(DEFAULT_USER_AGENT) == (
        '"Chromium";v="158", "Not.A/Brand";v="24", "Google Chrome";v="158"'
    )


def test_chrome_152_grease_brand():
    assert UAGen.generate_client_hints(BRANDED_152_UA) == (
        '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"'
    )


def test_edge_keeps_microsoft_edge_brand():
    hints = UAGen.generate_client_hints(EDGE_153_UA)
    assert '"Microsoft Edge";v="153"' in hints
    assert '"Chromium";v="153"' in hints
    assert '"Google Chrome"' not in hints


def test_firefox_hint_is_empty():
    assert UAGen.generate_client_hints(FIREFOX_UA) == ""


def test_safari_hint_keeps_safari_brand():
    hints = UAGen.generate_client_hints(SAFARI_UA)
    assert '"Safari";v="17"' in hints
    assert '"Google Chrome"' not in hints


def test_empty_user_agent_has_no_hints():
    assert UAGen.generate_client_hints("") == ""


def test_instance_method_matches_static_method():
    generator = UserAgentGenerator()
    for ua in (HEADLESS_158_UA, DEFAULT_USER_AGENT, BRANDED_152_UA, EDGE_153_UA, FIREFOX_UA, SAFARI_UA, ""):
        assert generator.generate_client_hints(ua) == UAGen.generate_client_hints(ua)


# --- BrowserConfig in attach mode -------------------------------------------

def test_attach_defaults_leave_browser_alone():
    config = BrowserConfig(browser_mode="custom", cdp_url=CDP_URL)
    assert config.user_agent == ""
    assert config.browser_hint == ""
    assert "sec-ch-ua" not in config.headers


def test_attach_via_use_managed_browser_and_cdp_url():
    config = BrowserConfig(use_managed_browser=True, cdp_url=CDP_URL)
    assert config.user_agent == ""
    assert config.browser_hint == ""


def test_attach_explicit_user_agent_is_honored():
    config = BrowserConfig(
        browser_mode="custom", cdp_url=CDP_URL, user_agent=HEADLESS_158_UA
    )
    assert config.user_agent == HEADLESS_158_UA
    assert config.browser_hint == '"Not.A/Brand";v="24", "Chromium";v="158"'
    assert config.headers["sec-ch-ua"] == config.browser_hint


def test_attach_explicit_empty_user_agent():
    config = BrowserConfig(browser_mode="custom", cdp_url=CDP_URL, user_agent="")
    assert config.user_agent == ""
    assert config.browser_hint == ""


def test_attach_random_user_agent_mode_is_explicit():
    config = BrowserConfig(
        browser_mode="custom", cdp_url=CDP_URL, user_agent_mode="random"
    )
    assert config.user_agent != ""
    assert config.browser_hint != ""


def test_attach_caller_sec_ch_ua_is_kept():
    config = BrowserConfig(
        browser_mode="custom",
        cdp_url=CDP_URL,
        headers={"sec-ch-ua": '"Custom";v="1"'},
    )
    assert config.headers["sec-ch-ua"] == '"Custom";v="1"'


def test_self_launched_default_is_unchanged():
    # No cdp_url: browsers crawl4ai launches itself keep the default UA.
    assert BrowserConfig().user_agent == DEFAULT_USER_AGENT
    assert BrowserConfig(browser_mode="builtin").user_agent == DEFAULT_USER_AGENT
    assert BrowserConfig(use_managed_browser=True).user_agent == DEFAULT_USER_AGENT


def test_attach_clone_keeps_empty_user_agent():
    config = BrowserConfig(browser_mode="custom", cdp_url=CDP_URL)
    assert config.clone().user_agent == ""
    explicit = BrowserConfig(
        browser_mode="custom", cdp_url=CDP_URL, user_agent=HEADLESS_158_UA
    )
    assert explicit.clone().user_agent == HEADLESS_158_UA


# --- real browser: attach must not rewrite the browser's identity -----------

PAGE = b"""<html><head><title>t</title></head><body><p>""" + b"Probe page with enough text to pass the content checks. " * 20 + b"""</p></body></html>"""

JS_PROBE = (
    "const el = document.createElement('pre'); el.id = 'c4a-probe'; "
    "el.textContent = JSON.stringify({"
    "ua: navigator.userAgent, "
    "platform: navigator.platform, "
    "brands: navigator.userAgentData ? navigator.userAgentData.brands.map(b => b.brand + ';v=' + b.version).join(', ') : null, "
    "uaPlatform: navigator.userAgentData ? navigator.userAgentData.platform : null}); "
    "document.body.appendChild(el);"
)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server():
    seen = {"headers": []}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/headers"):
                seen["headers"].append(dict(self.headers))
                body = json.dumps({"headers": dict(self.headers)}).encode()
                ctype = "application/json"
            else:
                body, ctype = PAGE, "text/html"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", seen
    httpd.shutdown()


@asynccontextmanager
async def external_browser():
    """A headless Chromium the test owns, exposed over CDP like Chrome for Testing."""
    from playwright.async_api import async_playwright

    port = _free_port()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=[f"--remote-debugging-port={port}"]
        )
        try:
            yield f"http://127.0.0.1:{port}", p
        finally:
            await browser.close()


async def _bare_wire_and_js(p, cdp_url, base_url):
    """Headers + page JS the browser sends with no crawl4ai attached."""
    browser = await p.chromium.connect_over_cdp(cdp_url)
    page = await browser.contexts[0].new_page()
    await page.goto(f"{base_url}/headers")
    headers = json.loads(await page.inner_text("body"))["headers"]
    await page.goto(f"{base_url}/page")
    js = await page.evaluate(
        "({ua: navigator.userAgent, platform: navigator.platform, "
        "brands: navigator.userAgentData ? navigator.userAgentData.brands.map(b => b.brand + ';v=' + b.version).join(', ') : null, "
        "uaPlatform: navigator.userAgentData ? navigator.userAgentData.platform : null})"
    )
    await page.close()
    await browser.close()
    return headers, js


async def _crawl4ai_wire_and_js(crawler, base_url):
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    r = await crawler.arun(f"{base_url}/headers", config=run)
    assert r.success, r.error_message
    wire = json.loads(re.search(r"\{.*\}", html.unescape(r.html), re.S).group(0))["headers"]
    r = await crawler.arun(
        f"{base_url}/page",
        config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, js_code=JS_PROBE),
    )
    assert r.success, r.error_message
    js = json.loads(re.search(r"\{.*\}", html.unescape(r.html), re.S).group(0))
    return wire, js


@pytest.mark.asyncio
async def test_attach_defaults_keep_browser_identity(server):
    base_url, _seen = server
    async with external_browser() as (cdp_url, p):
        bare_wire, bare_js = await _bare_wire_and_js(p, cdp_url, base_url)
        async with AsyncWebCrawler(
            config=BrowserConfig(browser_mode="custom", cdp_url=cdp_url)
        ) as crawler:
            wire, js = await _crawl4ai_wire_and_js(crawler, base_url)
        assert wire["User-Agent"] == bare_wire["User-Agent"]
        assert js["ua"] == bare_js["ua"]
        assert js["platform"] == bare_js["platform"]
        # The browser returns to normal once crawl4ai disconnects.
        bare_wire2, _ = await _bare_wire_and_js(p, cdp_url, base_url)
        assert bare_wire2["User-Agent"] == bare_wire["User-Agent"]


@pytest.mark.asyncio
async def test_attach_isolated_context_keeps_browser_identity(server):
    base_url, _seen = server
    async with external_browser() as (cdp_url, p):
        bare_wire, bare_js = await _bare_wire_and_js(p, cdp_url, base_url)
        async with AsyncWebCrawler(
            config=BrowserConfig(
                browser_mode="custom",
                cdp_url=cdp_url,
                create_isolated_context=True,
            )
        ) as crawler:
            wire, js = await _crawl4ai_wire_and_js(crawler, base_url)
        assert wire["User-Agent"] == bare_wire["User-Agent"]
        assert js["ua"] == bare_js["ua"]
        assert js["platform"] == bare_js["platform"]


@pytest.mark.asyncio
async def test_attach_explicit_user_agent_applies(server):
    base_url, _seen = server
    async with external_browser() as (cdp_url, p):
        bare_wire, _bare_js = await _bare_wire_and_js(p, cdp_url, base_url)
        async with AsyncWebCrawler(
            config=BrowserConfig(
                browser_mode="custom",
                cdp_url=cdp_url,
                user_agent=bare_wire["User-Agent"],
            )
        ) as crawler:
            wire, _js = await _crawl4ai_wire_and_js(crawler, base_url)
        assert wire["User-Agent"] == bare_wire["User-Agent"]
