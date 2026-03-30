"""
Reproduction test for issue #731:
scan_full_page=True only captures the final elements on virtual-scroll pages.

Creates a local HTML page that simulates virtual scrolling (DOM recycling)
and verifies that scan_full_page captures ALL items, not just the last batch.
"""

import asyncio
import os
import tempfile
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# HTML page that simulates virtual scrolling: only 10 items visible at a time,
# content is REPLACED (recycled) as you scroll — mimicking Twitter/X behavior.
VIRTUAL_SCROLL_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; font-family: sans-serif; }
  .item { height: 80px; padding: 10px; border-bottom: 1px solid #eee; }
  .item .name { font-weight: bold; }
  .item .handle { color: #666; }
</style>
</head>
<body>
<div id="feed"></div>
<script>
  // Simulate 50 total users, but only render 10 at a time (virtual scroll)
  const TOTAL = 50;
  const VISIBLE = 10;
  const allUsers = [];
  for (let i = 0; i < TOTAL; i++) {
    allUsers.push({ name: `User ${i+1}`, handle: `@user${i+1}` });
  }

  let startIdx = 0;
  const feed = document.getElementById('feed');

  function render() {
    feed.innerHTML = '';
    const end = Math.min(startIdx + VISIBLE, TOTAL);
    for (let i = startIdx; i < end; i++) {
      const div = document.createElement('div');
      div.className = 'item';
      div.setAttribute('data-testid', 'UserCell');
      div.innerHTML = `<div class="name">${allUsers[i].name}</div><div class="handle">${allUsers[i].handle}</div>`;
      feed.appendChild(div);
    }
    // Set body height to allow scrolling
    document.body.style.height = (TOTAL * 80) + 'px';
  }

  render();

  // On scroll, recycle DOM elements (virtual scroll behavior)
  window.addEventListener('scroll', () => {
    const scrollPos = window.scrollY;
    const newStart = Math.min(Math.floor(scrollPos / 80), TOTAL - VISIBLE);
    if (newStart !== startIdx) {
      startIdx = newStart;
      render();
    }
  });
</script>
</body>
</html>
"""


def start_server(html_dir, port=9731):
    """Start a simple HTTP server serving the test HTML."""
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=html_dir, **kwargs)
        def log_message(self, format, *args):
            pass  # suppress logs
    server = HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


async def test_scan_full_page_virtual_scroll():
    """
    BUG REPRODUCTION: scan_full_page=True on a virtual-scroll page.
    Expected: all 50 users captured.
    Actual (bug): only the last ~10 users captured.
    """
    # Write test HTML to a temp dir and serve it
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = os.path.join(tmpdir, "index.html")
        with open(html_path, "w") as f:
            f.write(VIRTUAL_SCROLL_HTML)

        server = start_server(tmpdir, port=9731)

        try:
            schema = {
                "name": "Users",
                "baseSelector": "[data-testid='UserCell']",
                "fields": [
                    {"name": "name", "selector": ".name", "type": "text"},
                    {"name": "handle", "selector": ".handle", "type": "text"},
                ],
            }
            extraction = JsonCssExtractionStrategy(schema)

            # --- Test 1: WITHOUT scan_full_page (baseline) ---
            config_no_scroll = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=extraction,
                scan_full_page=False,
            )
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url="http://127.0.0.1:9731/index.html", config=config_no_scroll)

            data_no_scroll = json.loads(result.extracted_content)
            names_no_scroll = [u["name"] for u in data_no_scroll]
            print(f"\n{'='*60}")
            print(f"WITHOUT scan_full_page: {len(data_no_scroll)} users")
            print(f"  Users: {names_no_scroll[:5]} ... {names_no_scroll[-3:] if len(names_no_scroll) > 5 else ''}")
            print(f"{'='*60}")

            # --- Test 2: WITH scan_full_page (the bug) ---
            config_scroll = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=extraction,
                scan_full_page=True,
                scroll_delay=0.3,
                max_scroll_steps=20,
            )
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url="http://127.0.0.1:9731/index.html", config=config_scroll)

            data_scroll = json.loads(result.extracted_content)
            names_scroll = [u["name"] for u in data_scroll]
            print(f"\n{'='*60}")
            print(f"WITH scan_full_page: {len(data_scroll)} users")
            print(f"  Users: {names_scroll[:5]} ... {names_scroll[-3:] if len(names_scroll) > 5 else ''}")
            print(f"{'='*60}")

            # --- Deduplicate by handle ---
            unique_scroll = {u["handle"]: u for u in data_scroll}

            # --- Verdict ---
            print(f"\n{'='*60}")
            print("VERDICT:")
            print(f"  Raw extracted: {len(data_scroll)}, Unique by handle: {len(unique_scroll)}")
            if len(unique_scroll) >= 40:
                print(f"  PASS — scan_full_page captured {len(unique_scroll)}/50 unique users (>= 40)")
                # Check coverage
                captured = sorted(unique_scroll.keys(), key=lambda h: int(h.replace("@user", "")))
                missing = [f"@user{i}" for i in range(1, 51) if f"@user{i}" not in unique_scroll]
                if missing:
                    print(f"  Missing {len(missing)} users: {missing[:10]}{'...' if len(missing) > 10 else ''}")
                else:
                    print(f"  All 50 users captured!")
            else:
                print(f"  BUG CONFIRMED — scan_full_page only captured {len(unique_scroll)}/50 unique users")
                handles = sorted(unique_scroll.keys())
                print(f"  Captured handles: {handles}")
            print(f"{'='*60}")

        finally:
            server.shutdown()


if __name__ == "__main__":
    asyncio.run(test_scan_full_page_virtual_scroll())
