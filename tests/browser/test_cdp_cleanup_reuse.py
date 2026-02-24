#!/usr/bin/env python3
"""
Tests for CDP connection cleanup and browser reuse.

These tests verify that:
1. WebSocket URLs are properly handled (skip HTTP verification)
2. cdp_cleanup_on_close properly disconnects without terminating the browser
3. The same browser can be reused by multiple sequential connections

Requirements:
- A CDP-compatible browser pool service running (e.g., chromepoold)
- Service should be accessible at CDP_SERVICE_URL (default: http://localhost:11235)

Usage:
    pytest tests/browser/test_cdp_cleanup_reuse.py -v

Or run directly:
    python tests/browser/test_cdp_cleanup_reuse.py
"""

import asyncio
import os
import pytest
import requests
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Configuration
CDP_SERVICE_URL = os.getenv("CDP_SERVICE_URL", "http://localhost:11235")


def is_cdp_service_available():
    """Check if CDP service is running."""
    try:
        resp = requests.get(f"{CDP_SERVICE_URL}/health", timeout=2)
        return resp.status_code == 200
    except:
        return False


def create_browser():
    """Create a browser via CDP service API."""
    resp = requests.post(
        f"{CDP_SERVICE_URL}/v1/browsers",
        json={"headless": True},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()


def get_browser_info(browser_id):
    """Get browser info from CDP service."""
    resp = requests.get(f"{CDP_SERVICE_URL}/v1/browsers", timeout=5)
    for browser in resp.json():
        if browser["id"] == browser_id:
            return browser
    return None


def delete_browser(browser_id):
    """Delete a browser via CDP service API."""
    try:
        requests.delete(f"{CDP_SERVICE_URL}/v1/browsers/{browser_id}", timeout=5)
    except:
        pass


# Skip all tests if CDP service is not available
pytestmark = pytest.mark.skipif(
    not is_cdp_service_available(),
    reason=f"CDP service not available at {CDP_SERVICE_URL}"
)


class TestCDPWebSocketURL:
    """Tests for WebSocket URL handling."""

    @pytest.mark.asyncio
    async def test_websocket_url_skips_http_verification(self):
        """WebSocket URLs should skip HTTP /json/version verification."""
        browser = create_browser()
        try:
            ws_url = browser["ws_url"]
            assert ws_url.startswith("ws://") or ws_url.startswith("wss://")

            async with AsyncWebCrawler(
                config=BrowserConfig(
                    browser_mode="cdp",
                    cdp_url=ws_url,
                    headless=True,
                    cdp_cleanup_on_close=True,
                )
            ) as crawler:
                result = await crawler.arun(
                    url="https://example.com",
                    config=CrawlerRunConfig(verbose=False),
                )
                assert result.success
                assert "Example Domain" in result.metadata.get("title", "")
        finally:
            delete_browser(browser["browser_id"])


class TestCDPCleanupOnClose:
    """Tests for cdp_cleanup_on_close behavior."""

    @pytest.mark.asyncio
    async def test_browser_survives_after_cleanup_close(self):
        """Browser should remain alive after close with cdp_cleanup_on_close=True."""
        browser = create_browser()
        browser_id = browser["browser_id"]
        ws_url = browser["ws_url"]

        try:
            # Verify browser exists
            info_before = get_browser_info(browser_id)
            assert info_before is not None
            pid_before = info_before["pid"]

            # Connect, crawl, and close with cleanup
            async with AsyncWebCrawler(
                config=BrowserConfig(
                    browser_mode="cdp",
                    cdp_url=ws_url,
                    headless=True,
                    cdp_cleanup_on_close=True,
                )
            ) as crawler:
                result = await crawler.arun(
                    url="https://example.com",
                    config=CrawlerRunConfig(verbose=False),
                )
                assert result.success

            # Browser should still exist with same PID
            info_after = get_browser_info(browser_id)
            assert info_after is not None, "Browser was terminated but should only disconnect"
            assert info_after["pid"] == pid_before, "Browser PID changed unexpectedly"
        finally:
            delete_browser(browser_id)


class TestCDPBrowserReuse:
    """Tests for reusing the same browser with multiple connections."""

    @pytest.mark.asyncio
    async def test_sequential_connections_same_browser(self):
        """Multiple sequential connections to the same browser should work."""
        browser = create_browser()
        browser_id = browser["browser_id"]
        ws_url = browser["ws_url"]

        try:
            urls = [
                "https://example.com",
                "https://httpbin.org/ip",
                "https://httpbin.org/headers",
            ]

            for i, url in enumerate(urls, 1):
                # Each connection uses cdp_cleanup_on_close=True
                async with AsyncWebCrawler(
                    config=BrowserConfig(
                        browser_mode="cdp",
                        cdp_url=ws_url,
                        headless=True,
                        cdp_cleanup_on_close=True,
                    )
                ) as crawler:
                    result = await crawler.arun(
                        url=url,
                        config=CrawlerRunConfig(verbose=False),
                    )
                    assert result.success, f"Connection {i} failed for {url}"

                # Verify browser is still healthy
                info = get_browser_info(browser_id)
                assert info is not None, f"Browser died after connection {i}"

        finally:
            delete_browser(browser_id)

    @pytest.mark.asyncio
    async def test_no_user_wait_needed_between_connections(self):
        """With cdp_cleanup_on_close=True, no user wait should be needed."""
        browser = create_browser()
        browser_id = browser["browser_id"]
        ws_url = browser["ws_url"]

        try:
            # Rapid-fire connections with NO sleep between them
            for i in range(3):
                async with AsyncWebCrawler(
                    config=BrowserConfig(
                        browser_mode="cdp",
                        cdp_url=ws_url,
                        headless=True,
                        cdp_cleanup_on_close=True,
                    )
                ) as crawler:
                    result = await crawler.arun(
                        url="https://example.com",
                        config=CrawlerRunConfig(verbose=False),
                    )
                    assert result.success, f"Rapid connection {i+1} failed"
                # NO asyncio.sleep() here - internal delay should be sufficient
        finally:
            delete_browser(browser_id)


class TestCDPBackwardCompatibility:
    """Tests for backward compatibility with existing CDP usage."""

    @pytest.mark.asyncio
    async def test_http_url_with_browser_id_works(self):
        """HTTP URL with browser_id query param should work (backward compatibility)."""
        browser = create_browser()
        browser_id = browser["browser_id"]
        try:
            # Use HTTP URL with browser_id query parameter
            http_url = f"{CDP_SERVICE_URL}?browser_id={browser_id}"

            async with AsyncWebCrawler(
                config=BrowserConfig(
                    browser_mode="cdp",
                    cdp_url=http_url,
                    headless=True,
                    cdp_cleanup_on_close=True,
                )
            ) as crawler:
                result = await crawler.arun(
                    url="https://example.com",
                    config=CrawlerRunConfig(verbose=False),
                )
                assert result.success
        finally:
            delete_browser(browser_id)


# Allow running directly
if __name__ == "__main__":
    if not is_cdp_service_available():
        print(f"CDP service not available at {CDP_SERVICE_URL}")
        print("Please start a CDP-compatible browser pool service first.")
        exit(1)

    async def run_tests():
        print("=" * 60)
        print("CDP Cleanup and Browser Reuse Tests")
        print("=" * 60)

        tests = [
            ("WebSocket URL handling", TestCDPWebSocketURL().test_websocket_url_skips_http_verification),
            ("Browser survives after cleanup", TestCDPCleanupOnClose().test_browser_survives_after_cleanup_close),
            ("Sequential connections", TestCDPBrowserReuse().test_sequential_connections_same_browser),
            ("No user wait needed", TestCDPBrowserReuse().test_no_user_wait_needed_between_connections),
            ("HTTP URL with browser_id", TestCDPBackwardCompatibility().test_http_url_with_browser_id_works),
        ]

        results = []
        for name, test_func in tests:
            print(f"\n--- {name} ---")
            try:
                await test_func()
                print(f"PASS")
                results.append((name, True))
            except Exception as e:
                print(f"FAIL: {e}")
                results.append((name, False))

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for name, passed in results:
            print(f"  {name}: {'PASS' if passed else 'FAIL'}")

        all_passed = all(r[1] for r in results)
        print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        return 0 if all_passed else 1

    exit(asyncio.run(run_tests()))
