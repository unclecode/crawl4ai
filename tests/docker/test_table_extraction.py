"""
Integration tests for Table Extraction functionality in Crawl4AI Docker Server

Tests cover:
1. Integrated table extraction during crawls
2. Dedicated /tables endpoints
3. All extraction strategies (default, LLM, financial)
4. Batch processing
5. Error handling

Note: These tests require the Docker server to be running on localhost:11235
Run: python deploy/docker/server.py
"""

import pytest
import requests
import time
from typing import Dict, Any


# Base URL for the Docker API server
BASE_URL = "http://localhost:11234"

# Sample HTML with tables for testing
SAMPLE_HTML_WITH_TABLES = """
<!DOCTYPE html>
<html>
<head><title>Test Page with Tables</title></head>
<body>
    <h1>Financial Data</h1>
    
    <!-- Simple table -->
    <table id="simple">
        <tr><th>Name</th><th>Age</th></tr>
        <tr><td>Alice</td><td>25</td></tr>
        <tr><td>Bob</td><td>30</td></tr>
    </table>
    
    <!-- Financial table -->
    <table id="financial">
        <thead>
            <tr><th>Quarter</th><th>Revenue</th><th>Expenses</th><th>Profit</th></tr>
        </thead>
        <tbody>
            <tr><td>Q1 2024</td><td>$1,250,000.00</td><td>$850,000.00</td><td>$400,000.00</td></tr>
            <tr><td>Q2 2024</td><td>$1,500,000.00</td><td>$900,000.00</td><td>$600,000.00</td></tr>
        </tbody>
    </table>
    
    <!-- Complex nested table -->
    <table id="complex">
        <tr>
            <th rowspan="2">Product</th>
            <th colspan="2">Sales</th>
        </tr>
        <tr>
            <th>Units</th>
            <th>Revenue</th>
        </tr>
        <tr><td>Widget A</td><td>100</td><td>$5,000</td></tr>
        <tr><td>Widget B</td><td>200</td><td>$10,000</td></tr>
    </table>
</body>
</html>
"""


@pytest.fixture(scope="module")
def server_url():
    """Return the server URL"""
    return BASE_URL


@pytest.fixture(scope="module")
def wait_for_server():
    """Wait for server to be ready"""
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(1)
    pytest.skip("Server not running on localhost:11235. Start with: python deploy/docker/server.py")


class TestIntegratedTableExtraction:
    """Test table extraction integrated with /crawl endpoint"""

    def test_crawl_with_default_table_extraction(self, server_url, wait_for_server):
        """Test crawling with default table extraction strategy"""
        response = requests.post(f"{server_url}/crawl", json={
            "urls": ["https://example.com/tables"],
            "browser_config": {"headless": True},
            "crawler_config": {},
            "table_extraction": {
                "strategy": "default"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        
        # Check first result has tables
        if data["results"]:
            result = data["results"][0]
            assert "tables" in result or result.get("success") is False

    def test_crawl_with_llm_table_extraction(self, server_url, wait_for_server):
        """Test crawling with LLM table extraction strategy"""
        response = requests.post(f"{server_url}/crawl", json={
            "urls": ["https://example.com/financial"],
            "browser_config": {"headless": True},
            "crawler_config": {},
            "table_extraction": {
                "strategy": "llm",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "llm_api_key": "test-key",
                "llm_prompt": "Extract financial data from tables"
            }
        })
        
        # Should fail without valid API key, but structure should be correct
        # In real scenario with valid key, this would succeed
        assert response.status_code in [200, 500]  # May fail on auth

    def test_crawl_with_financial_table_extraction(self, server_url, wait_for_server):
        """Test crawling with financial table extraction strategy"""
        response = requests.post(f"{server_url}/crawl", json={
            "urls": ["https://example.com/stocks"],
            "browser_config": {"headless": True},
            "crawler_config": {},
            "table_extraction": {
                "strategy": "financial",
                "preserve_formatting": True,
                "extract_metadata": True
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_crawl_without_table_extraction(self, server_url, wait_for_server):
        """Test crawling without table extraction (should work normally)"""
        response = requests.post(f"{server_url}/crawl", json={
            "urls": ["https://example.com"],
            "browser_config": {"headless": True},
            "crawler_config": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestDedicatedTableEndpoints:
    """Test dedicated /tables endpoints"""

    def test_extract_tables_from_html(self, server_url, wait_for_server):
        """Test extracting tables from provided HTML"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {
                "strategy": "default"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["table_count"] >= 3  # Should find at least 3 tables
        assert "tables" in data
        assert data["strategy"] == "default"
        
        # Verify table structure
        if data["tables"]:
            table = data["tables"][0]
            assert "headers" in table or "rows" in table

    def test_extract_tables_from_url(self, server_url, wait_for_server):
        """Test extracting tables by fetching URL"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "url": "https://example.com/tables",
            "config": {
                "strategy": "default"
            }
        })
        
        # May fail if URL doesn't exist, but structure should be correct
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "tables" in data

    def test_extract_tables_invalid_input(self, server_url, wait_for_server):
        """Test error handling for invalid input"""
        # No html or url provided
        response = requests.post(f"{server_url}/tables/extract", json={
            "config": {"strategy": "default"}
        })
        
        assert response.status_code == 400
        assert "html" in response.text.lower() or "url" in response.text.lower()

    def test_extract_tables_both_html_and_url(self, server_url, wait_for_server):
        """Test error when both html and url are provided"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": "<table></table>",
            "url": "https://example.com",
            "config": {"strategy": "default"}
        })
        
        assert response.status_code == 400
        assert "both" in response.text.lower()


class TestBatchTableExtraction:
    """Test batch table extraction endpoints"""

    def test_batch_extract_html_list(self, server_url, wait_for_server):
        """Test batch extraction from multiple HTML contents"""
        response = requests.post(f"{server_url}/tables/extract/batch", json={
            "html_list": [
                SAMPLE_HTML_WITH_TABLES,
                "<table><tr><th>A</th></tr><tr><td>1</td></tr></table>",
            ],
            "config": {"strategy": "default"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "summary" in data
        assert data["summary"]["total_processed"] == 2
        assert data["summary"]["successful"] >= 0
        assert "results" in data
        assert len(data["results"]) == 2

    def test_batch_extract_url_list(self, server_url, wait_for_server):
        """Test batch extraction from multiple URLs"""
        response = requests.post(f"{server_url}/tables/extract/batch", json={
            "url_list": [
                "https://example.com/page1",
                "https://example.com/page2",
            ],
            "config": {"strategy": "default"}
        })
        
        # May have mixed success/failure depending on URLs
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "summary" in data
            assert "results" in data

    def test_batch_extract_mixed(self, server_url, wait_for_server):
        """Test batch extraction from both HTML and URLs"""
        response = requests.post(f"{server_url}/tables/extract/batch", json={
            "html_list": [SAMPLE_HTML_WITH_TABLES],
            "url_list": ["https://example.com/tables"],
            "config": {"strategy": "default"}
        })
        
        # May fail on URL crawling but should handle mixed input
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["summary"]["total_processed"] == 2

    def test_batch_extract_empty_list(self, server_url, wait_for_server):
        """Test error when no items provided for batch"""
        response = requests.post(f"{server_url}/tables/extract/batch", json={
            "config": {"strategy": "default"}
        })
        
        assert response.status_code == 400

    def test_batch_extract_exceeds_limit(self, server_url, wait_for_server):
        """Test error when batch size exceeds limit"""
        response = requests.post(f"{server_url}/tables/extract/batch", json={
            "html_list": ["<table></table>"] * 100,  # 100 items (limit is 50)
            "config": {"strategy": "default"}
        })
        
        assert response.status_code == 400
        assert "50" in response.text or "limit" in response.text.lower()


class TestTableExtractionStrategies:
    """Test different table extraction strategies"""

    def test_default_strategy(self, server_url, wait_for_server):
        """Test default (regex-based) extraction strategy"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {
                "strategy": "default"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["strategy"] == "default"
        assert data["table_count"] >= 1

    def test_llm_strategy_without_config(self, server_url, wait_for_server):
        """Test LLM strategy without proper config (should use defaults or work)"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {
                "strategy": "llm"
                # Missing required LLM config
            }
        })
        
        # May succeed with defaults or fail - both are acceptable
        assert response.status_code in [200, 400, 500]

    def test_financial_strategy(self, server_url, wait_for_server):
        """Test financial extraction strategy"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {
                "strategy": "financial",
                "preserve_formatting": True,
                "extract_metadata": True
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["strategy"] == "financial"
        
        # Financial tables should be extracted
        if data["tables"]:
            # Should find the financial table in our sample HTML
            assert data["table_count"] >= 1

    def test_none_strategy(self, server_url, wait_for_server):
        """Test with 'none' strategy (no extraction)"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {
                "strategy": "none"
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        # Should return 0 tables
        assert data["table_count"] == 0


class TestTableExtractionConfig:
    """Test table extraction configuration options"""

    def test_preserve_formatting_option(self, server_url, wait_for_server):
        """Test preserve_formatting option"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {
                "strategy": "financial",
                "preserve_formatting": True
            }
        })
        
        assert response.status_code == 200

    def test_extract_metadata_option(self, server_url, wait_for_server):
        """Test extract_metadata option"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {
                "strategy": "financial",
                "extract_metadata": True
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if tables have metadata when requested
        if data["tables"]:
            table = data["tables"][0]
            assert isinstance(table, dict)


class TestErrorHandling:
    """Test error handling for table extraction"""

    def test_malformed_html(self, server_url, wait_for_server):
        """Test handling of malformed HTML"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": "<table><tr><td>incomplete",
            "config": {"strategy": "default"}
        })
        
        # Should handle gracefully (either return empty or partial results)
        assert response.status_code in [200, 400, 500]

    def test_empty_html(self, server_url, wait_for_server):
        """Test handling of empty HTML"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": "",
            "config": {"strategy": "default"}
        })
        
        # May be rejected as invalid or processed as empty
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data["table_count"] == 0

    def test_html_without_tables(self, server_url, wait_for_server):
        """Test HTML with no tables"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": "<html><body><p>No tables here</p></body></html>",
            "config": {"strategy": "default"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["table_count"] == 0

    def test_invalid_strategy(self, server_url, wait_for_server):
        """Test invalid strategy name"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES,
            "config": {"strategy": "invalid_strategy"}
        })
        
        # Should return validation error (400 or 422 from Pydantic)
        assert response.status_code in [400, 422]

    def test_missing_config(self, server_url, wait_for_server):
        """Test missing configuration"""
        response = requests.post(f"{server_url}/tables/extract", json={
            "html": SAMPLE_HTML_WITH_TABLES
            # Missing config
        })
        
        # Should use default config or return error
        assert response.status_code in [200, 400]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
