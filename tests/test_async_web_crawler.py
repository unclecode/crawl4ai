import pytest

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    MemoryAdaptiveDispatcher,
    RateLimiter,
)
from tests.helpers import EXAMPLE_URL


@pytest.mark.asyncio
async def test_arun():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=EXAMPLE_URL
        )
        assert result.status_code == 200
        assert result.url == EXAMPLE_URL
        assert result.markdown is not None

@pytest.mark.asyncio
async def test_arun_many():
    test_urls = [
        "https://www.python.org/",
        EXAMPLE_URL,
    ]
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=test_urls[:2],
        )
        assert len(results) == len(test_urls)
        for item in results:
            assert item.status_code == 200
            assert item.markdown is not None
            assert item.url in test_urls

@pytest.mark.asyncio
@pytest.mark.parametrize("viewport", [
    (800, 600),
    (1024, 768),
    (1920, 1080)
])
async def test_viewport_config(viewport):
    """Test different viewport configurations"""
    width, height = viewport
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=width,
        viewport_height=height
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=EXAMPLE_URL,
            config=CrawlerRunConfig(
                page_timeout=30000  # 30 seconds
            )
        )
        assert result.success

@pytest.mark.asyncio
async def test_memory_management():
    """Test memory-adaptive dispatching"""
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=1024,
        viewport_height=768
    )
    
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=5
    )
    
    urls = [EXAMPLE_URL] * 3  # Test with multiple identical URLs
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=CrawlerRunConfig(page_timeout=30000),
            dispatcher=dispatcher
        )
        assert len(results) == len(urls)

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting functionality"""
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )
    
    dispatcher = MemoryAdaptiveDispatcher(
        rate_limiter=RateLimiter(
            base_delay=(1.0, 2.0),
            max_delay=5.0,
            max_retries=2
        ),
        memory_threshold_percent=70.0
    )
    
    urls = [
        EXAMPLE_URL,
        "https://example.org",
        "https://example.net"
    ]
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=CrawlerRunConfig(page_timeout=30000),
            dispatcher=dispatcher
        )
        assert len(results) == len(urls)

@pytest.mark.asyncio
async def test_javascript_execution():
    """Test JavaScript execution capabilities"""
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        java_script_enabled=True
    )
    
    js_code = """
        document.body.style.backgroundColor = 'red';
        return document.body.style.backgroundColor;
    """
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=EXAMPLE_URL,
            config=CrawlerRunConfig(
                js_code=js_code,
                page_timeout=30000
            )
        )

    assert result.success

@pytest.mark.asyncio
@pytest.mark.parametrize("error_url", [
    "https://invalid.domain.test",
    "https://httpbin.org/status/404",
    "https://httpbin.org/status/503",
    "https://httpbin.org/status/403"
])
async def test_error_handling(error_url):
    """Test error handling for various failure scenarios"""
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=error_url,
            config=CrawlerRunConfig(
                page_timeout=10000
            )
        )

    assert not result.success
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_extract_media():
    async with AsyncWebCrawler() as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url)

        assert result.success
        assert result.media
        assert result.media["images"]
        assert any(img["src"] for img in result.media["images"])
        assert any(img["alt"] for img in result.media["images"])
        assert any(img["score"] for img in result.media["images"])

@pytest.mark.asyncio
async def test_extract_metadata():
    async with AsyncWebCrawler() as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url)

        assert result.success
        assert result.metadata
        assert all(
            key in result.metadata for key in ["title", "description", "keywords"]
        )
