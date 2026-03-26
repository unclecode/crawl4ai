"""
Tests for virtual scroll and progressive full-page scan.

Covers:
- VirtualScrollConfig: container DOM recycling, dedup, early termination, memory cap
- scan_full_page: window-level DOM recycling (issue #731), lazy-load backward compat
- VirtualScrollConfig window.scrollBy fallback
- Config serialization, from_dict forward-compat, error handling
"""

import asyncio
import re
import socket
import tempfile
import threading
from functools import partial
import http.server
import os

import pytest

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    VirtualScrollConfig,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def browser_config():
    return BrowserConfig(headless=True)


class _TestServer:
    """Lightweight HTTP server. Uses directory= to avoid os.chdir."""

    def __init__(self, html: str):
        self._tmpdir = tempfile.mkdtemp()
        self._filepath = os.path.join(self._tmpdir, "page.html")
        with open(self._filepath, "w") as f:
            f.write(html)
        self.port = _find_free_port()
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=self._tmpdir)
        self._httpd = http.server.HTTPServer(("127.0.0.1", self.port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.url = f"http://127.0.0.1:{self.port}/page.html"

    def shutdown(self):
        self._httpd.shutdown()
        os.unlink(self._filepath)
        os.rmdir(self._tmpdir)


# ---------------------------------------------------------------------------
# HTML templates — container-level virtual scroll (uses .format())
# ---------------------------------------------------------------------------

CONTAINER_VSCROLL_HTML = """
<html><head><style>
  #container {{ height: 500px; overflow-y: auto; }}
  .item {{ height: 50px; padding: 10px; border-bottom: 1px solid #eee; }}
</style></head><body>
<div id="container"></div>
<script>
  const container = document.getElementById('container');
  const TOTAL = {total};
  const PER_PAGE = {per_page};
  let startIdx = 0;
  const allData = Array.from({{length: TOTAL}}, (_, i) => ({{
    id: i, text: 'Item ' + (i+1) + ' of ' + TOTAL + ' - UID:' + i
  }}));

  function renderPage(start) {{
    const end = Math.min(start + PER_PAGE, TOTAL);
    container.innerHTML = allData.slice(start, end)
      .map(d => '<div class="item" data-index="' + d.id + '">' + d.text + '</div>')
      .join('');
    startIdx = start;
  }}
  renderPage(0);

  container.addEventListener('scroll', () => {{
    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 50) {{
      const next = startIdx + PER_PAGE;
      if (next < TOTAL) {{ renderPage(next); container.scrollTop = 10; }}
    }}
  }});
</script></body></html>
"""

# ---------------------------------------------------------------------------
# HTML templates — static strings (no .format())
# ---------------------------------------------------------------------------

NO_ATTR_VSCROLL_HTML = """
<html><head><style>
  #container { height: 200px; overflow-y: auto; }
  .card { height: 80px; padding: 8px; border-bottom: 1px solid #ddd; }
</style></head><body>
<div id="container"></div>
<script>
  const container = document.getElementById('container');
  const TOTAL = 50, PER_PAGE = 5;
  let startIdx = 0;
  function renderPage(start) {
    const end = Math.min(start + PER_PAGE, TOTAL);
    const items = [];
    for (let i = start; i < end; i++)
      items.push('<div class="card">Profile ' + (i+1) + ' joined 2024</div>');
    container.innerHTML = items.join('');
    startIdx = start;
  }
  renderPage(0);
  container.addEventListener('scroll', () => {
    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 40) {
      const next = startIdx + PER_PAGE;
      if (next < TOTAL) { renderPage(next); container.scrollTop = 5; }
    }
  });
</script></body></html>
"""

SAME_TEXT_VSCROLL_HTML = """
<html><head><style>
  #container { height: 200px; overflow-y: auto; }
  .item { height: 80px; padding: 5px; border-bottom: 1px solid #eee; box-sizing: border-box; }
</style></head><body>
<div id="container"></div>
<script>
  const container = document.getElementById('container');
  let page = 0;
  function renderPage(p) {
    const items = [];
    for (let i = 0; i < 5; i++) {
      const idx = p * 5 + i;
      items.push('<div class="item" data-index="' + idx + '">Duplicate Text Here</div>');
    }
    container.innerHTML = items.join('');
    page = p;
  }
  renderPage(0);
  container.addEventListener('scroll', () => {
    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 30) {
      if (page < 3) { renderPage(page + 1); container.scrollTop = 5; }
    }
  });
</script></body></html>
"""

STATIC_HTML = """
<html><head><style>
  #container { height: 200px; overflow-y: auto; }
  .item { height: 40px; }
</style></head><body>
<div id="container">
  <div class="item" data-index="0">Static item 1</div>
  <div class="item" data-index="1">Static item 2</div>
  <div class="item" data-index="2">Static item 3</div>
</div>
</body></html>
"""

WINDOW_RECYCLE_HTML = """
<html><head><style>
  body { margin: 0; font-family: sans-serif; }
  .item { height: 120px; padding: 20px; border-bottom: 2px solid #ccc; box-sizing: border-box; }
</style></head><body>
<h1 style="padding:10px">Feed</h1>
<div id="feed"></div>
<script>
  const feed = document.getElementById('feed');
  const TOTAL = 100, PER_PAGE = 8;
  let startIdx = 0;
  function renderPage(start) {
    const end = Math.min(start + PER_PAGE, TOTAL);
    const items = [];
    for (let i = start; i < end; i++)
      items.push('<div class="item" data-index="' + i + '">Post ' + (i+1) + '</div>');
    feed.innerHTML = items.join('');
    startIdx = start;
  }
  renderPage(0);
  window.addEventListener('scroll', () => {
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 100) {
      const next = startIdx + PER_PAGE;
      if (next < TOTAL) { renderPage(next); window.scrollTo(0, 100); }
    }
  });
</script></body></html>
"""

LAZY_LOAD_HTML = """
<html><head><style>
  .item { height: 100px; padding: 10px; border-bottom: 1px solid #ddd; }
</style></head><body>
<div id="content"></div>
<script>
  const content = document.getElementById('content');
  let loaded = 0;
  function loadBatch() {
    for (let i = 0; i < 10; i++) {
      const div = document.createElement('div');
      div.className = 'item';
      div.setAttribute('data-index', loaded);
      div.textContent = 'Lazy item ' + (loaded + 1);
      content.appendChild(div);
      loaded++;
    }
  }
  loadBatch();
  window.addEventListener('scroll', () => {
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 200) {
      if (loaded < 50) loadBatch();
    }
  });
</script></body></html>
"""


# ---------------------------------------------------------------------------
# VirtualScrollConfig tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vscroll_captures_all_items(browser_config):
    """100 items, 10 per page, DOM recycling — all must be captured."""
    server = _TestServer(CONTAINER_VSCROLL_HTML.format(total=100, per_page=10))
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#container",
                scroll_count=15,
                scroll_by="container_height",
                wait_after_scroll=0.15,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html))
        assert indices == set(range(100)), f"Missing: {set(range(100)) - indices}"
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_vscroll_final_chunk_not_lost(browser_config):
    """scroll_count exhausted before bottom — last chunk must still be captured."""
    server = _TestServer(CONTAINER_VSCROLL_HTML.format(total=200, per_page=10))
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#container",
                scroll_count=5,
                scroll_by="container_height",
                wait_after_scroll=0.15,
                max_no_change=0,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = sorted(set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html)))
        assert len(indices) > 10, f"Only {len(indices)} items — final chunk likely lost"
        assert set(range(max(indices) + 1)) == set(indices), "Gaps in captured range"
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_vscroll_early_termination(browser_config):
    """Static content with high scroll_count — must stop early via max_no_change."""
    server = _TestServer(STATIC_HTML)
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#container",
                scroll_count=50,
                scroll_by=100,
                wait_after_scroll=0.05,
                max_no_change=3,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html))
        assert indices == {0, 1, 2}
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_vscroll_text_dedup_no_attributes(browser_config):
    """Elements with no data-id/id — text-based dedup must capture unique profiles."""
    server = _TestServer(NO_ATTR_VSCROLL_HTML)
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#container",
                scroll_count=15,
                scroll_by="container_height",
                wait_after_scroll=0.15,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        profiles = set(int(p) for p in re.findall(r"Profile (\d+) joined", result.html))
        assert len(profiles) >= 30, f"Only {len(profiles)}/50 profiles captured"
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_vscroll_attr_dedup_same_text(browser_config):
    """Items with identical text but different data-index — all must survive."""
    server = _TestServer(SAME_TEXT_VSCROLL_HTML)
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#container",
                scroll_count=10,
                scroll_by="container_height",
                wait_after_scroll=0.15,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html))
        assert len(indices) >= 18, f"Only {len(indices)}/20 survived dedup"
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_vscroll_window_fallback(browser_config):
    """Container scrollTop has no effect — must fall back to window.scrollBy."""
    server = _TestServer(WINDOW_RECYCLE_HTML)
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#feed",
                scroll_count=20,
                scroll_by="page_height",
                wait_after_scroll=0.15,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html))
        assert len(indices) >= 80, f"Only {len(indices)}/100 — window fallback may have failed"
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_vscroll_memory_cap(browser_config):
    """max_captured_elements prevents unbounded accumulation."""
    server = _TestServer(CONTAINER_VSCROLL_HTML.format(total=500, per_page=10))
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#container",
                scroll_count=60,
                scroll_by="container_height",
                wait_after_scroll=0.1,
                max_captured_elements=50,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html))
        assert 20 <= len(indices) <= 150, f"Cap didn't work: {len(indices)} items"
    finally:
        server.shutdown()


# ---------------------------------------------------------------------------
# scan_full_page tests (issue #731)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_full_page_window_recycling(browser_config):
    """Issue #731: scan_full_page=True on window-level DOM recycling page."""
    server = _TestServer(WINDOW_RECYCLE_HTML)
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            scan_full_page=True,
            scroll_delay=0.15,
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html))
        assert len(indices) >= 90, f"Only {len(indices)}/100 captured with scan_full_page"
    finally:
        server.shutdown()


@pytest.mark.asyncio
async def test_scan_full_page_lazy_load(browser_config):
    """Backward compat: lazy-load page (no recycling) still works."""
    server = _TestServer(LAZY_LOAD_HTML)
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            scan_full_page=True,
            scroll_delay=0.2,
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        indices = set(int(m) for m in re.findall(r'data-index="(\d+)"', result.html))
        assert len(indices) >= 40, f"Only {len(indices)}/50 — lazy load regression"
    finally:
        server.shutdown()


# ---------------------------------------------------------------------------
# Config unit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_config_serialization():
    """VirtualScrollConfig round-trips through to_dict/from_dict."""
    cfg = VirtualScrollConfig(
        container_selector="#feed",
        scroll_count=20,
        scroll_by=300,
        wait_after_scroll=0.8,
        max_no_change=7,
        max_captured_elements=5000,
    )
    d = cfg.to_dict()
    assert d["max_no_change"] == 7
    assert d["max_captured_elements"] == 5000

    restored = VirtualScrollConfig.from_dict(d)
    assert restored.max_no_change == 7
    assert restored.scroll_by == 300


@pytest.mark.asyncio
async def test_config_from_dict_ignores_unknown_keys():
    """from_dict must not crash on keys from a newer config version."""
    d = {
        "container_selector": "#x",
        "scroll_count": 5,
        "unknown_future_field": 42,
        "another_new_thing": True,
    }
    cfg = VirtualScrollConfig.from_dict(d)
    assert cfg.container_selector == "#x"
    assert cfg.scroll_count == 5
    assert cfg.max_no_change == 5  # default


@pytest.mark.asyncio
async def test_vscroll_container_not_found(browser_config):
    """Wrong container selector — crawl must complete without crashing."""
    server = _TestServer(STATIC_HTML)
    try:
        await asyncio.sleep(0.3)
        config = CrawlerRunConfig(
            virtual_scroll_config=VirtualScrollConfig(
                container_selector="#nonexistent",
                scroll_count=3,
                scroll_by=100,
                wait_after_scroll=0.05,
            ),
            cache_mode=CacheMode.BYPASS,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=server.url, config=config)

        assert result.html is not None, "Crawl should return HTML even if vscroll fails"
        assert len(result.html) > 0
    finally:
        server.shutdown()
