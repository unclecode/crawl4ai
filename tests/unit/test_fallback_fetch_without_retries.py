"""A configured fallback must run after the only fetch attempt fails."""

from unittest.mock import AsyncMock, Mock

import pytest

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncCrawlerStrategy
from crawl4ai.models import AsyncCrawlResponse

URL = "https://example.com/"
HTML = "<html><body><p>" + "Recovered article content. " * 50 + "</p></body></html>"


@pytest.fixture
def crawler(tmp_path):
    strategy = Mock(spec=AsyncCrawlerStrategy)
    strategy.crawl = AsyncMock(side_effect=RuntimeError("fetch failed"))
    instance = AsyncWebCrawler(crawler_strategy=strategy, base_directory=str(tmp_path))
    instance.ready = True  # The fetch is mocked; no browser needs to start.
    return instance, strategy


def config(**kwargs):
    return CrawlerRunConfig(cache_mode=CacheMode.BYPASS, verbose=False, **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize("max_retries", [0, 1])
@pytest.mark.parametrize("failure", ["exception", "blocked"])
async def test_fallback_recovers_after_attempts_fail(crawler, max_retries, failure):
    instance, strategy = crawler
    callback = AsyncMock(return_value=HTML)
    if failure == "blocked":
        strategy.crawl.side_effect = None
        strategy.crawl.return_value = AsyncCrawlResponse(
            html="<html><body>Access denied</body></html>",
            status_code=403,
            response_headers={},
        )

    result = await instance.arun(
        URL, config=config(max_retries=max_retries, fallback_fetch_function=callback)
    )

    assert result.success, result.error_message
    assert "Recovered article content." in result.markdown.raw_markdown
    assert result.crawl_stats["resolved_by"] == "fallback_fetch"
    assert result.crawl_stats["fallback_fetch_used"] is True
    assert result.crawl_stats["attempts"] == max_retries + 1
    assert strategy.crawl.await_count == max_retries + 1
    callback.assert_awaited_once_with(URL)


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["empty", "exception"])
async def test_unsuccessful_fallback_keeps_the_fetch_failed(crawler, outcome):
    instance, _ = crawler
    callback = AsyncMock(return_value="")
    if outcome == "exception":
        callback.side_effect = RuntimeError("fallback failed")

    result = await instance.arun(URL, config=config(fallback_fetch_function=callback))

    assert not result.success
    assert "fetch failed" in result.error_message
    callback.assert_awaited_once_with(URL)
    assert result.crawl_stats["fallback_fetch_used"] is True
    assert result.crawl_stats["resolved_by"] is None


@pytest.mark.asyncio
async def test_no_fallback_preserves_the_original_fetch_error(crawler):
    instance, strategy = crawler

    result = await instance.arun(URL, config=config())

    assert not result.success
    assert "fetch failed" in result.error_message
    strategy.crawl.assert_awaited_once()


@pytest.mark.asyncio
async def test_raw_html_does_not_use_a_fetch_fallback(crawler):
    instance, strategy = crawler
    callback = AsyncMock(return_value=HTML)

    result = await instance.arun(
        "raw:<html><body>provided content</body></html>",
        config=config(fallback_fetch_function=callback),
    )

    assert not result.success
    assert "fetch failed" in result.error_message
    strategy.crawl.assert_awaited_once()
    callback.assert_not_awaited()


@pytest.mark.asyncio
async def test_successful_fetch_does_not_use_a_fallback(crawler):
    instance, strategy = crawler
    strategy.crawl.side_effect = None
    strategy.crawl.return_value = AsyncCrawlResponse(
        html=HTML, status_code=200, response_headers={}
    )
    callback = AsyncMock(return_value=HTML)

    result = await instance.arun(URL, config=config(fallback_fetch_function=callback))

    assert result.success, result.error_message
    assert result.crawl_stats["resolved_by"] == "direct"
    strategy.crawl.assert_awaited_once()
    callback.assert_not_awaited()
