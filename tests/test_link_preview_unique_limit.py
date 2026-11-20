from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from crawl4ai.async_configs import CrawlerRunConfig, LinkPreviewConfig
from crawl4ai.link_preview import LinkPreview
from crawl4ai.models import Link, Links


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("max_links", "expected"),
    [(1, ["a"]), (2, ["a", "b"]), (3, ["a", "b", "c"]), (10, ["a", "b", "c"])],
)
async def test_preview_limit_counts_unique_matching_urls(max_links, expected):
    links = Links(
        internal=[
            Link(href=f"https://example.test/{name}")
            for name in ["a", "a", "skip", "b"]
        ],
        external=[
            Link(href="https://example.test/b"),
            Link(href="https://example.test/c"),
            Link(href="https://other.test/ignored"),
        ],
    )
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_external=True,
            include_patterns=["https://example.test/*"],
            exclude_patterns=["*/skip"],
            max_links=max_links,
        )
    )
    preview = LinkPreview()
    preview.seeder = SimpleNamespace(extract_head_for_urls=AsyncMock(return_value=[]))

    await preview.extract_link_heads(links, config)

    sent = preview.seeder.extract_head_for_urls.await_args.kwargs["urls"]
    assert sent == [f"https://example.test/{name}" for name in expected]
