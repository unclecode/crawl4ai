"""Sibling source class filters must match complete HTML class tokens."""

import pytest

from crawl4ai import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonXPathExtractionStrategy,
)


@pytest.mark.parametrize(
    "strategy_class",
    [
        JsonCssExtractionStrategy,
        JsonLxmlExtractionStrategy,
        JsonXPathExtractionStrategy,
    ],
)
@pytest.mark.parametrize("entry_point", ["extract", "run"])
@pytest.mark.parametrize(
    "source,siblings,expected",
    [
        pytest.param(
            "+ div.details",
            '<div class="details-preview" data-price="99"></div>'
            '<div class="details" data-price="10"></div>',
            "10",
            id="prefix-is-not-class",
        ),
        pytest.param(
            "+ div.details",
            '<div class="old-details" data-price="99"></div>'
            '<div class="details" data-price="10"></div>',
            "10",
            id="suffix-is-not-class",
        ),
        pytest.param(
            "+ div.details",
            '<div class="old-details-preview" data-price="99"></div>'
            '<div class="details" data-price="10"></div>',
            "10",
            id="substring-is-not-class",
        ),
        pytest.param(
            "+ .details",
            '<aside class="details-preview" data-price="99"></aside>'
            '<aside class="details" data-price="10"></aside>',
            "10",
            id="class-only-source",
        ),
        pytest.param(
            "+ div.details.active",
            '<div class="details-preview inactive" data-price="99"></div>'
            '<div class="details active" data-price="10"></div>',
            "10",
            id="compound-class-false-match",
        ),
        pytest.param(
            "+ div.details",
            '<div class="details-preview" data-price="99"></div>',
            "N/A",
            id="only-partial-class-returns-default",
        ),
        pytest.param(
            "+ div.details.active",
            '<div class="primary active details" data-price="10"></div>',
            "10",
            id="exact-compound-classes",
        ),
        pytest.param(
            "+ div.details.active",
            '<div class="primary\tactive\n details  " data-price="10"></div>',
            "10",
            id="class-whitespace",
        ),
        pytest.param(
            "+ div.details",
            '<div data-price="99"></div>' '<div class="details" data-price="10"></div>',
            "10",
            id="skip-classless-sibling",
        ),
        pytest.param(
            "+ div.details",
            '<div data-price="99"></div>',
            "N/A",
            id="classless-returns-default",
        ),
        pytest.param(
            "+ div",
            '<div data-price="10"></div>',
            "10",
            id="tag-only-source",
        ),
        pytest.param(
            "+ div.details",
            '<aside class="details" data-price="99"></aside>',
            "N/A",
            id="wrong-tag-returns-default",
        ),
        pytest.param(
            "+ div.details",
            '<aside data-price="99"></aside>'
            '<div class="details" data-price="10"></div>'
            '<div class="details" data-price="20"></div>',
            "10",
            id="first-matching-following-sibling",
        ),
    ],
)
def test_source_matches_class_tokens(
    strategy_class, entry_point, source, siblings, expected
):
    schema = {
        "baseSelector": (
            "//article" if strategy_class is JsonXPathExtractionStrategy else "article"
        ),
        "fields": [
            {
                "name": "price",
                "source": source,
                "type": "attribute",
                "attribute": "data-price",
                "default": "N/A",
            }
        ],
    }
    html = '<div><article class="item">Product</article>' + siblings + "</div>"
    strategy = strategy_class(schema)
    content = [html] if entry_point == "run" else html

    assert getattr(strategy, entry_point)("", content) == [{"price": expected}]
