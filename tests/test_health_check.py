import pytest
import asyncio
from crawl4ai import AsyncWebCrawler


class TestHealthCheck:
    """Test cases for the health_check method"""

    @pytest.mark.asyncio
    async def test_health_check_accessible_url(self):
        """Test health check with an accessible URL"""
        async with AsyncWebCrawler() as crawler:
            # Use verify_ssl=False for better test environment compatibility
            result = await crawler.health_check("https://httpbin.org/get", verify_ssl=False)
            
            assert isinstance(result, dict)
            assert "accessible" in result
            assert "status_code" in result
            assert "response_time_ms" in result
            assert "final_url" in result
            assert "redirected" in result
            
            # Should be accessible
            assert result["accessible"] is True
            assert result["status_code"] == 200
            assert result["response_time_ms"] > 0
            assert "httpbin.org" in result["final_url"]

    @pytest.mark.asyncio
    async def test_health_check_with_redirect(self):
        """Test health check with a URL that redirects"""
        async with AsyncWebCrawler() as crawler:
            # httpbin.org/redirect/1 redirects to /get
            result = await crawler.health_check("https://httpbin.org/redirect/1")
            
            assert result["accessible"] is True
            assert result["redirected"] is True
            assert result["final_url"] != "https://httpbin.org/redirect/1"
            assert "/get" in result["final_url"]

    @pytest.mark.asyncio
    async def test_health_check_not_found(self):
        """Test health check with a 404 URL"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.health_check("https://httpbin.org/status/404")
            
            assert result["accessible"] is False
            assert result["status_code"] == 404
            assert "error" not in result  # 404 is a valid response, not an error

    @pytest.mark.asyncio
    async def test_health_check_invalid_domain(self):
        """Test health check with an invalid domain"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.health_check("https://invalid-domain-that-does-not-exist.com")
            
            assert result["accessible"] is False
            assert result["status_code"] is None
            assert "error" in result
            assert "error_type" in result
            assert result["response_time_ms"] > 0

    @pytest.mark.asyncio 
    async def test_health_check_timeout(self):
        """Test health check with a very short timeout"""
        async with AsyncWebCrawler() as crawler:
            # Use a very short timeout to force timeout error
            result = await crawler.health_check("https://httpbin.org/delay/10", timeout=1.0)
            
            assert result["accessible"] is False
            assert result["status_code"] is None
            assert "timed out" in result["error"].lower()
            assert result["error_type"] == "TimeoutError"

    @pytest.mark.asyncio
    async def test_health_check_result_structure(self):
        """Test that health check result has the expected structure"""
        async with AsyncWebCrawler() as crawler:
            result = await crawler.health_check("https://httpbin.org/get")
            
            # Check required fields are present
            required_fields = [
                "accessible", "status_code", "response_time_ms", 
                "content_type", "final_url", "redirected"
            ]
            
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
                
            # Check data types
            assert isinstance(result["accessible"], bool)
            assert isinstance(result["response_time_ms"], (int, float))
            assert isinstance(result["final_url"], str)
            assert isinstance(result["redirected"], bool)
            
            if result["accessible"]:
                assert isinstance(result["status_code"], int)
            else:
                # May be None for network errors
                assert result["status_code"] is None or isinstance(result["status_code"], int)


if __name__ == "__main__":
    # Run a simple test if this file is executed directly
    async def quick_test():
        async with AsyncWebCrawler() as crawler:
            print("Testing health check with httpbin.org...")
            result = await crawler.health_check("https://httpbin.org/get")
            print(f"Result: {result}")
            
            print("\nTesting health check with redirect...")
            result = await crawler.health_check("https://httpbin.org/redirect/1")
            print(f"Result: {result}")

    asyncio.run(quick_test())
