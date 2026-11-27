"""Structured table data must survive a normal public crawl cache hit."""

from copy import deepcopy
import json
from unittest.mock import patch

import aiosqlite
import pytest
import pytest_asyncio

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai import async_database, async_webcrawler
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.models import CrawlResult, MarkdownGenerationResult


@pytest_asyncio.fixture
async def isolated_cache(tmp_path, monkeypatch):
    # Keep SQLite, content files, version metadata, and crawler logs isolated.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(tmp_path))
    cache_dir = tmp_path / ".crawl4ai"
    cache_dir.mkdir()
    monkeypatch.setattr(async_database, "base_directory", str(cache_dir))
    monkeypatch.setattr(async_database, "DB_PATH", str(cache_dir / "crawl4ai.db"))
    manager = async_database.AsyncDatabaseManager()
    monkeypatch.setattr(async_webcrawler, "async_db_manager", manager)
    try:
        yield manager
    finally:
        await manager.cleanup()


@pytest.mark.asyncio
async def test_cached_local_crawl_preserves_tables(tmp_path, isolated_cache):
    html = """<html><head><title>Inventory report</title></head><body>
    <p>This inventory report records the available fruit and its current count.</p>
    <table><thead><tr><th>Item</th><th>Count</th></tr></thead>
    <tbody><tr><td>Apples</td><td>7</td></tr></tbody></table>
    </body></html>"""
    page = tmp_path / "inventory.html"
    page.write_text(html, encoding="utf-8")
    config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
    strategy = AsyncHTTPCrawlerStrategy()

    with patch.object(strategy, "crawl", wraps=strategy.crawl) as fetch:
        async with AsyncWebCrawler(
            crawler_strategy=strategy, base_directory=str(tmp_path)
        ) as crawler:
            first = await crawler.arun(page.as_uri(), config=config)
            cached = await crawler.arun(page.as_uri(), config=config)

    assert first.success, first.error_message
    assert cached.success, cached.error_message
    assert cached.cache_status == "hit"
    assert fetch.await_count == 1
    assert first.html == cached.html == html
    assert first.cleaned_html == cached.cleaned_html
    assert first.markdown.raw_markdown == cached.markdown.raw_markdown
    assert first.media == cached.media
    assert len(first.tables) == 1
    assert first.tables[0]["headers"] == ["Item", "Count"]
    assert first.tables[0]["rows"] == [["Apples", "7"]]
    assert cached.tables == first.tables


TABLE = {"headers": ["Item", "Count"], "rows": [["Apples", "7"]]}
LEGACY_TABLE = {"headers": ["Item", "Count"], "rows": [["Pears", "3"]]}


def make_result():
    return CrawlResult(
        url="file:///inventory.html",
        html="<html><body>Inventory report</body></html>",
        cleaned_html="<p>Inventory report</p>",
        markdown=MarkdownGenerationResult(
            raw_markdown="Inventory report",
            markdown_with_citations="Inventory report",
            references_markdown="",
        ),
        success=True,
        media={
            "images": [{"src": "photo.jpg"}],
            "videos": [{"src": "clip.mp4"}],
            "audios": [{"src": "clip.mp3"}],
            "custom": [{"label": "retained"}],
        },
        links={"internal": [{"href": "/inventory"}], "external": []},
        metadata={"title": "Inventory"},
        extracted_content='[{"item": "Apples"}]',
        screenshot="image-data",
        response_headers={"Content-Type": "text/html", "ETag": "inventory-v1"},
        downloaded_files=["inventory.csv"],
        head_fingerprint="inventory-fingerprint",
    )


def assert_other_cached_fields(actual, expected):
    assert actual is not None
    for name in (
        "url",
        "html",
        "cleaned_html",
        "success",
        "media",
        "links",
        "metadata",
        "extracted_content",
        "screenshot",
        "response_headers",
        "downloaded_files",
        "head_fingerprint",
    ):
        assert getattr(actual, name) == getattr(expected, name), name
    assert actual.markdown.raw_markdown == expected.markdown.raw_markdown


@pytest.mark.asyncio
async def test_cached_tables_insert_update_and_clear(isolated_cache):
    result = make_result()
    result.tables = [deepcopy(TABLE)]
    original_media = deepcopy(result.media)

    await isolated_cache.acache_url(result)
    cached = await isolated_cache.aget_cached_url(result.url)
    assert result.media == original_media
    assert_other_cached_fields(cached, result)
    assert cached.tables == [TABLE]
    assert "tables" not in cached.media

    cached.tables = [deepcopy(LEGACY_TABLE)]
    await isolated_cache.acache_url(cached)
    updated = await isolated_cache.aget_cached_url(result.url)
    assert_other_cached_fields(updated, result)
    assert updated.tables == [LEGACY_TABLE]

    # A modern read removes the legacy media key, so an explicit empty update
    # clears the stored tables instead of restoring the previous value.
    updated.tables = []
    await isolated_cache.acache_url(updated)
    cleared = await isolated_cache.aget_cached_url(result.url)
    assert_other_cached_fields(cleared, result)
    assert cleared.tables == []
    assert updated.media == original_media


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "historical_tables", [None, [LEGACY_TABLE]], ids=["missing", "legacy"]
)
async def test_old_media_json_records(isolated_cache, historical_tables):
    result = make_result()
    await isolated_cache.acache_url(result)
    stored_media = deepcopy(result.media)
    if historical_tables is not None:
        stored_media["tables"] = historical_tables

    # Seed the historical on-disk JSON shape, independent of the current writer.
    async with aiosqlite.connect(isolated_cache.db_path) as db:
        await db.execute(
            "UPDATE crawled_data SET media = ? WHERE url = ?",
            (json.dumps(stored_media), result.url),
        )
        await db.commit()

    cached = await isolated_cache.aget_cached_url(result.url)
    assert cached.tables == (historical_tables or [])
    assert_other_cached_fields(cached, result)
    assert "tables" not in cached.media


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "top_level_tables", [[], [TABLE]], ids=["legacy-input", "top-level-wins"]
)
async def test_table_write_precedence_preserves_input(isolated_cache, top_level_tables):
    result = make_result()
    expected_other_fields = result.model_copy(deep=True)
    result.media["tables"] = [deepcopy(LEGACY_TABLE)]
    result.tables = deepcopy(top_level_tables)
    original_media = deepcopy(result.media)

    await isolated_cache.acache_url(result)
    cached = await isolated_cache.aget_cached_url(result.url)

    assert result.media == original_media
    assert result.tables == top_level_tables
    assert cached.tables == (top_level_tables or [LEGACY_TABLE])
    assert_other_cached_fields(cached, expected_other_fields)
    assert "tables" not in cached.media
