"""Regression tests for the public domain mapper configuration boundary."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import DomainMapperConfig


@pytest.mark.parametrize("initialized", [False, True])
def test_amap_domain_preserves_explicit_config(tmp_path, initialized):
    config = DomainMapperConfig(
        source="sitemap",
        max_urls=3,
        concurrency=1,
        include_subdomains=False,
        extract_head=False,
        http_timeout=2.0,
    )
    expected = [{"url": "https://example.com/docs"}]
    mapper = AsyncMock()
    mapper.scan.return_value = expected
    crawler = AsyncWebCrawler(base_directory=str(tmp_path))
    if initialized:
        crawler._domain_mapper = mapper

    with patch(
        "crawl4ai.async_webcrawler.DomainMapper", return_value=mapper
    ) as factory:
        result = asyncio.run(crawler.amap_domain("example.com", config=config))

    mapper.scan.assert_awaited_once_with("example.com", config)
    assert result is expected
    if initialized:
        factory.assert_not_called()
    else:
        factory.assert_called_once_with(
            logger=crawler.logger, base_directory=crawler.crawl4ai_folder
        )


def test_amap_domain_overrides_without_mutating_config(tmp_path):
    config = DomainMapperConfig(source="sitemap", max_urls=3, include_subdomains=False)
    original = config.to_dict()
    mapper = AsyncMock()
    crawler = AsyncWebCrawler(base_directory=str(tmp_path))
    crawler._domain_mapper = mapper

    asyncio.run(crawler.amap_domain("example.com", config=config, max_urls=2))

    actual = mapper.scan.await_args.args[1]
    assert actual is not config
    assert actual.to_dict() == {**original, "max_urls": 2}
    assert config.to_dict() == original


def test_amap_domain_builds_config_from_kwargs(tmp_path):
    mapper = AsyncMock()
    crawler = AsyncWebCrawler(base_directory=str(tmp_path))
    crawler._domain_mapper = mapper

    asyncio.run(
        crawler.amap_domain(
            "example.com", source="feed", max_urls=4, include_subdomains=False
        )
    )

    actual = mapper.scan.await_args.args[1]
    assert (
        actual.to_dict()
        == DomainMapperConfig(
            source="feed", max_urls=4, include_subdomains=False
        ).to_dict()
    )


def test_amap_domain_creates_fresh_default_configs(tmp_path):
    mapper = AsyncMock()
    crawler = AsyncWebCrawler(base_directory=str(tmp_path))
    crawler._domain_mapper = mapper

    asyncio.run(crawler.amap_domain("example.com"))
    asyncio.run(crawler.amap_domain("example.org", config=None))

    first = mapper.scan.await_args_list[0].args[1]
    second = mapper.scan.await_args_list[1].args[1]
    assert first is not second
    assert first.to_dict() == second.to_dict() == DomainMapperConfig().to_dict()


def test_amap_domain_propagates_scan_errors(tmp_path):
    error = ValueError("invalid discovery source")
    mapper = AsyncMock()
    mapper.scan.side_effect = error
    crawler = AsyncWebCrawler(base_directory=str(tmp_path))
    crawler._domain_mapper = mapper
    config = DomainMapperConfig(source="invalid")

    with pytest.raises(ValueError) as raised:
        asyncio.run(crawler.amap_domain("example.com", config=config))

    assert raised.value is error
    mapper.scan.assert_awaited_once_with("example.com", config)
