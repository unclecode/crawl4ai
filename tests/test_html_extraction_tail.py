import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonLxmlExtractionStrategy_naive,
    JsonXPathExtractionStrategy,
)


@pytest.mark.parametrize(
    ("strategy_class", "base_selector", "selector"),
    [
        (JsonCssExtractionStrategy, "div.entry", "a"),
        (JsonLxmlExtractionStrategy, "div.entry", "a"),
        (JsonLxmlExtractionStrategy_naive, "div.entry", "a"),
        (JsonXPathExtractionStrategy, "//div[@class='entry']", ".//a"),
    ],
)
@pytest.mark.parametrize("inner_html", ["Read more", "Read <b>this</b> now"])
def test_html_field_excludes_text_outside_selected_element(
    strategy_class, base_selector, selector, inner_html
):
    expected = f'<a href="/detail">{inner_html}</a>'
    source = f'<div class="entry">{expected} unrelated text<span>Other</span></div>'
    schema = {
        "baseSelector": base_selector,
        "fields": [{"name": "link_html", "selector": selector, "type": "html"}],
    }

    result = strategy_class(schema).extract("https://example.test/", source)

    assert result == [{"link_html": expected}]
