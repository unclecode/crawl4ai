"""Public-entry coverage for total scores when preview filters skip links."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from crawl4ai.async_configs import CrawlerRunConfig, LinkPreviewConfig
from crawl4ai.link_preview import LinkPreview
from crawl4ai.models import Link, Links

INTERNAL_URL = "https://example.com/docs/guide"
EXTERNAL_URL = "https://example.net/reference"


def make_links(external_only=False):
    return Links(
        internal=(
            []
            if external_only
            else [Link(href=INTERNAL_URL, text="Guide", intrinsic_score=6.0)]
        ),
        external=[Link(href=EXTERNAL_URL, text="Reference", intrinsic_score=4.0)],
    )


def extract_links(links, preview_config, head_results=(), score_links=True):
    config = CrawlerRunConfig(
        score_links=score_links,
        link_preview_config=preview_config,
    )
    fetch = AsyncMock(return_value=list(head_results))
    preview = LinkPreview()
    # Replace only the fetch boundary with a caller-owned, initialized seeder.
    preview.seeder = SimpleNamespace(extract_head_for_urls=fetch)
    updated = asyncio.run(preview.extract_link_heads(links, config))
    return updated, fetch


@pytest.mark.parametrize(
    "preview_options,external_only",
    [
        ({"include_external": True, "exclude_patterns": ["*"]}, False),
        ({"include_external": True, "include_patterns": ["*/not-present/*"]}, False),
        ({}, True),
    ],
    ids=["exclude-all", "include-miss", "external-only-default-preview"],
)
@pytest.mark.parametrize("query", [None, "guide"])
@pytest.mark.parametrize("score_links", [True, False])
def test_no_selected_links_receive_fallback_scores_without_fetching(
    preview_options, external_only, query, score_links
):
    links = make_links(external_only)
    updated, fetch = extract_links(
        links,
        LinkPreviewConfig(query=query, **preview_options),
        score_links=score_links,
    )

    fetch.assert_not_awaited()
    assert [link.href for link in updated.internal] == [
        link.href for link in links.internal
    ]
    assert [link.href for link in updated.external] == [
        link.href for link in links.external
    ]
    for link in updated.internal + updated.external:
        assert link.total_score == (link.intrinsic_score if score_links else 5.0)
        assert link.head_data is None
        assert link.head_extraction_status is None
        assert link.contextual_score is None


@pytest.mark.parametrize("explicit_failure", [False, True], ids=["missing", "failed"])
def test_selected_links_with_no_head_score_keep_intrinsic_fallback(explicit_failure):
    head_results = (
        [
            {"url": url, "status": "failed", "error": "Head extraction failed"}
            for url in (INTERNAL_URL, EXTERNAL_URL)
        ]
        if explicit_failure
        else []
    )
    updated, fetch = extract_links(
        make_links(),
        LinkPreviewConfig(include_external=True, query="guide"),
        head_results,
    )

    fetch.assert_awaited_once()
    assert fetch.call_args.kwargs["urls"] == [INTERNAL_URL, EXTERNAL_URL]
    assert [link.total_score for link in updated.internal + updated.external] == [
        6.0,
        4.0,
    ]
    if explicit_failure:
        assert all(
            link.head_extraction_status == "failed"
            for link in updated.internal + updated.external
        )


@pytest.mark.parametrize(
    "preview_options",
    [{}, {"include_external": True, "exclude_patterns": ["https://example.net/*"]}],
    ids=["exclude-by-category", "exclude-by-pattern"],
)
def test_selected_links_keep_weighted_scores_and_unselected_links_keep_fallback(
    preview_options,
):
    updated, fetch = extract_links(
        make_links(),
        LinkPreviewConfig(query="guide", **preview_options),
        [
            {
                "url": INTERNAL_URL,
                "status": "valid",
                "head_data": {"title": "Guide"},
                "relevance_score": 0.8,
            }
        ],
    )

    fetch.assert_awaited_once()
    assert fetch.call_args.kwargs["urls"] == [INTERNAL_URL]
    assert updated.internal[0].total_score == pytest.approx(6.6)
    assert updated.internal[0].contextual_score == 0.8
    assert updated.internal[0].head_extraction_status == "valid"
    assert updated.external[0].total_score == 4.0
    assert updated.external[0].head_data is None
    assert updated.external[0].head_extraction_status is None


def test_empty_links_stay_empty_without_fetching():
    updated, fetch = extract_links(Links(), LinkPreviewConfig(query="guide"))

    fetch.assert_not_awaited()
    assert updated == Links()
