import asyncio
import os
import sys
import pytest

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)

@pytest.mark.asyncio
async def test_resource_filtering_launch():
    """Functional test to ensure browser launches correctly with filtering flags enabled."""
    browser_config = BrowserConfig(
        headless=True,
        avoid_ads=True,
        avoid_css=True,
        text_mode=True
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Simple crawl to verify functionality
        result = await crawler.arun(
            url="https://example.com",
            config=CrawlerRunConfig(cache_mode="bypass")
        )
        assert result.success
        logger.success("Browser launched and crawled successfully with filtering flags")

@pytest.mark.asyncio
async def test_avoid_css_only():
    """Test avoid_css without text_mode."""
    browser_config = BrowserConfig(
        headless=True,
        avoid_css=True,
        text_mode=False
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=CrawlerRunConfig(cache_mode="bypass")
        )
        assert result.success
        logger.success("Browser launched and crawled successfully with avoid_css only")

if __name__ == "__main__":
    asyncio.run(test_resource_filtering_launch())
    asyncio.run(test_avoid_css_only())

