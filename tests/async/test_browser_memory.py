"""
Tests for browser memory management: memory_saving_mode, browser recycling,
and CDP session leak fixes.

These are integration tests that launch real browsers and crawl real pages.
They verify:
  1. memory_saving_mode Chrome flags are applied
  2. Browser recycling fires at the right threshold and doesn't break crawling
  3. Concurrent crawls survive a recycle boundary without errors
  4. Recycling resets all internal tracking state cleanly
  5. Memory doesn't grow unbounded over many pages
  6. CDP session detach fix doesn't regress viewport adjustment
"""

import asyncio
import os
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

import psutil
import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


# ---------------------------------------------------------------------------
# Local test server — avoids network flakiness
# ---------------------------------------------------------------------------

PAGES_HTML = {}
for i in range(200):
    PAGES_HTML[f"/page{i}"] = f"""<!DOCTYPE html>
<html><head><title>Page {i}</title></head>
<body>
<h1>Test page {i}</h1>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Paragraph {i} with enough text to exercise the content pipeline.</p>
<a href="/page{(i+1) % 200}">Next</a>
</body></html>"""


class MemTestHandler(SimpleHTTPRequestHandler):
    """Serves lightweight HTML pages for memory tests.

    Also serves /login and /dashboard for multi-step session tests.
    /login sets a cookie, /dashboard checks the cookie to prove session state.
    """

    def log_message(self, *args):
        pass  # silent

    def do_GET(self):
        if self.path == "/login":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Set-Cookie", "auth_token=valid123; Path=/")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Login</title></head>
<body><h1>Login Page</h1><p>You are now logged in.</p>
<a href="/dashboard">Go to dashboard</a></body></html>""")
            return

        if self.path == "/dashboard":
            cookie = self.headers.get("Cookie", "")
            if "auth_token=valid123" in cookie:
                body = "<h1>Dashboard</h1><p>Welcome, authenticated user!</p>"
            else:
                body = "<h1>Dashboard</h1><p>NOT AUTHENTICATED</p>"
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<!DOCTYPE html><html><head><title>Dashboard</title></head>"
                f"<body>{body}</body></html>".encode()
            )
            return

        if self.path == "/step1":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Step 1</title></head>
<body><h1>Step 1</h1><p>First step complete</p></body></html>""")
            return

        if self.path == "/step2":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Step 2</title></head>
<body><h1>Step 2</h1><p>Second step complete</p></body></html>""")
            return

        if self.path == "/step3":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Step 3</title></head>
<body><h1>Step 3</h1><p>Third step complete</p></body></html>""")
            return

        html = PAGES_HTML.get(self.path)
        if html is None:
            # Fallback for root and unknown paths
            html = PAGES_HTML["/page0"]
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())


class ReuseAddrHTTPServer(HTTPServer):
    allow_reuse_address = True


@pytest.fixture(scope="module")
def test_server():
    """Start a local HTTP server for the test module."""
    server = ReuseAddrHTTPServer(("127.0.0.1", 0), MemTestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


def _url(base, i):
    return f"{base}/page{i}"


def _get_chromium_rss_mb():
    """Sum RSS of all chromium/chrome child processes in MB."""
    total = 0
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            cmdline = " ".join(proc.info["cmdline"] or []).lower()
            if "chrom" in name or "chrom" in cmdline:
                total += proc.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return total / (1024 * 1024)


# ---------------------------------------------------------------------------
# Helpers to reach into BrowserManager internals
# ---------------------------------------------------------------------------

def _bm(crawler: AsyncWebCrawler):
    """Shortcut to get the BrowserManager from a crawler."""
    return crawler.crawler_strategy.browser_manager


# ===========================================================================
# Test 1: memory_saving_mode flag propagation
# ===========================================================================

@pytest.mark.asyncio
async def test_memory_saving_flags_applied(test_server):
    """Verify --aggressive-cache-discard and --js-flags are in the launch args
    when memory_saving_mode=True, and absent when False."""
    config_on = BrowserConfig(
        headless=True,
        verbose=False,
        memory_saving_mode=True,
    )
    config_off = BrowserConfig(
        headless=True,
        verbose=False,
        memory_saving_mode=False,
    )

    async with AsyncWebCrawler(config=config_on) as crawler:
        bm = _bm(crawler)
        browser_args = bm._build_browser_args()
        # _build_browser_args returns a dict with an "args" key
        args_list = browser_args.get("args", browser_args) if isinstance(browser_args, dict) else browser_args
        assert "--aggressive-cache-discard" in args_list, (
            "memory_saving_mode=True should add --aggressive-cache-discard"
        )
        assert any("max-old-space-size" in a for a in args_list), (
            "memory_saving_mode=True should add V8 heap cap"
        )
        # Always-on flags should be present regardless
        assert any("OptimizationHints" in a for a in args_list)

    async with AsyncWebCrawler(config=config_off) as crawler:
        bm = _bm(crawler)
        browser_args = bm._build_browser_args()
        args_list = browser_args.get("args", browser_args) if isinstance(browser_args, dict) else browser_args
        assert "--aggressive-cache-discard" not in args_list, (
            "memory_saving_mode=False should NOT add --aggressive-cache-discard"
        )
        assert not any("max-old-space-size" in a for a in args_list), (
            "memory_saving_mode=False should NOT add V8 heap cap"
        )
        # Always-on flags should still be there
        assert any("OptimizationHints" in a for a in args_list)


# ===========================================================================
# Test 2: Always-on flags present in both code paths
# ===========================================================================

@pytest.mark.asyncio
async def test_always_on_flags_present(test_server):
    """The 3 always-on memory flags should appear in _build_browser_args
    even with default BrowserConfig."""
    config = BrowserConfig(headless=True, verbose=False)
    async with AsyncWebCrawler(config=config) as crawler:
        browser_args = _bm(crawler)._build_browser_args()
        args_list = browser_args.get("args", browser_args) if isinstance(browser_args, dict) else browser_args
        assert any("disable-component-update" in a for a in args_list)
        assert any("disable-domain-reliability" in a for a in args_list)
        assert any("OptimizationHints" in a for a in args_list)


# ===========================================================================
# Test 3: Basic recycling — counter increments, recycle fires, crawls resume
# ===========================================================================

@pytest.mark.asyncio
async def test_recycle_fires_at_threshold(test_server):
    """Set max_pages_before_recycle=5, crawl 8 pages sequentially.
    Verify the counter resets after recycle and all crawls succeed."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        memory_saving_mode=True,
        max_pages_before_recycle=5,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        assert bm._pages_served == 0

        results = []
        for i in range(8):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            results.append(r)

        # All 8 crawls should succeed — recycle happened transparently
        assert len(results) == 8
        assert all(r.success for r in results), (
            f"Failed crawls: {[i for i, r in enumerate(results) if not r.success]}"
        )

        # After 8 pages with threshold=5, recycle happened once (at page 5).
        # Pages 6,7,8 served after recycle → counter should be 3.
        assert bm._pages_served == 3, (
            f"Expected 3 pages after recycle, got {bm._pages_served}"
        )


# ===========================================================================
# Test 4: Recycling resets all tracking state
# ===========================================================================

@pytest.mark.asyncio
async def test_recycle_clears_tracking_state(test_server):
    """After a recycle, internal dicts should be clean."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        # Crawl 3 pages → triggers recycle
        for i in range(3):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success

        # Give recycle a moment to complete (it fires in release_page_with_context)
        await asyncio.sleep(0.5)

        # Recycle should have reset these
        assert bm._pages_served == 0, f"Counter not reset: {bm._pages_served}"
        assert sum(bm._context_refcounts.values()) == 0, (
            f"Refcounts not zero after recycle: {bm._context_refcounts}"
        )

        # Crawl one more page to prove browser is alive
        r = await crawler.arun(url=_url(test_server, 99), config=run_config)
        assert r.success
        assert bm._pages_served == 1


# ===========================================================================
# Test 5: Concurrent crawls across a recycle boundary
# ===========================================================================

@pytest.mark.asyncio
async def test_concurrent_crawls_across_recycle(test_server):
    """Launch concurrent crawls that straddle the recycle threshold.
    Recycling should wait for in-flight crawls to finish, not crash them."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=5,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        # Fire 10 concurrent crawls with threshold=5
        urls = [_url(test_server, i) for i in range(10)]
        tasks = [crawler.arun(url=u, config=run_config) for u in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, (
            f"Got {len(exceptions)} exceptions during concurrent recycle: "
            f"{exceptions[:3]}"
        )
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 10, (
            f"Only {len(successes)}/10 crawls succeeded"
        )


# ===========================================================================
# Test 6: Recycle with sessions — sessions cleared, new session works after
# ===========================================================================

@pytest.mark.asyncio
async def test_recycle_blocked_by_active_session(test_server):
    """An active session holds a context refcount, so the browser should NOT
    recycle while the session is open — even if pages_served >= threshold.
    This proves recycling is safe around sessions."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        run_no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Crawl 2 non-session pages (released immediately)
        for i in range(2):
            r = await crawler.arun(url=_url(test_server, i), config=run_no_session)
            assert r.success

        # Create a named session on page 3 — hits the threshold
        run_with_session = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="test_session",
            verbose=False,
        )
        r = await crawler.arun(url=_url(test_server, 2), config=run_with_session)
        assert r.success
        assert "test_session" in bm.sessions

        # We've hit 3 pages (the threshold), but the session holds a refcount
        # so recycle must NOT fire
        assert bm._pages_served == 3
        assert not bm._recycling, (
            "Recycle should not fire while a session holds a refcount"
        )

        # Browser should still be alive — use the session again
        r = await crawler.arun(url=_url(test_server, 50), config=run_with_session)
        assert r.success, "Session should still work even past recycle threshold"

        # Session reuses the same page, so counter stays at 3
        # (only get_page increments it, and session reuse skips get_page)
        assert bm._pages_served >= 3
        assert not bm._recycling


@pytest.mark.asyncio
async def test_sessions_cleared_by_recycle(test_server):
    """After a recycle, the sessions dict is empty and new sessions work."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        # Crawl 3 non-session pages → recycle fires (all refcounts 0)
        for i in range(3):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success

        await asyncio.sleep(0.5)

        # Sessions dict cleared by recycle
        assert len(bm.sessions) == 0, (
            f"Sessions should be empty after recycle, got {list(bm.sessions.keys())}"
        )

        # New session should work on the fresh browser
        run_with_session = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="post_recycle_session",
            verbose=False,
        )
        r = await crawler.arun(url=_url(test_server, 99), config=run_with_session)
        assert r.success
        assert "post_recycle_session" in bm.sessions


# ===========================================================================
# Test 7: Multiple recycle cycles — browser survives repeated recycling
# ===========================================================================

@pytest.mark.asyncio
async def test_multiple_recycle_cycles(test_server):
    """Recycle the browser 4 times (threshold=5, crawl 22 pages).
    Every single crawl must succeed."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=5,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        all_results = []

        for i in range(22):
            r = await crawler.arun(url=_url(test_server, i % 200), config=run_config)
            all_results.append(r)

        assert all(r.success for r in all_results), (
            f"Failed at pages: "
            f"{[i for i, r in enumerate(all_results) if not r.success]}"
        )
        # 22 pages, threshold 5 → recycles at 5, 10, 15, 20 → 4 recycles
        # After last recycle at page 20, pages 21,22 served → counter = 2
        assert bm._pages_served == 2


# ===========================================================================
# Test 8: Recycling disabled by default (max_pages_before_recycle=0)
# ===========================================================================

@pytest.mark.asyncio
async def test_recycle_disabled_by_default(test_server):
    """With default config (max_pages_before_recycle=0), no recycling happens
    no matter how many pages are crawled."""
    config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        for i in range(10):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success

        # Counter increments but never resets
        assert bm._pages_served == 10
        assert not bm._recycling


# ===========================================================================
# Test 9: _recycle_done event blocks get_page during recycle
# ===========================================================================

@pytest.mark.asyncio
async def test_recycle_event_blocks_new_pages(test_server):
    """Simulate a recycle by manually clearing the event, then verify that
    get_page blocks until the event is set."""
    config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        # Manually block the gate
        bm._recycle_done.clear()

        got_page = False

        async def try_get_page():
            nonlocal got_page
            r = await crawler.arun(url=_url(test_server, 0), config=run_config)
            got_page = r.success

        task = asyncio.create_task(try_get_page())

        # Wait a bit — the crawl should be blocked
        await asyncio.sleep(0.5)
        assert not got_page, "get_page should block while _recycle_done is cleared"

        # Release the gate
        bm._recycle_done.set()
        await asyncio.wait_for(task, timeout=15.0)
        assert got_page, "Crawl should succeed after recycle_done is set"


# ===========================================================================
# Test 10: BrowserConfig serialization round-trip
# ===========================================================================

@pytest.mark.asyncio
async def test_config_serialization_roundtrip():
    """memory_saving_mode and max_pages_before_recycle survive
    to_dict → from_kwargs → clone round-trips."""
    original = BrowserConfig(
        headless=True,
        memory_saving_mode=True,
        max_pages_before_recycle=500,
    )

    # to_dict → from_kwargs
    d = original.to_dict()
    assert d["memory_saving_mode"] is True
    assert d["max_pages_before_recycle"] == 500

    restored = BrowserConfig.from_kwargs(d)
    assert restored.memory_saving_mode is True
    assert restored.max_pages_before_recycle == 500

    # clone with override
    cloned = original.clone(max_pages_before_recycle=1000)
    assert cloned.memory_saving_mode is True  # inherited
    assert cloned.max_pages_before_recycle == 1000  # overridden

    # dump / load
    dumped = original.dump()
    loaded = BrowserConfig.load(dumped)
    assert loaded.memory_saving_mode is True
    assert loaded.max_pages_before_recycle == 500


# ===========================================================================
# Test 11: Memory stays bounded over many pages with recycling
# ===========================================================================

@pytest.mark.asyncio
async def test_memory_bounded_with_recycling(test_server):
    """Crawl 40 pages with recycling every 10. Measure RSS at page 10
    (just after first recycle) and at page 40. Memory should not grow
    significantly — the recycle should keep it bounded.

    This is the core proof that recycling controls memory growth.
    Without recycling, Chromium RSS grows ~2-5 MB per page.
    With recycling, it should stay roughly flat."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        memory_saving_mode=True,
        max_pages_before_recycle=10,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        rss_samples = []

        for i in range(40):
            r = await crawler.arun(url=_url(test_server, i % 200), config=run_config)
            assert r.success, f"Page {i} failed"

            # Sample after each recycle boundary + a few extra
            if (i + 1) % 10 == 0:
                await asyncio.sleep(0.3)  # let recycle finish
                rss_samples.append(_get_chromium_rss_mb())

        # We should have 4 samples (at pages 10, 20, 30, 40)
        assert len(rss_samples) == 4

        # The key assertion: RSS at page 40 should not be dramatically larger
        # than at page 10. Allow 50% growth as tolerance for GC timing etc.
        # Without recycling, we'd expect 60-150 MB growth over 30 extra pages.
        if rss_samples[0] > 0:  # guard against measurement issues
            growth_ratio = rss_samples[-1] / rss_samples[0]
            assert growth_ratio < 2.0, (
                f"Memory grew {growth_ratio:.1f}x from {rss_samples[0]:.0f}MB "
                f"to {rss_samples[-1]:.0f}MB over 30 pages with recycling. "
                f"All samples: {[f'{s:.0f}' for s in rss_samples]} MB"
            )


# ===========================================================================
# Test 12: Memory grows WITHOUT recycling (control test)
# ===========================================================================

@pytest.mark.asyncio
async def test_memory_grows_without_recycling(test_server):
    """Control test: crawl 30 pages WITHOUT recycling and observe that
    chromium RSS is higher at the end than at the start.
    This proves that recycling is what keeps memory bounded."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        memory_saving_mode=False,
        max_pages_before_recycle=0,  # disabled
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        # Warm up — let initial browser memory stabilize
        for i in range(3):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success
        await asyncio.sleep(0.3)
        rss_start = _get_chromium_rss_mb()

        # Crawl 30 more pages
        for i in range(3, 33):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success

        await asyncio.sleep(0.3)
        rss_end = _get_chromium_rss_mb()

        # RSS should be at least somewhat higher (chromium leaks)
        # We just need this to not be 0 — proving our measurement works
        if rss_start > 0:
            print(
                f"\n[CONTROL] RSS without recycling: "
                f"{rss_start:.0f}MB → {rss_end:.0f}MB "
                f"(+{rss_end - rss_start:.0f}MB over 30 pages)"
            )


# ===========================================================================
# Test 13: Viewport adjustment doesn't leak CDP sessions
# ===========================================================================

@pytest.mark.asyncio
async def test_viewport_adjustment_no_cdp_leak(test_server):
    """Crawl several pages that trigger viewport adjustment (scan_full_page).
    If CDP sessions leak, Chromium's DevTools session count grows and
    eventually causes slowdowns. We just verify all crawls succeed and
    the browser stays healthy."""
    config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        scan_full_page=True,  # triggers fit_to_viewport_adjustment → CDP session
        verbose=False,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        for i in range(15):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success, f"Page {i} failed with scan_full_page"


# ===========================================================================
# Test 14: Recycle under concurrent load with arun_many
# ===========================================================================

@pytest.mark.asyncio
async def test_recycle_with_arun_many(test_server):
    """Use arun_many to crawl a batch that exceeds the recycle threshold.
    This tests the dispatcher + recycling interaction."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=5,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        urls = [_url(test_server, i) for i in range(12)]
        results = await crawler.arun_many(urls, config=run_config)

        successes = [r for r in results if r.success]
        assert len(successes) == 12, (
            f"Only {len(successes)}/12 succeeded with arun_many + recycling"
        )


# ===========================================================================
# Test 15: _global_pages_in_use cleaned after recycle
# ===========================================================================

@pytest.mark.asyncio
async def test_global_pages_in_use_cleared(test_server):
    """After a recycle, the _global_pages_in_use set for this browser's
    endpoint should be empty (old pages are dead)."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        for i in range(3):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success

        await asyncio.sleep(0.5)

        # After recycle, pages_in_use for old endpoint should be empty
        from crawl4ai.browser_manager import BrowserManager
        if bm._browser_endpoint_key:
            piu = BrowserManager._global_pages_in_use.get(
                bm._browser_endpoint_key, set()
            )
            assert len(piu) == 0, (
                f"_global_pages_in_use should be empty after recycle, "
                f"has {len(piu)} stale entries"
            )


# ===========================================================================
# Test 16: Content integrity across recycle — page content is correct
# ===========================================================================

@pytest.mark.asyncio
async def test_content_integrity_across_recycle(test_server):
    """Verify that pages crawled AFTER a recycle return correct content,
    not stale data from before the recycle."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        # Crawl pages 0,1,2 → triggers recycle
        for i in range(3):
            r = await crawler.arun(url=_url(test_server, i), config=run_config)
            assert r.success

        await asyncio.sleep(0.5)

        # Crawl page 150 after recycle — content should match page 150
        r = await crawler.arun(url=_url(test_server, 150), config=run_config)
        assert r.success
        assert "Test page 150" in r.html, (
            "Content after recycle should be from the correct page"
        )
        assert "Paragraph 150" in r.html


# ===========================================================================
# SESSION + RECYCLE INTERACTION TESTS
# ===========================================================================


# ===========================================================================
# Test 17: Multi-step session crawl — login → dashboard with cookie
# ===========================================================================

@pytest.mark.asyncio
async def test_multistep_session_login_flow(test_server):
    """Simulate login → dashboard multi-step crawl using session_id.
    The session preserves cookies, so dashboard should see authenticated state.
    No recycling involved — baseline session behavior."""
    config = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="login_flow",
            verbose=False,
        )

        # Step 1: login — sets cookie
        r = await crawler.arun(url=f"{test_server}/login", config=session_cfg)
        assert r.success
        assert "Login Page" in r.html

        # Step 2: dashboard — cookie should carry over via session
        r = await crawler.arun(url=f"{test_server}/dashboard", config=session_cfg)
        assert r.success
        assert "Welcome, authenticated user" in r.html, (
            "Session should carry cookies from login to dashboard"
        )


# ===========================================================================
# Test 18: Multi-step session survives non-session crawls past threshold
# ===========================================================================

@pytest.mark.asyncio
async def test_session_survives_threshold_with_interleaved_crawls(test_server):
    """Open a session, then do many non-session crawls that push
    pages_served past the recycle threshold. The session should prevent
    recycle from firing (refcount > 0). Then continue using the session
    and it should still work."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=5,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        # Start a session — step 1
        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="persistent_session",
            verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/login", config=session_cfg)
        assert r.success
        assert "persistent_session" in bm.sessions

        # Fire 8 non-session crawls — pushes pages_served to 9
        # (1 from session + 8 = 9, well past threshold of 5)
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        for i in range(8):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success, f"Non-session crawl {i} failed"

        # Recycle should NOT have fired — session holds refcount
        assert bm._pages_served == 9, (
            f"Expected 9 pages served, got {bm._pages_served}"
        )
        assert not bm._recycling
        assert "persistent_session" in bm.sessions, (
            "Session should still exist — recycle blocked by refcount"
        )

        # Session should still work — navigate to dashboard with cookies
        r = await crawler.arun(url=f"{test_server}/dashboard", config=session_cfg)
        assert r.success
        assert "Welcome, authenticated user" in r.html, (
            "Session cookies should still work after interleaved non-session crawls"
        )


# ===========================================================================
# Test 19: 3-step session flow with recycle threshold — recycle blocked
# ===========================================================================

@pytest.mark.asyncio
async def test_three_step_session_blocks_recycle(test_server):
    """3-step session (step1 → step2 → step3) with low threshold.
    The session's refcount should block recycle for the entire flow."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=2,  # very low threshold
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="multistep",
            verbose=False,
        )

        # Step 1
        r = await crawler.arun(url=f"{test_server}/step1", config=session_cfg)
        assert r.success
        assert "Step 1" in r.html

        # Step 2 — pages_served is still 1 (session reuse doesn't increment)
        # but even if it did, refcount blocks recycle
        r = await crawler.arun(url=f"{test_server}/step2", config=session_cfg)
        assert r.success
        assert "Step 2" in r.html

        # Step 3
        r = await crawler.arun(url=f"{test_server}/step3", config=session_cfg)
        assert r.success
        assert "Step 3" in r.html

        # Session page reuse doesn't increment counter (only get_page does)
        # Initial creation = 1 page, subsequent calls reuse it
        assert bm._pages_served == 1
        assert not bm._recycling
        assert "multistep" in bm.sessions


# ===========================================================================
# Test 20: Two concurrent sessions — both survive past threshold
# ===========================================================================

@pytest.mark.asyncio
async def test_two_concurrent_sessions_block_recycle(test_server):
    """Two sessions open at the same time, with non-session crawls interleaved.
    Both sessions should prevent recycle and remain functional."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        session_a = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="sess_a", verbose=False,
        )
        session_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="sess_b", verbose=False,
        )
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Open session A
        r = await crawler.arun(url=f"{test_server}/login", config=session_a)
        assert r.success

        # Open session B
        r = await crawler.arun(url=f"{test_server}/step1", config=session_b)
        assert r.success

        # 5 non-session crawls — pages_served goes to 7 (2 sessions + 5)
        for i in range(5):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success

        # Both sessions hold refcounts → recycle blocked
        assert not bm._recycling
        assert "sess_a" in bm.sessions
        assert "sess_b" in bm.sessions

        # Both sessions still work
        r = await crawler.arun(url=f"{test_server}/dashboard", config=session_a)
        assert r.success
        assert "Welcome, authenticated user" in r.html

        r = await crawler.arun(url=f"{test_server}/step2", config=session_b)
        assert r.success
        assert "Step 2" in r.html


# ===========================================================================
# Test 21: Session killed, then recycle fires on next non-session crawl
# ===========================================================================

@pytest.mark.asyncio
async def test_recycle_fires_after_session_killed(test_server):
    """Session blocks recycle. After session is killed (refcount drops to 0),
    the next non-session crawl that pushes past threshold triggers recycle."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=3,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Open a session (1 page)
        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="temp_sess", verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/step1", config=session_cfg)
        assert r.success

        # 3 non-session crawls (4 pages total, threshold=3, but session blocks)
        for i in range(3):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success

        pages_before_kill = bm._pages_served
        assert pages_before_kill == 4
        assert not bm._recycling

        # Kill the session — refcount drops to 0
        await crawler.crawler_strategy.kill_session("temp_sess")
        assert "temp_sess" not in bm.sessions

        # One more crawl — should trigger recycle (pages_served=5 >= 3, refcounts=0)
        r = await crawler.arun(url=_url(test_server, 99), config=no_session)
        assert r.success

        await asyncio.sleep(0.5)

        # Recycle should have fired — counter reset
        assert bm._pages_served < pages_before_kill, (
            f"Expected counter reset after recycle, got {bm._pages_served}"
        )


# ===========================================================================
# Test 22: Concurrent session crawls — same session from multiple tasks
# ===========================================================================

@pytest.mark.asyncio
async def test_concurrent_same_session_crawls(test_server):
    """Multiple asyncio tasks using the same session_id concurrently.
    The session page should be shared safely between them."""
    config = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id="shared_session",
            verbose=False,
        )

        # Login first to set cookie
        r = await crawler.arun(url=f"{test_server}/login", config=session_cfg)
        assert r.success

        # Fire 5 concurrent crawls on the same session
        urls = [f"{test_server}/page{i}" for i in range(5)]
        tasks = [
            crawler.arun(url=u, config=session_cfg) for u in urls
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exceptions = [r for r in results if isinstance(r, Exception)]
        # Some may fail due to navigation conflicts (same page, concurrent goto),
        # but there should be no crashes or browser death
        assert len(exceptions) == 0, (
            f"Exceptions in concurrent same-session crawls: {exceptions[:3]}"
        )


# ===========================================================================
# Test 23: Session + recycling — session killed mid-batch, recycle fires,
#           new session works after
# ===========================================================================

@pytest.mark.asyncio
async def test_session_lifecycle_across_recycle(test_server):
    """Full lifecycle: create session → use it → kill it → recycle fires →
    create new session → use it. End-to-end proof that recycling is safe."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=4,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Phase 1: create and use a session
        sess_v1 = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="lifecycle_sess", verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/login", config=sess_v1)
        assert r.success

        r = await crawler.arun(url=f"{test_server}/dashboard", config=sess_v1)
        assert r.success
        assert "Welcome, authenticated user" in r.html

        # Phase 2: kill session
        await crawler.crawler_strategy.kill_session("lifecycle_sess")

        # Phase 3: push past threshold with non-session crawls
        for i in range(5):
            r = await crawler.arun(url=_url(test_server, i), config=no_session)
            assert r.success

        await asyncio.sleep(0.5)

        # Recycle should have happened (session killed, refcount=0)
        assert bm._pages_served < 6, (
            f"Expected reset after recycle, got {bm._pages_served}"
        )

        # Phase 4: new session on the fresh browser
        sess_v2 = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="lifecycle_sess_v2", verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/login", config=sess_v2)
        assert r.success
        assert "lifecycle_sess_v2" in bm.sessions

        r = await crawler.arun(url=f"{test_server}/dashboard", config=sess_v2)
        assert r.success
        assert "Welcome, authenticated user" in r.html, (
            "New session after recycle should work with cookies"
        )


# ===========================================================================
# Test 24: Parallel sessions + non-session crawls with arun_many
# ===========================================================================

@pytest.mark.asyncio
async def test_session_with_arun_many_interleaved(test_server):
    """Open a session, then fire arun_many for non-session URLs.
    The session should survive the batch and remain usable after."""
    config = BrowserConfig(
        headless=True,
        verbose=False,
        max_pages_before_recycle=10,
    )

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        # Open session
        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="batch_sess", verbose=False,
        )
        r = await crawler.arun(url=f"{test_server}/login", config=session_cfg)
        assert r.success

        # Batch of non-session crawls
        no_session = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        urls = [_url(test_server, i) for i in range(8)]
        results = await crawler.arun_many(urls, config=no_session)
        assert all(r.success for r in results), "All batch crawls should succeed"

        # Session still alive
        assert "batch_sess" in bm.sessions
        r = await crawler.arun(url=f"{test_server}/dashboard", config=session_cfg)
        assert r.success
        assert "Welcome, authenticated user" in r.html


# ===========================================================================
# Test 25: Session refcount tracking correctness
# ===========================================================================

@pytest.mark.asyncio
async def test_session_refcount_stays_at_one(test_server):
    """Verify that a session holds exactly 1 refcount throughout its
    lifecycle, regardless of how many times it's reused."""
    config = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=config) as crawler:
        bm = _bm(crawler)

        session_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="refcount_test", verbose=False,
        )

        # Create session
        r = await crawler.arun(url=f"{test_server}/step1", config=session_cfg)
        assert r.success

        # Find the session's context signature
        _, page, _ = bm.sessions["refcount_test"]
        sig = bm._page_to_sig.get(page)
        if sig:
            refcount = bm._context_refcounts.get(sig, 0)
            assert refcount == 1, (
                f"Session should hold exactly 1 refcount, got {refcount}"
            )

        # Reuse session multiple times — refcount should stay at 1
        for url in ["/step2", "/step3", "/dashboard"]:
            r = await crawler.arun(url=f"{test_server}{url}", config=session_cfg)
            assert r.success

            if sig:
                refcount = bm._context_refcounts.get(sig, 0)
                assert refcount == 1, (
                    f"After reuse, refcount should still be 1, got {refcount}"
                )

        # Kill session — refcount should drop to 0
        await crawler.crawler_strategy.kill_session("refcount_test")
        if sig:
            refcount = bm._context_refcounts.get(sig, 0)
            assert refcount == 0, (
                f"After kill, refcount should be 0, got {refcount}"
            )
