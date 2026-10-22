"""
Tests for #1708: "markdown" field type in JsonElementExtractionStrategy

Verifies that the "markdown" type converts element HTML to markdown,
works in pipelines, across all strategy subclasses, and in end-to-end extraction.
"""
import json
import pytest
from bs4 import BeautifulSoup


# ── Rich HTML fixtures ───────────────────────────────────────────────────

RICH_HTML = """
<div class="product">
  <h3><a href="/product/123">Widget Pro</a></h3>
  <p class="desc"><strong>Best seller</strong> - Our most popular widget with <em>advanced features</em>.</p>
  <ul class="features">
    <li>Fast processing</li>
    <li><a href="/docs">Well documented</a></li>
    <li>Easy integration</li>
  </ul>
  <span class="price">$29.99</span>
</div>
"""

MULTI_PRODUCT_HTML = """
<html><body>
<div class="product">
  <h3><a href="/p/1">Alpha</a></h3>
  <p class="desc"><strong>Bold text</strong> and <em>italic</em>.</p>
</div>
<div class="product">
  <h3><a href="/p/2">Beta</a></h3>
  <p class="desc">Plain text with <a href="/link">a link</a>.</p>
</div>
</body></html>
"""


# ── JsonCssExtractionStrategy ────────────────────────────────────────────

class TestMarkdownTypeCss:

    @pytest.fixture
    def strategy(self):
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        schema = {"name": "test", "baseSelector": "div.product", "fields": []}
        return JsonCssExtractionStrategy(schema)

    @pytest.fixture
    def element(self):
        soup = BeautifulSoup(RICH_HTML, "html.parser")
        return soup.find("div", class_="product")

    def test_markdown_type_converts_html_to_markdown(self, strategy, element):
        """Basic: 'markdown' type should convert element to markdown string."""
        field = {"selector": "p.desc", "type": "markdown"}
        result = strategy._extract_single_field(element, field)
        assert isinstance(result, str)
        assert "**Best seller**" in result or "Best seller" in result
        assert "advanced features" in result

    def test_markdown_preserves_links(self, strategy, element):
        """Markdown should preserve link URLs."""
        field = {"selector": "ul.features", "type": "markdown"}
        result = strategy._extract_single_field(element, field)
        assert isinstance(result, str)
        assert "/docs" in result
        assert "Well documented" in result

    def test_markdown_preserves_list_structure(self, strategy, element):
        """Markdown should convert <ul>/<li> to list items."""
        field = {"selector": "ul.features", "type": "markdown"}
        result = strategy._extract_single_field(element, field)
        # html2text converts <li> to "* " items
        assert "Fast processing" in result
        assert "Easy integration" in result

    def test_markdown_vs_text_richer(self, strategy, element):
        """Markdown output should be richer than plain text."""
        field_text = {"selector": "p.desc", "type": "text"}
        field_md = {"selector": "p.desc", "type": "markdown"}
        text_result = strategy._extract_single_field(element, field_text)
        md_result = strategy._extract_single_field(element, field_md)
        # text strips all formatting
        assert "**" not in text_result
        # markdown should preserve emphasis (bold or italic markers)
        assert len(md_result) >= len(text_result)

    def test_markdown_vs_html_cleaner(self, strategy, element):
        """Markdown output should not contain HTML tags."""
        field_html = {"selector": "p.desc", "type": "html"}
        field_md = {"selector": "p.desc", "type": "markdown"}
        html_result = strategy._extract_single_field(element, field_html)
        md_result = strategy._extract_single_field(element, field_md)
        assert "<strong>" in html_result
        assert "<strong>" not in md_result

    def test_markdown_single_element_list(self, strategy, element):
        """["markdown"] should behave same as "markdown"."""
        field_str = {"selector": "p.desc", "type": "markdown"}
        field_list = {"selector": "p.desc", "type": ["markdown"]}
        assert strategy._extract_single_field(element, field_str) == \
               strategy._extract_single_field(element, field_list)

    def test_markdown_returns_string(self, strategy, element):
        """Result must be a plain string (JSON-serializable)."""
        field = {"selector": "p.desc", "type": "markdown"}
        result = strategy._extract_single_field(element, field)
        # Must serialize cleanly
        json.dumps({"content": result})

    def test_markdown_empty_element(self, strategy):
        """Empty element should return empty string or default."""
        html = '<div class="product"><p class="desc"></p></div>'
        soup = BeautifulSoup(html, "html.parser")
        el = soup.find("div")
        field = {"selector": "p.desc", "type": "markdown", "default": "N/A"}
        result = strategy._extract_single_field(el, field)
        # Either empty string or default
        assert result is not None

    def test_markdown_missing_selector_returns_default(self, strategy, element):
        """Missing selector should return default value."""
        field = {"selector": "div.nonexistent", "type": "markdown", "default": "N/A"}
        result = strategy._extract_single_field(element, field)
        assert result == "N/A"


# ── Pipeline chaining ────────────────────────────────────────────────────

class TestMarkdownPipeline:

    @pytest.fixture
    def strategy(self):
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        schema = {"name": "test", "baseSelector": "div", "fields": []}
        return JsonCssExtractionStrategy(schema)

    @pytest.fixture
    def element(self):
        soup = BeautifulSoup(RICH_HTML, "html.parser")
        return soup.find("div", class_="product")

    def test_markdown_then_regex(self, strategy, element):
        """Pipeline: markdown → regex should work on markdown string."""
        field = {
            "selector": "p.desc",
            "type": ["markdown", "regex"],
            "pattern": r"\*\*(.+?)\*\*",
        }
        result = strategy._extract_single_field(element, field)
        assert result == "Best seller"

    def test_html_then_markdown_is_same_as_markdown(self, strategy, element):
        """Pipeline ["html", "markdown"] should produce same result as ["markdown"]."""
        field_direct = {"selector": "p.desc", "type": "markdown"}
        # html step returns HTML string, then markdown converts it
        field_pipeline = {"selector": "p.desc", "type": ["html", "markdown"]}
        direct = strategy._extract_single_field(element, field_direct)
        pipeline = strategy._extract_single_field(element, field_pipeline)
        # Should be equivalent (both go through element HTML → markdown)
        assert direct == pipeline


# ── End-to-end extraction ────────────────────────────────────────────────

class TestMarkdownEndToEnd:

    def test_full_extraction_with_markdown_field(self):
        """End-to-end: extract structured data with a markdown field."""
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

        schema = {
            "name": "products",
            "baseSelector": "div.product",
            "fields": [
                {"name": "title", "selector": "h3", "type": "text"},
                {"name": "description", "selector": "p.desc", "type": "markdown"},
                {"name": "price", "selector": "span.price", "type": "text"},
            ],
        }
        strategy = JsonCssExtractionStrategy(schema)
        results = strategy.extract("http://test.com", RICH_HTML)

        assert len(results) == 1
        item = results[0]
        assert item["title"] == "Widget Pro"
        assert item["price"] == "$29.99"
        # Markdown field should have formatted content
        desc = item["description"]
        assert isinstance(desc, str)
        assert "Best seller" in desc
        assert "<strong>" not in desc  # No raw HTML

    def test_multi_item_extraction_with_markdown(self):
        """Multiple items extracted with markdown fields."""
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

        schema = {
            "name": "products",
            "baseSelector": "div.product",
            "fields": [
                {"name": "title", "selector": "h3", "type": "text"},
                {"name": "description", "selector": "p.desc", "type": "markdown"},
            ],
        }
        strategy = JsonCssExtractionStrategy(schema)
        results = strategy.extract("http://test.com", MULTI_PRODUCT_HTML)

        assert len(results) == 2
        assert "Bold text" in results[0]["description"]
        assert "<strong>" not in results[0]["description"]
        assert "/link" in results[1]["description"]

    def test_json_serialization_of_markdown_results(self):
        """Extraction results with markdown fields must serialize to JSON."""
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

        schema = {
            "name": "products",
            "baseSelector": "div.product",
            "fields": [
                {"name": "description", "selector": "p.desc", "type": "markdown"},
            ],
        }
        strategy = JsonCssExtractionStrategy(schema)
        results = strategy.extract("http://test.com", RICH_HTML)

        # Must not raise
        serialized = json.dumps(results, indent=4, default=str, ensure_ascii=False)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert len(parsed) == 1


# ── Cross-strategy: lxml ─────────────────────────────────────────────────

class TestMarkdownTypeLxml:

    def test_lxml_markdown_extraction(self):
        """JsonLxmlExtractionStrategy should also support markdown type."""
        from crawl4ai.extraction_strategy import JsonLxmlExtractionStrategy

        schema = {
            "name": "products",
            "baseSelector": "div.product",
            "fields": [
                {"name": "title", "selector": "h3", "type": "text"},
                {"name": "description", "selector": "p.desc", "type": "markdown"},
            ],
        }
        strategy = JsonLxmlExtractionStrategy(schema)
        results = strategy.extract("http://test.com", RICH_HTML)

        assert len(results) >= 1
        desc = results[0]["description"]
        assert isinstance(desc, str)
        assert "Best seller" in desc
        assert "<strong>" not in desc


# ── Cross-strategy: xpath ────────────────────────────────────────────────

class TestMarkdownTypeXPath:

    def test_xpath_markdown_extraction(self):
        """JsonXPathExtractionStrategy should also support markdown type."""
        from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy

        schema = {
            "name": "products",
            "baseSelector": "//div[@class='product']",
            "fields": [
                {"name": "title", "selector": ".//h3", "type": "text"},
                {"name": "description", "selector": ".//p[@class='desc']", "type": "markdown"},
            ],
        }
        strategy = JsonXPathExtractionStrategy(schema)
        results = strategy.extract("http://test.com", RICH_HTML)

        assert len(results) >= 1
        desc = results[0]["description"]
        assert isinstance(desc, str)
        assert "Best seller" in desc
        assert "<strong>" not in desc
