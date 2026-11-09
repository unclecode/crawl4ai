import asyncio
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace

import pytest

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig, utils
from crawl4ai.async_configs import LLMConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.async_database import async_db_manager
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.markdown_generation_strategy import CustomHTML2Text


@pytest.fixture
def site(tmp_path):
    (tmp_path / "page.html").write_text(
        "<html><head><title>Test</title></head><body><h1>Test page</h1><p>"
        + "A real page with enough content for the crawler. " * 60
        + "</p></body></html>",
        encoding="utf-8",
    )
    with ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=tmp_path)
    ) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/page.html"
        finally:
            server.shutdown()
            thread.join()


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(async_db_manager, "db_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(
        async_db_manager, "content_paths", utils.ensure_content_dirs(str(tmp_path))
    )
    monkeypatch.setattr(async_db_manager.version_manager, "needs_update", lambda: False)
    monkeypatch.setattr(async_db_manager, "_initialized", False)


async def crawl(crawler, url, mode=CacheMode.ENABLED, **kwargs):
    return await crawler.arun(url, config=CrawlerRunConfig(cache_mode=mode, **kwargs))


@pytest.mark.parametrize(
    ("method", "message"),
    [
        ("update_params", "Error in markdown generation: controlled failure"),
        ("handle", "Error converting HTML to markdown: controlled failure"),
    ],
)
def test_markdown_error_does_not_replace_good_cache(
    site, cache, monkeypatch, method, message
):
    def fail(*args, **kwargs):
        raise RuntimeError("controlled failure")

    async def run():
        await async_db_manager.ainit_db()
        await async_db_manager.update_db_schema()
        try:
            async with AsyncWebCrawler(
                crawler_strategy=AsyncHTTPCrawlerStrategy(), verbose=False
            ) as crawler:
                good = await crawl(crawler, site)
                assert good.cache_status == "miss"
                assert "A real page" in good.markdown

                with monkeypatch.context() as patch:
                    patch.setattr(CustomHTML2Text, method, fail)
                    failed = await crawl(crawler, site, CacheMode.WRITE_ONLY)
                    assert failed.success
                    assert message in failed.markdown.raw_markdown

                replay = await crawl(crawler, site)
                assert replay.cache_status == "hit"
                assert replay.markdown.raw_markdown == good.markdown.raw_markdown
        finally:
            await async_db_manager.cleanup()

    asyncio.run(run())


def test_llm_error_is_retried_instead_of_replayed(site, cache, monkeypatch):
    call_count = 0

    async def completion(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("controlled provider failure")
        return SimpleNamespace(
            usage=SimpleNamespace(
                completion_tokens=1,
                prompt_tokens=2,
                total_tokens=3,
                completion_tokens_details=None,
                prompt_tokens_details=None,
            ),
            choices=[
                SimpleNamespace(message=SimpleNamespace(content='[{"answer":"ok"}]'))
            ],
        )

    monkeypatch.setattr(utils, "aperform_completion_with_backoff", completion)
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/unused",
            api_token="test-token",
            base_url="http://127.0.0.1:9",
        ),
        force_json_response=True,
    )

    async def run():
        await async_db_manager.ainit_db()
        await async_db_manager.update_db_schema()
        try:
            async with AsyncWebCrawler(
                crawler_strategy=AsyncHTTPCrawlerStrategy(), verbose=False
            ) as crawler:
                failed = await crawl(crawler, site, extraction_strategy=strategy)
                assert failed.success
                assert call_count == 1
                assert json.loads(failed.extracted_content) == [
                    {
                        "index": 0,
                        "error": True,
                        "tags": ["error"],
                        "content": "controlled provider failure",
                    }
                ]

                recovered = await crawl(crawler, site, extraction_strategy=strategy)
                assert recovered.cache_status == "miss"
                assert json.loads(recovered.extracted_content) == [
                    {"answer": "ok", "error": False}
                ]
                replay = await crawl(crawler, site, extraction_strategy=strategy)
                assert replay.cache_status == "hit"
                assert replay.extracted_content == recovered.extracted_content
                assert call_count == 2
        finally:
            await async_db_manager.cleanup()

    asyncio.run(run())


def test_error_shaped_extracted_data_is_cacheable(site, cache, monkeypatch):
    data = {"error": True, "tags": ["error"], "content": "a ticket's data"}
    calls = 0

    async def completion(*args, **kwargs):
        nonlocal calls
        calls += 1
        return SimpleNamespace(
            usage=SimpleNamespace(
                completion_tokens=1,
                prompt_tokens=2,
                total_tokens=3,
                completion_tokens_details=None,
                prompt_tokens_details=None,
            ),
            choices=[
                SimpleNamespace(message=SimpleNamespace(content=json.dumps(data)))
            ],
        )

    monkeypatch.setattr(utils, "aperform_completion_with_backoff", completion)
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/unused",
            api_token="test-token",
            base_url="http://127.0.0.1:9",
        )
    )

    async def run():
        await async_db_manager.ainit_db()
        await async_db_manager.update_db_schema()
        try:
            async with AsyncWebCrawler(
                crawler_strategy=AsyncHTTPCrawlerStrategy(), verbose=False
            ) as crawler:
                result = await crawl(crawler, site, extraction_strategy=strategy)
                assert result.cache_status == "miss"
                assert json.loads(result.extracted_content) == [data]

                replay = await crawl(crawler, site, extraction_strategy=strategy)
                assert replay.cache_status == "hit"
                assert replay.extracted_content == result.extracted_content
                assert calls == 1
        finally:
            await async_db_manager.cleanup()

    asyncio.run(run())
