"""Raw-HTML base URLs must survive configuration cloning."""

from unittest.mock import Mock

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncCrawlerStrategy

BASE_URL = "https://example.test/docs/"


@pytest.mark.parametrize("base_url", [None, BASE_URL])
def test_base_url_from_kwargs(base_url):
    config = CrawlerRunConfig.from_kwargs({"base_url": base_url})

    assert config.base_url == base_url


@pytest.mark.parametrize("base_url", [None, BASE_URL])
def test_base_url_dict_roundtrip(base_url):
    config = CrawlerRunConfig(base_url=base_url)
    config_dict = config.to_dict()

    assert config_dict["base_url"] == base_url
    assert CrawlerRunConfig.from_kwargs(config_dict).base_url == base_url


@pytest.mark.parametrize("base_url", [None, BASE_URL])
@pytest.mark.parametrize("updates", [{}, {"stream": True}])
def test_clone_preserves_base_url(base_url, updates):
    config = CrawlerRunConfig(base_url=base_url)
    cloned = config.clone(**updates)

    assert cloned is not config
    assert cloned.base_url == base_url
    assert cloned.stream is updates.get("stream", False)
    assert config.base_url == base_url
    assert config.stream is False


@pytest.mark.parametrize("base_url", [None, "https://other.test/content/"])
def test_clone_can_update_base_url(base_url):
    config = CrawlerRunConfig(base_url=BASE_URL)
    cloned = config.clone(base_url=base_url)

    assert cloned.base_url == base_url
    assert config.base_url == BASE_URL


@pytest.mark.asyncio
@pytest.mark.parametrize("prefetch", [True, False])
async def test_cloned_config_preserves_raw_html_link_resolution(tmp_path, prefetch):
    html = '<html><body><p>Read the <a href="guide.html">guide</a>.</p></body></html>'
    expected = "https://example.test/docs/guide.html"
    # Process supplied HTML directly without starting or calling the strategy.
    strategy = Mock(spec=AsyncCrawlerStrategy)
    crawler = AsyncWebCrawler(
        crawler_strategy=strategy,
        config=BrowserConfig(verbose=False),
        base_directory=str(tmp_path),
    )
    config = CrawlerRunConfig(
        base_url=BASE_URL, prefetch=prefetch, word_count_threshold=0
    )

    async def process(run_config):
        return await crawler.aprocess_html(
            url="raw:" + html,
            html=html,
            extracted_content=None,
            config=run_config,
            screenshot_data=None,
            pdf_data=None,
            verbose=False,
        )

    control = await process(config)
    result = await process(config.clone(stream=True))

    assert strategy.mock_calls == []
    for processed in (control, result):
        assert processed.success
        if prefetch:
            hrefs = [
                link["href"] for links in processed.links.values() for link in links
            ]
            assert expected in hrefs
        else:
            assert expected in processed.markdown.raw_markdown
