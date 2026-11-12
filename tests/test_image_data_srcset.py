"""Image src values must be individual URLs, never an entire srcset value."""

import pytest

from crawl4ai import LXMLWebScrapingStrategy


@pytest.mark.parametrize(
    ("attributes", "expected"),
    [
        pytest.param(
            'data-srcset="https://cdn.example/a.jpg 400w, https://cdn.example/b.jpg 800w"',
            [("https://cdn.example/a.jpg", 400), ("https://cdn.example/b.jpg", 800)],
            id="absolute-data-srcset",
        ),
        pytest.param(
            'data-srcset="https://cdn.example/a.jpg 400w"',
            [("https://cdn.example/a.jpg", 400)],
            id="single-data-srcset-candidate",
        ),
        pytest.param(
            'data-srcset="a.jpg 400w, b.jpg 800w"',
            [("a.jpg", 400), ("b.jpg", 800)],
            id="relative-data-srcset",
        ),
        pytest.param(
            'src="https://cdn.example/a.jpg"',
            [("https://cdn.example/a.jpg", None)],
            id="ordinary-src",
        ),
        pytest.param(
            'data-src="https://cdn.example/a.jpg"',
            [("https://cdn.example/a.jpg", None)],
            id="ordinary-data-src",
        ),
        pytest.param(
            'src="https://cdn.example/preview.jpg" '
            'srcset="https://cdn.example/a.jpg 400w, https://cdn.example/b.jpg 800w"',
            [
                ("https://cdn.example/preview.jpg", None),
                ("https://cdn.example/a.jpg", 400),
                ("https://cdn.example/b.jpg", 800),
            ],
            id="ordinary-src-and-srcset-order",
        ),
        pytest.param(
            'data-lazy-src="https://cdn.example/a.jpg"',
            [("https://cdn.example/a.jpg", None)],
            id="framework-source",
        ),
    ],
)
def test_public_scrap_returns_individual_image_urls(attributes, expected):
    html = (
        '<html><body><img width="400" height="300" alt="Photo" '
        f"{attributes}></body></html>"
    )

    result = LXMLWebScrapingStrategy().scrap("https://example.test/", html)

    assert result.success
    assert [(item.src, item.width) for item in result.media.images] == expected
    serialized = result.model_dump()["media"]["images"]
    assert [(item["src"], item["width"]) for item in serialized] == expected
