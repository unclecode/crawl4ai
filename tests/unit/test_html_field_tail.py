"""HTML fields must serialize the selected subtree, not its following text."""

import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonXPathExtractionStrategy,
)


@pytest.fixture(
    params=[
        JsonCssExtractionStrategy,
        JsonXPathExtractionStrategy,
        JsonLxmlExtractionStrategy,
    ],
    ids=["css", "xpath", "lxml"],
)
def strategy_class(request):
    return request.param


@pytest.fixture(params=["extract", "run"])
def extract_items(request, strategy_class):
    def extract(schema, html):
        strategy = strategy_class(schema)
        if request.param == "run":
            return strategy.run("https://example.com", [html])
        return strategy.extract("https://example.com", html)

    return extract


def selector(strategy_class, tag, *, base=False):
    if strategy_class is JsonXPathExtractionStrategy:
        return ("//" if base else ".//") + tag
    return tag


@pytest.mark.parametrize("base_field", [False, True], ids=["child", "base"])
def test_html_field_excludes_own_tail(strategy_class, extract_items, base_field):
    selected_html = "<section>before<b>bold</b>after<i>italic</i>end</section>"
    html = f"<div>{selected_html}OUTSIDE<aside>sibling</aside></div>"
    field = {"name": "html", "type": "html"}
    schema = {
        "baseSelector": selector(
            strategy_class, "section" if base_field else "div", base=True
        ),
        "fields": [],
    }
    if base_field:
        schema["baseFields"] = [field]
    else:
        field["selector"] = selector(strategy_class, "section")
        schema["fields"] = [field]

    assert extract_items(schema, html) == [{"html": selected_html}]


def test_html_field_retains_descendant_tails(strategy_class, extract_items):
    selected_html = "<section>before<b>bold<i>italic</i>inner</b>after</section>"
    html = f"<div>{selected_html}<aside>sibling</aside></div>"
    schema = {
        "baseSelector": selector(strategy_class, "div", base=True),
        "fields": [
            {
                "name": "html",
                "selector": selector(strategy_class, "section"),
                "type": "html",
            }
        ],
    }

    assert extract_items(schema, html) == [{"html": selected_html}]


def test_text_and_attribute_fields_are_unchanged(strategy_class, extract_items):
    html = '<div><span data-id="123">selected</span>OUTSIDE<aside>sibling</aside></div>'
    schema = {
        "baseSelector": selector(strategy_class, "div", base=True),
        "fields": [
            {
                "name": "text",
                "selector": selector(strategy_class, "span"),
                "type": "text",
            },
            {
                "name": "id",
                "selector": selector(strategy_class, "span"),
                "type": "attribute",
                "attribute": "data-id",
            },
        ],
    }

    assert extract_items(schema, html) == [{"text": "selected", "id": "123"}]


def test_html_field_keeps_existing_serialization_mode(strategy_class, extract_items):
    html = '<div><section>before<br>after<img src="image.png">end</section></div>'
    schema = {
        "baseSelector": selector(strategy_class, "div", base=True),
        "fields": [
            {
                "name": "html",
                "selector": selector(strategy_class, "section"),
                "type": "html",
            }
        ],
    }
    expected = (
        '<section>before<br>after<img src="image.png">end</section>'
        if strategy_class is JsonLxmlExtractionStrategy
        else '<section>before<br/>after<img src="image.png"/>end</section>'
    )

    assert extract_items(schema, html) == [{"html": expected}]
