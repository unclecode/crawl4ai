# ==== File: test_rest_api_pdf_crawl.py ====

import pytest
import pytest_asyncio
import httpx
import json
import asyncio
import os
from typing import List, Dict, Any, AsyncGenerator

from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file if present

# --- Test Configuration ---
BASE_URL = os.getenv("CRAWL4AI_TEST_URL", "http://localhost:11235") # If server is running in Docker, use the host's IP
BASE_URL = os.getenv("CRAWL4AI_TEST_URL", "http://localhost:8020") # If server is running in dev debug mode
PDF_TEST_URL = "https://arxiv.org/pdf/2310.06825"
PDF_TEST_INVALID_URL = "https://docs.crawl4ai.com/samples/deepcrawl/"

# --- Helper Functions ---
def load_proxies_from_env() -> List[Dict]:
    """Load proxies from PROXIES environment variable"""
    proxies = []
    proxies_str = os.getenv("PROXIES", "")
    if not proxies_str:
        print("PROXIES environment variable not set or empty.")
        return proxies
    try:
        proxy_list = proxies_str.split(",")
        for proxy in proxy_list:
            proxy = proxy.strip()
            if not proxy:
                continue
            parts = proxy.split(":")
            if len(parts) == 4:
                ip, port, username, password = parts
                proxies.append({
                    "server": f"http://{ip}:{port}", # Assuming http, adjust if needed
                    "username": username,
                    "password": password,
                    "ip": ip  # Store original IP if available
                })
            elif len(parts) == 2: # ip:port only
                 ip, port = parts
                 proxies.append({
                    "server": f"http://{ip}:{port}",
                    "ip": ip
                 })
            else:
                 print(f"Skipping invalid proxy string format: {proxy}")

    except Exception as e:
        print(f"Error loading proxies from environment: {e}")
    return proxies


async def check_server_health(client: httpx.AsyncClient):
    """Check if the server is healthy before running tests."""
    try:
        response = await client.get("/health")
        response.raise_for_status()
        print(f"\nServer healthy: {response.json()}")
        return True
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        pytest.fail(f"Server health check failed: {e}. Is the server running at {BASE_URL}?", pytrace=False)

async def assert_crawl_result_structure(result: Dict[str, Any], check_ssl=False):
    """Asserts the basic structure of a single crawl result."""
    assert isinstance(result, dict)
    assert "url" in result
    assert "success" in result
    assert "html" in result # Basic crawls should return HTML
    assert "metadata" in result
    assert isinstance(result["metadata"], dict)
    assert "depth" in result["metadata"] # Deep crawls add depth

    if check_ssl:
        assert "ssl_certificate" in result # Check if SSL info is present
        assert isinstance(result["ssl_certificate"], dict) or result["ssl_certificate"] is None


async def process_streaming_response(response: httpx.Response) -> List[Dict[str, Any]]:
    """Processes an NDJSON streaming response."""
    results = []
    completed = False
    async for line in response.aiter_lines():
        if line:
            try:
                data = json.loads(line)
                if data.get("status") == "completed":
                    completed = True
                    break # Stop processing after completion marker
                elif data.get("url"): # Ensure it looks like a result object
                    results.append(data)
                else:
                    print(f"Received non-result JSON line: {data}") # Log other status messages if needed
            except json.JSONDecodeError:
                pytest.fail(f"Failed to decode JSON line: {line}")
    assert completed, "Streaming response did not end with a completion marker."
    return results


# --- Pytest Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an async HTTP client"""
    # Increased timeout for potentially longer deep crawls
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=300.0) as client:
        yield client
    # No explicit close needed with 'async with'

# --- Test Class for PDF Scraping ---
@pytest.mark.asyncio
class TestPdfScraping:

    @pytest_asyncio.fixture(autouse=True)
    async def check_health_before_tests(self, async_client: httpx.AsyncClient):
        """Fixture to ensure server is healthy before each test in the class."""
        await check_server_health(async_client)

    async def test_pdf_scraping_basic(self, async_client: httpx.AsyncClient):
        """Test basic PDF scraping for a single PDF URL."""
        payload = {
            "urls": [PDF_TEST_URL],  # URL of a test PDF
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "scraping_strategy": {
                        "type": "PdfScrapingStrategy",  # Custom PDF scraping strategy
                        "params": {}
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {"max_depth": 0, "max_pages": 1}
                    }
                }
            }
        }

        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert len(data["results"]) == 1

        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "extracted_content" in result
        assert result["extracted_content"] is not None

        extracted_text = result["extracted_content"].get("text", "")
        assert isinstance(extracted_text, str)
        assert len(extracted_text) > 0

    async def test_pdf_scraping_with_metadata(self, async_client: httpx.AsyncClient):
        """Test PDF scraping with metadata extraction."""
        payload = {
            "urls": [PDF_TEST_URL],
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "scraping_strategy": {
                        "type": "PdfScrapingStrategy",
                        "params": {"extract_metadata": True}
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {"max_depth": 0, "max_pages": 1}
                    }
                }
            }
        }

        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        result = data["results"][0]
        assert "extracted_content" in result
        metadata = result["extracted_content"].get("metadata", {})
        assert isinstance(metadata, dict)

        assert "title" in metadata or "author" in metadata

    async def test_pdf_scraping_non_accessible(self, async_client: httpx.AsyncClient):
        """Test PDF scraping when PDF is not accessible."""
        payload = {
            "urls": [PDF_TEST_INVALID_URL],
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "scraping_strategy": {
                        "type": "PdfScrapingStrategy",
                        "params": {}
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {"max_depth": 0, "max_pages": 1}
                    }
                }
            }
        }

        response = await async_client.post("/crawl", json=payload)

        data = response.json()
        assert data["success"] is True
        result = data["results"][0]
        assert result["success"] is False
        assert "extracted_content" not in result or result["extracted_content"] is None


# --- Main Execution Block (for running script directly) ---
if __name__ == "__main__":
    pytest_args = ["-v", "-s", __file__]
    # Example: Run only proxy test
    # pytest_args.append("-k test_deep_crawl_with_proxies")
    print(f"Running pytest with args: {pytest_args}")
    exit_code = pytest.main(pytest_args)
    print(f"Pytest finished with exit code: {exit_code}")