"""
Reproduction test for issue #1455:
Extraction strategy is skipped when cache_mode=ENABLED and cache hits.

Uses JsonCssExtractionStrategy (no LLM needed) to verify that extraction
runs on cached HTML, not just on fresh fetches.
"""

import asyncio
import json
import socket
import threading
import time
import pytest
from aiohttp import web

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


PRODUCT_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Product Catalog - Test Store</title>
<meta name="description" content="Browse our product catalog with great deals">
</head>
<body>
<header><h1>Test Store Product Catalog</h1>
<nav><a href="/">Home</a> <a href="/products">Products</a> <a href="/about">About</a></nav>
</header>
<main>
<p>Welcome to our store. Browse our selection of quality products below.
We offer competitive prices and fast shipping on all orders.</p>
<div class="product" data-testid="product">
  <span class="name">Widget A</span>
  <span class="price">$9.99</span>
  <p>A high-quality widget for everyday use. Built to last with premium materials.</p>
</div>
<div class="product" data-testid="product">
  <span class="name">Widget B</span>
  <span class="price">$19.99</span>
  <p>Our premium widget with advanced features and extended warranty included.</p>
</div>
</main>
<footer><p>Copyright 2026 Test Store. All rights reserved.</p></footer>
</body></html>
"""

SCHEMA = {
    "name": "Products",
    "baseSelector": "div.product[data-testid='product']",
    "fields": [
        {"name": "name", "selector": "span.name", "type": "text"},
        {"name": "price", "selector": "span.price", "type": "text"},
    ],
}


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def test_server():
    port = _find_free_port()

    async def handle(request):
        return web.Response(text=PRODUCT_PAGE, content_type="text/html")

    app = web.Application()
    app.router.add_get("/products", handle)

    ready = threading.Event()

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        runner = web.AppRunner(app)
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, "localhost", port)
        loop.run_until_complete(site.start())
        ready.set()
        loop.run_forever()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    assert ready.wait(timeout=10)
    time.sleep(0.2)
    yield f"http://localhost:{port}"


@pytest.mark.asyncio
async def test_extraction_runs_on_cache_hit(test_server):
    """
    Bug #1455: extraction strategy must run even when result comes from cache.

    1. First crawl WITHOUT extraction (populates cache)
    2. Second crawl WITH extraction + cache_mode=ENABLED (cache hit)
    3. Verify extracted_content is populated (not empty)
    """
    url = f"{test_server}/products"

    # Step 1: Warm the cache (no extraction strategy)
    config_warm = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
    )
    async with AsyncWebCrawler(verbose=False) as crawler:
        result1 = await crawler.arun(url=url, config=config_warm)
    assert result1.success

    # Step 2: Crawl again WITH extraction strategy (should hit cache)
    extraction = JsonCssExtractionStrategy(SCHEMA)
    config_extract = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        extraction_strategy=extraction,
    )
    async with AsyncWebCrawler(verbose=False) as crawler:
        result2 = await crawler.arun(url=url, config=config_extract)

    assert result2.success
    data = json.loads(result2.extracted_content)
    assert len(data) == 2, f"Expected 2 products, got {len(data)}"
    assert data[0]["name"] == "Widget A"
    assert data[1]["name"] == "Widget B"


@pytest.mark.asyncio
async def test_cache_without_extraction_still_works(test_server):
    """Cache hit without extraction strategy should still return normally."""
    url = f"{test_server}/products"

    config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url, config=config)
    assert result.success
    assert "Widget A" in result.html


if __name__ == "__main__":
    asyncio.run(test_extraction_runs_on_cache_hit.__wrapped__(None))
