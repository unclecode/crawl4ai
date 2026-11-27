import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
)

CASES = (
    pytest.param(
        "article.card",
        "span.price",
        '<article class="card"><span class="price-label">Price</span></article>',
        "unavailable",
        id="missing-class-token",
    ),
    pytest.param(
        "article.card",
        'a[data-role="buy"]',
        '<article class="card"><a data-role="compare">Compare</a></article>',
        "unavailable",
        id="missing-attribute-constraint",
    ),
    pytest.param(
        "article.card",
        "section.prices .value",
        (
            '<article class="card"><section class="discount">'
            '<span class="value">€2 off</span></section></article>'
        ),
        "unavailable",
        id="missing-ancestor-constraint",
    ),
    pytest.param(
        "article.card",
        "table tr td:nth-child(2) span.current",
        (
            '<article class="card"><table><tr>'
            '<td><span class="current">€3</span></td>'
            '<td><span class="retired">€4</span></td>'
            "</tr></table></article>"
        ),
        "unavailable",
        id="missing-position-and-class",
    ),
    pytest.param(
        "article.card",
        "table tr td:nth-child(2) span.current",
        (
            '<article class="card"><table><tr>'
            '<td><span class="current">€3</span></td>'
            '<td><span class="current">€4</span></td>'
            "</tr></table></article>"
        ),
        "€4",
        id="matching-position-and-class",
    ),
    pytest.param(
        "article.card",
        "span.price",
        (
            '<article class="card"><span class="price-label">Price</span>'
            '<span class="price">€21</span></article>'
        ),
        "€21",
        id="matching-class-token",
    ),
    pytest.param(
        "article.card",
        "section > span.price",
        (
            '<article class="card"><section><p><span class="price">€3</span></p>'
            '<span class="price">€21</span></section></article>'
        ),
        "€21",
        id="child-combinator",
    ),
    pytest.param(
        "article.card",
        "span.price",
        '<article class="card"><p>Contact us</p></article>',
        "unavailable",
        id="no-lookalike",
    ),
    pytest.param(
        "article.card",
        "input:checked + label",
        (
            '<article class="card"><input type="checkbox" checked>'
            "<label>available</label></article>"
        ),
        "available",
        id="checked-input",
    ),
    pytest.param(
        "article.card",
        "input:checked + label",
        (
            '<article class="card"><input type="checkbox"><label>unknown</label>'
            '<input type="checkbox" checked><label>available</label></article>'
        ),
        "available",
        id="checked-after-unchecked-input",
    ),
    pytest.param(
        "article.card",
        "input:enabled + label",
        (
            '<article class="card"><input type="text" disabled><label>archived</label>'
            '<input type="text"><label>available</label></article>'
        ),
        "available",
        id="enabled-input",
    ),
    pytest.param(
        "article.card",
        "input:disabled + label",
        (
            '<article class="card"><input type="text"><label>available</label>'
            '<input type="text" disabled><label>archived</label></article>'
        ),
        "archived",
        id="disabled-input",
    ),
    pytest.param(
        "article.card",
        "a:link",
        (
            '<article class="card"><a>Coming soon</a>'
            '<a href="/products/new">New products</a></article>'
        ),
        "New products",
        id="link-requires-destination",
    ),
    pytest.param(
        "ARTICLE.card",
        "SPAN.price",
        '<ARTICLE class="card"><SPAN class="price">€21</SPAN></ARTICLE>',
        "€21",
        id="html-tag-case-insensitive",
    ),
)


@pytest.mark.parametrize(
    "strategy, options",
    [
        pytest.param(JsonLxmlExtractionStrategy, {}, id="lxml"),
        pytest.param(
            JsonLxmlExtractionStrategy,
            {"optimize_common_patterns": False, "use_caching": False},
            id="lxml-no-optimizations",
        ),
        pytest.param(JsonCssExtractionStrategy, {}, id="css"),
    ],
)
@pytest.mark.parametrize("base_selector, field_selector, html, expected", CASES)
def test_schema_matches_the_complete_css_selector(
    strategy, options, base_selector, field_selector, html, expected
):
    schema = {
        "baseSelector": base_selector,
        "fields": [
            {
                "name": "price",
                "selector": field_selector,
                "type": "text",
                "default": "unavailable",
            }
        ],
    }

    result = strategy(schema, **options).run("https://example.test/products", [html])

    assert result == [{"price": expected}]


def test_invalid_lxml_field_selector_still_uses_default():
    schema = {
        "baseSelector": "article",
        "fields": [
            {
                "name": "price",
                "selector": "span[",
                "type": "text",
                "default": "unavailable",
            },
        ],
    }
    strategy = JsonLxmlExtractionStrategy(schema)

    result = strategy.extract("https://example.test/products", "<article></article>")

    assert result == [{"price": "unavailable"}]
