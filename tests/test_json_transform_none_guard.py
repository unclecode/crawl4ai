"""Regression tests for applying a field `transform` to a ``None`` value.

A field in a JSON (CSS/XPath) extraction schema may pair a fail-capable
extraction step (a ``type: "regex"`` that does not match, or a
``type: "attribute"`` whose attribute is absent) with an optional
``transform`` (``lowercase`` / ``uppercase`` / ``strip``).

When the type pipeline yields ``None``, ``_apply_transform`` used to be
called unconditionally, doing ``None.lower()`` / ``None.strip()`` and
raising ``AttributeError: 'NoneType' object has no attribute ...``.
The ``transform`` block must be skipped for a ``None`` value so it flows to
the existing ``default`` handling, exactly like the very next line already
assumes it can.
"""

import pytest
from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
)


# ---------------------------------------------------------------------------
# CSS strategy
# ---------------------------------------------------------------------------
class TestCssTransformNoneGuard:
    """JsonCssExtractionStrategy: transform must not crash on a missing value."""

    def test_basefields_regex_miss_with_transform_returns_default(self):
        """A baseField regex that misses + transform must not raise; use default.

        The ``baseFields`` loop in ``extract()`` has no try/except, so the
        crash aborts the whole extraction rather than falling back.
        """
        html = "<div class='row'><span class='code'>abc</span></div>"
        schema = {
            "name": "codes",
            "baseSelector": "div.row",
            "baseFields": [
                {
                    "name": "num",
                    "selector": "span.code",
                    "type": "regex",
                    "pattern": r"(\d+)",
                    "transform": "lowercase",
                    "default": "NA",
                },
            ],
            "fields": [
                {"name": "code", "selector": "span.code", "type": "text"},
            ],
        }
        results = JsonCssExtractionStrategy(schema).extract(None, html)
        assert results == [{"num": "NA", "code": "abc"}]

    def test_list_regex_miss_with_transform_keeps_valid_siblings(self):
        """One non-matching sibling must not drop the entire list."""
        html = """<div class='wrap'>
          <ul>
            <li class='x'>id-123</li>
            <li class='x'>nope</li>
            <li class='x'>id-999</li>
          </ul>
        </div>"""
        schema = {
            "name": "ids",
            "baseSelector": "div.wrap",
            "fields": [
                {
                    "name": "items",
                    "selector": "li.x",
                    "type": "list",
                    "fields": [
                        {
                            "name": "id",
                            "type": "regex",
                            "pattern": r"id-(\d+)",
                            "transform": "lowercase",
                        },
                    ],
                },
            ],
        }
        results = JsonCssExtractionStrategy(schema).extract(None, html)
        assert len(results) == 1
        items = results[0]["items"]
        assert len(items) == 3
        # Valid siblings survive; the missing one is simply empty.
        assert items[0] == {"id": "123"}
        assert items[1] == {}
        assert items[2] == {"id": "999"}

    def test_list_attribute_missing_with_transform_keeps_valid_links(self):
        """An anchor lacking href must not silently lose the valid links."""
        html = """<div class='wrap'>
          <ul>
            <li><a class='lnk' href='http://x'>a</a></li>
            <li><a class='lnk'>b</a></li>
            <li><a class='lnk' href='http://z'>c</a></li>
          </ul>
        </div>"""
        schema = {
            "name": "links",
            "baseSelector": "div.wrap",
            "fields": [
                {
                    "name": "links",
                    "selector": "a.lnk",
                    "type": "list",
                    "fields": [
                        {
                            "name": "href",
                            "type": "attribute",
                            "attribute": "href",
                            "transform": "lowercase",
                        },
                    ],
                },
            ],
        }
        results = JsonCssExtractionStrategy(schema).extract(None, html)
        assert len(results) == 1
        links = results[0]["links"]
        assert links[0] == {"href": "http://x"}
        assert links[1] == {}
        assert links[2] == {"href": "http://z"}

    def test_transform_still_applied_when_value_present(self):
        """The guard must not disable transform for genuine values."""
        html = "<div class='row'><span class='name'>HeLLo</span></div>"
        schema = {
            "name": "names",
            "baseSelector": "div.row",
            "fields": [
                {
                    "name": "name",
                    "selector": "span.name",
                    "type": "text",
                    "transform": "lowercase",
                },
            ],
        }
        results = JsonCssExtractionStrategy(schema).extract(None, html)
        assert results == [{"name": "hello"}]


# ---------------------------------------------------------------------------
# XPath strategy (same shared base-class code path)
# ---------------------------------------------------------------------------
class TestXPathTransformNoneGuard:
    """JsonXPathExtractionStrategy exercises the same _extract_single_field."""

    def test_attribute_missing_with_transform_returns_default(self):
        html = "<div class='row'><a class='lnk'>b</a></div>"
        schema = {
            "name": "links",
            "baseSelector": "//div[@class='row']",
            "fields": [
                {
                    "name": "href",
                    "selector": ".//a[@class='lnk']",
                    "type": "attribute",
                    "attribute": "href",
                    "transform": "lowercase",
                    "default": "no-href",
                },
            ],
        }
        results = JsonXPathExtractionStrategy(schema).extract(None, html)
        assert results == [{"href": "no-href"}]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
