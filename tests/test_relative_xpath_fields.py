"""Relative XPath field paths must retain their context and valid syntax."""

import pytest
from lxml import html as lhtml

from crawl4ai import JsonXPathExtractionStrategy

HTML = """
<section>
  <h2><span data-code="section">Section heading</span></h2>
  <article><h2><span data-code="widget">Widget</span></h2></article>
  <article><h2><span data-code="gadget">Gadget</span></h2></article>
</section>
"""
PRODUCTS = [
    {"title": "Widget", "code": "widget"},
    {"title": "Gadget", "code": "gadget"},
]


@pytest.mark.parametrize("method", ["extract", "run"])
@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        pytest.param("h2/span", PRODUCTS, id="relative-path"),
        pytest.param("./h2/span", PRODUCTS, id="explicit-current-path"),
        pytest.param("/h2/span", PRODUCTS, id="scoped-leading-slash"),
        pytest.param("//h2/span", PRODUCTS, id="scoped-leading-double-slash"),
        pytest.param("child::h2/span", PRODUCTS, id="relative-child-axis"),
        pytest.param("h2 > span", PRODUCTS, id="css-child"),
        pytest.param("h2 span", PRODUCTS, id="css-descendant"),
        pytest.param("span", PRODUCTS, id="css-tag"),
        pytest.param(
            "../h2/span",
            [{"title": "Section heading", "code": "section"}] * 2,
            id="parent-path",
        ),
        pytest.param(
            "h2/missing",
            [{"title": "MISSING", "code": "MISSING"}] * 2,
            id="missing-relative-path",
        ),
    ],
)
def test_xpath_field_paths_through_public_extraction(method, selector, expected):
    """Text and attribute fields resolve per item through both public entry points."""
    strategy = JsonXPathExtractionStrategy(
        {
            "baseSelector": "//article",
            "fields": [
                {
                    "name": "title",
                    "selector": selector,
                    "type": "text",
                    "default": "MISSING",
                },
                {
                    "name": "code",
                    "selector": selector,
                    "type": "attribute",
                    "attribute": "data-code",
                    "default": "MISSING",
                },
            ],
        }
    )

    content = [HTML] if method == "run" else HTML
    result = getattr(strategy, method)("https://example.com/", content)

    assert result == expected


@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        ("h2/span/text()", ["Widget"]),
        ("./h2/span/text()", ["Widget"]),
        ("h2/span/@data-code", ["widget"]),
        ("./h2/span/@data-code", ["widget"]),
    ],
)
def test_relative_scalar_xpath_selection(selector, expected):
    """Check selection itself, independently of scalar-node value extraction."""
    strategy = JsonXPathExtractionStrategy({"baseSelector": "//article", "fields": []})
    article = lhtml.fromstring(HTML).xpath("//article")[0]

    assert strategy._get_elements(article, selector) == expected
