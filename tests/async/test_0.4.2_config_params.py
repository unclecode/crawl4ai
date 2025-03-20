import os, sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.chunking_strategy import RegexChunking


# Category 1: Browser Configuration Tests
async def test_browser_config_object():
    """Test the new BrowserConfig object with various browser settings"""
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
        use_managed_browser=True,
        user_agent_mode="random",
        user_agent_generator_config={"device_type": "desktop", "os_type": "windows"},
    )

    async with AsyncWebCrawler(config=browser_config, verbose=True) as crawler:
        result = await crawler.arun("https://example.com", cache_mode=CacheMode.BYPASS)
        assert result.success, "Browser config crawl failed"
        assert len(result.html) > 0, "No HTML content retrieved"


async def test_browser_performance_config():
    """Test browser configurations focused on performance"""
    browser_config = BrowserConfig(
        text_mode=True,
        light_mode=True,
        extra_args=["--disable-gpu", "--disable-software-rasterizer"],
        ignore_https_errors=True,
        java_script_enabled=False,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://example.com")
        assert result.success, "Performance optimized crawl failed"
        assert result.status_code == 200, "Unexpected status code"


# Category 2: Content Processing Tests
async def test_content_extraction_config():
    """Test content extraction with various strategies"""
    crawler_config = CrawlerRunConfig(
        word_count_threshold=300,
        extraction_strategy=JsonCssExtractionStrategy(
            schema={
                "name": "article",
                "baseSelector": "div",
                "fields": [{"name": "title", "selector": "h1", "type": "text"}],
            }
        ),
        chunking_strategy=RegexChunking(),
        content_filter=PruningContentFilter(),
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://example.com/article", config=crawler_config
        )
        assert result.extracted_content is not None, "Content extraction failed"
        assert "title" in result.extracted_content, "Missing expected content field"


# Category 3: Cache and Session Management Tests
async def test_cache_and_session_management():
    """Test different cache modes and session handling"""
    browser_config = BrowserConfig(use_persistent_context=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.WRITE_ONLY,
        process_iframes=True,
        remove_overlay_elements=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First request - should write to cache
        result1 = await crawler.arun("https://example.com", config=crawler_config)

        # Second request - should use fresh fetch due to WRITE_ONLY mode
        result2 = await crawler.arun("https://example.com", config=crawler_config)

        assert result1.success and result2.success, "Cache mode crawl failed"
        assert result1.html == result2.html, "Inconsistent results between requests"


# Category 4: Media Handling Tests
async def test_media_handling_config():
    """Test configurations related to media handling"""
    # Get the base path for home directroy ~/.crawl4ai/downloads, make sure it exists
    os.makedirs(os.path.expanduser("~/.crawl4ai/downloads"), exist_ok=True)
    browser_config = BrowserConfig(
        viewport_width=1920,
        viewport_height=1080,
        accept_downloads=True,
        downloads_path=os.path.expanduser("~/.crawl4ai/downloads"),
    )
    crawler_config = CrawlerRunConfig(
        screenshot=True,
        pdf=True,
        adjust_viewport_to_content=True,
        wait_for_images=True,
        screenshot_height_threshold=20000,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun("https://example.com", config=crawler_config)
        assert result.screenshot is not None, "Screenshot capture failed"
        assert result.pdf is not None, "PDF generation failed"


# Category 5: Anti-Bot and Site Interaction Tests
async def test_antibot_config():
    """Test configurations for handling anti-bot measures"""
    crawler_config = CrawlerRunConfig(
        simulate_user=True,
        override_navigator=True,
        magic=True,
        wait_for="js:()=>document.querySelector('body')",
        delay_before_return_html=1.0,
        log_console=True,
        cache_mode=CacheMode.BYPASS,
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=crawler_config)
        assert result.success, "Anti-bot measure handling failed"


# Category 6: Parallel Processing Tests
async def test_parallel_processing():
    """Test parallel processing capabilities"""
    crawler_config = CrawlerRunConfig(mean_delay=0.5, max_range=1.0, semaphore_count=5)

    urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(urls, config=crawler_config)
        assert len(results) == len(urls), "Not all URLs were processed"
        assert all(r.success for r in results), "Some parallel requests failed"


# Category 7: Backwards Compatibility Tests
async def test_legacy_parameter_support():
    """Test that legacy parameters still work"""
    async with AsyncWebCrawler(
        headless=True, browser_type="chromium", viewport_width=1024, viewport_height=768
    ) as crawler:
        result = await crawler.arun(
            "https://example.com",
            screenshot=True,
            word_count_threshold=200,
            bypass_cache=True,
            css_selector=".main-content",
        )
        assert result.success, "Legacy parameter support failed"


# Category 8: Mixed Configuration Tests
async def test_mixed_config_usage():
    """Test mixing new config objects with legacy parameters"""
    browser_config = BrowserConfig(headless=True)
    crawler_config = CrawlerRunConfig(screenshot=True)

    async with AsyncWebCrawler(
        config=browser_config,
        verbose=True,  # legacy parameter
    ) as crawler:
        result = await crawler.arun(
            "https://example.com",
            config=crawler_config,
            cache_mode=CacheMode.BYPASS,  # legacy parameter
            css_selector="body",  # legacy parameter
        )
        assert result.success, "Mixed configuration usage failed"


if __name__ == "__main__":

    async def run_tests():
        test_functions = [
            test_browser_config_object,
            # test_browser_performance_config,
            # test_content_extraction_config,
            # test_cache_and_session_management,
            # test_media_handling_config,
            # test_antibot_config,
            # test_parallel_processing,
            # test_legacy_parameter_support,
            # test_mixed_config_usage
        ]

        for test in test_functions:
            print(f"\nRunning {test.__name__}...")
            try:
                await test()
                print(f"✓ {test.__name__} passed")
            except AssertionError as e:
                print(f"✗ {test.__name__} failed: {str(e)}")
            except Exception as e:
                print(f"✗ {test.__name__} error: {str(e)}")

    asyncio.run(run_tests())
