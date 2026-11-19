import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonXPathExtractionStrategy,
)


@pytest.mark.parametrize("entrypoint", ["extract", "run"])
@pytest.mark.parametrize(
    "html,field,expected",
    [
        (
            '<a class="star-rating Three">Book</a>',
            {
                "type": ["attribute", "regex"],
                "attribute": "class",
                "pattern": r"star-rating (\w+)",
            },
            "Three",
        ),
        (
            '<a rel="external nofollow">Book</a>',
            {
                "type": ["attribute", "regex"],
                "attribute": "rel",
                "pattern": r"external (\w+)",
            },
            "nofollow",
        ),
        (
            '<a class="One Two">Book</a>',
            {"type": ["attribute", "text"], "attribute": "class"},
            "One Two",
        ),
        (
            '<a class="">Book</a>',
            {"type": ["attribute", "text"], "attribute": "class"},
            "",
        ),
        (
            '<a class="">Book</a>',
            {"type": ["attribute", "regex"], "attribute": "class", "pattern": r"(.*)"},
            "",
        ),
        (
            '<a class="One Two">Book</a>',
            {
                "type": ["attribute", "regex"],
                "attribute": "class",
                "pattern": r"(Absent)",
            },
            "missing",
        ),
        (
            '<a class="One Two">Book</a>',
            {"type": "attribute", "attribute": "class"},
            ["One", "Two"],
        ),
        ('<a class="">Book</a>', {"type": "attribute", "attribute": "class"}, []),
        (
            '<a href="/item/123">Book</a>',
            {
                "type": ["attribute", "regex"],
                "attribute": "href",
                "pattern": r"/item/(\d+)",
            },
            "123",
        ),
        ("<a>Book Three</a>", {"type": "regex", "pattern": r"Book (\w+)"}, "Three"),
        (
            "<a>Book</a>",
            {"type": ["attribute", "regex"], "attribute": "class", "pattern": r"(.*)"},
            "missing",
        ),
        (
            '<a class="One\tTwo\nThree">Book</a>',
            {"type": ["attribute", "text"], "attribute": "class"},
            "One Two Three",
        ),
    ],
)
def test_token_attributes_in_public_pipeline(entrypoint, html, field, expected):
    strategy = JsonCssExtractionStrategy(
        {
            "name": "tokens",
            "baseSelector": "div",
            "fields": [
                {"name": "value", "selector": "a", "default": "missing", **field}
            ],
        }
    )
    document = f"<div>{html}</div>"
    argument = [document] if entrypoint == "run" else document
    assert getattr(strategy, entrypoint)("https://example.test/", argument) == [
        {"value": expected}
    ]


@pytest.mark.parametrize("value", [["token", 3], [None], [{"token": "value"}]])
def test_non_string_lists_are_not_coerced(value):
    strategy = JsonCssExtractionStrategy(
        {"name": "tokens", "baseSelector": "div", "fields": []}
    )
    with pytest.raises(AttributeError):
        strategy._get_element_text(value)


@pytest.mark.parametrize(
    "strategy_class", [JsonLxmlExtractionStrategy, JsonXPathExtractionStrategy]
)
@pytest.mark.parametrize("entrypoint", ["extract", "run"])
def test_other_strategies_keep_string_attributes(strategy_class, entrypoint):
    is_xpath = strategy_class is JsonXPathExtractionStrategy
    selector = ".//a" if is_xpath else "a"
    strategy = strategy_class(
        {
            "name": "tokens",
            "baseSelector": "//div" if is_xpath else "div",
            "fields": [
                {
                    "name": "plain",
                    "selector": selector,
                    "type": "attribute",
                    "attribute": "class",
                },
                {
                    "name": "rating",
                    "selector": selector,
                    "type": ["attribute", "regex"],
                    "attribute": "class",
                    "pattern": r"star-rating (\w+)",
                },
            ],
        }
    )
    html = '<div><a class="star-rating Three">Book</a></div>'
    argument = [html] if entrypoint == "run" else html
    assert getattr(strategy, entrypoint)("https://example.test/", argument) == [
        {"plain": "star-rating Three", "rating": "Three"}
    ]
