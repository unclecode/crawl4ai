"""Nested JSON extraction uses explicit defaults when no node matches."""

import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonXPathExtractionStrategy,
)

HTML = '<main><article><div class="present"><span>value</span></div></article></main>'


@pytest.fixture(
    params=[
        JsonCssExtractionStrategy,
        JsonLxmlExtractionStrategy,
        JsonXPathExtractionStrategy,
    ],
    ids=["css", "lxml", "xpath"],
)
def extraction_strategy(request):
    return request.param


def _extract(strategy_class, selector, default_marker=...):
    is_xpath = strategy_class is JsonXPathExtractionStrategy
    schema = {
        "baseSelector": "//article" if is_xpath else "article",
        "fields": [
            {
                "name": "details",
                "selector": selector,
                "type": "nested",
                "fields": [{"name": "value", "type": "text"}],
                **({} if default_marker is ... else {"default": default_marker}),
            }
        ],
    }
    return strategy_class(schema).extract("https://example.test", HTML)


@pytest.mark.parametrize("default", [{"status": "missing"}, 0, False, ""])
def test_nested_field_uses_explicit_default_when_selector_matches_nothing(
    extraction_strategy, default
):
    selector = (
        ".missing"
        if extraction_strategy is not JsonXPathExtractionStrategy
        else ".//div[@class='missing']"
    )

    result = _extract(extraction_strategy, selector, default)

    assert result == [{"details": default}]
    assert type(result[0]["details"]) is type(default)


def test_nested_field_without_default_keeps_empty_object(extraction_strategy):
    selector = (
        ".missing"
        if extraction_strategy is not JsonXPathExtractionStrategy
        else ".//div[@class='missing']"
    )

    assert _extract(extraction_strategy, selector) == [{"details": {}}]


def test_nested_field_uses_extracted_value_when_selector_matches(extraction_strategy):
    selector = (
        ".present"
        if extraction_strategy is not JsonXPathExtractionStrategy
        else ".//div[@class='present']"
    )

    assert _extract(extraction_strategy, selector, {"status": "missing"}) == [
        {"details": {"value": "value"}}
    ]
