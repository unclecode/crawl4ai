"""
A "nested" field whose selector matches an element without child elements
must still be extracted by the lxml-based strategies.

lxml elements are falsy when they have no children, so a truthiness check
on the matched element returned {} for JsonLxmlExtractionStrategy and
JsonXPathExtractionStrategy while JsonCssExtractionStrategy got the values.
"""

import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonXPathExtractionStrategy,
)

HTML = """
<div class="product"><h2>Pen</h2><span class="price" data-currency="USD">10</span></div>
<div class="product"><h2>Ink</h2></div>
"""

PRICE_FIELDS = [
    {"name": "amount", "type": "text"},
    {"name": "currency", "type": "attribute", "attribute": "data-currency"},
]

CSS_SCHEMA = {
    "baseSelector": "div.product",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {
            "name": "price",
            "selector": "span.price",
            "type": "nested",
            "fields": PRICE_FIELDS,
        },
    ],
}

XPATH_SCHEMA = {
    "baseSelector": "//div[@class='product']",
    "fields": [
        {"name": "title", "selector": ".//h2", "type": "text"},
        {
            "name": "price",
            "selector": ".//span[@class='price']",
            "type": "nested",
            "fields": PRICE_FIELDS,
        },
    ],
}

EXPECTED = [
    {"title": "Pen", "price": {"amount": "10", "currency": "USD"}},
    {"title": "Ink", "price": {}},
]


@pytest.mark.parametrize(
    "strategy",
    [
        JsonCssExtractionStrategy(CSS_SCHEMA),
        JsonLxmlExtractionStrategy(CSS_SCHEMA),
        JsonXPathExtractionStrategy(XPATH_SCHEMA),
    ],
    ids=["css", "lxml", "xpath"],
)
def test_nested_field_on_element_without_children(strategy):
    assert strategy.extract(None, HTML) == EXPECTED
