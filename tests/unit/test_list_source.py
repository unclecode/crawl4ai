"""Sibling sources on fields inside JSON extraction lists."""

import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonXPathExtractionStrategy,
)


@pytest.fixture(params=["extract", "run"])
def entrypoint(request):
    return request.param


@pytest.fixture(
    params=[
        JsonCssExtractionStrategy,
        JsonLxmlExtractionStrategy,
        JsonXPathExtractionStrategy,
    ],
    ids=["css", "lxml", "xpath"],
)
def extract_items(request, entrypoint):
    def extract_items(html, fields):
        is_xpath = request.param is JsonXPathExtractionStrategy
        schema = {
            "baseSelector": "//section" if is_xpath else "section",
            "fields": [
                {
                    "name": "items",
                    "type": "list",
                    "selector": ".//div[@class='item']" if is_xpath else "div.item",
                    "fields": fields,
                }
            ],
        }
        strategy = request.param(schema)
        url = "https://example.test/items"
        if entrypoint == "run":
            return strategy.run(url, [html])
        return strategy.extract(url, html)

    return extract_items


def test_list_field_reads_sibling_without_changing_other_fields(extract_items):
    html = """
    <section>
      <div class="item">Alpha</div><div class="details">42</div>
      <div class="item">Beta</div><div class="details">7</div>
    </section>
    """
    fields = [
        {"name": "score", "type": "text", "source": "+ div.details"},
        {"name": "name", "type": "text"},
    ]

    assert extract_items(html, fields) == [
        {"items": [{"score": "42", "name": "Alpha"}, {"score": "7", "name": "Beta"}]}
    ]


def test_list_field_source_supports_selectors_and_value_processing(extract_items):
    html = """
    <section>
      <div class="item"><span>Alpha</span></div>
      <div class="details"><span>42 points</span><a href="/items/42">Details</a></div>
      <div class="item"><span>Beta</span></div>
      <div class="details"><span>7 points</span><a href="/items/7">Details</a></div>
    </section>
    """
    fields = [
        {
            "name": "score",
            "type": "text",
            "source": "+ div.details",
            "selector": "span",
            "transform": "uppercase",
        },
        {
            "name": "href",
            "type": "attribute",
            "source": "+ div.details",
            "selector": "a",
            "attribute": "href",
        },
        {
            "name": "points",
            "type": "regex",
            "source": "+ div.details",
            "selector": "span",
            "pattern": r"(\d+) points",
        },
        {
            "name": "id",
            "type": ["attribute", "regex"],
            "source": "+ div.details",
            "selector": "a",
            "attribute": "href",
            "pattern": r"/items/(\d+)",
        },
    ]

    assert extract_items(html, fields) == [
        {
            "items": [
                {"score": "42 POINTS", "href": "/items/42", "points": "42", "id": "42"},
                {"score": "7 POINTS", "href": "/items/7", "points": "7", "id": "7"},
            ]
        }
    ]


@pytest.mark.parametrize("default", ["unavailable", "", 0, False])
def test_list_field_missing_source_uses_default_or_omits_field(extract_items, default):
    html = '<section><div class="item">Alpha</div></section>'
    fields = [
        {
            "name": "score",
            "type": "text",
            "source": "+ div.details",
            "default": default,
        },
        {"name": "optional", "type": "text", "source": "+ div.details"},
        {"name": "name", "type": "text"},
    ]

    assert extract_items(html, fields) == [
        {"items": [{"score": default, "name": "Alpha"}]}
    ]


def test_list_fields_without_source_are_unchanged(extract_items):
    html = """
    <section>
      <div class="item" data-id="alpha"><span>Alpha</span></div>
      <div class="item" data-id="beta"><span>Beta</span></div>
    </section>
    """
    fields = [
        {"name": "name", "type": "text", "selector": "span", "transform": "lowercase"},
        {"name": "id", "type": "attribute", "attribute": "data-id"},
    ]

    assert extract_items(html, fields) == [
        {"items": [{"name": "alpha", "id": "alpha"}, {"name": "beta", "id": "beta"}]}
    ]
