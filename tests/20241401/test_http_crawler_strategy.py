import sys
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy, ConnectionTimeoutError
from crawl4ai.async_logger import AsyncLogger
from crawl4ai import CrawlerRunConfig, HTTPCrawlerConfig
import pytest
import pytest_asyncio
from httpx import codes

@pytest_asyncio.fixture
async def crawler():
    async with AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(),
        logger=AsyncLogger(verbose=True)
    ) as crawler:
        yield crawler

@pytest.mark.asyncio
async def test_basic_get(crawler: AsyncHTTPCrawlerStrategy):
    result = await crawler.crawl("https://example.com")
    assert result.status_code == codes.OK
    assert result.html
    assert result.response_headers
    print(f"Status: {result.status_code}")
    print(f"Content length: {len(result.html)}")
    print(f"Headers: {dict(result.response_headers)}")

@pytest.mark.asyncio
async def test_post_with_json(crawler: AsyncHTTPCrawlerStrategy):
    crawler.browser_config = crawler.browser_config.clone(
        method="POST",
        json={"test": "data"},
        headers={"Content-Type": "application/json"}
    )
    result = await crawler.crawl(
        "https://httpbin.org/post",
    )
    assert result.status_code == codes.OK
    assert result.html
    print(f"Response: {result.html[:200]}...")

@pytest.mark.asyncio
async def test_file_handling(crawler: AsyncHTTPCrawlerStrategy):
    crawler.browser_config = HTTPCrawlerConfig()
    # Create a tmp file with test content
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False) as f:
        f.write(b"<html><body>Test content</body></html>")
        f.close()
        result = await crawler.crawl(f"file://{f.name}")
        assert result.status_code == codes.OK
        assert result.html == "<html><body>Test content</body></html>"

@pytest.mark.asyncio
async def test_raw_content(crawler: AsyncHTTPCrawlerStrategy):
    raw_html = "raw://<html><body>Raw test content</body></html>"
    result = await crawler.crawl(raw_html)
    assert result.status_code == codes.OK
    assert result.html == "<html><body>Raw test content</body></html>"

@pytest.mark.asyncio
async def test_custom_hooks(crawler: AsyncHTTPCrawlerStrategy):
    before_called: bool = False
    async def before_request(url, kwargs):
        print(f"Before request to {url}")
        kwargs['headers']['X-Custom'] = 'test'
        nonlocal before_called
        before_called = True

    after_called: bool = False
    async def after_request(response):
        print(f"After request, status: {response.status_code}")
        nonlocal after_called
        after_called = True

    crawler.set_hook('before_request', before_request)
    crawler.set_hook('after_request', after_request)
    result = await crawler.crawl("https://example.com")
    assert result.status_code == codes.OK
    assert result.html
    assert before_called
    assert after_called

@pytest.mark.asyncio
async def test_error_handling(crawler: AsyncHTTPCrawlerStrategy):
    with pytest.raises(ConnectionError):
        await crawler.crawl("https://nonexistent.domain.test")

@pytest.mark.asyncio
async def test_redirects(crawler: AsyncHTTPCrawlerStrategy):
    crawler.browser_config = HTTPCrawlerConfig(follow_redirects=True)
    result = await crawler.crawl("http://httpbin.org/redirect/1")
    assert result.status_code == codes.OK
    assert result.redirected_url == "http://httpbin.org/get"

@pytest.mark.asyncio
async def test_custom_timeout(crawler: AsyncHTTPCrawlerStrategy):
    print("\n=== Test 8: Custom timeout ===")
    with pytest.raises(ConnectionTimeoutError):
        await crawler.crawl(
            "https://httpbin.org/delay/5",
            config=CrawlerRunConfig(page_timeout=2)
        )

@pytest.mark.asyncio
async def test_ssl_verify_off(crawler: AsyncHTTPCrawlerStrategy):
    crawler.browser_config = HTTPCrawlerConfig(verify_ssl=False)
    result = await crawler.crawl("https://expired.badssl.com/")
    assert result.status_code == codes.OK

@pytest.mark.asyncio
async def test_ssl_verify_on(crawler: AsyncHTTPCrawlerStrategy):
    with pytest.raises(ConnectionError):
        crawler.browser_config = HTTPCrawlerConfig()
        await crawler.crawl("https://expired.badssl.com/")

@pytest.mark.asyncio
async def test_large_file_streaming(crawler: AsyncHTTPCrawlerStrategy):
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile() as f:
        f.write(b"<html><body>" + b"X" * 1024 * 1024 * 10 + b"</body></html>")
        f.flush()
        size: int = f.tell()
        result = await crawler.crawl("file://" + f.name)
        assert result.status_code == codes.OK
        assert len(result.html) == size
        f.close()

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
