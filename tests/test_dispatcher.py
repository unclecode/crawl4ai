import pytest
import asyncio
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, RateLimitConfig
from crawl4ai.dispatcher import DisplayMode

@pytest.mark.asyncio
async def test_crawler_with_dispatcher():
    # Create test URLs
    urls = [f"https://example.com/page_{i}" for i in range(5)]
    
    # Configure browser
    browser_config = BrowserConfig(headless=True, verbose=False)
    
    # Configure crawler with rate limiting
    run_config = CrawlerRunConfig(
        enable_rate_limiting=True,
        rate_limit_config=RateLimitConfig(
            base_delay=(1.0, 2.0),
            max_delay=30.0,
            max_retries=2,
            rate_limit_codes=[429, 503]
        ),
        memory_threshold_percent=70.0,
        check_interval=0.5,
        max_session_permit=3,
        display_mode=DisplayMode.DETAILED.value
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls, config=run_config)
        
        # Basic validation
        assert len(results) == len(urls)
        for result in results:
            assert result is not None
            # Note: example.com URLs will fail, which is expected for this test
            assert not result.success  # We expect these to fail since they're fake URLs
