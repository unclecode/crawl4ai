"""Tests for issue #1254: JSONCSSSelector fails to handle sibling CSS selectors.

The bug: _resolve_source() only supported '+' (adjacent sibling).
The fix adds '~' (general sibling) support across all extraction strategies.
"""

import pytest
import json
from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonLxmlExtractionStrategy,
    JsonXPathExtractionStrategy,
)


HACKER_NEWS_HTML = """
<html><body>
<table>
    <tr class="athing" id="1">
        <td class="title"><a class="titlelink" href="https://example.com/1">First Story</a></td>
    </tr>
    <tr class="subtext-row">
        <td><span class="age" title="2024-01-01T00:00:00">2 hours ago</span>
            <span class="score">100 points</span></td>
    </tr>
    <tr class="athing" id="2">
        <td class="title"><a class="titlelink" href="https://example.com/2">Second Story</a></td>
    </tr>
    <tr class="subtext-row">
        <td><span class="age" title="2024-01-02T00:00:00">5 hours ago</span>
            <span class="score">50 points</span></td>
    </tr>
</table>
</body></html>
"""

GENERAL_SIBLING_HTML = """
<html><body>
<div class="container">
    <div class="item" id="a">
        <span class="name">Alice</span>
    </div>
    <div class="spacer">---</div>
    <div class="details">
        <span class="info">Alice info here</span>
    </div>
    <div class="item" id="b">
        <span class="name">Bob</span>
    </div>
    <div class="spacer">---</div>
    <div class="details">
        <span class="info">Bob info here</span>
    </div>
</div>
</body></html>
"""


def _extract(strategy_cls, html, schema):
    strategy = strategy_cls(schema)
    return strategy.extract("http://test.com", html)


class TestAdjacentSiblingPlus:
    """Test '+' adjacent sibling combinator (existing behavior)."""

    def test_bs4_adjacent_sibling(self):
        schema = {
            "name": "stories",
            "baseSelector": "tr.athing",
            "fields": [
                {"name": "title", "selector": "a.titlelink", "type": "text"},
                {"name": "age", "selector": "span.age", "type": "attribute",
                 "attribute": "title", "source": "+ tr"},
            ],
        }
        items = _extract(JsonCssExtractionStrategy, HACKER_NEWS_HTML, schema)
        assert len(items) == 2
        assert items[0]["age"] == "2024-01-01T00:00:00"
        assert items[1]["age"] == "2024-01-02T00:00:00"

    def test_lxml_adjacent_sibling(self):
        schema = {
            "name": "stories",
            "baseSelector": "tr.athing",
            "fields": [
                {"name": "title", "selector": "a.titlelink", "type": "text"},
                {"name": "age", "selector": "span.age", "type": "attribute",
                 "attribute": "title", "source": "+ tr"},
            ],
        }
        items = _extract(JsonLxmlExtractionStrategy, HACKER_NEWS_HTML, schema)
        assert len(items) == 2
        assert items[0]["age"] == "2024-01-01T00:00:00"

    def test_plus_with_class_filter(self):
        schema = {
            "name": "items",
            "baseSelector": "tr.athing",
            "fields": [
                {"name": "title", "selector": "a.titlelink", "type": "text"},
                {"name": "age", "selector": "span.age", "type": "attribute",
                 "attribute": "title", "source": "+ tr.subtext-row"},
            ],
        }
        items = _extract(JsonCssExtractionStrategy, HACKER_NEWS_HTML, schema)
        assert len(items) == 2
        assert items[0]["age"] == "2024-01-01T00:00:00"


class TestGeneralSiblingTilde:
    """Test '~' general sibling combinator (new behavior)."""

    def test_bs4_general_sibling(self):
        schema = {
            "name": "items",
            "baseSelector": "div.item",
            "fields": [
                {"name": "name", "selector": "span.name", "type": "text"},
                {"name": "info", "selector": "span.info", "type": "text",
                 "source": "~ div.details"},
            ],
        }
        items = _extract(JsonCssExtractionStrategy, GENERAL_SIBLING_HTML, schema)
        assert len(items) == 2
        assert items[0]["info"] == "Alice info here"

    def test_lxml_general_sibling(self):
        schema = {
            "name": "items",
            "baseSelector": "div.item",
            "fields": [
                {"name": "name", "selector": "span.name", "type": "text"},
                {"name": "info", "selector": "span.info", "type": "text",
                 "source": "~ div.details"},
            ],
        }
        items = _extract(JsonLxmlExtractionStrategy, GENERAL_SIBLING_HTML, schema)
        assert len(items) == 2
        assert items[0]["info"] == "Alice info here"

    def test_xpath_general_sibling(self):
        schema = {
            "name": "items",
            "baseSelector": "//div[contains(@class,'item')]",
            "fields": [
                {"name": "name", "selector": ".//span[contains(@class,'name')]", "type": "text"},
                {"name": "info", "selector": ".//span[contains(@class,'info')]", "type": "text",
                 "source": "~ div.details"},
            ],
        }
        items = _extract(JsonXPathExtractionStrategy, GENERAL_SIBLING_HTML, schema)
        assert len(items) == 2
        assert items[0]["info"] == "Alice info here"

    def test_tilde_no_match_returns_none(self):
        schema = {
            "name": "items",
            "baseSelector": "div.item",
            "fields": [
                {"name": "name", "selector": "span.name", "type": "text"},
                {"name": "missing", "selector": "span.info", "type": "text",
                 "source": "~ div.nonexistent"},
            ],
        }
        items = _extract(JsonCssExtractionStrategy, GENERAL_SIBLING_HTML, schema)
        assert len(items) == 2
        assert items[0].get("missing") in (None, "")


class TestEdgeCases:
    def test_unsupported_combinator_returns_none(self):
        schema = {
            "name": "items",
            "baseSelector": "tr.athing",
            "fields": [
                {"name": "title", "selector": "a.titlelink", "type": "text"},
                {"name": "bad", "selector": "span", "type": "text",
                 "source": "> div"},
            ],
        }
        items = _extract(JsonCssExtractionStrategy, HACKER_NEWS_HTML, schema)
        assert len(items) == 2
        assert items[0].get("bad") in (None, "")

    def test_source_with_whitespace(self):
        schema = {
            "name": "stories",
            "baseSelector": "tr.athing",
            "fields": [
                {"name": "title", "selector": "a.titlelink", "type": "text"},
                {"name": "age", "selector": "span.age", "type": "attribute",
                 "attribute": "title", "source": "  + tr  "},
            ],
        }
        items = _extract(JsonCssExtractionStrategy, HACKER_NEWS_HTML, schema)
        assert len(items) == 2
        assert items[0]["age"] == "2024-01-01T00:00:00"

    def test_no_source_field_works_normally(self):
        schema = {
            "name": "stories",
            "baseSelector": "tr.athing",
            "fields": [
                {"name": "title", "selector": "a.titlelink", "type": "text"},
            ],
        }
        items = _extract(JsonCssExtractionStrategy, HACKER_NEWS_HTML, schema)
        assert len(items) == 2
        assert items[0]["title"] == "First Story"
