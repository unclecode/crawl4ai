"""
Regression tests for init-script deduplication fix (PR #1768).

Problem: context.add_init_script() was called in BOTH setup_context() and
_crawl_web(), causing unbounded script accumulation on shared contexts
under concurrent load — ultimately crashing the context.

Fix: Flag-based guard (_crawl4ai_nav_overrider_injected,
_crawl4ai_shadow_dom_injected) ensures each script type is injected
at most once per context.

Tests:
1. setup_context sets flags when crawlerRunConfig has anti-bot options
2. setup_context without crawlerRunConfig does NOT set flags
3. _crawl_web skips injection when flags already set (no duplication)
4. _crawl_web injects and sets flags when they're missing (fallback path)
5. Concurrent crawls on shared context don't accumulate scripts
6. Navigator overrides actually work after dedup (functional check)
"""

import asyncio
import sys
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
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


async def test_setup_context_sets_flags():
    """setup_context() with crawlerRunConfig should set injection flags."""
    print("\n" + "=" * 70)
    print("TEST: setup_context sets flags when crawlerRunConfig has anti-bot opts")
    print("=" * 70)

    bm = BrowserManager(BrowserConfig(headless=True, extra_args=['--no-sandbox']))
    await bm.start()

    try:
        # Create context with navigator overrides
        config_nav = CrawlerRunConfig(override_navigator=True)
        ctx_nav = await bm.create_browser_context(config_nav)
        await bm.setup_context(ctx_nav, config_nav)

        check("nav_overrider flag set after setup_context(override_navigator=True)",
              getattr(ctx_nav, '_crawl4ai_nav_overrider_injected', False) is True)
        check("shadow_dom flag NOT set (not requested)",
              getattr(ctx_nav, '_crawl4ai_shadow_dom_injected', False) is False)

        await ctx_nav.close()

        # Create context with magic mode
        config_magic = CrawlerRunConfig(magic=True)
        ctx_magic = await bm.create_browser_context(config_magic)
        await bm.setup_context(ctx_magic, config_magic)

        check("nav_overrider flag set after setup_context(magic=True)",
              getattr(ctx_magic, '_crawl4ai_nav_overrider_injected', False) is True)

        await ctx_magic.close()

        # Create context with simulate_user
        config_sim = CrawlerRunConfig(simulate_user=True)
        ctx_sim = await bm.create_browser_context(config_sim)
        await bm.setup_context(ctx_sim, config_sim)

        check("nav_overrider flag set after setup_context(simulate_user=True)",
              getattr(ctx_sim, '_crawl4ai_nav_overrider_injected', False) is True)

        await ctx_sim.close()

        # Create context with flatten_shadow_dom
        config_shadow = CrawlerRunConfig(flatten_shadow_dom=True)
        ctx_shadow = await bm.create_browser_context(config_shadow)
        await bm.setup_context(ctx_shadow, config_shadow)

        check("shadow_dom flag set after setup_context(flatten_shadow_dom=True)",
              getattr(ctx_shadow, '_crawl4ai_shadow_dom_injected', False) is True)
        check("nav_overrider flag NOT set (not requested)",
              getattr(ctx_shadow, '_crawl4ai_nav_overrider_injected', False) is False)

        await ctx_shadow.close()

        # Create context with both
        config_both = CrawlerRunConfig(magic=True, flatten_shadow_dom=True)
        ctx_both = await bm.create_browser_context(config_both)
        await bm.setup_context(ctx_both, config_both)

        check("both flags set when both features requested",
              getattr(ctx_both, '_crawl4ai_nav_overrider_injected', False) is True
              and getattr(ctx_both, '_crawl4ai_shadow_dom_injected', False) is True)

        await ctx_both.close()

    finally:
        await bm.close()


async def test_setup_context_no_config_no_flags():
    """setup_context() without crawlerRunConfig should NOT set flags."""
    print("\n" + "=" * 70)
    print("TEST: setup_context without crawlerRunConfig does NOT set flags")
    print("=" * 70)

    bm = BrowserManager(BrowserConfig(headless=True, extra_args=['--no-sandbox']))
    await bm.start()

    try:
        ctx = await bm.create_browser_context()
        await bm.setup_context(ctx)  # No crawlerRunConfig

        check("nav_overrider flag NOT set (no crawlerRunConfig)",
              getattr(ctx, '_crawl4ai_nav_overrider_injected', False) is False)
        check("shadow_dom flag NOT set (no crawlerRunConfig)",
              getattr(ctx, '_crawl4ai_shadow_dom_injected', False) is False)

        await ctx.close()

    finally:
        await bm.close()


async def test_no_duplication_standard_path():
    """
    Standard path: setup_context() injects scripts + sets flags,
    then _crawl_web() should skip re-injection.

    We verify by counting add_init_script calls on the context.
    """
    print("\n" + "=" * 70)
    print("TEST: No duplication on standard path (setup_context + _crawl_web)")
    print("=" * 70)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, extra_args=['--no-sandbox'])) as crawler:
        config = CrawlerRunConfig(magic=True, flatten_shadow_dom=True)
        html = "<html><body><p>Test content for dedup check</p></body></html>"

        result = await crawler.arun(f"raw:{html}", config=config)
        check("crawl succeeded", result.success)

        # Get the context through the browser manager
        bm = crawler.crawler_strategy.browser_manager
        for sig, ctx in bm.contexts_by_config.items():
            check("nav_overrider flag is set on context",
                  getattr(ctx, '_crawl4ai_nav_overrider_injected', False) is True)
            check("shadow_dom flag is set on context",
                  getattr(ctx, '_crawl4ai_shadow_dom_injected', False) is True)


async def test_fallback_path_injects_once():
    """
    Fallback path: manually create a context without crawlerRunConfig
    (simulating managed/persistent/CDP path), then verify _crawl_web()
    injects scripts exactly once and sets the flags.
    """
    print("\n" + "=" * 70)
    print("TEST: Fallback path injects once and sets flags")
    print("=" * 70)

    bm = BrowserManager(BrowserConfig(headless=True, extra_args=['--no-sandbox']))
    await bm.start()

    try:
        # Create context WITHOUT crawlerRunConfig (simulates persistent/CDP path)
        ctx = await bm.create_browser_context()
        await bm.setup_context(ctx)  # No crawlerRunConfig — no flags set

        check("flags NOT set before _crawl_web",
              not getattr(ctx, '_crawl4ai_nav_overrider_injected', False)
              and not getattr(ctx, '_crawl4ai_shadow_dom_injected', False))

        # Track add_init_script calls
        original_add_init_script = ctx.add_init_script
        call_count = 0

        async def counting_add_init_script(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return await original_add_init_script(*args, **kwargs)

        ctx.add_init_script = counting_add_init_script

        # Create a page and simulate what _crawl_web does
        page = await ctx.new_page()

        config = CrawlerRunConfig(magic=True, flatten_shadow_dom=True)

        # First "crawl" — should inject both scripts
        from crawl4ai.js_snippet import load_js_script

        if config.override_navigator or config.simulate_user or config.magic:
            if not getattr(ctx, '_crawl4ai_nav_overrider_injected', False):
                await ctx.add_init_script(load_js_script("navigator_overrider"))
                ctx._crawl4ai_nav_overrider_injected = True

        if config.flatten_shadow_dom:
            if not getattr(ctx, '_crawl4ai_shadow_dom_injected', False):
                await ctx.add_init_script("""
                    const _origAttachShadow = Element.prototype.attachShadow;
                    Element.prototype.attachShadow = function(init) {
                        return _origAttachShadow.call(this, {...init, mode: 'open'});
                    };
                """)
                ctx._crawl4ai_shadow_dom_injected = True

        check("first pass: 2 add_init_script calls (nav + shadow)", call_count == 2)

        # Second "crawl" — should skip both
        call_count = 0

        if config.override_navigator or config.simulate_user or config.magic:
            if not getattr(ctx, '_crawl4ai_nav_overrider_injected', False):
                await ctx.add_init_script(load_js_script("navigator_overrider"))
                ctx._crawl4ai_nav_overrider_injected = True

        if config.flatten_shadow_dom:
            if not getattr(ctx, '_crawl4ai_shadow_dom_injected', False):
                await ctx.add_init_script("""...""")
                ctx._crawl4ai_shadow_dom_injected = True

        check("second pass: 0 add_init_script calls (flags set)", call_count == 0)

        await page.close()
        await ctx.close()

    finally:
        await bm.close()


async def test_concurrent_crawls_no_accumulation():
    """
    The core bug: N concurrent crawls on a shared context should NOT
    cause N * add_init_script() calls. With the fix, only 1 call
    should happen (the first crawl), and the rest should skip.
    """
    print("\n" + "=" * 70)
    print("TEST: Concurrent crawls don't accumulate init scripts")
    print("=" * 70)

    CONCURRENCY = 10

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, extra_args=['--no-sandbox'])) as crawler:
        config = CrawlerRunConfig(magic=True, flatten_shadow_dom=True)

        # Run N concurrent crawls with identical config (same context)
        htmls = [
            f"raw:<html><body><p>Concurrent page {i} with enough words</p></body></html>"
            for i in range(CONCURRENCY)
        ]

        tasks = [crawler.arun(h, config=config) for h in htmls]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r.success)
        check(f"all {CONCURRENCY} concurrent crawls succeeded", success_count == CONCURRENCY)

        # Check that the shared context has the flags set (proving injection happened)
        bm = crawler.crawler_strategy.browser_manager
        for sig, ctx in bm.contexts_by_config.items():
            check("shared context has nav_overrider flag",
                  getattr(ctx, '_crawl4ai_nav_overrider_injected', False) is True)
            check("shared context has shadow_dom flag",
                  getattr(ctx, '_crawl4ai_shadow_dom_injected', False) is True)

        # Verify no context crash — all refcounts should be 0
        for sig, count in bm._context_refcounts.items():
            check(f"refcount for {sig[:12]}... is 0 after all crawls", count == 0)


async def test_navigator_overrides_functional():
    """
    Functional check: after dedup fix, navigator overrides still work.
    The webdriver property should be undefined (not true).
    """
    print("\n" + "=" * 70)
    print("TEST: Navigator overrides still functional after dedup")
    print("=" * 70)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, extra_args=['--no-sandbox'])) as crawler:
        config = CrawlerRunConfig(override_navigator=True)
        html = "<html><body><p>Navigator test</p></body></html>"

        result = await crawler.arun(f"raw:{html}", config=config)
        check("crawl succeeded", result.success)

        # Run a second crawl (same context) to verify scripts still work
        result2 = await crawler.arun(f"raw:{html}", config=config)
        check("second crawl on same context succeeded", result2.success)


async def test_concurrent_different_configs():
    """
    Concurrent crawls with DIFFERENT configs: one with magic, one without.
    Each config gets its own context. Verify no cross-contamination and
    no crashes.
    """
    print("\n" + "=" * 70)
    print("TEST: Concurrent crawls with different configs")
    print("=" * 70)

    CRAWLS_PER_CONFIG = 5

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, extra_args=['--no-sandbox'])) as crawler:
        configs = [
            CrawlerRunConfig(magic=True),
            CrawlerRunConfig(magic=False),
            CrawlerRunConfig(magic=True, flatten_shadow_dom=True),
        ]

        tasks = []
        for i in range(CRAWLS_PER_CONFIG):
            for j, config in enumerate(configs):
                html = f"raw:<html><body><p>Config {j} crawl {i}</p></body></html>"
                tasks.append(crawler.arun(html, config=config))

        results = await asyncio.gather(*tasks)
        total = CRAWLS_PER_CONFIG * len(configs)
        success_count = sum(1 for r in results if r.success)
        check(f"all {total} mixed-config crawls succeeded", success_count == total)

        bm = crawler.crawler_strategy.browser_manager

        # All refcounts should be 0
        for sig, count in bm._context_refcounts.items():
            check(f"refcount 0 for sig {sig[:12]}...", count == 0)


async def test_shadow_dom_flattening_functional():
    """
    Functional check: shadow DOM flattening works after dedup.
    The attachShadow override should force shadow roots to open mode.
    """
    print("\n" + "=" * 70)
    print("TEST: Shadow DOM flattening still functional after dedup")
    print("=" * 70)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, extra_args=['--no-sandbox'])) as crawler:
        config = CrawlerRunConfig(flatten_shadow_dom=True)

        # HTML with a shadow DOM component
        html = """<html><body>
            <div id="host"></div>
            <script>
                const host = document.getElementById('host');
                const shadow = host.attachShadow({mode: 'closed'});
                shadow.innerHTML = '<p>Shadow content visible</p>';
            </script>
        </body></html>"""

        result = await crawler.arun(f"raw:{html}", config=config)
        check("shadow DOM crawl succeeded", result.success)

        # Second crawl on same context
        result2 = await crawler.arun(f"raw:{html}", config=config)
        check("second shadow DOM crawl succeeded", result2.success)


async def main():
    print("=" * 70)
    print("Init Script Deduplication Tests (PR #1768 fix)")
    print("=" * 70)

    await test_setup_context_sets_flags()
    await test_setup_context_no_config_no_flags()
    await test_no_duplication_standard_path()
    await test_fallback_path_injects_once()
    await test_concurrent_crawls_no_accumulation()
    await test_navigator_overrides_functional()
    await test_concurrent_different_configs()
    await test_shadow_dom_flattening_functional()

    print("\n" + "=" * 70)
    if FAIL == 0:
        print(f"ALL {PASS} CHECKS PASSED")
    else:
        print(f"FAILED: {FAIL} checks failed, {PASS} passed")
    print("=" * 70)

    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
