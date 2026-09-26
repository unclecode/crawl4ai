"""crawler_configs must reach arun_many for one URL and on the streaming path.

The per-URL config list (#1837) was only applied when a non-streaming request
carried two or more URLs. With one URL the handler called arun(), which takes a
single config, and /crawl/stream never passed the list down, so both requests
ran with crawler_config alone and still answered HTTP 200.

With the list applied, it also has to decide the crawler: a list of PDF entries
runs on PDFCrawlerStrategy, and one crawler cannot serve a list mixing PDF and
browser entries, so that is refused instead of failing mid-crawl.
"""

import asyncio

import pytest
from fastapi import HTTPException

from crawl4ai import CrawlerRunConfig
from crawl4ai.models import CrawlResult

PER_URL = [
    {
        "type": "CrawlerRunConfig",
        "params": {"url_matcher": "*example.com*", "word_count_threshold": 7},
    },
]


class RecordingCrawler:
    def __init__(self):
        self.calls = []

    async def arun(self, url, config=None, **kwargs):
        self.calls.append(("arun", url, config))
        return CrawlResult(url=url, html="", success=True)

    async def arun_many(self, urls, config=None, **kwargs):
        self.calls.append(("arun_many", urls, config))
        return [CrawlResult(url=url, html="", success=True) for url in urls]


def _install(monkeypatch, crawler):
    import api
    import crawler_pool

    async def get_crawler(*args, **kwargs):
        return crawler

    async def release_crawler(*args, **kwargs):
        return None

    # Offline: the seed check resolves DNS.
    monkeypatch.setattr(api, "validate_url_destination", lambda url: None)
    monkeypatch.setattr(crawler_pool, "get_crawler", get_crawler)
    monkeypatch.setattr(crawler_pool, "release_crawler", release_crawler)
    return api


def test_single_url_uses_the_config_list(server_module, monkeypatch):
    crawler = RecordingCrawler()
    api = _install(monkeypatch, crawler)

    asyncio.run(
        api.handle_crawl_request(
            urls=["https://example.com/"],
            browser_config={},
            crawler_config={},
            config=server_module.config,
            crawler_configs=PER_URL,
        )
    )

    [(method, urls, config)] = crawler.calls
    assert method == "arun_many"
    assert urls == ["https://example.com/"]
    assert [c.word_count_threshold for c in config] == [7]


def test_single_url_without_a_list_still_uses_arun(server_module, monkeypatch):
    crawler = RecordingCrawler()
    api = _install(monkeypatch, crawler)

    asyncio.run(
        api.handle_crawl_request(
            urls=["https://example.com/"],
            browser_config={},
            crawler_config={},
            config=server_module.config,
        )
    )

    [(method, url, config)] = crawler.calls
    assert method == "arun"
    assert url == "https://example.com/"
    assert isinstance(config, CrawlerRunConfig)


def test_stream_passes_the_config_list(server_module, monkeypatch):
    crawler = RecordingCrawler()
    api = _install(monkeypatch, crawler)

    asyncio.run(
        api.handle_stream_crawl_request(
            urls=["https://example.com/", "https://example.org/"],
            browser_config={},
            crawler_config={},
            config=server_module.config,
            crawler_configs=PER_URL,
        )
    )

    [(method, urls, config)] = crawler.calls
    assert method == "arun_many"
    assert [c.word_count_threshold for c in config] == [7]
    # arun_many takes the stream flag from the first config of a list.
    assert all(c.stream for c in config)


def test_stream_endpoint_forwards_the_list(server_module, monkeypatch):
    captured = {}

    async def fake_handle_stream(**kwargs):
        captured.update(kwargs)
        raise RuntimeError("stop after capture")

    monkeypatch.setattr(
        server_module, "handle_stream_crawl_request", fake_handle_stream
    )
    request = server_module.CrawlRequestWithHooks(
        urls=["https://example.com/"], crawler_configs=PER_URL
    )

    try:
        asyncio.run(server_module.stream_process(crawl_request=request))
    except RuntimeError:
        pass

    assert captured["crawler_configs"] == PER_URL


PDF = {"type": "PDFContentScrapingStrategy", "params": {}}
ALL_PDF = [
    {
        "type": "CrawlerRunConfig",
        "params": {"url_matcher": "*.pdf", "scraping_strategy": PDF},
    },
]
MIXED = ALL_PDF + [{"type": "CrawlerRunConfig", "params": {"url_matcher": "*"}}]


class RecordingPdfCrawler(RecordingCrawler):
    """Stands in for AsyncWebCrawler(crawler_strategy=PDFCrawlerStrategy())."""

    def __init__(self, crawler_strategy=None, **kwargs):
        super().__init__()
        self.crawler_strategy = crawler_strategy

    async def start(self):
        return self

    async def close(self):
        return None


def test_a_list_of_pdf_entries_runs_on_the_pdf_crawler(server_module, monkeypatch):
    from crawl4ai.processors.pdf import PDFCrawlerStrategy

    api = _install(monkeypatch, RecordingCrawler())
    made = []

    def pdf_crawler(**kwargs):
        made.append(RecordingPdfCrawler(**kwargs))
        return made[-1]

    monkeypatch.setattr(api, "AsyncWebCrawler", pdf_crawler)

    asyncio.run(
        api.handle_crawl_request(
            urls=["https://example.com/a.pdf"],
            browser_config={},
            crawler_config={},
            config=server_module.config,
            crawler_configs=ALL_PDF,
        )
    )

    [crawler] = made
    assert isinstance(crawler.crawler_strategy, PDFCrawlerStrategy)
    [(method, urls, config)] = crawler.calls
    assert method == "arun_many"
    # SSRF: every per-URL PDF entry still gets the destination check.
    assert config[0].scraping_strategy.url_validator is api.validate_url_destination


@pytest.mark.parametrize("stream", [False, True])
def test_a_list_mixing_pdf_and_browser_entries_is_refused(
    server_module, monkeypatch, stream
):
    api = _install(monkeypatch, RecordingCrawler())
    handler = api.handle_stream_crawl_request if stream else api.handle_crawl_request

    with pytest.raises(HTTPException) as refused:
        asyncio.run(
            handler(
                urls=["https://example.com/a.pdf", "https://example.com/"],
                browser_config={},
                crawler_config={},
                config=server_module.config,
                crawler_configs=MIXED,
            )
        )

    assert refused.value.status_code == 400
