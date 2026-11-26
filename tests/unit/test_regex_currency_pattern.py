"""Tests for the built-in Currency pattern of RegexExtractionStrategy (grouped amounts)."""

import pytest

from crawl4ai.extraction_strategy import RegexExtractionStrategy


def _currency(text):
    strategy = RegexExtractionStrategy(
        pattern=RegexExtractionStrategy.Currency, input_format="text"
    )
    return [m["value"] for m in strategy.extract("https://example.com", text)]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$1,234.56", ["$1,234.56"]),
        ("$1,234", ["$1,234"]),
        ("$12,345,678.90", ["$12,345,678.90"]),
        ("$1,000,000,000", ["$1,000,000,000"]),
        ("€2.499,00", ["€2.499,00"]),
        ("£1.000.000,50", ["£1.000.000,50"]),
        ("USD 1,000", ["USD 1,000"]),
        ("EUR 2.499,00", ["EUR 2.499,00"]),
        ("RM 1,234.50", ["RM 1,234.50"]),
        ("Total: $1,234.56.", ["$1,234.56"]),
        ("cost $1,234, then $2,345.", ["$1,234", "$2,345"]),
        ("Price: $1,234.56, sale €2.499,00", ["$1,234.56", "€2.499,00"]),
    ],
)
def test_grouped_amounts_match_whole(text, expected):
    assert _currency(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$5", ["$5"]),
        ("$5.99", ["$5.99"]),
        ("$0.99", ["$0.99"]),
        ("$1999", ["$1999"]),
        ("€12.50", ["€12.50"]),
        ("$5,99", ["$5,99"]),
        ("RM5", ["RM5"]),
        ("USD 100", ["USD 100"]),
        ("$ 1999.00", ["$ 1999.00"]),
    ],
)
def test_ungrouped_amounts_unchanged(text, expected):
    assert _currency(text) == expected


@pytest.mark.parametrize(
    "text",
    ["12,345.67", "1 234,50 €", "price $", "USD", "$abc", "$,5", "$.99"],
)
def test_text_without_a_leading_symbol_and_amount_does_not_match(text):
    assert _currency(text) == []
