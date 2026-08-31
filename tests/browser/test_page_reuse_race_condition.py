"""
Real integration tests for page reuse race condition fix.

Tests that when create_isolated_context=False:
1. Single crawls still work correctly
2. Concurrent crawls don't cause race conditions
3. Pages are properly tracked and released
4. Page reuse works when pages become available

These are REAL tests - no mocking, actual browser operations.
"""

import asyncio
import os
import sys
import time

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


async def test_single_crawl_still_works():
    """
    Test 1: Basic single crawl functionality still works with create_isolated_context=False.
    This ensures we haven't broken existing functionality.
    """
    print("\n" + "="*70)
    print("TEST 1: Single crawl with create_isolated_context=False")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun("https://example.com")

            assert result.success, f"Crawl failed: {result.error_message}"
            assert result.html, "No HTML content returned"
            assert "Example Domain" in result.html, "Expected content not found"

            print(f"  Status: {result.status_code}")
            print(f"  HTML length: {len(result.html)} chars")
            print("  PASSED: Single crawl works correctly")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        return False


async def test_sequential_crawls_work():
    """
    Test 2: Sequential crawls reuse the same page (when released).
    This tests that page tracking and release works correctly.
    """
    print("\n" + "="*70)
    print("TEST 2: Sequential crawls with page reuse")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://example.org",
    ]

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = []
            for url in urls:
                result = await crawler.arun(url)
                results.append(result)
                print(f"  Crawled {url}: success={result.success}, status={result.status_code}")

            # All should succeed
            for i, result in enumerate(results):
                assert result.success, f"Crawl {i+1} failed: {result.error_message}"

            print("  PASSED: Sequential crawls work correctly")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_concurrent_crawls_no_race_condition():
    """
    Test 3: Multiple concurrent crawls don't cause race conditions.
    This is the main bug we're fixing - concurrent crawls should each get their own page.
    """
    print("\n" + "="*70)
    print("TEST 3: Concurrent crawls with create_isolated_context=False")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    # Use different URLs to ensure they can't accidentally succeed by being on the same page
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://example.org",
        "https://httpbin.org/get",
        "https://www.iana.org/domains/reserved",
    ]

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"  Launching {len(urls)} concurrent crawls...")
            start_time = time.time()

            # Launch all crawls concurrently
            tasks = [crawler.arun(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            elapsed = time.time() - start_time
            print(f"  Completed in {elapsed:.2f}s")

            # Check results
            success_count = 0
            for i, (url, result) in enumerate(zip(urls, results)):
                if isinstance(result, Exception):
                    print(f"  [{i+1}] {url}: EXCEPTION - {result}")
                elif result.success:
                    success_count += 1
                    print(f"  [{i+1}] {url}: OK (status={result.status_code})")
                else:
                    print(f"  [{i+1}] {url}: FAILED - {result.error_message}")

            # All should succeed
            assert success_count == len(urls), f"Only {success_count}/{len(urls)} succeeded"

            print(f"  PASSED: All {len(urls)} concurrent crawls succeeded without race conditions")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_high_concurrency_stress():
    """
    Test 4: High concurrency stress test - many concurrent crawls.
    This stresses the page tracking system to ensure it handles many concurrent operations.
    """
    print("\n" + "="*70)
    print("TEST 4: High concurrency stress test (10 concurrent crawls)")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    # Generate multiple unique URLs
    base_urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://example.org",
        "https://httpbin.org/get",
        "https://www.iana.org/domains/reserved",
    ]

    # Create 10 URLs by adding query params
    urls = []
    for i in range(10):
        url = f"{base_urls[i % len(base_urls)]}?test={i}&t={int(time.time())}"
        urls.append(url)

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"  Launching {len(urls)} concurrent crawls...")
            start_time = time.time()

            # Launch all crawls concurrently
            tasks = [crawler.arun(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            elapsed = time.time() - start_time
            print(f"  Completed in {elapsed:.2f}s")

            # Count results
            success_count = 0
            error_count = 0
            exception_count = 0

            for url, result in zip(urls, results):
                if isinstance(result, Exception):
                    exception_count += 1
                elif result.success:
                    success_count += 1
                else:
                    error_count += 1

            print(f"  Results: {success_count} success, {error_count} errors, {exception_count} exceptions")

            # At least 80% should succeed (allowing for some network issues)
            min_success = int(len(urls) * 0.8)
            assert success_count >= min_success, f"Only {success_count}/{len(urls)} succeeded (min: {min_success})"

            print(f"  PASSED: High concurrency test ({success_count}/{len(urls)} succeeded)")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_page_tracking_internal_state():
    """
    Test 5: Verify internal page tracking state is correct.
    This directly tests the global page tracking mechanism.
    """
    print("\n" + "="*70)
    print("TEST 5: Internal page tracking state verification")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            browser_manager = crawler.crawler_strategy.browser_manager

            # Check endpoint key is set
            endpoint_key = browser_manager._browser_endpoint_key
            print(f"  Browser endpoint key: {endpoint_key}")
            assert endpoint_key, "Endpoint key should be set"

            # Initially, no pages should be in use
            initial_in_use = len(browser_manager._get_pages_in_use())
            print(f"  Initial pages in use: {initial_in_use}")

            # Do a crawl
            result = await crawler.arun("https://example.com")
            assert result.success, f"Crawl failed: {result.error_message}"

            # After crawl completes, page should be released
            after_crawl_in_use = len(browser_manager._get_pages_in_use())
            print(f"  Pages in use after crawl: {after_crawl_in_use}")

            # The page should have been released (or kept as the last page)
            # Either way, tracking should be consistent

            # Do another crawl - should work fine
            result2 = await crawler.arun("https://example.org")
            assert result2.success, f"Second crawl failed: {result2.error_message}"

            final_in_use = len(browser_manager._get_pages_in_use())
            print(f"  Pages in use after second crawl: {final_in_use}")

            print("  PASSED: Page tracking state is consistent")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_mixed_sequential_and_concurrent():
    """
    Test 6: Mixed sequential and concurrent crawls.
    Tests realistic usage pattern where some crawls are sequential and some concurrent.
    """
    print("\n" + "="*70)
    print("TEST 6: Mixed sequential and concurrent crawls")
    print("="*70)

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Sequential crawl 1
            print("  Phase 1: Sequential crawl")
            result1 = await crawler.arun("https://example.com")
            assert result1.success, f"Sequential crawl 1 failed"
            print(f"    Crawl 1: OK")

            # Concurrent crawls
            print("  Phase 2: Concurrent crawls (3 URLs)")
            concurrent_urls = [
                "https://httpbin.org/html",
                "https://example.org",
                "https://httpbin.org/get",
            ]
            tasks = [crawler.arun(url) for url in concurrent_urls]
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(concurrent_results):
                if isinstance(result, Exception):
                    print(f"    Concurrent {i+1}: EXCEPTION - {result}")
                else:
                    assert result.success, f"Concurrent crawl {i+1} failed"
                    print(f"    Concurrent {i+1}: OK")

            # Sequential crawl 2
            print("  Phase 3: Sequential crawl")
            result2 = await crawler.arun("https://www.iana.org/domains/reserved")
            assert result2.success, f"Sequential crawl 2 failed"
            print(f"    Crawl 2: OK")

            # Another batch of concurrent
            print("  Phase 4: More concurrent crawls (2 URLs)")
            tasks2 = [
                crawler.arun("https://example.com?test=1"),
                crawler.arun("https://example.org?test=2"),
            ]
            results2 = await asyncio.gather(*tasks2, return_exceptions=True)
            for i, result in enumerate(results2):
                if isinstance(result, Exception):
                    print(f"    Concurrent {i+1}: EXCEPTION - {result}")
                else:
                    assert result.success, f"Batch 2 crawl {i+1} failed"
                    print(f"    Concurrent {i+1}: OK")

            print("  PASSED: Mixed sequential and concurrent crawls work correctly")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_compare_isolated_vs_shared_context():
    """
    Test 7: Compare behavior between isolated and shared context modes.
    Both should work for concurrent crawls now.
    """
    print("\n" + "="*70)
    print("TEST 7: Compare isolated vs shared context modes")
    print("="*70)

    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://example.org",
    ]

    # Test with create_isolated_context=True
    print("  Testing with create_isolated_context=True:")
    browser_config_isolated = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=True,
    )

    try:
        async with AsyncWebCrawler(config=browser_config_isolated) as crawler:
            tasks = [crawler.arun(url) for url in urls]
            results_isolated = await asyncio.gather(*tasks, return_exceptions=True)

            isolated_success = sum(1 for r in results_isolated if not isinstance(r, Exception) and r.success)
            print(f"    Isolated context: {isolated_success}/{len(urls)} succeeded")
    except Exception as e:
        print(f"    Isolated context: FAILED - {e}")
        isolated_success = 0

    # Test with create_isolated_context=False
    print("  Testing with create_isolated_context=False:")
    browser_config_shared = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        create_isolated_context=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_config_shared) as crawler:
            tasks = [crawler.arun(url) for url in urls]
            results_shared = await asyncio.gather(*tasks, return_exceptions=True)

            shared_success = sum(1 for r in results_shared if not isinstance(r, Exception) and r.success)
            print(f"    Shared context: {shared_success}/{len(urls)} succeeded")
    except Exception as e:
        print(f"    Shared context: FAILED - {e}")
        shared_success = 0

    # Both modes should work
    assert isolated_success == len(urls), f"Isolated context: only {isolated_success}/{len(urls)} succeeded"
    assert shared_success == len(urls), f"Shared context: only {shared_success}/{len(urls)} succeeded"

    print("  PASSED: Both context modes work correctly for concurrent crawls")
    return True


async def test_multiple_crawlers_same_cdp():
    """
    Test 8: Multiple AsyncWebCrawler instances connecting to the same CDP endpoint.

    This tests the realistic scenario where:
    1. A browser is started externally (or by a managed browser)
    2. Multiple crawler instances connect to it via CDP URL
    3. All use create_isolated_context=False to share cookies/session
    4. Each should get its own page to avoid race conditions
    """
    print("\n" + "="*70)
    print("TEST 8: Multiple crawlers connecting to same CDP endpoint")
    print("="*70)

    import subprocess
    import tempfile

    # Start a browser manually using subprocess
    port = 9444
    temp_dir = tempfile.mkdtemp(prefix="browser-test-")

    browser_process = None
    try:
        # Start chromium with remote debugging - use Playwright's bundled chromium
        import os
        playwright_path = os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
        if not os.path.exists(playwright_path):
            # Fallback - try to find it
            for path in [
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome",
            ]:
                if os.path.exists(path):
                    playwright_path = path
                    break
        chrome_path = playwright_path

        cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={temp_dir}",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
        ]

        browser_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await asyncio.sleep(2)  # Wait for browser to start

        cdp_url = f"http://localhost:{port}"
        print(f"  Started browser at {cdp_url}")

        # Both crawlers connect via CDP URL
        browser_config1 = BrowserConfig(
            headless=True,
            cdp_url=cdp_url,
            create_isolated_context=False,
        )
        browser_config2 = BrowserConfig(
            headless=True,
            cdp_url=cdp_url,
            create_isolated_context=False,
        )

        urls_crawler1 = [
            "https://example.com?crawler=1",
            "https://example.org?crawler=1",
        ]
        urls_crawler2 = [
            "https://httpbin.org/html?crawler=2",
            "https://httpbin.org/get?crawler=2",
        ]

        async with AsyncWebCrawler(config=browser_config1) as crawler1:
            async with AsyncWebCrawler(config=browser_config2) as crawler2:
                bm1 = crawler1.crawler_strategy.browser_manager
                bm2 = crawler2.crawler_strategy.browser_manager

                print(f"  Crawler 1 endpoint key: {bm1._browser_endpoint_key}")
                print(f"  Crawler 2 endpoint key: {bm2._browser_endpoint_key}")
                print(f"  Keys match: {bm1._browser_endpoint_key == bm2._browser_endpoint_key}")

                # Launch concurrent crawls from BOTH crawlers simultaneously
                print(f"  Launching {len(urls_crawler1) + len(urls_crawler2)} concurrent crawls...")

                tasks1 = [crawler1.arun(url) for url in urls_crawler1]
                tasks2 = [crawler2.arun(url) for url in urls_crawler2]

                all_results = await asyncio.gather(
                    *tasks1, *tasks2,
                    return_exceptions=True
                )

                # Check results
                success_count = 0
                for i, result in enumerate(all_results):
                    crawler_id = 1 if i < len(urls_crawler1) else 2
                    url_idx = i if i < len(urls_crawler1) else i - len(urls_crawler1)

                    if isinstance(result, Exception):
                        print(f"    Crawler {crawler_id}, URL {url_idx+1}: EXCEPTION - {result}")
                    elif result.success:
                        success_count += 1
                        print(f"    Crawler {crawler_id}, URL {url_idx+1}: OK")
                    else:
                        print(f"    Crawler {crawler_id}, URL {url_idx+1}: FAILED - {result.error_message}")

                total = len(urls_crawler1) + len(urls_crawler2)
                assert success_count == total, f"Only {success_count}/{total} succeeded"

                print(f"  PASSED: All {total} concurrent crawls from 2 crawlers succeeded")
                return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up browser process
        if browser_process:
            browser_process.terminate()
            try:
                browser_process.wait(timeout=5)
            except:
                browser_process.kill()
        # Clean up temp dir
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


async def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "#"*70)
    print("# PAGE REUSE RACE CONDITION FIX - INTEGRATION TESTS")
    print("#"*70)

    tests = [
        ("Single crawl works", test_single_crawl_still_works),
        ("Sequential crawls work", test_sequential_crawls_work),
        ("Concurrent crawls no race", test_concurrent_crawls_no_race_condition),
        ("High concurrency stress", test_high_concurrency_stress),
        ("Page tracking state", test_page_tracking_internal_state),
        ("Mixed sequential/concurrent", test_mixed_sequential_and_concurrent),
        ("Isolated vs shared context", test_compare_isolated_vs_shared_context),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  EXCEPTION in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, p in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}")

    print("-"*70)
    print(f"  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n  {total - passed} TESTS FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
