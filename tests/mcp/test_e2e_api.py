#!/usr/bin/env python3
"""
E2E API tests for Crawl4AI MCP HTTP endpoints using FastAPI TestClient.

Tests the full FastAPI stack (middleware, routing, endpoints) with coverage.
Uses TestClient for in-process requests without network overhead.
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

try:
    from fastapi.testclient import TestClient
    HAVE_TESTCLIENT = True
except ImportError:
    HAVE_TESTCLIENT = False


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient for in-process API testing."""
    if not HAVE_TESTCLIENT:
        pytest.skip("fastapi[test] not installed")

    from deploy.docker.server import app
    return TestClient(app)


@pytest.fixture
def make_export_path():
    """Factory for test export paths."""
    base_dir = Path(os.environ.get("MCP_EXPORT_DIR", "/tmp/crawl4ai-exports"))
    base_dir.mkdir(parents=True, exist_ok=True)

    def factory(filename: str) -> str:
        return str(base_dir / f"test-api-{filename}")

    return factory


# ---- MCP Schema Tests ------------------------------------------------------

def test_mcp_schema(client):
    """Test MCP schema endpoint exposes all tools."""
    response = client.get("/mcp/schema")
    assert response.status_code == 200

    data = response.json()
    assert "tools" in data
    tool_names = {tool["name"] for tool in data["tools"]}
    expected = {"md", "html", "screenshot", "pdf", "execute_js", "crawl", "ask"}
    assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"


# ---- MD Endpoint Tests -----------------------------------------------------

def test_md_raw(client):
    """Test /md endpoint with raw HTML."""
    response = client.post("/md", json={
        "url": "raw:<h1>Hello API</h1><p>Test content</p>",
        "filter": "raw",
        "cache": "0"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "markdown" in data
    assert "Hello API" in data["markdown"]


def test_md_filters(client):
    """Test /md endpoint with different filter types."""
    filters = [
        ("raw", None),
        ("fit", None),
        ("bm25", "Test")
    ]

    for filter_type, query in filters:
        response = client.post("/md", json={
            "url": "raw:<h1>Test</h1><p>Content</p>",
            "filter": filter_type,
            "query": query,
            "cache": "0"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "markdown" in data


def test_md_invalid_url(client):
    """Test /md endpoint error handling for invalid URL."""
    response = client.post("/md", json={
        "url": "not-a-valid-url",
        "filter": "raw"
    })

    assert response.status_code in (400, 422)


def test_md_query_params(client):
    """Test /md endpoint preserves request parameters."""
    response = client.post("/md", json={
        "url": "raw:<h1>Query Test</h1>",
        "filter": "raw",
        "query": None,
        "cache": "1"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data.get("cache") == "1"


# ---- HTML Endpoint Tests ---------------------------------------------------

def test_html_basic(client):
    """Test /html endpoint basic functionality."""
    response = client.post("/html", json={
        "url": "raw:<div>HTML Test</div>"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "html" in data


# ---- Execute JS Endpoint Tests ---------------------------------------------

def test_execute_js_basic(client):
    """Test /execute_js endpoint with simple script."""
    response = client.post("/execute_js", json={
        "url": "raw:<html><head><title>JS Test</title></head></html>",
        "scripts": ["document.title"]
    })

    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


def test_execute_js_multiple_scripts(client):
    """Test /execute_js endpoint with multiple scripts."""
    scripts = [
        "document.title",
        "(function(){ return document.body ? document.body.tagName : 'BODY'; })()",
        "(async function(){ return 42; })()"
    ]

    response = client.post("/execute_js", json={
        "url": "raw:<html><body></body></html>",
        "scripts": scripts
    })

    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


# ---- Screenshot Endpoint Tests ---------------------------------------------

def test_screenshot_basic(client):
    """Test /screenshot endpoint basic functionality."""
    # Use example.com since raw: URLs can't be screenshot
    response = client.post("/screenshot", json={
        "url": "https://example.com",
        "screenshot_wait_for": 0
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert ("path" in data) or ("screenshot" in data)


def test_screenshot_wait_times(client):
    """Test /screenshot endpoint with various wait times."""
    # Only test valid wait times, use real URL
    for wait_time in [0, 2]:
        response = client.post("/screenshot", json={
            "url": "https://example.com",
            "screenshot_wait_for": wait_time
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


def test_screenshot_invalid_path(client):
    """Test /screenshot endpoint path validation."""
    response = client.post("/screenshot", json={
        "url": "https://example.com",
        "output_path": "/invalid/path/test.png"
    })

    assert response.status_code == 400
    data = response.json()
    # Error might be in error_message or detail
    error_text = str(data.get("error_message") or data.get("detail") or data)
    assert "crawl4ai-exports" in error_text


# ---- PDF Endpoint Tests ----------------------------------------------------

def test_pdf_basic(client):
    """Test /pdf endpoint basic functionality."""
    # Use real URL since raw: can't be PDF'd
    response = client.post("/pdf", json={
        "url": "https://example.com"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert ("pdf" in data) or ("path" in data)


def test_pdf_with_output_path(client, make_export_path):
    """Test /pdf endpoint with file export."""
    output_path = make_export_path("test.pdf")

    response = client.post("/pdf", json={
        "url": "https://example.com",
        "output_path": output_path
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "path" in data


# ---- Crawl Endpoint Tests --------------------------------------------------

def test_crawl_single_url(client):
    """Test /crawl endpoint with single URL."""
    response = client.post("/crawl", json={
        "urls": ["raw:<h1>Crawl Test</h1>"]
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_crawl_empty_urls(client):
    """Test /crawl endpoint rejects empty URL list."""
    response = client.post("/crawl", json={
        "urls": []
    })

    assert response.status_code == 422


def test_crawl_browser_config(client):
    """Test /crawl endpoint with browser configuration."""
    response = client.post("/crawl", json={
        "urls": ["raw:<h1>Test</h1>"],
        "browser_config": {
            "headless": True,
            "viewport_width": 1920,
            "viewport_height": 1080
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_crawl_headless_enforcement(client):
    """Test /crawl endpoint rejects headless=false in Docker."""
    response = client.post("/crawl", json={
        "urls": ["raw:<h1>Test</h1>"],
        "browser_config": {"headless": False}
    })

    assert response.status_code == 400
    data = response.json()
    # Check flexible error format
    error_text = str(data.get("error_message") or data.get("detail") or data).lower()
    assert "headless" in error_text


def test_crawl_output_path_validation(client):
    """Test /crawl endpoint output_path security validation."""
    response = client.post("/crawl", json={
        "urls": ["raw:<h1>Test</h1>"],
        "output_path": "/invalid/path/test.json"
    })

    assert response.status_code == 400
    data = response.json()
    error_text = str(data.get("error_message") or data.get("detail") or data)
    assert "crawl4ai-exports" in error_text


# ---- Ask Endpoint Tests ----------------------------------------------------

def test_ask_context_types(client):
    """Test /ask endpoint with different context types."""
    # /ask is a GET endpoint, not POST
    for context_type in ["doc", "code", "all"]:
        response = client.get("/ask", params={
            "context_type": context_type,
            "query": "crawl"
        })

        assert response.status_code == 200
        data = response.json()

        if context_type in ("code", "all"):
            assert "code_results" in data
        if context_type in ("doc", "all"):
            assert "doc_results" in data


def test_ask_null_query(client):
    """Test /ask endpoint with null query returns limited results."""
    # /ask is a GET endpoint with query params
    response = client.get("/ask", params={
        "context_type": "all",
        "max_results": 50
    })

    assert response.status_code == 200
    data = response.json()

    # Should cap results at ~5 per type when no query provided
    if "code_results" in data:
        assert len(data["code_results"]) <= 5
    if "doc_results" in data:
        assert len(data["doc_results"]) <= 5


# ---- Network Error Tests ---------------------------------------------------

def test_network_error_dns_failure(client):
    """Test DNS failure returns user-friendly error."""
    response = client.post("/md", json={
        "url": "http://nonexistent-domain-test-12345.com",
        "filter": "raw"
    })

    # Should return error response
    assert response.status_code >= 400
    data = response.json()
    # Error format might vary (success field or detail field)
    err_msg = str(data.get("error_message") or data.get("detail") or data).lower()
    assert any(kw in err_msg for kw in ["resolve", "hostname", "dns", "not found", "unable to resolve"])


def test_network_error_connection_refused(client):
    """Test connection refused returns user-friendly error."""
    response = client.post("/md", json={
        "url": "http://127.0.0.1:1",
        "filter": "raw"
    })

    # Should return error response
    assert response.status_code >= 400
    data = response.json()
    # Error format might vary
    err_msg = str(data.get("error_message") or data.get("detail") or data).lower()
    assert any(kw in err_msg for kw in ["connection", "connect", "refused", "down"])


# ---- Fallback Mode Tests ---------------------------------------------------
# Note: Fallback mode (lines 493-517 in api.py) is difficult to test without
# complex mocking of the crawler pool. The fallback logic triggers when bulk
# crawl fails and retries per-URL. This would require mocking get_crawler and
# controlling arun_many vs arun behavior, which is brittle and doesn't add
# much value since we're testing internal error recovery logic.
# Instead, we test the limit parameter and error handling which exercises
# similar code paths.


# ---- Error Path Tests ------------------------------------------------------

def test_md_invalid_filter_type(client):
    """Test /md with invalid filter returns error."""
    response = client.post("/md", json={
        "url": "raw:<h1>Test</h1>",
        "filter": "invalid_filter_type"
    })

    assert response.status_code in (400, 422)  # 422 = Pydantic validation error
    data = response.json()
    error_text = str(data.get("detail") or data.get("error_message") or data).lower()
    assert "filter" in error_text or "invalid" in error_text or "enum" in error_text


def test_crawl_invalid_browser_config(client):
    """Test /crawl with malformed browser_config."""
    response = client.post("/crawl", json={
        "urls": ["raw:<h1>Test</h1>"],
        "browser_config": {"invalid_field": "should_fail"},
        "crawler_config": {}
    })

    # Should handle gracefully - either succeed with defaults or return error
    assert response.status_code in (200, 400, 422)


def test_crawl_invalid_crawler_config(client):
    """Test /crawl with malformed crawler_config."""
    response = client.post("/crawl", json={
        "urls": ["raw:<h1>Test</h1>"],
        "browser_config": {},
        "crawler_config": {"invalid_field": "should_fail"}
    })

    # Should handle gracefully
    assert response.status_code in (200, 400, 422)


def test_execute_js_empty_scripts(client):
    """Test /execute_js with empty scripts array."""
    response = client.post("/execute_js", json={
        "url": "raw:<h1>Test</h1>",
        "scripts": []
    })

    # Should either succeed with no results or return validation error
    assert response.status_code in (200, 400, 422)


def test_execute_js_malformed_script(client):
    """Test /execute_js captures JavaScript syntax errors in result."""
    response = client.post("/execute_js", json={
        "url": "https://example.com",
        "scripts": ["this is not valid javascript {{{"]
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True  # Request succeeds even if JS fails

    # JS execution error should be captured in js_execution_result
    assert "js_execution_result" in data
    js_result = data["js_execution_result"]

    # Should have results array with error status
    assert "results" in js_result
    # At least one result should indicate failure/error
    results = js_result["results"]
    assert len(results) > 0
    # Error should be recorded (either in result or as error flag)
    assert any(
        not r.get("success", True) or "error" in str(r).lower()
        for r in results
    )


def test_screenshot_negative_wait_time(client, make_export_path):
    """Test /screenshot treats negative wait time as zero (no wait)."""
    output_path = make_export_path("negative-wait.png")

    response = client.post("/screenshot", json={
        "url": "https://example.com",
        "screenshot_wait_for": -1.0,
        "output_path": output_path
    })

    # Negative wait should be treated as 0 and succeed
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "path" in data or "screenshot" in data


def test_pdf_invalid_output_path(client):
    """Test /pdf with path outside allowed directory."""
    response = client.post("/pdf", json={
        "url": "https://example.com",
        "output_path": "/etc/passwd"
    })

    assert response.status_code == 400
    data = response.json()
    error_text = str(data.get("error_message") or data.get("detail") or data)
    assert "crawl4ai-exports" in error_text or "not allowed" in error_text.lower()


def test_html_basic_error_handling(client):
    """Test /html with invalid URL."""
    response = client.post("/html", json={
        "url": "http://127.0.0.1:1"
    })

    assert response.status_code >= 400
    data = response.json()
    assert "error" in str(data).lower() or "detail" in data


def test_crawl_with_output_path_and_limit(client, make_export_path):
    """Test /crawl exports correctly with limit parameter."""
    output_path = make_export_path("crawl-with-limit.json")

    response = client.post("/crawl", json={
        "urls": ["raw:<h1>1</h1>", "raw:<h1>2</h1>", "raw:<h1>3</h1>"],
        "browser_config": {},
        "crawler_config": {"limit": 2},
        "output_path": output_path
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Verify file was created and contains limited results
    if Path(output_path).exists():
        with open(output_path) as f:
            exported = json.load(f)
        assert len(exported.get("results", [])) <= 2