"""Issue #2493: stale default User-Agent, empty sec-ch-ua, service worker UA."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.browser_manager import BrowserManager, ManagedBrowser
from crawl4ai.user_agent_generator import DEFAULT_USER_AGENT, UAGen

FIREFOX_UA = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"


# --- config level -----------------------------------------------------------

def test_default_user_agent_is_well_formed():
    config = BrowserConfig()
    assert config.user_agent == DEFAULT_USER_AGENT
    assert "(KHTML, like Gecko)" in config.user_agent
    assert "Chrome/116" not in config.user_agent
    assert config.headers["sec-ch-ua"] == config.browser_hint != ""


@pytest.mark.parametrize("ua", ["", "MyBot/1.0", FIREFOX_UA])
def test_no_empty_sec_ch_ua(ua):
    config = BrowserConfig(user_agent=ua)
    assert config.browser_hint == ""
    assert "sec-ch-ua" not in config.headers


def test_caller_sec_ch_ua_is_kept():
    config = BrowserConfig(user_agent="", headers={"sec-ch-ua": '"Chromium";v="158"'})
    assert config.headers["sec-ch-ua"] == '"Chromium";v="158"'


def test_firefox_hint_is_empty():
    assert UAGen.generate_client_hints(FIREFOX_UA) == ""


# --- launch flags -----------------------------------------------------------

def test_launch_flags_carry_user_agent():
    config = BrowserConfig(user_agent="MyBot/1.0")
    assert "--user-agent=MyBot/1.0" in ManagedBrowser.build_browser_flags(config)
    assert "--user-agent=MyBot/1.0" in BrowserManager(config)._build_browser_args()["args"]


def test_empty_user_agent_adds_no_launch_flag():
    config = BrowserConfig(user_agent="")
    assert not any(a.startswith("--user-agent") for a in ManagedBrowser.build_browser_flags(config))
    assert not any(a.startswith("--user-agent") for a in BrowserManager(config)._build_browser_args()["args"])


def test_extra_args_user_agent_wins():
    # Chromium uses the last --user-agent; extra_args must come after ours.
    config = BrowserConfig(user_agent="A/1", extra_args=["--user-agent=B/2"])
    ua_args = [a for a in BrowserManager(config)._build_browser_args()["args"] if a.startswith("--user-agent")]
    assert ua_args[-1] == "--user-agent=B/2"


# --- real browser -----------------------------------------------------------

PAGE = b"""<html><body><p>""" + b"User-Agent test page with enough text to pass the content checks. " * 20 + b"""</p><script>
navigator.serviceWorker.register('/sw.js');
</script></body></html>"""
SW = b"self.addEventListener('install', () => fetch('/sw-ua?ua=' + encodeURIComponent(navigator.userAgent)));"


@pytest.fixture
def server():
    seen = {"page": [], "sw_ua": []}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/sw.js":
                body, ctype = SW, "application/javascript"
            elif url.path == "/sw-ua":
                seen["sw_ua"].append(parse_qs(url.query)["ua"][0])
                body, ctype = b"", "text/plain"
            else:
                seen["page"].append(dict(self.headers))
                body, ctype = PAGE, "text/html"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://localhost:{httpd.server_port}/", seen
    httpd.shutdown()


def _headers(seen):
    return {k.lower(): v for k, v in seen["page"][-1].items()}


async def _crawl(url, browser_config, run_config=None):
    run_config = run_config or CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url, config=run_config)
    assert result.success, result.error_message


@pytest.mark.asyncio
async def test_default_ua_reaches_page_and_service_worker(server):
    url, seen = server
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, delay_before_return_html=1.0)
    await _crawl(url, BrowserConfig(headless=True), run)
    headers = _headers(seen)
    assert headers["user-agent"] == DEFAULT_USER_AGENT
    assert headers["sec-ch-ua"].startswith('"Chromium";v="158"')
    assert seen["sw_ua"] == [DEFAULT_USER_AGENT]


@pytest.mark.asyncio
@pytest.mark.parametrize("ua", ["", "MyBot/1.0"])
async def test_no_empty_sec_ch_ua_sent(server, ua):
    url, seen = server
    await _crawl(url, BrowserConfig(headless=True, user_agent=ua))
    headers = _headers(seen)
    if ua:
        assert headers["user-agent"] == ua
    # Chromium may send its own sec-ch-ua for the native UA; never an empty one.
    assert headers.get("sec-ch-ua", "x") != ""


@pytest.mark.asyncio
async def test_per_run_user_agent_sends_no_empty_sec_ch_ua(server):
    url, seen = server
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, user_agent="MyBot/1.0")
    await _crawl(url, BrowserConfig(headless=True), run)
    headers = _headers(seen)
    assert headers["user-agent"] == "MyBot/1.0"
    assert headers.get("sec-ch-ua", "x") != ""


@pytest.mark.asyncio
async def test_per_run_user_agent_updates_auto_sec_ch_ua(server):
    url, seen = server
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, user_agent=DEFAULT_USER_AGENT.replace("158", "150"))
    await _crawl(url, BrowserConfig(headless=True), run)
    assert _headers(seen)["sec-ch-ua"].startswith('"Chromium";v="150"')


@pytest.mark.asyncio
@pytest.mark.parametrize("run_ua", ["MyBot/1.0", DEFAULT_USER_AGENT.replace("158", "150")])
async def test_per_run_user_agent_keeps_user_sec_ch_ua(server, run_ua):
    url, seen = server
    custom = '"Custom";v="1"'
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, user_agent=run_ua)
    await _crawl(url, BrowserConfig(headless=True, headers={"sec-ch-ua": custom}), run)
    assert _headers(seen)["sec-ch-ua"] == custom
