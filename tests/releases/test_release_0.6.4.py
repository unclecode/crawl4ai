import pytest
import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode


@pytest.mark.asyncio
async def test_wait_for_timeout_separate_from_page_timeout():
    """Test that wait_for has its own timeout separate from page_timeout"""
    browser_config = BrowserConfig(headless=True)
    
    # Test with short wait_for_timeout but longer page_timeout
    config = CrawlerRunConfig(
        wait_for="css:.nonexistent-element",
        wait_for_timeout=2000,  # 2 seconds
        page_timeout=10000,     # 10 seconds
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        start_time = time.time()
        result = await crawler.arun("https://example.com", config=config)
        elapsed = time.time() - start_time
        
        # Should timeout after ~2 seconds (wait_for_timeout), not 10 seconds
        assert elapsed < 5, f"Expected timeout around 2s, but took {elapsed:.2f}s"
        assert result.success, "Crawl should still succeed even if wait_for times out"


@pytest.mark.asyncio
async def test_wait_for_timeout_with_existing_element():
    """Test that wait_for_timeout works correctly when element exists"""
    browser_config = BrowserConfig(headless=True)
    
    config = CrawlerRunConfig(
        wait_for="css:body",  # This should exist quickly
        wait_for_timeout=5000,
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        start_time = time.time()
        result = await crawler.arun("https://example.com", config=config)
        elapsed = time.time() - start_time
        
        # Should complete quickly since body element exists
        assert elapsed < 3, f"Expected quick completion, but took {elapsed:.2f}s"
        assert result.success
        assert "<body" in result.html


@pytest.mark.asyncio
async def test_javascript_wait_for_timeout():
    """Test wait_for_timeout with JavaScript condition"""
    browser_config = BrowserConfig(headless=True)
    
    config = CrawlerRunConfig(
        wait_for="js:() => window.nonExistentVariable === true",
        wait_for_timeout=2000,
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        start_time = time.time()
        result = await crawler.arun("https://example.com", config=config)
        elapsed = time.time() - start_time
        
        # Should timeout after ~2 seconds
        assert elapsed < 4, f"Expected timeout around 2s, but took {elapsed:.2f}s"
        assert result.success


@pytest.mark.asyncio
async def test_google_analytics_integration():
    """Test that Google Analytics scripts are properly integrated"""
    browser_config = BrowserConfig(headless=True)
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    # Test with a simple HTML page that we can control
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test GA Integration</title>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('config', 'GA_MEASUREMENT_ID');
        </script>
    </head>
    <body>
        <h1>Test Page</h1>
        <p>Testing Google Analytics integration</p>
    </body>
    </html>
    """
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(f"raw://{html_content}", config=config)
        
        assert result.success
        # Check that GA scripts are preserved in the HTML
        assert "googletagmanager.com/gtag/js" in result.html
        assert "dataLayer" in result.html
        assert "gtag('config'" in result.html


@pytest.mark.asyncio
async def test_mkdocs_no_duplicate_gtag():
    """Test that there are no duplicate gtag.js entries in documentation"""
    browser_config = BrowserConfig(headless=True)
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    # Simulate MkDocs-like HTML structure
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crawl4AI Documentation</title>
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('config', 'G-XXXXXXXXXX');
        </script>
    </head>
    <body>
        <h1>Crawl4AI Documentation</h1>
        <p>Welcome to the documentation</p>
    </body>
    </html>
    """
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(f"raw://{html_content}", config=config)
        
        assert result.success
        # Count occurrences of gtag.js to ensure no duplicates
        gtag_count = result.html.count("googletagmanager.com/gtag/js")
        assert gtag_count <= 1, f"Found {gtag_count} gtag.js scripts, expected at most 1"
        
        # Ensure the analytics functionality is still there
        if gtag_count == 1:
            assert "dataLayer" in result.html
            assert "gtag('config'" in result.html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])