"""
Tests for PR #1290 and #1668

- #1290: Type-list pipeline in JsonCssExtractionStrategy._extract_single_field
- #1668: --json-ensure-ascii CLI flag and JSON_ENSURE_ASCII config
"""
import json
import pytest
from bs4 import BeautifulSoup


# ── PR #1290: Type-list pipeline in _extract_single_field ─────────────────


class TestTypePipeline:
    """Test that field type can be a list for chained extraction."""

    @pytest.fixture
    def strategy(self):
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        schema = {"name": "test", "baseSelector": "div", "fields": []}
        return JsonCssExtractionStrategy(schema)

    @pytest.fixture
    def element(self):
        html = '<div><a class="link" href="/product/12345?ref=home">Product Name</a></div>'
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("div")

    def test_single_type_text_still_works(self, strategy, element):
        """Single string type 'text' should still work as before."""
        field = {"selector": "a", "type": "text"}
        result = strategy._extract_single_field(element, field)
        assert result == "Product Name"

    def test_single_type_attribute_still_works(self, strategy, element):
        """Single string type 'attribute' should still work."""
        field = {"selector": "a", "type": "attribute", "attribute": "href"}
        result = strategy._extract_single_field(element, field)
        assert result == "/product/12345?ref=home"

    def test_single_type_html_still_works(self, strategy, element):
        """Single string type 'html' should still work."""
        field = {"selector": "a", "type": "html"}
        result = strategy._extract_single_field(element, field)
        assert "Product Name" in result
        assert "href" in result

    def test_single_type_regex_still_works(self, strategy, element):
        """Single string type 'regex' should still work (reads text, applies pattern)."""
        field = {"selector": "a", "type": "regex", "pattern": r"Product (\w+)"}
        result = strategy._extract_single_field(element, field)
        assert result == "Name"

    def test_pipeline_attribute_then_regex(self, strategy, element):
        """Pipeline: get attribute, then regex-extract from it."""
        field = {
            "selector": "a",
            "type": ["attribute", "regex"],
            "attribute": "href",
            "pattern": r"/product/(\d+)",
        }
        result = strategy._extract_single_field(element, field)
        assert result == "12345"

    def test_pipeline_html_then_regex(self, strategy, element):
        """Pipeline: get HTML, then regex-extract from it."""
        field = {
            "selector": "a",
            "type": ["html", "regex"],
            "pattern": r'href="([^"]+)"',
        }
        result = strategy._extract_single_field(element, field)
        assert result == "/product/12345?ref=home"

    def test_pipeline_text_then_regex(self, strategy, element):
        """Pipeline: get text, then regex — same as single 'regex' type."""
        field = {
            "selector": "a",
            "type": ["text", "regex"],
            "pattern": r"Product (\w+)",
        }
        result = strategy._extract_single_field(element, field)
        assert result == "Name"

    def test_pipeline_stops_on_none(self, strategy, element):
        """Pipeline should stop and return default when a step yields None."""
        field = {
            "selector": "a",
            "type": ["attribute", "regex"],
            "attribute": "href",
            "pattern": r"NOMATCH(\d+)",
            "default": "N/A",
        }
        result = strategy._extract_single_field(element, field)
        assert result == "N/A"

    def test_pipeline_custom_group(self, strategy):
        """Pipeline with custom regex group number."""
        html = '<div><span data-info="key:value123">text</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        doc = soup.find("div")
        field = {
            "selector": "span",
            "type": ["attribute", "regex"],
            "attribute": "data-info",
            "pattern": r"(\w+):(\w+)",
            "group": 2,
        }
        result = strategy._extract_single_field(doc, field)
        assert result == "value123"

    def test_single_element_list_same_as_string(self, strategy, element):
        """A list with one element should behave identically to a string."""
        field_str = {"selector": "a", "type": "text"}
        field_list = {"selector": "a", "type": ["text"]}
        assert strategy._extract_single_field(element, field_str) == \
               strategy._extract_single_field(element, field_list)


# ── PR #1668: JSON_ENSURE_ASCII config setting ────────────────────────────


class TestJsonEnsureAsciiConfig:
    """Test the JSON_ENSURE_ASCII configuration setting."""

    def test_user_settings_has_json_ensure_ascii(self):
        """USER_SETTINGS should include JSON_ENSURE_ASCII."""
        from crawl4ai.config import USER_SETTINGS
        assert "JSON_ENSURE_ASCII" in USER_SETTINGS
        assert USER_SETTINGS["JSON_ENSURE_ASCII"]["default"] is True
        assert USER_SETTINGS["JSON_ENSURE_ASCII"]["type"] == "boolean"

    def test_ensure_ascii_true_escapes_unicode(self):
        """With ensure_ascii=True, non-ASCII chars should be escaped."""
        data = {"name": "Ján Kováč"}
        output = json.dumps(data, ensure_ascii=True)
        assert "\\u" in output
        assert "Ján" not in output

    def test_ensure_ascii_false_preserves_unicode(self):
        """With ensure_ascii=False, non-ASCII chars should be preserved."""
        data = {"name": "Ján Kováč"}
        output = json.dumps(data, ensure_ascii=False)
        assert "Ján Kováč" in output
        assert "\\u" not in output

    def test_cli_has_json_ensure_ascii_option(self):
        """The crawl_cmd should accept --json-ensure-ascii flag."""
        import click
        from crawl4ai.cli import crawl_cmd
        # Get the click command's params
        param_names = [p.name for p in crawl_cmd.params]
        assert "json_ensure_ascii" in param_names

    def test_default_cmd_has_json_ensure_ascii_option(self):
        """The default command should accept --json-ensure-ascii flag."""
        from crawl4ai.cli import default
        param_names = [p.name for p in default.params]
        assert "json_ensure_ascii" in param_names

    def test_cli_source_uses_ensure_ascii_in_dumps(self):
        """cli.py should pass ensure_ascii to json.dumps calls."""
        import inspect
        from crawl4ai import cli
        source = inspect.getsource(cli)
        assert "ensure_ascii=ensure_ascii" in source
