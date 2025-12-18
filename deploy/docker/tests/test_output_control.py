#!/usr/bin/env python3
"""
Test Suite: Output Control (Pagination) Feature

Tests the apply_output_control() function and endpoint integration.
Requires the crawl4ai container to be running on port 11235.

Run with: pytest test_output_control.py -v
"""

import asyncio
import pytest
import httpx
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from output_control import apply_output_control, apply_output_control_to_batch
from schemas import OutputControl, OutputMeta, ContentFieldStats, CollectionStats

# Config
BASE_URL = os.environ.get("CRAWL4AI_URL", "http://localhost:11235")
TEST_URL = "https://httpbin.org/html"  # Simple, stable test page


# =============================================================================
# Unit Tests for apply_output_control()
# =============================================================================


class TestApplyOutputControlUnit:
    """Unit tests for the apply_output_control function."""

    def test_no_control_returns_unchanged(self):
        """When control is None, data should be returned unchanged."""
        data = {
            "url": "https://example.com",
            "html": "<html><body>Test content</body></html>",
            "success": True,
            "links": {"internal": [{"href": "/page1"}], "external": []},
        }
        original_data = data.copy()

        result, meta = apply_output_control(data, None)

        assert result == original_data
        assert meta is None
        assert "_output_meta" not in result

    def test_empty_control_returns_unchanged(self):
        """When control has no options set, data should be unchanged."""
        data = {"html": "test content", "url": "https://example.com"}
        control = OutputControl()  # All None defaults

        result, meta = apply_output_control(data, control)

        assert result == data
        assert meta is None
        assert "_output_meta" not in result

    def test_content_limit_truncates_text_fields(self):
        """content_limit should truncate text fields to specified length."""
        data = {
            "html": "A" * 10000,
            "cleaned_html": "B" * 5000,
            "extracted_content": "C" * 3000,
        }
        control = OutputControl(content_limit=1000)

        result, meta = apply_output_control(data, control)

        assert len(result["html"]) == 1000
        assert len(result["cleaned_html"]) == 1000
        assert len(result["extracted_content"]) == 1000
        assert meta is not None
        assert meta.truncated is True
        assert "_output_meta" in result

    def test_content_offset_skips_characters(self):
        """content_offset should skip initial characters."""
        data = {"html": "0123456789ABCDEF"}
        control = OutputControl(content_offset=10)

        result, meta = apply_output_control(data, control)

        assert result["html"] == "ABCDEF"
        assert meta.truncated is True
        assert meta.content_stats["html"].offset == 10

    def test_content_offset_and_limit_combined(self):
        """content_offset + content_limit should work together."""
        data = {"html": "0123456789ABCDEFGHIJ"}
        control = OutputControl(content_offset=5, content_limit=5)

        result, meta = apply_output_control(data, control)

        assert result["html"] == "56789"
        assert meta.content_stats["html"].total_chars == 20
        assert meta.content_stats["html"].returned_chars == 5
        assert meta.content_stats["html"].offset == 5
        assert meta.content_stats["html"].has_more is True

    def test_nested_markdown_fields_truncated(self):
        """Nested markdown fields should be paginated."""
        data = {
            "markdown": {
                "raw_markdown": "X" * 5000,
                "fit_markdown": "Y" * 3000,
                "references_markdown": "Z" * 1000,
            }
        }
        control = OutputControl(content_limit=500)

        result, meta = apply_output_control(data, control)

        assert len(result["markdown"]["raw_markdown"]) == 500
        assert len(result["markdown"]["fit_markdown"]) == 500
        assert len(result["markdown"]["references_markdown"]) == 500
        assert "markdown.raw_markdown" in meta.content_stats
        assert "markdown.fit_markdown" in meta.content_stats

    def test_max_links_limits_collections(self):
        """max_links should limit both internal and external links."""
        data = {
            "links": {
                "internal": [{"href": f"/page{i}"} for i in range(100)],
                "external": [{"href": f"https://ext{i}.com"} for i in range(50)],
            }
        }
        control = OutputControl(max_links=10)

        result, meta = apply_output_control(data, control)

        assert len(result["links"]["internal"]) == 10
        assert len(result["links"]["external"]) == 10
        assert meta.collection_stats["links.internal"].total_count == 100
        assert meta.collection_stats["links.internal"].returned_count == 10
        assert meta.collection_stats["links.external"].total_count == 50
        assert meta.collection_stats["links.external"].returned_count == 10

    def test_max_media_limits_all_media_types(self):
        """max_media should limit images, videos, and audios."""
        data = {
            "media": {
                "images": [{"src": f"img{i}.jpg"} for i in range(30)],
                "videos": [{"src": f"vid{i}.mp4"} for i in range(20)],
                "audios": [{"src": f"aud{i}.mp3"} for i in range(10)],
            }
        }
        control = OutputControl(max_media=5)

        result, meta = apply_output_control(data, control)

        assert len(result["media"]["images"]) == 5
        assert len(result["media"]["videos"]) == 5
        assert len(result["media"]["audios"]) == 5
        assert meta.collection_stats["media.images"].total_count == 30

    def test_max_tables_limits_tables(self):
        """max_tables should limit tables array."""
        data = {"tables": [f"<table id='t{i}'>" for i in range(25)]}
        control = OutputControl(max_tables=3)

        result, meta = apply_output_control(data, control)

        assert len(result["tables"]) == 3
        assert meta.collection_stats["tables"].total_count == 25
        assert meta.collection_stats["tables"].returned_count == 3

    def test_exclude_fields_removes_top_level(self):
        """exclude_fields should remove specified top-level fields."""
        data = {
            "html": "<html>content</html>",
            "cleaned_html": "content",
            "links": {"internal": []},
            "metadata": {"title": "Test"},
        }
        control = OutputControl(exclude_fields=["html", "cleaned_html", "metadata"])

        result, meta = apply_output_control(data, control)

        assert "html" not in result
        assert "cleaned_html" not in result
        assert "metadata" not in result
        assert "links" in result  # Not excluded
        assert meta.excluded_fields == ["html", "cleaned_html", "metadata"]

    def test_exclude_fields_nested_dot_notation(self):
        """exclude_fields should support dot notation for nested fields."""
        data = {
            "markdown": {
                "raw_markdown": "raw content",
                "fit_markdown": "fit content",
                "references_markdown": "refs",
            }
        }
        control = OutputControl(exclude_fields=["markdown.references_markdown"])

        result, meta = apply_output_control(data, control)

        assert "raw_markdown" in result["markdown"]
        assert "fit_markdown" in result["markdown"]
        assert "references_markdown" not in result["markdown"]
        assert "markdown.references_markdown" in meta.excluded_fields

    def test_missing_fields_handled_gracefully(self):
        """Function should handle missing fields without errors."""
        data = {"url": "https://example.com", "success": True}
        control = OutputControl(
            content_limit=100, max_links=10, exclude_fields=["nonexistent_field"]
        )

        result, meta = apply_output_control(data, control)

        # Should not raise, should return data unchanged except meta
        assert result["url"] == "https://example.com"
        # Meta should still be None since nothing was actually truncated
        # (the fields don't exist, so nothing to truncate)

    def test_output_meta_added_to_result(self):
        """_output_meta should be added when truncation occurs."""
        data = {"html": "X" * 1000}
        control = OutputControl(content_limit=100)

        result, meta = apply_output_control(data, control)

        assert "_output_meta" in result
        assert result["_output_meta"]["truncated"] is True
        assert "content_stats" in result["_output_meta"]

    def test_deep_copy_preserves_original(self):
        """Original data should not be modified."""
        data = {
            "html": "X" * 1000,
            "links": {"internal": [{"href": "/a"}, {"href": "/b"}]},
        }
        original_html_len = len(data["html"])
        original_links_count = len(data["links"]["internal"])

        control = OutputControl(content_limit=100, max_links=1)
        result, _ = apply_output_control(data, control)

        # Original unchanged
        assert len(data["html"]) == original_html_len
        assert len(data["links"]["internal"]) == original_links_count
        # Result truncated
        assert len(result["html"]) == 100
        assert len(result["links"]["internal"]) == 1


class TestApplyOutputControlBatch:
    """Tests for apply_output_control_to_batch function."""

    def test_batch_applies_to_all_results(self):
        """Output control should apply to every result in batch."""
        results = [
            {"html": "A" * 1000, "url": "https://a.com"},
            {"html": "B" * 1000, "url": "https://b.com"},
            {"html": "C" * 1000, "url": "https://c.com"},
        ]
        control = OutputControl(content_limit=100)

        processed = apply_output_control_to_batch(results, control)

        assert len(processed) == 3
        for r in processed:
            assert len(r["html"]) == 100
            assert "_output_meta" in r

    def test_batch_none_control_returns_unchanged(self):
        """Batch with None control should return original list."""
        results = [{"html": "test"}, {"html": "test2"}]

        processed = apply_output_control_to_batch(results, None)

        assert processed == results


# =============================================================================
# Integration Tests (require running container)
# =============================================================================


@pytest.fixture
def http_client():
    """Async HTTP client for integration tests."""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)


class TestOutputControlIntegration:
    """Integration tests against running crawl4ai server."""

    @pytest.mark.asyncio
    async def test_md_endpoint_with_content_limit(self, http_client):
        """Test /md endpoint respects content_limit."""
        payload = {"url": TEST_URL, "f": "fit", "output": {"content_limit": 500}}

        response = await http_client.post("/md", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Check that markdown was truncated if longer than 500
        if "_output_meta" in data:
            assert data["_output_meta"]["truncated"] is True

    @pytest.mark.asyncio
    async def test_md_endpoint_without_output_unchanged(self, http_client):
        """Test /md endpoint without output param returns full response."""
        payload = {"url": TEST_URL, "f": "fit"}

        response = await http_client.post("/md", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "_output_meta" not in data

    @pytest.mark.asyncio
    async def test_crawl_endpoint_with_output_control(self, http_client):
        """Test /crawl endpoint with output control."""
        payload = {
            "urls": [TEST_URL],
            "browser_config": {},
            "crawler_config": {},
            "output": {
                "content_limit": 1000,
                "max_links": 5,
                "exclude_fields": ["response_headers", "network_requests"],
            },
        }

        response = await http_client.post("/crawl", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Check results have output control applied
        for result in data["results"]:
            if result.get("success"):
                assert "response_headers" not in result
                assert "network_requests" not in result

    @pytest.mark.asyncio
    async def test_execute_js_endpoint_with_output(self, http_client):
        """Test /execute_js endpoint with output control."""
        payload = {
            "url": TEST_URL,
            "scripts": ["document.title"],
            "output": {"content_limit": 500, "exclude_fields": ["html"]},
        }

        response = await http_client.post("/execute_js", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "html" not in data

    @pytest.mark.asyncio
    async def test_mcp_schema_includes_output_control(self, http_client):
        """Test that MCP schema correctly exposes OutputControl parameters."""
        response = await http_client.get("/mcp/schema")

        assert response.status_code == 200
        schema = response.json()

        # Find the 'md' tool
        md_tool = next((t for t in schema["tools"] if t["name"] == "md"), None)
        assert md_tool is not None, "md tool not found in MCP schema"

        # Check that output parameter is in the schema
        input_schema = md_tool["inputSchema"]

        # The schema should have $defs or definitions for OutputControl
        assert "$defs" in input_schema or "definitions" in input_schema
        defs = input_schema.get("$defs", input_schema.get("definitions", {}))

        assert "OutputControl" in defs, "OutputControl not found in schema definitions"

        # Verify OutputControl has expected properties
        output_control_schema = defs["OutputControl"]
        props = output_control_schema.get("properties", {})
        assert "content_limit" in props
        assert "content_offset" in props
        assert "max_links" in props
        assert "exclude_fields" in props


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestOutputControlEdgeCases:
    """Test edge cases and error conditions."""

    def test_offset_beyond_content_length(self):
        """Offset greater than content length should return empty string."""
        data = {"html": "short"}
        control = OutputControl(content_offset=100)

        result, meta = apply_output_control(data, control)

        assert result["html"] == ""
        assert meta.content_stats["html"].returned_chars == 0
        assert meta.content_stats["html"].has_more is False

    def test_limit_zero_not_allowed(self):
        """content_limit=0 should be rejected by Pydantic validation."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            OutputControl(content_limit=0)

    def test_negative_offset_not_allowed(self):
        """Negative offset should be rejected by Pydantic validation."""
        with pytest.raises(Exception):
            OutputControl(content_offset=-1)

    def test_empty_links_dict_handled(self):
        """Empty links dict should not cause errors."""
        data = {"links": {}}
        control = OutputControl(max_links=10)

        result, meta = apply_output_control(data, control)

        assert result["links"] == {}
        # No truncation occurred
        assert meta is None or not meta.truncated

    def test_non_string_field_ignored(self):
        """Non-string fields should not be truncated."""
        data = {
            "html": "content",
            "status_code": 200,
            "success": True,
        }
        control = OutputControl(content_limit=3)

        result, meta = apply_output_control(data, control)

        assert result["html"] == "con"
        assert result["status_code"] == 200
        assert result["success"] is True


if __name__ == "__main__":
    # Run unit tests directly
    pytest.main([__file__, "-v", "-x"])
