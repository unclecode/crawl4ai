#!/usr/bin/env python3
"""
End-to-end tests for the URL Discovery endpoint.

This test suite verifies the complete functionality of the /urls/discover endpoint
including happy path scenarios and error handling.
"""

import asyncio
import httpx
import json
import pytest
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:11235"
TEST_TIMEOUT = 30.0


class TestURLDiscoveryEndpoint:
    """End-to-end test suite for URL Discovery endpoint."""
    
    @pytest.fixture
    async def client(self):
        """Create an async HTTP client for testing."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TEST_TIMEOUT) as client:
            yield client
    
    async def test_server_health(self, client):
        """Test that the server is healthy before running other tests."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    async def test_endpoint_exists(self, client):
        """Test that the /urls/discover endpoint exists and is documented."""
        # Check OpenAPI spec includes our endpoint
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        assert "/urls/discover" in openapi_spec["paths"]
        
        endpoint_spec = openapi_spec["paths"]["/urls/discover"]
        assert "post" in endpoint_spec
        assert endpoint_spec["post"]["summary"] == "URL Discovery and Seeding"
    
    async def test_basic_url_discovery_happy_path(self, client):
        """Test basic URL discovery with minimal configuration."""
        request_data = {
            "domain": "example.com",
            "seeding_config": {
                "source": "sitemap",
                "max_urls": 5
            }
        }
        
        response = await client.post("/urls/discover", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Note: We don't assert length > 0 because URL discovery 
        # may legitimately return empty results
    
    async def test_minimal_request_with_defaults(self, client):
        """Test that minimal request works with default seeding_config."""
        request_data = {
            "domain": "example.com"
        }
        
        response = await client.post("/urls/discover", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    async def test_advanced_configuration(self, client):
        """Test advanced configuration options."""
        request_data = {
            "domain": "example.com",
            "seeding_config": {
                "source": "sitemap+cc",
                "pattern": "*/docs/*",
                "extract_head": True,
                "max_urls": 3,
                "live_check": True,
                "concurrency": 50,
                "hits_per_sec": 5,
                "verbose": True
            }
        }
        
        response = await client.post("/urls/discover", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # If URLs are returned, they should have the expected structure
        for url_obj in data:
            assert isinstance(url_obj, dict)
            # Should have at least a URL field
            assert "url" in url_obj
    
    async def test_bm25_scoring_configuration(self, client):
        """Test BM25 relevance scoring configuration."""
        request_data = {
            "domain": "example.com",
            "seeding_config": {
                "source": "sitemap",
                "extract_head": True,  # Required for scoring
                "query": "documentation",
                "scoring_method": "bm25",
                "score_threshold": 0.1,
                "max_urls": 5
            }
        }
        
        response = await client.post("/urls/discover", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # If URLs are returned with scoring, check structure
        for url_obj in data:
            assert isinstance(url_obj, dict)
            assert "url" in url_obj
            # Scoring may or may not add score field depending on implementation
    
    async def test_missing_required_domain_field(self, client):
        """Test error handling when required domain field is missing."""
        request_data = {
            "seeding_config": {
                "source": "sitemap",
                "max_urls": 5
            }
        }
        
        response = await client.post("/urls/discover", json=request_data)
        assert response.status_code == 422  # Validation error
        
        error_data = response.json()
        assert "detail" in error_data
        assert any("domain" in str(error).lower() for error in error_data["detail"])
    
    async def test_invalid_request_body_structure(self, client):
        """Test error handling with completely invalid request body."""
        invalid_request = {
            "invalid_field": "test_value",
            "another_invalid": 123
        }
        
        response = await client.post("/urls/discover", json=invalid_request)
        assert response.status_code == 422  # Validation error
        
        error_data = response.json()
        assert "detail" in error_data
    
    async def test_invalid_seeding_config_parameters(self, client):
        """Test handling of invalid seeding configuration parameters."""
        request_data = {
            "domain": "example.com",
            "seeding_config": {
                "source": "invalid_source",  # Invalid source
                "max_urls": "not_a_number"   # Invalid type
            }
        }
        
        response = await client.post("/urls/discover", json=request_data)
        # The endpoint should handle this gracefully
        # It may return 200 with empty results or 500 with error details
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # May be empty due to invalid config
        else:
            # Should have error details
            error_data = response.json()
            assert "detail" in error_data
    
    async def test_empty_seeding_config(self, client):
        """Test with empty seeding_config object."""
        request_data = {
            "domain": "example.com",
            "seeding_config": {}
        }
        
        response = await client.post("/urls/discover", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    async def test_response_structure_consistency(self, client):
        """Test that response structure is consistent."""
        request_data = {
            "domain": "example.com",
            "seeding_config": {
                "source": "sitemap",
                "max_urls": 1
            }
        }
        
        # Make multiple requests to ensure consistency
        for _ in range(3):
            response = await client.post("/urls/discover", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            
            # If there are results, check they have consistent structure
            for url_obj in data:
                assert isinstance(url_obj, dict)
                assert "url" in url_obj
    
    async def test_content_type_validation(self, client):
        """Test that endpoint requires JSON content type."""
        # Test with wrong content type
        response = await client.post(
            "/urls/discover",
            content="domain=example.com",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422


# Standalone test runner for when pytest is not available
async def run_tests_standalone():
    """Run tests without pytest framework."""
    print("🧪 Running URL Discovery Endpoint Tests")
    print("=" * 50)
    
    # Check server health first
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TEST_TIMEOUT) as client:
        try:
            response = await client.get("/health")
            assert response.status_code == 200
            print("✅ Server health check passed")
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            return False
    
    test_suite = TestURLDiscoveryEndpoint()
    
    # Run tests manually
    tests = [
        ("Endpoint exists", test_suite.test_endpoint_exists),
        ("Basic URL discovery", test_suite.test_basic_url_discovery_happy_path),
        ("Minimal request", test_suite.test_minimal_request_with_defaults),
        ("Advanced configuration", test_suite.test_advanced_configuration),
        ("BM25 scoring", test_suite.test_bm25_scoring_configuration),
        ("Missing domain error", test_suite.test_missing_required_domain_field),
        ("Invalid request body", test_suite.test_invalid_request_body_structure),
        ("Invalid config handling", test_suite.test_invalid_seeding_config_parameters),
        ("Empty config", test_suite.test_empty_seeding_config),
        ("Response consistency", test_suite.test_response_structure_consistency),
        ("Content type validation", test_suite.test_content_type_validation),
    ]
    
    passed = 0
    failed = 0
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TEST_TIMEOUT) as client:
        for test_name, test_func in tests:
            try:
                await test_func(client)
                print(f"✅ {test_name}")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    # Run tests standalone
    success = asyncio.run(run_tests_standalone())
    exit(0 if success else 1)