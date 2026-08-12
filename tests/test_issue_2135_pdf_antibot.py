import pytest

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig, CrawlResult
from crawl4ai.processors.pdf import PDFCrawlerStrategy


@pytest.mark.asyncio
async def test_pdf_response_skips_antibot_retries_and_fallback():
    fallback_calls = []

    async def process_html(url, html, **kwargs):
        return CrawlResult(url=url, html=html, success=True, status_code=200)

    async def fallback(url):
        fallback_calls.append(url)
        return "<html>fallback</html>"

    crawler = AsyncWebCrawler(crawler_strategy=PDFCrawlerStrategy())
    crawler.aprocess_html = process_html
    result = await crawler.arun(
        "https://example.com/document.pdf",
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            max_retries=1,
            fallback_fetch_function=fallback,
        ),
    )
    assert result.success
    assert result.crawl_stats["attempts"] == 1
    assert fallback_calls == []
