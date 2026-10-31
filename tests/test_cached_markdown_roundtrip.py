"""Markdown variants must survive the filesystem/SQLite cache round trip."""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
from crawl4ai.async_database import AsyncDatabaseManager
from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.models import CrawlResult, MarkdownGenerationResult
from crawl4ai.utils import ensure_content_dirs


@pytest_asyncio.fixture
async def database(tmp_path):
    manager = AsyncDatabaseManager()
    manager.db_path = str(tmp_path / "crawl4ai.db")
    manager.content_paths = ensure_content_dirs(str(tmp_path))
    # Set up the real schema without running user-cache migrations.
    await manager.ainit_db()
    await manager.update_db_schema()
    manager._initialized = True
    try:
        yield manager
    finally:
        await manager.cleanup()


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_markdown", ["# Full page", "", "false", "123"])
async def test_cached_markdown_preserves_all_variants(database, raw_markdown):
    markdown = MarkdownGenerationResult(
        raw_markdown=raw_markdown,
        markdown_with_citations="Relevant text ⟨1⟩",
        references_markdown="⟨1⟩ https://example.com/source",
        fit_markdown="Relevant text 中文",
        fit_html="<p>Relevant text 中文</p>",
    )
    result = CrawlResult(
        url="https://example.com/article",
        html="<p>Full page</p>",
        cleaned_html="<p>Full page</p>",
        success=True,
        markdown=markdown,
    )

    await database.acache_url(result)
    restored = await database.aget_cached_url(result.url)

    assert restored is not None
    assert restored.markdown is not None
    assert restored.markdown.model_dump() == markdown.model_dump()
    assert str(restored.markdown) == raw_markdown


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content_filter",
    [
        PruningContentFilter(),
        BM25ContentFilter(user_query="memory retrieval", bm25_threshold=-1),
    ],
)
async def test_generated_filtered_markdown_survives_cache(
    database, content_filter, monkeypatch, tmp_path
):
    html = (
        "<html><body><article><h1>Memory retrieval</h1>"
        "<p>Memory retrieval gives agents access to relevant information from previous conversations. "
        'Read the <a href="https://example.com/source">source document</a> for details.</p>'
        "<p>Persistent storage preserves these results for the next retrieval request.</p>"
        "</article></body></html>"
    )
    markdown = DefaultMarkdownGenerator(
        content_filter=content_filter
    ).generate_markdown(html)
    assert markdown.fit_markdown
    assert markdown.references_markdown
    result = CrawlResult(
        url="https://example.com/article", html=html, success=True, markdown=markdown
    )

    await database.acache_url(result)
    monkeypatch.setattr("crawl4ai.async_webcrawler.async_db_manager", database)
    strategy = AsyncHTTPCrawlerStrategy()
    strategy.crawl = AsyncMock(
        side_effect=AssertionError("A cache hit must not fetch the page")
    )
    async with AsyncWebCrawler(
        crawler_strategy=strategy, base_directory=str(tmp_path)
    ) as crawler:
        restored = await crawler.arun(
            result.url, config=CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        )

    assert restored.success
    assert restored.cache_status == "hit"
    strategy.crawl.assert_not_awaited()
    assert restored.markdown.model_dump() == markdown.model_dump()


@pytest.mark.asyncio
@pytest.mark.parametrize("structured", [False, True])
async def test_loads_existing_plaintext_and_structured_cache_entries(
    database, structured
):
    markdown = MarkdownGenerationResult(
        raw_markdown="# Legacy page",
        markdown_with_citations="Legacy text ⟨1⟩",
        references_markdown="⟨1⟩ https://example.com/source",
        fit_markdown="Legacy text",
        fit_html="<p>Legacy text</p>",
    )
    result = CrawlResult(
        url="https://example.com/legacy",
        html="<p>Legacy page</p>",
        success=True,
        markdown=markdown,
    )
    await database.acache_url(result)
    content = markdown.model_dump_json() if structured else markdown.raw_markdown
    content_hash = await database._store_content(content, "markdown")

    async def replace_markdown(db):
        await db.execute(
            "UPDATE crawled_data SET markdown = ? WHERE url = ?",
            (content_hash, result.url),
        )

    await database.execute_with_retry(replace_markdown)
    restored = await database.aget_cached_url(result.url)

    assert restored is not None
    assert restored.markdown.raw_markdown == markdown.raw_markdown
    if structured:
        assert restored.markdown.model_dump() == markdown.model_dump()
