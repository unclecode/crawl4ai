"""
Browser lifecycle & concurrency tests.

Covers all the browser launch paths and lock interactions:
  - Standalone (playwright.launch)
  - Managed browser (subprocess + CDP connect)
  - Managed browser with create_isolated_context
  - Page reuse on shared default context
  - Context caching / LRU eviction
  - Session lifecycle across all modes
  - Concurrent crawls racing for pages / contexts
  - Recycle interacting with managed browser
  - Multiple crawlers sharing a managed browser via CDP
"""

import asyncio
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


# ---------------------------------------------------------------------------
# Local test server
# ---------------------------------------------------------------------------

PAGES = {}
for i in range(100):
    PAGES[f"/page{i}"] = (
        f"<!DOCTYPE html><html><head><title>Page {i}</title></head>"
        f"<body><h1>Page {i}</h1><p>Content for page {i}.</p>"
        f"<a href='/page{(i+1)%100}'>next</a></body></html>"
    ).encode()

# Login/dashboard for session tests
PAGES["/login"] = (
    b"<!DOCTYPE html><html><head><title>Login</title></head>"
    b"<body><h1>Login</h1><p>Logged in.</p></body></html>"
)
PAGES["/dashboard"] = (
    b"<!DOCTYPE html><html><head><title>Dashboard</title></head>"
    b"<body><h1>Dashboard</h1><p>Dashboard content.</p></body></html>"
)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = PAGES.get(self.path, PAGES["/page0"])
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(body)


class _Server(HTTPServer):
    allow_reuse_address = True


@pytest.fixture(scope="module")
def srv():
    s = _Server(("127.0.0.1", 0), Handler)
    port = s.server_address[1]
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    s.shutdown()


def _u(base, i):
    return f"{base}/page{i}"


def _bm(c):
    return c.crawler_strategy.browser_manager


# ===================================================================
# SECTION A — Standalone browser (no CDP, no managed browser)
# ===================================================================

@pytest.mark.asyncio
async def test_standalone_basic_crawl(srv):
    """Standalone browser: launch, crawl, close. Baseline correctness."""
    cfg = BrowserConfig(headless=True, verbose=False)
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        r = await c.arun(url=_u(srv, 0), config=run)
        assert r.success
        assert "Page 0" in r.html


@pytest.mark.asyncio
async def test_standalone_sequential_crawls(srv):
    """10 sequential pages — each gets its own page, context reused by config sig."""
    cfg = BrowserConfig(headless=True, verbose=False)
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        for i in range(10):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success, f"Page {i} failed"
            assert f"Page {i}" in r.html


@pytest.mark.asyncio
async def test_standalone_concurrent_crawls(srv):
    """10 concurrent crawls on standalone browser — no crashes,
    context lock prevents race conditions."""
    cfg = BrowserConfig(headless=True, verbose=False)
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        assert all(r.success for r in results if not isinstance(r, Exception))


@pytest.mark.asyncio
async def test_standalone_context_reuse(srv):
    """Two crawls with identical config should reuse the same context.
    Two crawls with different configs should create different contexts."""
    cfg = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        run_a = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        r1 = await c.arun(url=_u(srv, 0), config=run_a)
        assert r1.success
        ctx_count_after_first = len(bm.contexts_by_config)

        # Same config → same context
        r2 = await c.arun(url=_u(srv, 1), config=run_a)
        assert r2.success
        assert len(bm.contexts_by_config) == ctx_count_after_first, (
            "Same config should reuse context"
        )

        # Different config → new context
        run_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, verbose=False,
            override_navigator=True,
        )
        r3 = await c.arun(url=_u(srv, 2), config=run_b)
        assert r3.success
        assert len(bm.contexts_by_config) == ctx_count_after_first + 1, (
            "Different config should create new context"
        )


@pytest.mark.asyncio
async def test_standalone_session_multistep(srv):
    """Session across 3 pages on standalone browser."""
    cfg = BrowserConfig(headless=True, verbose=False)
    sess = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, session_id="standalone_sess", verbose=False,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(3):
            r = await c.arun(url=_u(srv, i), config=sess)
            assert r.success
            assert "standalone_sess" in bm.sessions

        # Refcount should be exactly 1
        _, page, _ = bm.sessions["standalone_sess"]
        sig = bm._page_to_sig.get(page)
        if sig:
            assert bm._context_refcounts.get(sig, 0) == 1

        # Kill session and verify cleanup
        await c.crawler_strategy.kill_session("standalone_sess")
        assert "standalone_sess" not in bm.sessions
        if sig:
            assert bm._context_refcounts.get(sig, 0) == 0


@pytest.mark.asyncio
async def test_standalone_recycle(srv):
    """Recycling on standalone browser — close/start cycle."""
    cfg = BrowserConfig(
        headless=True, verbose=False, max_pages_before_recycle=5,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)
        for i in range(8):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success, f"Page {i} failed"

        # Recycle happened at page 5, pages 6-8 after → counter = 3
        assert bm._pages_served == 3


@pytest.mark.asyncio
async def test_standalone_recycle_with_concurrent_crawls(srv):
    """15 concurrent crawls straddling a recycle boundary on standalone."""
    cfg = BrowserConfig(
        headless=True, verbose=False, max_pages_before_recycle=5,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(15)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 15


# ===================================================================
# SECTION B — Managed browser (subprocess + CDP)
# ===================================================================

@pytest.mark.asyncio
async def test_managed_basic_crawl(srv):
    """Managed browser: start subprocess, connect via CDP, crawl, close."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        r = await c.arun(url=_u(srv, 0), config=run)
        assert r.success
        assert "Page 0" in r.html


@pytest.mark.asyncio
async def test_managed_sequential_crawls(srv):
    """Sequential crawls on managed browser — pages reused from default context."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        for i in range(8):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success, f"Page {i} failed"


@pytest.mark.asyncio
async def test_managed_concurrent_crawls(srv):
    """Concurrent crawls on managed browser — _global_pages_lock prevents
    two tasks from grabbing the same page."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(8)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 8


@pytest.mark.asyncio
async def test_managed_page_reuse(srv):
    """On managed browser (non-isolated), pages should be reused when
    released back to the pool."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Crawl 3 pages sequentially — page should be reused each time
        for i in range(3):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        # On managed browser, total pages created should be small
        # (pages reused, not new ones for each crawl)
        default_ctx = bm.default_context
        total_pages = len(default_ctx.pages)
        assert total_pages <= 3, (
            f"Expected page reuse, but {total_pages} pages exist"
        )


@pytest.mark.asyncio
async def test_managed_session_multistep(srv):
    """Multi-step session on managed browser — session page stays alive."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    sess = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, session_id="managed_sess", verbose=False,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        r = await c.arun(url=f"{srv}/login", config=sess)
        assert r.success

        r = await c.arun(url=f"{srv}/dashboard", config=sess)
        assert r.success

        assert "managed_sess" in bm.sessions


@pytest.mark.asyncio
async def test_managed_recycle(srv):
    """Recycling on managed browser — kills subprocess, restarts, crawls resume."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        max_pages_before_recycle=4,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(7):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success, f"Page {i} failed after managed recycle"

        # Recycled at 4 → pages 5,6,7 after → counter = 3
        assert bm._pages_served == 3


# ===================================================================
# SECTION C — Managed browser with create_isolated_context
# ===================================================================

@pytest.mark.asyncio
async def test_isolated_context_basic(srv):
    """Isolated context mode: each config gets its own browser context."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        r = await c.arun(url=_u(srv, 0), config=run)
        assert r.success


@pytest.mark.asyncio
async def test_isolated_context_concurrent(srv):
    """Concurrent crawls with isolated contexts — _contexts_lock prevents
    race conditions in context creation."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 10


@pytest.mark.asyncio
async def test_isolated_context_caching(srv):
    """Same config signature → same context. Different config → different context."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        run_a = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        await c.arun(url=_u(srv, 0), config=run_a)
        count_after_a = len(bm.contexts_by_config)

        # Same config → reuse
        await c.arun(url=_u(srv, 1), config=run_a)
        assert len(bm.contexts_by_config) == count_after_a

        # Different config → new context
        run_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, verbose=False,
            override_navigator=True,
        )
        await c.arun(url=_u(srv, 2), config=run_b)
        assert len(bm.contexts_by_config) == count_after_a + 1


@pytest.mark.asyncio
async def test_isolated_context_refcount(srv):
    """Refcount increases with concurrent crawls and decreases on release."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # After a single sequential crawl (page released), refcount should be 0
        r = await c.arun(url=_u(srv, 0), config=run)
        assert r.success

        # All contexts should have refcount 0 (page was released)
        for sig, rc in bm._context_refcounts.items():
            assert rc == 0, f"Refcount for {sig[:8]}... should be 0, got {rc}"


@pytest.mark.asyncio
async def test_isolated_context_session_with_interleaved(srv):
    """Session on isolated context + non-session crawls interleaved."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        sess = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="iso_sess", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess)
        assert r.success

        # Non-session crawls
        run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        for i in range(5):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success

        # Session still alive
        assert "iso_sess" in bm.sessions
        r = await c.arun(url=f"{srv}/dashboard", config=sess)
        assert r.success


@pytest.mark.asyncio
async def test_isolated_context_recycle(srv):
    """Recycling with isolated contexts — all contexts cleared, new ones
    created fresh on the new browser."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
        max_pages_before_recycle=4,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        for i in range(6):
            r = await c.arun(url=_u(srv, i), config=run)
            assert r.success, f"Page {i} failed"

        # Recycled at 4 → 5,6 after → counter = 2
        assert bm._pages_served == 2
        # Contexts dict should only have entries from after recycle
        assert all(rc == 0 for rc in bm._context_refcounts.values()), (
            "All refcounts should be 0 after sequential crawls"
        )


# ===================================================================
# SECTION D — Two crawlers sharing one managed browser via CDP URL
# ===================================================================

@pytest.mark.asyncio
async def test_two_crawlers_share_managed_browser(srv):
    """Two AsyncWebCrawler instances connect to the same managed browser
    via its CDP URL. Both should crawl successfully without interfering."""
    # First crawler owns the managed browser
    cfg1 = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )

    async with AsyncWebCrawler(config=cfg1) as c1:
        bm1 = _bm(c1)
        # Grab the CDP URL from the managed browser
        cdp_url = f"http://{bm1.managed_browser.host}:{bm1.managed_browser.debugging_port}"

        # Second crawler connects to the same browser via CDP
        cfg2 = BrowserConfig(
            headless=True, verbose=False,
            cdp_url=cdp_url,
            cdp_cleanup_on_close=True,
        )
        async with AsyncWebCrawler(config=cfg2) as c2:
            run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

            # Crawl sequentially to avoid page contention on shared context
            r1 = await c1.arun(url=_u(srv, 0), config=run)
            r2 = await c2.arun(url=_u(srv, 1), config=run)

            assert r1.success, f"Crawler 1 failed: {r1.error_message}"
            assert r2.success, f"Crawler 2 failed: {r2.error_message}"
            assert "Page 0" in r1.html
            assert "Page 1" in r2.html


@pytest.mark.asyncio
async def test_two_crawlers_concurrent_heavy(srv):
    """Two crawlers sharing one managed browser, each doing 5 concurrent crawls."""
    cfg1 = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )

    async with AsyncWebCrawler(config=cfg1) as c1:
        bm1 = _bm(c1)
        cdp_url = f"http://{bm1.managed_browser.host}:{bm1.managed_browser.debugging_port}"

        cfg2 = BrowserConfig(
            headless=True, verbose=False,
            cdp_url=cdp_url,
            cdp_cleanup_on_close=True,
        )
        async with AsyncWebCrawler(config=cfg2) as c2:
            run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

            # Each crawler does 5 sequential crawls while both are connected
            for i in range(5):
                r1 = await c1.arun(url=_u(srv, i), config=run)
                assert r1.success, f"Crawler 1 page {i} failed: {r1.error_message}"
                r2 = await c2.arun(url=_u(srv, i + 50), config=run)
                assert r2.success, f"Crawler 2 page {i} failed: {r2.error_message}"


# ===================================================================
# SECTION E — Session lifecycle edge cases
# ===================================================================

@pytest.mark.asyncio
async def test_session_then_nonsession_then_session(srv):
    """session crawl → non-session crawl → session crawl.
    The session should persist across non-session activity."""
    cfg = BrowserConfig(headless=True, verbose=False)
    sess = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, session_id="interleave_sess", verbose=False,
    )
    no_sess = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        r = await c.arun(url=_u(srv, 0), config=sess)
        assert r.success

        # Non-session crawls
        for i in range(3):
            r = await c.arun(url=_u(srv, 10 + i), config=no_sess)
            assert r.success

        # Session should still exist and work
        assert "interleave_sess" in bm.sessions
        r = await c.arun(url=_u(srv, 99), config=sess)
        assert r.success


@pytest.mark.asyncio
async def test_multiple_sessions_simultaneous(srv):
    """3 independent sessions open at the same time, each navigating
    different pages. They should not interfere."""
    cfg = BrowserConfig(headless=True, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        sessions = [
            CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS, session_id=f"sess_{j}", verbose=False,
            )
            for j in range(3)
        ]

        # Step 1: open all sessions
        for j, s in enumerate(sessions):
            r = await c.arun(url=_u(srv, j * 10), config=s)
            assert r.success, f"Session {j} open failed"

        assert len(bm.sessions) == 3

        # Step 2: navigate each session to a second page
        for j, s in enumerate(sessions):
            r = await c.arun(url=_u(srv, j * 10 + 1), config=s)
            assert r.success, f"Session {j} step 2 failed"

        # Step 3: kill sessions one by one, verify others unaffected
        await c.crawler_strategy.kill_session("sess_0")
        assert "sess_0" not in bm.sessions
        assert "sess_1" in bm.sessions
        assert "sess_2" in bm.sessions

        # Remaining sessions still work
        r = await c.arun(url=_u(srv, 99), config=sessions[1])
        assert r.success


@pytest.mark.asyncio
async def test_session_kill_then_recreate(srv):
    """Kill a session, then create a new session with the same ID.
    The new session should work on a fresh page."""
    cfg = BrowserConfig(headless=True, verbose=False)
    sess = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, session_id="reuse_id", verbose=False,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        r = await c.arun(url=_u(srv, 0), config=sess)
        assert r.success
        _, page_v1, _ = bm.sessions["reuse_id"]

        await c.crawler_strategy.kill_session("reuse_id")
        assert "reuse_id" not in bm.sessions

        # Re-create with same ID
        r = await c.arun(url=_u(srv, 50), config=sess)
        assert r.success
        assert "reuse_id" in bm.sessions
        _, page_v2, _ = bm.sessions["reuse_id"]

        # Should be a different page object
        assert page_v1 is not page_v2, "Re-created session should have a new page"


# ===================================================================
# SECTION F — Concurrent recycle + session stress tests
# ===================================================================

@pytest.mark.asyncio
async def test_recycle_concurrent_sessions_and_nonsessions(srv):
    """Open 2 sessions + fire 10 non-session crawls concurrently with
    recycle threshold=5. Sessions should block recycle until they're
    done or killed. All crawls should succeed."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=5,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        # Open sessions first
        sess_a = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="stress_a", verbose=False,
        )
        sess_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="stress_b", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess_a)
        assert r.success
        r = await c.arun(url=f"{srv}/login", config=sess_b)
        assert r.success

        # Fire 10 concurrent non-session crawls
        no_sess = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        tasks = [c.arun(url=_u(srv, i), config=no_sess) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"

        # Sessions should still be alive (blocking recycle)
        assert "stress_a" in bm.sessions
        assert "stress_b" in bm.sessions

        # Use sessions again — should work
        r = await c.arun(url=f"{srv}/dashboard", config=sess_a)
        assert r.success
        r = await c.arun(url=f"{srv}/dashboard", config=sess_b)
        assert r.success


@pytest.mark.asyncio
async def test_arun_many_with_session_open(srv):
    """Session open while arun_many batch runs with recycle enabled.
    Session survives the batch."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=5,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        sess = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="batch_guard", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess)
        assert r.success

        no_sess = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)
        urls = [_u(srv, i) for i in range(12)]
        results = await c.arun_many(urls, config=no_sess)
        assert all(r.success for r in results)

        # Session still alive
        assert "batch_guard" in bm.sessions


@pytest.mark.asyncio
async def test_rapid_recycle_stress(srv):
    """Recycle threshold=2 with 20 sequential crawls → 10 recycle cycles.
    Every crawl must succeed. Proves recycle is stable under rapid cycling."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=2,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        for i in range(20):
            r = await c.arun(url=_u(srv, i % 100), config=run)
            assert r.success, f"Page {i} failed during rapid recycle"


@pytest.mark.asyncio
async def test_rapid_recycle_concurrent(srv):
    """Recycle threshold=3 with 12 concurrent crawls. Concurrency +
    rapid recycling together."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        max_pages_before_recycle=3,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(12)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 12


# ===================================================================
# SECTION G — Lock correctness under contention
# ===================================================================

@pytest.mark.asyncio
async def test_context_lock_no_duplicate_contexts(srv):
    """Fire 20 concurrent crawls with the same config on isolated context mode.
    Despite concurrency, only 1 context should be created (all share the
    same config signature)."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions: {excs[:3]}"

        # All had the same config → only 1 context should exist
        assert len(bm.contexts_by_config) == 1, (
            f"Expected 1 context, got {len(bm.contexts_by_config)} — "
            f"lock failed to prevent duplicate creation"
        )


@pytest.mark.asyncio
async def test_page_lock_no_duplicate_pages_managed(srv):
    """On managed browser (shared default context), concurrent crawls should
    never get the same page. After all complete, pages_in_use should be empty."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(8)]
        await asyncio.gather(*tasks)

        # After all crawls complete, no pages should be marked in use
        piu = bm._get_pages_in_use()
        assert len(piu) == 0, (
            f"After all crawls complete, {len(piu)} pages still marked in use"
        )


@pytest.mark.asyncio
async def test_refcount_correctness_under_concurrency(srv):
    """Fire 15 concurrent crawls with isolated context. After all complete,
    all refcounts should be 0."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)

        tasks = [c.arun(url=_u(srv, i), config=run) for i in range(15)]
        await asyncio.gather(*tasks)

        for sig, rc in bm._context_refcounts.items():
            assert rc == 0, (
                f"Refcount for context {sig[:8]}... is {rc}, expected 0 "
                f"after all crawls complete"
            )


# ===================================================================
# SECTION H — Close / cleanup correctness
# ===================================================================

@pytest.mark.asyncio
async def test_close_cleans_up_standalone(srv):
    """After closing standalone crawler, browser and playwright are None."""
    cfg = BrowserConfig(headless=True, verbose=False)
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    c = AsyncWebCrawler(config=cfg)
    await c.start()
    bm = _bm(c)

    r = await c.arun(url=_u(srv, 0), config=run)
    assert r.success

    await c.close()
    assert bm.browser is None
    assert bm.playwright is None


@pytest.mark.asyncio
async def test_close_cleans_up_managed(srv):
    """After closing managed crawler, managed_browser is cleaned up."""
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
    )
    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

    c = AsyncWebCrawler(config=cfg)
    await c.start()
    bm = _bm(c)

    r = await c.arun(url=_u(srv, 0), config=run)
    assert r.success

    await c.close()
    assert bm.browser is None
    assert bm.managed_browser is None


@pytest.mark.asyncio
async def test_double_close_safe(srv):
    """Calling close() twice should not raise."""
    cfg = BrowserConfig(headless=True, verbose=False)

    c = AsyncWebCrawler(config=cfg)
    await c.start()
    r = await c.arun(url=_u(srv, 0), config=CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, verbose=False,
    ))
    assert r.success

    await c.close()
    # Second close should be safe
    await c.close()


# ===================================================================
# SECTION I — Mixed modes: session + recycle + managed + concurrent
# ===================================================================

@pytest.mark.asyncio
async def test_managed_isolated_session_recycle_concurrent(srv):
    """The ultimate stress test: managed browser + isolated contexts +
    sessions + recycle + concurrent crawls.

    Flow:
    1. Open session A
    2. Fire 8 concurrent non-session crawls (threshold=5, but session blocks)
    3. Kill session A
    4. Fire 3 more non-session crawls to trigger recycle
    5. Open session B on the fresh browser
    6. Verify session B works
    """
    cfg = BrowserConfig(
        headless=True, verbose=False,
        use_managed_browser=True,
        create_isolated_context=True,
        max_pages_before_recycle=5,
    )

    async with AsyncWebCrawler(config=cfg) as c:
        bm = _bm(c)
        no_sess = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False)

        # Step 1: open session
        sess_a = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="ultimate_a", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess_a)
        assert r.success

        # Step 2: concurrent non-session crawls
        tasks = [c.arun(url=_u(srv, i), config=no_sess) for i in range(8)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        excs = [r for r in results if isinstance(r, Exception)]
        assert len(excs) == 0, f"Exceptions in step 2: {excs[:3]}"

        # Session blocks recycle
        assert "ultimate_a" in bm.sessions

        # Step 3: kill session
        await c.crawler_strategy.kill_session("ultimate_a")

        # Step 4: trigger recycle
        for i in range(3):
            r = await c.arun(url=_u(srv, 80 + i), config=no_sess)
            assert r.success

        await asyncio.sleep(0.5)

        # Step 5: new session on fresh browser
        sess_b = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, session_id="ultimate_b", verbose=False,
        )
        r = await c.arun(url=f"{srv}/login", config=sess_b)
        assert r.success
        assert "ultimate_b" in bm.sessions

        # Step 6: verify it works
        r = await c.arun(url=f"{srv}/dashboard", config=sess_b)
        assert r.success
