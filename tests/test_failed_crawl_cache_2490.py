"""
Tests for #2490: caching a failed crawl (no markdown) must not raise, so the
crawl's own error message reaches the caller under CacheMode.ENABLED.
"""
import pytest

from crawl4ai.async_database import AsyncDatabaseManager
from crawl4ai.models import CrawlResult
from crawl4ai.utils import ensure_content_dirs


@pytest.mark.asyncio
async def test_cache_failed_result_without_markdown(tmp_path):
    db = AsyncDatabaseManager()
    db.db_path = str(tmp_path / "crawl4ai.db")
    db.content_paths = ensure_content_dirs(str(tmp_path))
    await db.initialize()
    await db.update_db_schema()  # version marker is global; a fresh file still needs the columns
    try:
        url = "https://unreachable.invalid/"
        await db.acache_url(
            CrawlResult(url=url, html="", success=False, error_message="net::ERR_CONNECTION_REFUSED")
        )
        cached = await db.aget_cached_url(url)
        assert cached is not None and not cached.success
    finally:
        await db.cleanup()
