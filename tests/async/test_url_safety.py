import os
import sys
import threading
import http.server
import importlib

import pytest

# Make the local package importable when running from the repo root.
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from crawl4ai.url_safety import (
    check_url_destination,
    is_internal_url,
    BlockedURLError,
)
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy


# ---------------------------------------------------------------------------
# Pure url_safety classification (deterministic: only IP literals / no DNS)
# ---------------------------------------------------------------------------

INTERNAL_URLS = [
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]",
    "http://10.0.0.5",
    "http://192.168.1.1",
    "http://172.16.0.1",
    "http://0.0.0.0",
    "http://100.64.0.1",  # CGN / shared address space
]

EXTERNAL_URLS = [
    "http://1.1.1.1",
    "http://8.8.8.8",
    "http://[2606:4700:4700::1111]",  # global IPv6 literal
    "raw://<html>hi</html>",
    "file:///etc/passwd",
]


@pytest.mark.parametrize("url", INTERNAL_URLS)
def test_is_internal_url_true(url):
    assert is_internal_url(url) is True


@pytest.mark.parametrize("url", EXTERNAL_URLS)
def test_is_internal_url_false(url):
    assert is_internal_url(url) is False


def test_check_url_destination_raises_on_internal():
    with pytest.raises(BlockedURLError):
        check_url_destination("http://127.0.0.1")


def test_check_url_destination_passes_on_external():
    # 1.1.1.1 is a global IP literal; no DNS resolution required.
    check_url_destination("http://1.1.1.1")  # must not raise


def test_check_url_destination_allow_env_override(monkeypatch):
    import crawl4ai.url_safety as us

    monkeypatch.setattr(us, "ALLOW_INTERNAL_URLS", True)
    us.check_url_destination("http://127.0.0.1")  # must not raise
    monkeypatch.setattr(us, "ALLOW_INTERNAL_URLS", False)


# ---------------------------------------------------------------------------
# CrawlerRunConfig field
# ---------------------------------------------------------------------------


def test_config_default_false():
    assert CrawlerRunConfig().block_internal_urls is False


def test_config_set_true():
    assert CrawlerRunConfig(block_internal_urls=True).block_internal_urls is True


def test_config_to_dict_roundtrip():
    c = CrawlerRunConfig(block_internal_urls=True)
    assert c.to_dict()["block_internal_urls"] is True
    c2 = CrawlerRunConfig.from_kwargs(c.to_dict())
    assert c2.block_internal_urls is True


def test_config_clone_preserves():
    c = CrawlerRunConfig(block_internal_urls=True)
    assert c.clone().block_internal_urls is True


# ---------------------------------------------------------------------------
# Integration: the chokepoint in AsyncCrawlerStrategy.crawl() actually fires
# ---------------------------------------------------------------------------


def _start_local_server():
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>LOCAL_OK</body></html>")

        def log_message(self, *args):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


@pytest.mark.asyncio
async def test_http_strategy_blocks_internal():
    srv, port = _start_local_server()
    try:
        strat = AsyncHTTPCrawlerStrategy()
        cfg = CrawlerRunConfig(block_internal_urls=True)
        with pytest.raises(BlockedURLError):
            await strat.crawl(f"http://127.0.0.1:{port}/", config=cfg)
    finally:
        srv.shutdown()


@pytest.mark.asyncio
async def test_http_strategy_allows_by_default():
    srv, port = _start_local_server()
    try:
        strat = AsyncHTTPCrawlerStrategy()
        cfg = CrawlerRunConfig(block_internal_urls=False)
        resp = await strat.crawl(f"http://127.0.0.1:{port}/", config=cfg)
        assert resp.html is not None
        assert "LOCAL_OK" in resp.html
    finally:
        srv.shutdown()
