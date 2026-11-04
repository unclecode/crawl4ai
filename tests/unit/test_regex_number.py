"""Regression coverage for the built-in numeric extraction pattern."""

import pytest

from crawl4ai.extraction_strategy import RegexExtractionStrategy


@pytest.mark.parametrize("value", ["1234", "1234567", "1234.56"])
def test_number_extracts_complete_ungrouped_values(value):
    strategy = RegexExtractionStrategy(
        pattern=RegexExtractionStrategy.Number, input_format="text"
    )
    url = "https://example.test/numbers"
    content = f"Total: {value} units"

    assert strategy.extract(url, content) == [
        {
            "url": url,
            "label": "number",
            "value": value,
            "span": [7, 7 + len(value)],
        }
    ]


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "7",
        "42",
        "999",
        "12.34",
        "1,234",
        "1,234,567",
        "1.234",
        "1.234.567",
        "1 234",
        "1 234 567",
        "1,234.56",
    ],
)
def test_number_preserves_short_and_grouped_values(value):
    strategy = RegexExtractionStrategy(
        pattern=RegexExtractionStrategy.Number, input_format="text"
    )
    url = "https://example.test/numbers"
    content = f"Total: {value} units"

    assert strategy.extract(url, content) == [
        {
            "url": url,
            "label": "number",
            "value": value,
            "span": [7, 7 + len(value)],
        }
    ]


def test_custom_number_pattern_overrides_builtin():
    strategy = RegexExtractionStrategy(
        pattern=RegexExtractionStrategy.Number,
        custom={"number": r"\bID-\d+\b"},
        input_format="text",
    )
    url = "https://example.test/numbers"

    assert strategy.extract(url, "1234 ID-5678") == [
        {
            "url": url,
            "label": "number",
            "value": "ID-5678",
            "span": [5, 12],
        }
    ]


def test_number_run_preserves_complete_values_across_sections():
    strategy = RegexExtractionStrategy(
        pattern=RegexExtractionStrategy.Number, input_format="text"
    )
    url = "https://example.test/numbers"

    results = strategy.run(url, ["1234", "Total: 1234.56 units"])

    assert sorted(results, key=lambda item: item["value"]) == [
        {"url": url, "label": "number", "value": "1234", "span": [0, 4]},
        {"url": url, "label": "number", "value": "1234.56", "span": [7, 14]},
    ]


@pytest.mark.parametrize("content", ["No numbers here.", "item1234", "1234items"])
def test_number_returns_no_matches_without_standalone_numbers(content):
    strategy = RegexExtractionStrategy(
        pattern=RegexExtractionStrategy.Number, input_format="text"
    )

    assert strategy.extract("https://example.test/numbers", content) == []
