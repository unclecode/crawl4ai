"""Audio/video context must survive conversion to public MediaItem results."""

import pytest

from crawl4ai import LXMLWebScrapingStrategy, WebScrapingStrategy


@pytest.mark.parametrize(
    "strategy_cls",
    [LXMLWebScrapingStrategy, WebScrapingStrategy],
    ids=["lxml", "legacy-alias"],
)
@pytest.mark.parametrize("media_type", ["video", "audio"])
@pytest.mark.parametrize("source_kind", ["direct", "source-child"])
@pytest.mark.parametrize(
    ("context", "expected"),
    [
        pytest.param("Clip introduction", "Clip introduction", id="plain-context"),
        pytest.param(
            "Clip <strong>introduction</strong>",
            "Clip introduction",
            id="inline-context",
        ),
        pytest.param("", "", id="no-context"),
    ],
)
def test_media_description_survives_public_scrap(
    strategy_cls, media_type, source_kind, context, expected
):
    """Direct media and source alternatives retain context in the documented desc field."""
    source_url = "/clip.mp4" if media_type == "video" else "/clip.mp3"
    if source_kind == "direct":
        media_html = f'<{media_type} src="{source_url}"></{media_type}>'
        expected_sources = [source_url]
    else:
        media_html = f'<{media_type}><source src="{source_url}"></{media_type}>'
        expected_sources = [None, source_url]
    html = f"<html><body><div>{context}{media_html}</div></body></html>"

    result = strategy_cls().scrap(
        "https://example.com/",
        html,
        word_count_threshold=0,
        image_description_min_word_threshold=1,
    )

    assert result.success
    items = getattr(result.media, f"{media_type}s")
    assert [item.src for item in items] == expected_sources
    assert all(item.type == media_type for item in items)
    assert [item.desc for item in items] == [expected] * len(items)
    serialized = result.model_dump()["media"][f"{media_type}s"]
    assert [item["desc"] for item in serialized] == [expected] * len(items)


@pytest.mark.parametrize(
    "strategy_cls",
    [LXMLWebScrapingStrategy, WebScrapingStrategy],
    ids=["lxml", "legacy-alias"],
)
def test_image_description_is_unchanged(strategy_cls):
    """Image context already uses desc and remains consistent with audio/video context."""
    result = strategy_cls().scrap(
        "https://example.com/",
        '<html><body><div>Clip introduction<img src="/photo.jpg" alt="Photo"></div></body></html>',
        word_count_threshold=0,
        image_description_min_word_threshold=1,
        image_score_threshold=0,
    )

    assert result.success
    assert len(result.media.images) == 1
    assert result.media.images[0].src == "/photo.jpg"
    assert result.media.images[0].desc == "Clip introduction"
