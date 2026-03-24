"""
Tests for _strip_markdown_fences helper and agenerate_schema() JSON parsing fix.

Covers:
- Unit tests for _strip_markdown_fences (pure logic, no API calls)
- Real integration tests calling Anthropic/OpenAI/Groq against quotes.toscrape.com
- Regression tests ensuring clean JSON is never corrupted
"""

import json
import os
import pytest

from crawl4ai.extraction_strategy import (
    _strip_markdown_fences,
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
)
from crawl4ai.async_configs import LLMConfig


# ---------------------------------------------------------------------------
# Sample schemas for unit tests
# ---------------------------------------------------------------------------

SIMPLE_SCHEMA = {
    "name": "Quotes",
    "baseSelector": ".quote",
    "fields": [
        {"name": "text", "selector": ".text", "type": "text"},
        {"name": "author", "selector": ".author", "type": "text"},
    ],
}

NESTED_SCHEMA = {
    "name": "Products",
    "baseSelector": ".product-card",
    "baseFields": [{"name": "id", "selector": "", "type": "attribute", "attribute": "data-id"}],
    "fields": [
        {"name": "title", "selector": "h2.title", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {"name": "description", "selector": ".desc", "type": "text"},
        {"name": "image", "selector": "img.product-img", "type": "attribute", "attribute": "src"},
    ],
}

TEST_URL = "https://quotes.toscrape.com/"


# ===========================================================================
# Unit tests for _strip_markdown_fences
# ===========================================================================


class TestStripMarkdownFences:
    """Direct unit tests for the _strip_markdown_fences helper."""

    def test_clean_json_passthrough(self):
        """Clean JSON (no fences) must pass through unchanged."""
        raw = json.dumps(SIMPLE_SCHEMA)
        assert _strip_markdown_fences(raw) == raw

    def test_json_fence(self):
        """```json ... ``` wrapping is stripped correctly."""
        raw = '```json\n{"key": "value"}\n```'
        assert json.loads(_strip_markdown_fences(raw)) == {"key": "value"}

    def test_bare_fence(self):
        """``` ... ``` (no language tag) is stripped correctly."""
        raw = '```\n{"key": "value"}\n```'
        assert json.loads(_strip_markdown_fences(raw)) == {"key": "value"}

    def test_fence_with_language_variants(self):
        """Various language tags after ``` are stripped."""
        for lang in ["json", "JSON", "javascript", "js", "text", "jsonc"]:
            raw = f"```{lang}\n{{\"a\": 1}}\n```"
            result = _strip_markdown_fences(raw)
            assert json.loads(result) == {"a": 1}, f"Failed for language tag: {lang}"

    def test_leading_trailing_whitespace(self):
        """Whitespace around fenced content is stripped."""
        raw = '  \n  ```json\n{"key": "value"}\n```  \n  '
        assert json.loads(_strip_markdown_fences(raw)) == {"key": "value"}

    def test_no_fences_with_whitespace(self):
        """Plain JSON with surrounding whitespace is handled."""
        raw = '  \n  {"key": "value"}  \n  '
        assert json.loads(_strip_markdown_fences(raw)) == {"key": "value"}

    def test_nested_code_block_in_value(self):
        """JSON with a string value containing ``` is not corrupted."""
        inner = {"code": "Use ```python\\nprint()\\n``` for code blocks"}
        raw = f'```json\n{json.dumps(inner)}\n```'
        result = _strip_markdown_fences(raw)
        parsed = json.loads(result)
        assert "```python" in parsed["code"]

    def test_complex_schema(self):
        """A real-world multi-field schema wrapped in fences parses correctly."""
        raw = f"```json\n{json.dumps(NESTED_SCHEMA, indent=2)}\n```"
        result = _strip_markdown_fences(raw)
        assert json.loads(result) == NESTED_SCHEMA

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert _strip_markdown_fences("") == ""

    def test_only_whitespace(self):
        """Whitespace-only string returns empty string."""
        assert _strip_markdown_fences("   \n\n  ") == ""

    def test_only_fences(self):
        """Bare fences with nothing inside return empty string."""
        assert _strip_markdown_fences("```json\n```") == ""

    def test_multiline_json(self):
        """Multiline pretty-printed JSON inside fences."""
        pretty = json.dumps(SIMPLE_SCHEMA, indent=4)
        raw = f"```json\n{pretty}\n```"
        assert json.loads(_strip_markdown_fences(raw)) == SIMPLE_SCHEMA

    def test_already_clean_does_not_mutate(self):
        """Passing already-clean JSON multiple times is idempotent."""
        raw = json.dumps(SIMPLE_SCHEMA)
        once = _strip_markdown_fences(raw)
        twice = _strip_markdown_fences(once)
        assert once == twice == raw


# ===========================================================================
# Real integration tests — actual LLM API calls against quotes.toscrape.com
# ===========================================================================


def _validate_schema(schema: dict):
    """Validate that a generated schema has the expected structure."""
    assert isinstance(schema, dict), f"Schema must be a dict, got {type(schema)}"
    assert "name" in schema, "Schema must have a 'name' field"
    assert "baseSelector" in schema, "Schema must have a 'baseSelector' field"
    assert "fields" in schema, "Schema must have a 'fields' field"
    assert isinstance(schema["fields"], list), "'fields' must be a list"
    assert len(schema["fields"]) > 0, "'fields' must not be empty"
    for field in schema["fields"]:
        assert "name" in field, f"Each field must have a 'name': {field}"
        assert "selector" in field, f"Each field must have a 'selector': {field}"
        assert "type" in field, f"Each field must have a 'type': {field}"


class TestRealAnthropicSchemaGeneration:
    """Real API calls to Anthropic models — the exact scenario from the bug report."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("CRAWL4AI_ANTHROPIC_KEY"),
        reason="CRAWL4AI_ANTHROPIC_KEY not set",
    )
    async def test_anthropic_haiku_css_schema(self):
        """Reproduce the original bug: anthropic/claude-haiku-4-5 + CSS schema."""
        schema = await JsonCssExtractionStrategy.agenerate_schema(
            url=TEST_URL,
            schema_type="CSS",
            query="Extract all quotes with their text, author, and tags",
            llm_config=LLMConfig(
                provider="anthropic/claude-haiku-4-5",
                api_token=os.getenv("CRAWL4AI_ANTHROPIC_KEY"),
            ),
        )
        _validate_schema(schema)
        print(f"\n[Anthropic Haiku CSS] Generated schema: {json.dumps(schema, indent=2)}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("CRAWL4AI_ANTHROPIC_KEY"),
        reason="CRAWL4AI_ANTHROPIC_KEY not set",
    )
    async def test_anthropic_haiku_xpath_schema(self):
        """Anthropic haiku with XPath schema type."""
        schema = await JsonXPathExtractionStrategy.agenerate_schema(
            url=TEST_URL,
            schema_type="XPATH",
            query="Extract all quotes with their text, author, and tags",
            llm_config=LLMConfig(
                provider="anthropic/claude-haiku-4-5",
                api_token=os.getenv("CRAWL4AI_ANTHROPIC_KEY"),
            ),
        )
        _validate_schema(schema)
        print(f"\n[Anthropic Haiku XPath] Generated schema: {json.dumps(schema, indent=2)}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("CRAWL4AI_ANTHROPIC_KEY"),
        reason="CRAWL4AI_ANTHROPIC_KEY not set",
    )
    async def test_anthropic_no_query(self):
        """Anthropic with no query — should auto-detect schema from page structure."""
        schema = await JsonCssExtractionStrategy.agenerate_schema(
            url=TEST_URL,
            schema_type="CSS",
            llm_config=LLMConfig(
                provider="anthropic/claude-haiku-4-5",
                api_token=os.getenv("CRAWL4AI_ANTHROPIC_KEY"),
            ),
        )
        _validate_schema(schema)
        print(f"\n[Anthropic Haiku no-query] Generated schema: {json.dumps(schema, indent=2)}")


class TestRealOpenAISchemaGeneration:
    """OpenAI models — should still work as before (regression check)."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("CRAWL4AI_OPENAI_KEY"),
        reason="CRAWL4AI_OPENAI_KEY not set",
    )
    async def test_openai_gpt4o_mini_css_schema(self):
        """OpenAI gpt-4o-mini with CSS — this already worked, must not regress."""
        schema = await JsonCssExtractionStrategy.agenerate_schema(
            url=TEST_URL,
            schema_type="CSS",
            query="Extract all quotes with their text, author, and tags",
            llm_config=LLMConfig(
                provider="openai/gpt-4o-mini",
                api_token=os.getenv("CRAWL4AI_OPENAI_KEY"),
            ),
        )
        _validate_schema(schema)
        print(f"\n[OpenAI gpt-4o-mini CSS] Generated schema: {json.dumps(schema, indent=2)}")


class TestRealGroqSchemaGeneration:
    """Groq with the updated model name."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("CRAWL4AI_GROQ_KEY") and not os.getenv("GROQ_API_KEY"),
        reason="No Groq API key set",
    )
    async def test_groq_llama33_css_schema(self):
        """Groq with llama-3.3-70b-versatile (replacement for decommissioned 3.1)."""
        api_key = os.getenv("CRAWL4AI_GROQ_KEY") or os.getenv("GROQ_API_KEY")
        schema = await JsonCssExtractionStrategy.agenerate_schema(
            url=TEST_URL,
            schema_type="CSS",
            query="Extract all quotes with their text, author, and tags",
            llm_config=LLMConfig(
                provider="groq/llama-3.3-70b-versatile",
                api_token=api_key,
            ),
        )
        _validate_schema(schema)
        print(f"\n[Groq llama-3.3] Generated schema: {json.dumps(schema, indent=2)}")


# ===========================================================================
# Regression: ensure _strip_markdown_fences doesn't break valid JSON
# ===========================================================================


class TestRegressionNoBreakage:
    """Ensure the fix doesn't break any currently-working JSON formats."""

    @pytest.mark.parametrize(
        "raw_json",
        [
            '{"simple": true}',
            '[]',
            '[{"a": 1}, {"a": 2}]',
            '{"nested": {"deep": {"value": 42}}}',
            '{"unicode": "\u3053\u3093\u306b\u3061\u306f\u4e16\u754c"}',
            '{"special": "line1\\nline2\\ttab"}',
            '{"url": "https://example.com/path?q=1&b=2"}',
            json.dumps(SIMPLE_SCHEMA),
            json.dumps(NESTED_SCHEMA),
            json.dumps(NESTED_SCHEMA, indent=2),
            json.dumps(NESTED_SCHEMA, indent=4),
        ],
        ids=[
            "simple_object",
            "empty_array",
            "array_of_objects",
            "deeply_nested",
            "unicode_content",
            "escape_sequences",
            "url_in_value",
            "simple_schema_compact",
            "nested_schema_compact",
            "nested_schema_indent2",
            "nested_schema_indent4",
        ],
    )
    def test_clean_json_unchanged(self, raw_json):
        """Already-clean JSON must parse identically after stripping."""
        original = json.loads(raw_json)
        after_strip = json.loads(_strip_markdown_fences(raw_json))
        assert after_strip == original

    @pytest.mark.parametrize(
        "raw_json",
        [
            '{"simple": true}',
            '[]',
            '[{"a": 1}, {"a": 2}]',
            json.dumps(SIMPLE_SCHEMA),
            json.dumps(NESTED_SCHEMA, indent=2),
        ],
        ids=[
            "simple_object",
            "empty_array",
            "array_of_objects",
            "simple_schema",
            "nested_schema",
        ],
    )
    def test_fenced_json_matches_clean(self, raw_json):
        """Fenced version of any JSON must parse to the same value as clean."""
        original = json.loads(raw_json)
        fenced = f"```json\n{raw_json}\n```"
        after_strip = json.loads(_strip_markdown_fences(fenced))
        assert after_strip == original
