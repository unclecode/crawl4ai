import pytest

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, BestFirstCrawlingStrategy


@pytest.mark.asyncio
@pytest.mark.parametrize("strategy_cls", [BFSDeepCrawlStrategy, BestFirstCrawlingStrategy])
@pytest.mark.parametrize(
    "url",
    [
        "http://intranet/path",
        "https://localhost:8443/path",
        "http://127.0.0.1/path",
        "http://[::1]/path",
    ],
)
async def test_can_process_url_accepts_valid_single_label_and_ip_hosts(strategy_cls, url):
    strategy = strategy_cls(max_depth=1)

    assert await strategy.can_process_url(url, depth=0)


@pytest.mark.asyncio
@pytest.mark.parametrize("strategy_cls", [BFSDeepCrawlStrategy, BestFirstCrawlingStrategy])
@pytest.mark.parametrize(
    "url",
    [
        "intranet/path",
        "ftp://intranet/path",
        "http:///path",
        "http://:8080/path",
    ],
)
async def test_can_process_url_rejects_missing_or_invalid_hosts(strategy_cls, url):
    strategy = strategy_cls(max_depth=1)

    assert not await strategy.can_process_url(url, depth=0)
