"""XPath text-node selectors must retain their extracted values."""

import pytest

from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy


@pytest.mark.parametrize("selector", [".//h1/text()", ".//h1"])
@pytest.mark.parametrize("method", ["extract", "run"])
def test_xpath_text_field(selector, method):
    schema = {
        "baseSelector": "//div[@class='product']",
        "fields": [{"name": "title", "selector": selector, "type": "text"}],
    }
    strategy = JsonXPathExtractionStrategy(schema)
    html = '<div class="product"><h1>Widget</h1></div>'
    result = getattr(strategy, method)("", [html] if method == "run" else html)
    assert result == [{"title": "Widget"}]


@pytest.mark.parametrize(
    "selector, expected",
    [
        (".//h1/text()", "First"),
        (".//h1", "First bold last"),
        (".//b/following-sibling::text()[1]", "last"),
        (".//h1/@data-title", "Attribute"),
        (".//h2/text()", "missing"),
        (".//span/text()", ""),
    ],
)
def test_xpath_text_result_types(selector, expected):
    schema = {
        "baseSelector": "//div",
        "fields": [
            {
                "name": "value",
                "selector": selector,
                "type": "text",
                "default": "missing",
            }
        ],
    }
    result = JsonXPathExtractionStrategy(schema).extract(
        "",
        '<div><h1 data-title=" Attribute "> First <b>bold</b> last </h1>'
        "<span>   </span></div>",
    )
    assert result == [{"value": expected}]


def test_xpath_text_base_field():
    schema = {
        "baseSelector": "//div",
        "baseFields": [{"name": "title", "selector": ".//h1/text()", "type": "text"}],
        "fields": [],
    }
    assert JsonXPathExtractionStrategy(schema).extract(
        "", "<div><h1>Widget</h1></div>"
    ) == [{"title": "Widget"}]


def test_xpath_text_list_keeps_each_node():
    schema = {
        "baseSelector": "//div",
        "fields": [
            {
                "name": "names",
                "selector": ".//span/text()",
                "type": "list",
                "fields": [{"name": "name", "type": "text"}],
            }
        ],
    }
    assert JsonXPathExtractionStrategy(schema).extract(
        "", "<div><span> First </span><span>Second</span></div>"
    ) == [{"names": [{"name": "First"}, {"name": "Second"}]}]


@pytest.mark.parametrize("field_type", ["regex", ["text", "regex"]])
def test_xpath_text_regex_pipeline(field_type):
    schema = {
        "baseSelector": "//div",
        "fields": [
            {
                "name": "value",
                "selector": ".//span/text()",
                "type": field_type,
                "pattern": r"Price: (\d+)",
                "transform": "uppercase",
            }
        ],
    }
    assert JsonXPathExtractionStrategy(schema).extract(
        "", "<div><span> Price: 42 </span></div>"
    ) == [{"value": "42"}]
