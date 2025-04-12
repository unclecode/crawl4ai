from tkinter import N
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.async_logger import AsyncLogger
from crawl4ai import CrawlerRunConfig, HTTPCrawlerConfig
from crawl4ai.async_crawler_strategy import ConnectionTimeoutError
import asyncio
import os

async def main():
    """Test the AsyncHTTPCrawlerStrategy with various scenarios"""
    logger = AsyncLogger(verbose=True)

    # Initialize the strategy with default HTTPCrawlerConfig
    crawler = AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(),
        logger=logger
    )
    # Test 1: Basic HTTP GET
    print("\n=== Test 1: Basic HTTP GET ===")
    result = await crawler.crawl("https://example.com")
    print(f"Status: {result.status_code}")
    print(f"Content length: {len(result.html)}")
    print(f"Headers: {dict(result.response_headers)}")

    # Test 2: POST request with JSON
    print("\n=== Test 2: POST with JSON ===")
    crawler.browser_config = crawler.browser_config.clone(
        method="POST",
        json={"test": "data"},
        headers={"Content-Type": "application/json"}
    )
    try:
        result = await crawler.crawl(
            "https://httpbin.org/post",
        )
        print(f"Status: {result.status_code}")
        print(f"Response: {result.html[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: File handling
    crawler.browser_config = HTTPCrawlerConfig()
    print("\n=== Test 3: Local file handling ===")
    # Create a tmp file with test content
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False) as f:
        f.write(b"<html><body>Test content</body></html>")
        f.close()
        result = await crawler.crawl(f"file://{f.name}")
        print(f"File content: {result.html}")

    # Test 4: Raw content
    print("\n=== Test 4: Raw content handling ===")
    raw_html = "raw://<html><body>Raw test content</body></html>"
    result = await crawler.crawl(raw_html)
    print(f"Raw content: {result.html}")

    # Test 5: Custom hooks
    print("\n=== Test 5: Custom hooks ===")
    async def before_request(url, kwargs):
        print(f"Before request to {url}")
        kwargs['headers']['X-Custom'] = 'test'

    async def after_request(response):
        print(f"After request, status: {response.status_code}")

    crawler.set_hook('before_request', before_request)
    crawler.set_hook('after_request', after_request)
    result = await crawler.crawl("https://example.com")

    # Test 6: Error handling
    print("\n=== Test 6: Error handling ===")
    try:
        await crawler.crawl("https://nonexistent.domain.test")
    except Exception as e:
        print(f"Expected error: {e}")

    # Test 7: Redirects
    print("\n=== Test 7: Redirect handling ===")
    crawler.browser_config = HTTPCrawlerConfig(follow_redirects=True)
    result = await crawler.crawl("http://httpbin.org/redirect/1")
    print(f"Final URL: {result.redirected_url}")

    # Test 8: Custom timeout
    print("\n=== Test 8: Custom timeout ===")
    try:
        await crawler.crawl(
            "https://httpbin.org/delay/5",
            config=CrawlerRunConfig(page_timeout=2)
        )
    except ConnectionTimeoutError as e:
        print(f"Expected timeout: {e}")

    # Test 9: SSL verification
    print("\n=== Test 9: SSL verification ===")
    crawler.browser_config = HTTPCrawlerConfig(verify_ssl=False)
    try:
        await crawler.crawl("https://expired.badssl.com/")
        print("Connected to invalid SSL site with verification disabled")
    except Exception as e:
        print(f"SSL error: {e}")

    # Test 10: Large file streaming
    print("\n=== Test 10: Large file streaming ===")
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False) as f:
        f.write(b"<html><body>" + b"X" * 1024 * 1024 * 10 + b"</body></html>")
        f.close()
        result = await crawler.crawl("file://" + f.name)
        print(f"Large file content length: {len(result.html)}")
        os.remove(f.name)

    crawler.close()

if __name__ == "__main__":
    asyncio.run(main())