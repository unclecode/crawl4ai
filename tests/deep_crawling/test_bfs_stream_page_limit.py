import pytest

from crawl4ai import CrawlResult, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

ROOT = "https://example.test/"
CHILDREN = [f"{ROOT}child-{index}" for index in range(3)]


class PageGraphCrawler:
    """Return real result/config objects without starting a browser."""

    def __init__(self, failed_urls=()):
        self.failed_urls = set(failed_urls)
        self.produced_urls = []

    async def arun_many(self, urls, config):
        def result(url):
            self.produced_urls.append(url)
            return CrawlResult(
                url=url,
                html="",
                success=url not in self.failed_urls,
                links={
                    "internal": (
                        [{"href": child} for child in CHILDREN] if url == ROOT else []
                    ),
                    "external": [],
                },
            )

        if config.stream:

            async def stream():
                for url in urls:
                    yield result(url)

            return stream()
        return [result(url) for url in urls]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("limit", [1, 2, 3, 4])
async def test_bfs_returns_the_page_that_reaches_the_limit(stream, limit):
    crawler = PageGraphCrawler()
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=limit)
    result = await strategy.arun(ROOT, crawler, CrawlerRunConfig(stream=stream))
    pages = [page async for page in result] if stream else result

    assert [page.url for page in pages] == [ROOT, *CHILDREN][:limit]
    assert len(crawler.produced_urls) == limit
    assert pages[0].metadata == {"depth": 0, "parent_url": None}
    for page in pages[1:]:
        assert page.metadata == {"depth": 1, "parent_url": ROOT}


@pytest.mark.asyncio
async def test_bfs_resumed_stream_yields_failures_and_the_last_allowed_success():
    crawler = PageGraphCrawler(failed_urls=[CHILDREN[0]])
    strategy = BFSDeepCrawlStrategy(
        max_depth=1,
        max_pages=3,
        resume_state={
            "visited": [ROOT],
            "pending": [{"url": url, "parent_url": ROOT} for url in CHILDREN],
            "depths": {ROOT: 0, **dict.fromkeys(CHILDREN, 1)},
            "pages_crawled": 2,
        },
    )
    result = await strategy.arun(ROOT, crawler, CrawlerRunConfig(stream=True))
    pages = [page async for page in result]

    assert [page.url for page in pages] == CHILDREN[:2]
    assert [page.success for page in pages] == [False, True]
    assert crawler.produced_urls == CHILDREN[:2]
    assert pages[-1].metadata == {"depth": 1, "parent_url": ROOT}


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_bfs_without_a_page_limit_returns_all_available_pages(stream):
    crawler = PageGraphCrawler()
    strategy = BFSDeepCrawlStrategy(max_depth=1)
    result = await strategy.arun(ROOT, crawler, CrawlerRunConfig(stream=stream))
    pages = [page async for page in result] if stream else result

    assert [page.url for page in pages] == [ROOT, *CHILDREN]
