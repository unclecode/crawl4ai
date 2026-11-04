"""
file:// URLs must load the local file they point to.

Path.as_uri() builds standard file URLs: the path is percent-encoded (a space
becomes %20) and on Windows the drive letter follows a slash
(file:///C:/Users/...). The crawler strategies stripped the "file://" prefix
(or took urlparse().path) without decoding, so these URLs raised
FileNotFoundError, and on Windows the HTTP strategy could not read the
f"file://{path}" form from the docs either. Both forms must work.
"""

import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.async_crawler_strategy import (
    AsyncHTTPCrawlerStrategy,
    AsyncPlaywrightCrawlerStrategy,
)

HTML = "<html><body><h1>Local page</h1></body></html>"


@pytest.fixture
def local_page(tmp_path):
    # A space in the folder name makes Path.as_uri() percent-encode the path.
    folder = tmp_path / "my docs"
    folder.mkdir()
    page = folder / "page.html"
    page.write_text(HTML, encoding="utf-8")
    return page


def _file_url(page, form):
    return page.as_uri() if form == "as_uri" else f"file://{page}"


@pytest.mark.asyncio
@pytest.mark.parametrize("form", ["as_uri", "f-string"])
async def test_playwright_strategy_reads_file_url(local_page, form):
    """The fast path (no browser needed) reads both file URL forms."""
    strategy = AsyncPlaywrightCrawlerStrategy()
    response = await strategy.crawl(_file_url(local_page, form), CrawlerRunConfig())
    assert response.html == HTML


@pytest.mark.asyncio
@pytest.mark.parametrize("form", ["as_uri", "f-string"])
async def test_http_strategy_reads_file_url(local_page, form):
    """AsyncHTTPCrawlerStrategy reads both file URL forms."""
    strategy = AsyncHTTPCrawlerStrategy()
    response = await strategy.crawl(_file_url(local_page, form), CrawlerRunConfig())
    assert response.html == HTML


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strategy_cls", [AsyncPlaywrightCrawlerStrategy, AsyncHTTPCrawlerStrategy]
)
@pytest.mark.parametrize("form", ["as_uri", "f-string"])
async def test_missing_local_file_still_raises(tmp_path, strategy_cls, form):
    """A file URL to a missing file still raises FileNotFoundError."""
    url = _file_url(tmp_path / "missing.html", form)
    with pytest.raises(FileNotFoundError):
        await strategy_cls().crawl(url, CrawlerRunConfig())
