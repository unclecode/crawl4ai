"""Tests for the close_after_screenshot functionality in screenshot methods."""

import pytest
import base64
from pathlib import Path
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from dataclasses import dataclass
from typing import Optional

@dataclass
class TestDeps:
    browser_config: Optional[BrowserConfig] = None
    crawler: Optional[AsyncWebCrawler] = None
    crawler_strategy: Optional[AsyncPlaywrightCrawlerStrategy] = None

    async def initialize(self):
        """Initialize browser and crawler if not already done."""
        if self.browser_config is None:
            self.browser_config = BrowserConfig(
                headless=False,
                verbose=True,
            )

        if self.crawler_strategy is None:
            self.crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                browser_config=self.browser_config
            )
            await self.crawler_strategy.start()

        if self.crawler is None:
            self.crawler = AsyncWebCrawler(
                crawler_strategy=self.crawler_strategy,
                config=self.browser_config
            )
            await self.crawler.start()

    async def cleanup(self):
        """Clean up browser resources."""
        if self.crawler:
            await self.crawler.close()
            self.crawler = None
        
        if self.crawler_strategy:
            await self.crawler_strategy.close()
            self.crawler_strategy = None

@pytest.mark.asyncio
async def test_screenshot_without_close(deps):
    """Test that page remains open after screenshot when close_after_screenshot=False."""
    session_id = "test_screenshot_session"

    # Initial configuration with screenshot but without closing
    config = CrawlerRunConfig(
        screenshot=True,
        close_after_screenshot=False,
        cache_mode=CacheMode.BYPASS,
        session_id=session_id,
        wait_until="networkidle",
        page_timeout=30000
    )
    
    # First call to take the screenshot
    result1 = await deps.crawler.arun(url="https://example.com", config=config)
    assert result1.success, "Screenshot capture failed"
    assert result1.screenshot, "Screenshot was not generated"

    # Second call to verify the page is still accessible
    result2 = await deps.crawler.arun(url="https://example.com", config=config)
    assert result2.success, "Page is no longer accessible after screenshot"

@pytest.mark.asyncio
async def test_screenshot_with_close(deps):
    """Test that page is closed after screenshot when close_after_screenshot=True."""
    session_id = "test_screenshot_close_session"

    # Configuration with automatic closure after screenshot
    config = CrawlerRunConfig(
        screenshot=True,
        close_after_screenshot=True,
        cache_mode=CacheMode.BYPASS,
        session_id=session_id,
        wait_until="networkidle",
        page_timeout=30000
    )
    
    # Take screenshot with automatic closure
    result = await deps.crawler.arun(url="https://example.com", config=config)
    assert result.success, "Screenshot capture failed"
    assert result.screenshot, "Screenshot was not generated"

@pytest.mark.asyncio
async def test_multiple_screenshots_same_session(deps):
    """Test taking multiple screenshots in the same session with different close settings."""
    session_id = "test_multiple_screenshots_session"

    # First screenshot without closure
    config1 = CrawlerRunConfig(
        screenshot=True,
        close_after_screenshot=False,
        cache_mode=CacheMode.BYPASS,
        session_id=session_id,
        wait_until="networkidle",
        page_timeout=30000
    )
    
    result1 = await deps.crawler.arun(url="https://example.com", config=config1)
    assert result1.success, "First screenshot failed"
    assert result1.screenshot, "First screenshot was not generated"

    # Second screenshot with closure
    config2 = CrawlerRunConfig(
        screenshot=True,
        close_after_screenshot=True,
        cache_mode=CacheMode.BYPASS,
        session_id=session_id,
        wait_until="networkidle",
        page_timeout=30000
    )
    
    result2 = await deps.crawler.arun(url="https://example.com", config=config2)
    assert result2.success, "Second screenshot failed"
    assert result2.screenshot, "Second screenshot was not generated"

async def run_tests():
    """Run all tests manually without pytest."""
    # Create test dependencies
    deps = TestDeps()
    
    # Liste des tests à exécuter
    tests = [
        test_screenshot_without_close,
        test_screenshot_with_close,
        test_multiple_screenshots_same_session
    ]
    
    try:
        # Initialisation une seule fois avant tous les tests
        print("Initializing browser...")
        await deps.initialize()
        
        # Exécution de chaque test
        for test in tests:
            try:
                print(f"\nRunning {test.__name__}...")
                await test(deps)
                print(f"✅ {test.__name__} passed")
            except AssertionError as e:
                print(f"❌ {test.__name__} failed: {str(e)}")
            except Exception as e:
                print(f"❌ {test.__name__} error: {str(e)}")
                
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
    finally:
        # Nettoyage final après tous les tests
        print("\nCleaning up...")
        await deps.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tests()) 