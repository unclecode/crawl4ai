import hashlib
import json
from unittest.mock import AsyncMock, MagicMock
import asyncio

from crawl4ai import CrawlerRunConfig
from crawl4ai.models import CrawlResult, MarkdownGenerationResult
from crawl4ai.source_receipt import attach_source_receipt


def test_arun_live_then_cache_uses_persisted_metadata(tmp_path, monkeypatch):
    async def exercise():
        from crawl4ai import AsyncWebCrawler, CacheMode
        from crawl4ai.models import AsyncCrawlResponse
        from crawl4ai.async_database import async_db_manager

        import crawl4ai.async_webcrawler as module
        from crawl4ai.utils import RobotsParser

        monkeypatch.setattr(
            module,
            "RobotsParser",
            lambda: RobotsParser(cache_dir=str(tmp_path / "robots")),
        )
        strategy = MagicMock()
        strategy.crawl = AsyncMock(
            return_value=AsyncCrawlResponse(
                html="<html><body><p>Fictional example page.</p></body></html>",
                response_headers={},
                status_code=200,
            )
        )
        crawler = AsyncWebCrawler(
            crawler_strategy=strategy, base_directory=str(tmp_path)
        )
        crawler.ready = True
        crawler.aprocess_html = AsyncMock(return_value=result())
        cached = None

        async def read(_url):
            return cached

        async def write(item):
            nonlocal cached
            cached = result(
                metadata=json.loads(json.dumps(item.metadata)), cached_at=2000
            )

        monkeypatch.setattr(async_db_manager, "aget_cached_url", read)
        monkeypatch.setattr(async_db_manager, "acache_url", write)
        config = CrawlerRunConfig(source_receipt=True, cache_mode=CacheMode.ENABLED)
        first = await crawler.arun("https://example.org/page", config=config)
        assert first.success
        assert first.source_receipt["fetched_at"] is not None
        replay = await crawler.arun("https://example.org/page", config=config)
        assert replay.source_receipt["cache_status"] == "hit"
        assert replay.source_receipt["fetched_at"] == first.source_receipt["fetched_at"]
        strategy.crawl.assert_awaited_once()
        crawler.aprocess_html.assert_awaited_once()

    asyncio.run(exercise())


def result(**kwargs):
    return CrawlResult(
        url="https://example.org/page?token=synthetic",
        html="<p>Example</p>",
        success=True,
        markdown=MarkdownGenerationResult(
            raw_markdown="中文\n\n",
            markdown_with_citations="",
            references_markdown="",
            fit_markdown="fit",
            fit_html="",
        ),
        **kwargs,
    )


def test_exact_returned_text_and_serialization():
    item = result(cache_status="miss")
    attach_source_receipt(item, CrawlerRunConfig(source_receipt=True), fetched_at=1000)
    receipt = item.source_receipt
    assert (
        receipt["outputs"]["raw_markdown"]["sha256"]
        == hashlib.sha256("中文\n\n".encode()).hexdigest()
    )
    assert receipt["outputs"]["raw_markdown"]["utf8_bytes"] == 8
    assert receipt["fetched_at"].startswith("1970-01-01T00:16:40")
    assert "synthetic" not in json.dumps(receipt)
    assert item.model_dump()["source_receipt"] == receipt


def test_cache_hit_preserves_fetch_and_processing_identity():
    item = result(cache_status="miss")
    attach_source_receipt(item, CrawlerRunConfig(), fetched_at=1000)
    original = item.source_receipt
    # Cache persists metadata; it need not persist the opt-in result field itself.
    replay = result(cache_status="hit", metadata=json.loads(json.dumps(item.metadata)))
    attach_source_receipt(replay, CrawlerRunConfig(word_count_threshold=999))
    assert replay.source_receipt["fetched_at"] == original["fetched_at"]
    assert (
        replay.source_receipt["processing_fingerprint"]
        == original["processing_fingerprint"]
    )
    assert replay.source_receipt["outputs"] == original["outputs"]


def test_legacy_cache_keeps_unknown_fetch_time_and_configuration():
    item = result(cache_status="hit_fallback", cached_at=1000)
    attach_source_receipt(item, CrawlerRunConfig())
    assert item.source_receipt["fetched_at"] is None
    assert item.source_receipt["processing_fingerprint"] is None
    assert item.source_receipt["served_at"]


def test_receipt_is_opt_in_and_config_round_trips():
    assert CrawlerRunConfig().source_receipt is False
    assert result().source_receipt is None
    assert CrawlerRunConfig(source_receipt=True).clone().source_receipt is True


def test_no_raw_html_or_credentials_and_failed_results_have_no_receipt():
    item = CrawlResult(url="raw:<p>private fixture</p>", html="", success=True)
    attach_source_receipt(item, CrawlerRunConfig(), fetched_at=1000)
    assert item.source_receipt["requested_url"] is None
    assert item.source_receipt["fetched_at"] is None
    assert "private fixture" not in json.dumps(item.source_receipt)
    failed = CrawlResult(url="https://example.org", html="", success=False)
    attach_source_receipt(failed, CrawlerRunConfig())
    assert failed.source_receipt is None
