import sys

import pytest

from crawl4ai import CacheMode
from crawl4ai.async_webcrawler import AsyncWebCrawler
from pytest_httpserver import HTTPServer


@pytest.mark.asyncio
@pytest.mark.skip("The result of this test is flaky")
async def test_word_count_threshold():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result_no_threshold = await crawler.arun(
            url=url, word_count_threshold=0, cache_mode=CacheMode.BYPASS
        )
        result_with_threshold = await crawler.arun(
            url=url, word_count_threshold=100, cache_mode=CacheMode.BYPASS
        )
        assert result_no_threshold.success
        assert result_with_threshold.success
        assert result_no_threshold.markdown
        assert result_with_threshold.markdown
        assert len(result_no_threshold.markdown) > len(result_with_threshold.markdown)


@pytest.mark.asyncio
async def test_css_selector():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        css_selector = "h1, h2, h3"
        result = await crawler.arun(
            url=url, css_selector=css_selector, cache_mode=CacheMode.BYPASS
        )

        assert result.success
        assert result.cleaned_html
        assert (
            "<h1" in result.cleaned_html
            or "<h2" in result.cleaned_html
            or "<h3" in result.cleaned_html
        )


@pytest.mark.asyncio
async def test_javascript_execution():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"

        # Crawl without JS
        result_without_more = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)
        assert result_without_more.success
        assert result_without_more.markdown
        js_code = [
            """function waitForBlobSizeChange(initialSize, timeout = 5000, interval = 100) {
                return new Promise((resolve, reject) => {
                    const startTime = Date.now();
                    const check = () => {
                        const currentSize = new Blob([document.documentElement.outerHTML]).size;

                        if (currentSize !== initialSize) {
                            resolve(currentSize);
                            return;
                        }

                        if (Date.now() - startTime > timeout) {
                            reject(new Error('Timeout: Blob size did not change.'));
                            return;
                        }

                        setTimeout(check, interval);
                    };

                    check();
                });
            }"""
            "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));"
            """if (loadMoreButton == null) {
                throw new Error('Load More button not found');
            } else {
                let initialSize = new Blob([document.documentElement.outerHTML]).size;
                loadMoreButton.click();
                return waitForBlobSizeChange(initialSize);
            }
            """,
        ]
        result_with_more = await crawler.arun(
            url=url, js_code=js_code, cache_mode=CacheMode.BYPASS
        )

        assert result_with_more.success
        assert result_with_more.markdown
        assert len(result_with_more.markdown) > len(result_without_more.markdown)


@pytest.mark.asyncio
async def test_screenshot():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(
            url=url, screenshot=True, cache_mode=CacheMode.BYPASS
        )

        assert result.success
        assert result.screenshot
        assert isinstance(result.screenshot, str)  # Should be a base64 encoded string


@pytest.mark.asyncio
async def test_custom_user_agent(httpserver: HTTPServer):
    custom_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Crawl4AI/1.0"
    httpserver.expect_request("/", headers={"User-Agent": custom_user_agent}).respond_with_data(
        content_type="text/html",
        response_data="<html><body>Simple page</body></html>"
    )
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=httpserver.url_for("/"), user_agent=custom_user_agent, cache_mode=CacheMode.BYPASS
        )

        assert result.success


@pytest.mark.asyncio
async def test_extract_media_and_links():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)

        assert result.success
        assert result.media
        assert isinstance(result.media, dict)
        assert "images" in result.media
        assert result.links
        assert isinstance(result.links, dict)
        assert "internal" in result.links and "external" in result.links


@pytest.mark.asyncio
async def test_metadata_extraction():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, cache_mode=CacheMode.BYPASS)

        assert result.success
        assert result.metadata
        assert isinstance(result.metadata, dict)
        # Check for common metadata fields
        assert any(
            key in result.metadata for key in ["title", "description", "keywords"]
        )


# Entry point for debugging
if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
