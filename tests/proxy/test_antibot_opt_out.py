from unittest.mock import AsyncMock, Mock

import pytest

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.models import AsyncCrawlResponse, CrawlResult


@pytest.mark.asyncio
async def test_check_blocked_false_skips_antibot_detector(monkeypatch, tmp_path):
    url = "https://example.com/small"
    html = "<html><body>small legitimate page</body></html>"
    response = AsyncCrawlResponse(html=html, response_headers={}, status_code=200)
    strategy = Mock(crawl=AsyncMock(return_value=response))
    crawler = AsyncWebCrawler(crawler_strategy=strategy, base_directory=str(tmp_path))
    crawler.ready = True
    page = CrawlResult(url=url, html=html, success=True)
    crawler.aprocess_html = AsyncMock(return_value=page)
    monkeypatch.setattr(
        "crawl4ai.async_webcrawler.is_blocked",
        Mock(side_effect=AssertionError("detector should be skipped")),
    )

    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, check_blocked=False)
    result = await crawler.arun(url, config=config)

    assert result.success is True
    assert result.crawl_stats["proxies_used"][0]["blocked"] is False
