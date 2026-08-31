"""
Regression tests for PR #1640 — memory leak / hang under high concurrency
with max_pages_before_recycle enabled.

Tests three bugs that were fixed:

Bug 1: Race condition — release_page_with_context() runs BEFORE
       _maybe_bump_browser_version() adds the sig to _pending_cleanup.
       FIX: Don't add refcount-0 sigs to pending; clean them up immediately.

Bug 2: The finally block in _crawl_web can fail before calling
       release_page_with_context(), leaking the refcount permanently.
       FIX: Call release_page_with_context() FIRST in the finally block.

Bug 3: Accumulated pending_cleanup entries hit _max_pending_browsers cap,
       blocking ALL get_page() calls → system-wide deadlock.
       FIX: 30s timeout on safety cap wait + force-clean stuck entries.

Exit code 0 = all tests pass. Exit code 1 = regression found.
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.browser_manager import BrowserManager

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name}")


async def test_bug1_multi_config_race():
    """
    Bug 1 fix: idle sigs (refcount=0) must NOT be added to _pending_cleanup.
    They should be cleaned up immediately during the version bump.
    """
    print("\n" + "="*70)
    print("TEST: Bug 1 — idle sig must not get stuck in _pending_cleanup")
    print("="*70)

    config = BrowserConfig(
        headless=True,
        extra_args=['--no-sandbox', '--disable-gpu'],
        max_pages_before_recycle=3,
    )
    bm = BrowserManager(config)
    await bm.start()

    try:
        config_a = CrawlerRunConfig(magic=True, cache_mode="bypass")
        config_b = CrawlerRunConfig(magic=False, cache_mode="bypass")

        # Use config A, then release → refcount 0
        page_a, _ = await bm.get_page(config_a)
        sig_a = bm._page_to_sig.get(page_a)
        await bm.release_page_with_context(page_a)
        await page_a.close()

        print(f"  sig_a refcount after release: {bm._context_refcounts.get(sig_a)}")

        # Use config B twice → pages_served hits threshold → version bump
        page_b1, _ = await bm.get_page(config_b)
        page_b2, _ = await bm.get_page(config_b)
        sig_b = bm._page_to_sig.get(page_b1)

        # At this point the version should have bumped (3 pages served >= threshold 3)
        print(f"  _browser_version: {bm._browser_version}")
        print(f"  _pending_cleanup sigs: {list(bm._pending_cleanup.keys())}")

        # sig_a (refcount=0) must NOT be in _pending_cleanup
        check("sig_a NOT in _pending_cleanup",
              sig_a not in bm._pending_cleanup)

        # sig_a should have been cleaned up from _context_refcounts
        check("sig_a cleaned from _context_refcounts",
              sig_a not in bm._context_refcounts)

        # sig_b (refcount>0) SHOULD be in _pending_cleanup (it will drain naturally)
        check("sig_b IS in _pending_cleanup (active, will drain)",
              sig_b in bm._pending_cleanup)

        # Release B pages → sig_b drains → cleaned up
        await bm.release_page_with_context(page_b1)
        await page_b1.close()
        await bm.release_page_with_context(page_b2)
        await page_b2.close()

        check("sig_b cleaned after release",
              sig_b not in bm._pending_cleanup)

        check("_pending_cleanup is empty",
              len(bm._pending_cleanup) == 0)

    finally:
        await bm.close()


async def test_bug2_release_always_called():
    """
    Bug 2 fix: release_page_with_context() must be called even when
    the browser is in a bad state.

    The fix moves release_page_with_context() to the FIRST line of
    the finally block in _crawl_web, wrapped in try/except.
    Here we verify that release_page_with_context itself works even
    after browser crash, and that the fixed finally block pattern
    always decrements the refcount.
    """
    print("\n" + "="*70)
    print("TEST: Bug 2 — release_page_with_context must work after browser crash")
    print("="*70)

    config = BrowserConfig(
        headless=True,
        extra_args=['--no-sandbox', '--disable-gpu'],
        max_pages_before_recycle=5,
    )
    bm = BrowserManager(config)
    await bm.start()

    try:
        crawl_config = CrawlerRunConfig(magic=True, cache_mode="bypass")

        page, ctx = await bm.get_page(crawl_config)
        sig = bm._page_to_sig.get(page)
        print(f"  sig refcount before crash: {bm._context_refcounts.get(sig)}")

        check("refcount is 1 before crash",
              bm._context_refcounts.get(sig) == 1)

        # Simulate browser crash
        if bm.browser:
            await bm.browser.close()
            bm.browser = None

        # The FIX: call release_page_with_context even after crash
        # (simulating what the fixed finally block does)
        try:
            await bm.release_page_with_context(page)
        except Exception:
            pass

        refcount_after = bm._context_refcounts.get(sig, 0)
        print(f"  sig refcount after crash + release: {refcount_after}")

        check("refcount decremented to 0 after crash + release",
              refcount_after == 0)

        check("page removed from _page_to_sig",
              page not in bm._page_to_sig)

    finally:
        bm.browser = None
        bm.contexts_by_config.clear()
        bm._context_refcounts.clear()
        bm._context_last_used.clear()
        bm._page_to_sig.clear()
        if bm.playwright:
            await bm.playwright.stop()


async def test_bug3_safety_cap_timeout():
    """
    Bug 3 fix: the safety cap wait must have a timeout.
    When stuck entries accumulate, the timeout fires and force-cleans
    entries with refcount 0, preventing permanent deadlock.
    """
    print("\n" + "="*70)
    print("TEST: Bug 3 — safety cap wait must not block forever")
    print("="*70)

    config = BrowserConfig(
        headless=True,
        extra_args=['--no-sandbox', '--disable-gpu'],
        max_pages_before_recycle=2,
    )
    bm = BrowserManager(config)
    await bm.start()

    try:
        crawl_config = CrawlerRunConfig(magic=True, cache_mode="bypass")

        # Inject stuck entries WITH refcount 0 (simulating leaked refcounts
        # that were later force-decremented or never properly tracked)
        print(f"  Safety cap: {bm._max_pending_browsers}")
        for i in range(bm._max_pending_browsers):
            fake_sig = f"stuck_sig_{i}"
            bm._pending_cleanup[fake_sig] = {"version": i, "done": asyncio.Event()}
            # refcount 0 = stuck (no future release will clean these up)
            bm._context_refcounts[fake_sig] = 0

        print(f"  Injected {len(bm._pending_cleanup)} stuck entries (refcount=0)")

        bm._pages_served = bm.config.max_pages_before_recycle

        # The fix: get_page should NOT block forever.
        # The 30s timeout will fire, force-clean stuck entries, and proceed.
        # We use a 35s test timeout to allow the 30s internal timeout to fire.
        print(f"  Calling get_page() — should unblock after ~30s timeout...")
        start = time.monotonic()
        try:
            page, ctx = await asyncio.wait_for(
                bm.get_page(crawl_config),
                timeout=35.0
            )
            elapsed = time.monotonic() - start
            print(f"  get_page() returned after {elapsed:.1f}s")

            check("get_page() did NOT deadlock (returned within 35s)", True)
            check("stuck entries were force-cleaned",
                  len(bm._pending_cleanup) < bm._max_pending_browsers)

            await bm.release_page_with_context(page)
            await page.close()

        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start
            print(f"  get_page() STILL blocked after {elapsed:.1f}s")
            check("get_page() did NOT deadlock", False)

    finally:
        bm._pending_cleanup.clear()
        bm._context_refcounts.clear()
        await bm.close()


async def test_real_concurrent_crawl():
    """
    Integration test: run many concurrent crawls with recycling
    and verify no stuck entries or deadlocks.
    """
    print("\n" + "="*70)
    print("TEST: Real concurrent crawls with recycling")
    print("="*70)

    config = BrowserConfig(
        headless=True,
        extra_args=['--no-sandbox', '--disable-gpu'],
        max_pages_before_recycle=10,
    )
    bm = BrowserManager(config)
    await bm.start()

    TOTAL = 80
    CONCURRENT = 8
    completed = 0
    errors = 0

    sem = asyncio.Semaphore(CONCURRENT)

    async def do_crawl(i):
        nonlocal completed, errors
        async with sem:
            try:
                crawl_config = CrawlerRunConfig(magic=True, cache_mode="bypass")
                page, ctx = await asyncio.wait_for(
                    bm.get_page(crawl_config),
                    timeout=30.0
                )

                try:
                    await page.goto("https://example.com", timeout=15000)
                except Exception:
                    pass

                # Use the FIXED finally pattern: release first, then close
                try:
                    await bm.release_page_with_context(page)
                except Exception:
                    pass
                try:
                    await page.close()
                except Exception:
                    pass

                completed += 1
                if completed % 20 == 0:
                    print(f"  [{completed}/{TOTAL}] version={bm._browser_version} "
                          f"pending={len(bm._pending_cleanup)} "
                          f"pages_served={bm._pages_served}")

            except asyncio.TimeoutError:
                errors += 1
                print(f"  [{i}] TIMEOUT in get_page()!")
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [{i}] Error: {e}")

    start = time.monotonic()
    tasks = [asyncio.create_task(do_crawl(i)) for i in range(TOTAL)]
    await asyncio.gather(*tasks)
    elapsed = time.monotonic() - start

    print(f"\n  Results: {completed}/{TOTAL} completed, {errors} errors, {elapsed:.1f}s")

    stuck = [s for s in bm._pending_cleanup if bm._context_refcounts.get(s, 0) == 0]

    check(f"all {TOTAL} crawls completed", completed == TOTAL)
    check("no errors", errors == 0)
    check("no stuck entries in _pending_cleanup", len(stuck) == 0)
    check("no timeouts (no deadlock)", errors == 0)

    await bm.close()


async def test_multi_config_concurrent():
    """
    Integration test: concurrent crawls with DIFFERENT configs to
    exercise the multi-sig path that triggered Bug 1.
    """
    print("\n" + "="*70)
    print("TEST: Multi-config concurrent crawls")
    print("="*70)

    config = BrowserConfig(
        headless=True,
        extra_args=['--no-sandbox', '--disable-gpu'],
        max_pages_before_recycle=5,
    )
    bm = BrowserManager(config)
    await bm.start()

    TOTAL = 40
    CONCURRENT = 6
    completed = 0
    errors = 0

    sem = asyncio.Semaphore(CONCURRENT)
    configs = [
        CrawlerRunConfig(magic=True, cache_mode="bypass"),
        CrawlerRunConfig(magic=False, cache_mode="bypass"),
        CrawlerRunConfig(magic=True, simulate_user=True, cache_mode="bypass"),
    ]

    async def do_crawl(i):
        nonlocal completed, errors
        async with sem:
            try:
                crawl_config = configs[i % len(configs)]
                page, ctx = await asyncio.wait_for(
                    bm.get_page(crawl_config),
                    timeout=30.0
                )

                try:
                    await page.goto("https://example.com", timeout=15000)
                except Exception:
                    pass

                try:
                    await bm.release_page_with_context(page)
                except Exception:
                    pass
                try:
                    await page.close()
                except Exception:
                    pass

                completed += 1

            except asyncio.TimeoutError:
                errors += 1
                print(f"  [{i}] TIMEOUT!")
                print(f"    pending={len(bm._pending_cleanup)}")
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [{i}] Error: {e}")

    start = time.monotonic()
    tasks = [asyncio.create_task(do_crawl(i)) for i in range(TOTAL)]
    await asyncio.gather(*tasks)
    elapsed = time.monotonic() - start

    stuck = [s for s in bm._pending_cleanup if bm._context_refcounts.get(s, 0) == 0]

    print(f"\n  Results: {completed}/{TOTAL}, {errors} errors, {elapsed:.1f}s")
    print(f"  Final: version={bm._browser_version} pending={len(bm._pending_cleanup)} stuck={len(stuck)}")

    check(f"all {TOTAL} multi-config crawls completed", completed == TOTAL)
    check("no stuck entries", len(stuck) == 0)
    check("no timeouts", errors == 0)

    await bm.close()


async def main():
    print("="*70)
    print("PR #1640 Regression Tests")
    print("="*70)

    await test_bug2_release_always_called()
    await test_bug1_multi_config_race()
    await test_bug3_safety_cap_timeout()
    await test_real_concurrent_crawl()
    await test_multi_config_concurrent()

    print("\n" + "="*70)
    if FAIL == 0:
        print(f"ALL {PASS} CHECKS PASSED")
    else:
        print(f"FAILED: {FAIL} checks failed, {PASS} passed")
    print("="*70)

    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
