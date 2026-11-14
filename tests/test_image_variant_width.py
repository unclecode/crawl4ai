"""Keep detected srcset width metadata when image URLs are deduplicated."""

import pytest

from crawl4ai import LXMLWebScrapingStrategy, WebScrapingStrategy


@pytest.mark.parametrize(
    ("attributes", "expected"),
    [
        pytest.param(
            'src="photo.jpg" srcset="photo.jpg 640w"',
            [("photo.jpg", 640)],
            id="src-duplicate",
        ),
        pytest.param(
            'data-src="photo.jpg" data-srcset="photo.jpg 640w"',
            [("photo.jpg", 640)],
            id="lazy-src-duplicate",
        ),
        pytest.param(
            'srcset="photo.jpg 640w"',
            [("photo.jpg", 640)],
            id="srcset-only",
        ),
        pytest.param(
            'src="small.jpg" srcset="photo.jpg 640w"',
            [("small.jpg", None), ("photo.jpg", 640)],
            id="distinct-urls",
        ),
        pytest.param(
            'srcset="photo.jpg 640w, photo.jpg 1280w"',
            [("photo.jpg", 640)],
            id="first-width-kept",
        ),
        pytest.param(
            'src="photo.jpg" srcset="photo.jpg 640w, photo.jpg 1280w"',
            [("photo.jpg", 640)],
            id="first-width-fills-duplicate",
        ),
        pytest.param(
            'src="photo.jpg" srcset="photo.jpg"',
            [("photo.jpg", None)],
            id="missing-width",
        ),
        pytest.param(
            'srcset="photo.jpg invalidw"',
            [("photo.jpg", None)],
            id="invalid-width",
        ),
        pytest.param(
            'src="photo.jpg" srcset="photo.jpg invalidw"',
            [("photo.jpg", None)],
            id="duplicate-invalid-width",
        ),
        pytest.param(
            'src="photo.jpg" srcset="photo.jpg 2x"',
            [("photo.jpg", None)],
            id="density-descriptor",
        ),
        pytest.param(
            'src="photo.jpg" width="42" srcset="photo.jpg 640w"',
            [("photo.jpg", 640)],
            id="descriptor-not-rendered-width",
        ),
        pytest.param(
            'srcset="photo.jpg, photo.jpg 640w"',
            [("photo.jpg", 640)],
            id="widthless-srcset-duplicate",
        ),
        pytest.param(
            'srcset="photo.jpg invalidw, photo.jpg 640w"',
            [("photo.jpg", None)],
            id="invalid-first-width-kept",
        ),
        pytest.param(
            'srcset="photo.jpg 0w, photo.jpg 640w"',
            [("photo.jpg", 0)],
            id="zero-first-width-kept",
        ),
    ],
)
def test_srcset_width_survives_public_scrap(attributes, expected):
    html = f'<html><body><img {attributes} alt="Photo"></body></html>'

    result = LXMLWebScrapingStrategy().scrap("https://example.test/", html)

    assert result.success
    assert [(item.src, item.width) for item in result.media.images] == expected
    serialized = result.model_dump()["media"]["images"]
    assert [(item["src"], item["width"]) for item in serialized] == expected


def test_legacy_strategy_alias_preserves_srcset_width():
    assert WebScrapingStrategy is LXMLWebScrapingStrategy

    result = WebScrapingStrategy().scrap(
        "https://example.test/",
        '<html><body><img srcset="photo.jpg 640w" alt="Photo"></body></html>',
    )

    assert [(item.src, item.width) for item in result.media.images] == [
        ("photo.jpg", 640)
    ]
