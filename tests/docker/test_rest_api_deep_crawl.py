# ==== File: test_rest_api_deep_crawl.py ====

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
DEEP_CRAWL_BASE_URL = "https://docs.crawl4ai.com/samples/deepcrawl/"
DEEP_CRAWL_DOMAIN = "docs.crawl4ai.com" # Used for domain filter

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

# --- Test Class ---
@pytest.mark.asyncio
class TestDeepCrawlEndpoints:

    @pytest_asyncio.fixture(autouse=True)
    async def check_health_before_tests(self, async_client: httpx.AsyncClient):
        """Fixture to ensure server is healthy before each test in the class."""
        await check_server_health(async_client)

    # 1. Basic Deep Crawl
    async def test_deep_crawl_basic_bfs(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with limited depth and pages."""
        max_depth = 1
        max_pages = 3 # start_url + 2 more
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS", # Use string value for CacheMode
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            # Minimal filters for basic test
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {
                                            "type": "DomainFilter",
                                            "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 1 # Should be more than just the start URL
        assert len(data["results"]) <= max_pages # Respect max_pages

        found_depth_0 = False
        found_depth_1 = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert DEEP_CRAWL_DOMAIN in result["url"]
            depth = result["metadata"]["depth"]
            assert depth <= max_depth
            if depth == 0: found_depth_0 = True
            if depth == 1: found_depth_1 = True

        assert found_depth_0
        assert found_depth_1

    # 2. Deep Crawl with Filtering
    async def test_deep_crawl_with_filters(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with content type and domain filters."""
        max_depth = 1
        max_pages = 5
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {
                                            "type": "DomainFilter",
                                            "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}
                                        },
                                        {
                                            "type": "ContentTypeFilter",
                                            "params": {"allowed_types": ["text/html"]}
                                        },
                                        # Example: Exclude specific paths using regex
                                        {
                                            "type": "URLPatternFilter",
                                             "params": {
                                                 "patterns": ["*/category-3/*"], # Block category 3
                                                 "reverse": True # Block if match
                                             }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert len(data["results"]) > 0
        assert len(data["results"]) <= max_pages

        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert DEEP_CRAWL_DOMAIN in result["url"]
            assert "category-3" not in result["url"] # Check if filter worked
            assert result["metadata"]["depth"] <= max_depth

    # 3. Deep Crawl with Scoring
    async def test_deep_crawl_with_scoring(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with URL scoring."""
        max_depth = 1
        max_pages = 4
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": { # Keep basic domain filter
                                "type": "FilterChain",
                                "params": { "filters": [{"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}}]}
                            },
                            "url_scorer": { # Add scorer
                                "type": "CompositeScorer",
                                "params": {
                                    "scorers": [
                                        {   # Favor pages with 'product' in the URL
                                            "type": "KeywordRelevanceScorer",
                                            "params": {"keywords": ["product"], "weight": 1.0}
                                        },
                                        {   # Penalize deep paths slightly
                                            "type": "PathDepthScorer",
                                            "params": {"optimal_depth": 2, "weight": -0.2}
                                        }
                                    ]
                                }
                            },
                            # Set a threshold if needed: "score_threshold": 0.1
                        }
                    }
                }
            }
        }
        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert len(data["results"]) > 0
        assert len(data["results"]) <= max_pages

        # Check if results seem biased towards products (harder to assert strictly without knowing exact scores)
        product_urls_found = any("product_" in result["url"] for result in data["results"] if result["metadata"]["depth"] > 0)
        print(f"Product URLs found among depth > 0 results: {product_urls_found}")
        # We expect scoring to prioritize product pages if available within limits
        # assert product_urls_found # This might be too strict depending on site structure and limits

        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["metadata"]["depth"] <= max_depth

    # 4. Deep Crawl with CSS Extraction
    async def test_deep_crawl_with_css_extraction(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl combined with JsonCssExtractionStrategy."""
        max_depth = 6 # Go deep enough to reach product pages
        max_pages = 20
        # Schema to extract product details
        product_schema = {
            "name": "ProductDetails",
            "baseSelector": "div.container", # Base for product page
            "fields": [
                {"name": "product_title", "selector": "h1", "type": "text"},
                {"name": "price", "selector": ".product-price", "type": "text"},
                {"name": "description", "selector": ".product-description p", "type": "text"},
                {"name": "specs", "selector": ".product-specs li", "type": "list", "fields":[
                     {"name": "spec_name", "selector": ".spec-name", "type": "text"},
                     {"name": "spec_value", "selector": ".spec-value", "type": "text"}
                ]}
            ]
        }
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "extraction_strategy": { # Apply extraction to ALL crawled pages
                        "type": "JsonCssExtractionStrategy",
                        "params": {"schema": {"type": "dict", "value": product_schema}}
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": { # Only crawl HTML on our domain
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}},
                                        {"type": "ContentTypeFilter", "params": {"allowed_types": ["text/html"]}}
                                    ]
                                }
                            }
                            # Optional: Add scoring to prioritize product pages for extraction
                        }
                    }
                }
            }
        }
        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert len(data["results"]) > 0
        # assert len(data["results"]) <= max_pages

        found_extracted_product = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert "extracted_content" in result
            if "product_" in result["url"]: # Check product pages specifically
                 assert result["extracted_content"] is not None
                 try:
                     extracted = json.loads(result["extracted_content"])
                     # Schema returns list even if one base match
                     assert isinstance(extracted, list)
                     if extracted:
                         item = extracted[0]
                         assert "product_title" in item and item["product_title"]
                         assert "price" in item and item["price"]
                         # Specs might be empty list if not found
                         assert "specs" in item and isinstance(item["specs"], list)
                         found_extracted_product = True
                         print(f"Extracted product: {item.get('product_title')}")
                 except (json.JSONDecodeError, AssertionError, IndexError) as e:
                      pytest.fail(f"Extraction validation failed for {result['url']}: {e}\nContent: {result['extracted_content']}")
            # else:
            #      # Non-product pages might have None or empty list depending on schema match
            #      assert result["extracted_content"] is None or json.loads(result["extracted_content"]) == []

        assert found_extracted_product, "Did not find any pages where product data was successfully extracted."

    # 5. Deep Crawl with LLM Extraction (Requires Server LLM Setup)
    async def test_deep_crawl_with_llm_extraction(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl combined with LLMExtractionStrategy."""
        max_depth = 1 # Limit depth to keep LLM calls manageable
        max_pages = 3
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "extraction_strategy": { # Apply LLM extraction to crawled pages
                        "type": "LLMExtractionStrategy",
                        "params": {
                            "instruction": "Extract the main H1 title and the text content of the first paragraph.",
                            "llm_config": { # Example override, rely on server default if possible
                               "type": "LLMConfig",
                               "params": {"provider": "openai/gpt-4.1-mini"} # Use a cheaper model for testing
                            },
                             "schema": { # Expected JSON output
                                "type": "dict",
                                "value": {
                                    "title": "PageContent", "type": "object",
                                    "properties": {
                                        "h1_title": {"type": "string"},
                                        "first_paragraph": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}},
                                        {"type": "ContentTypeFilter", "params": {"allowed_types": ["text/html"]}}
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }

        try:
            response = await async_client.post("/crawl", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            pytest.fail(f"Deep Crawl + LLM extraction request failed: {e}. Response: {e.response.text}. Check server logs and LLM API key setup.")
        except httpx.RequestError as e:
             pytest.fail(f"Deep Crawl + LLM extraction request failed: {e}.")


        assert data["success"] is True
        assert len(data["results"]) > 0
        assert len(data["results"]) <= max_pages

        found_llm_extraction = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert "extracted_content" in result
            assert result["extracted_content"] is not None
            try:
                extracted = json.loads(result["extracted_content"])
                if isinstance(extracted, list): extracted = extracted[0] # Handle list output
                assert isinstance(extracted, dict)
                assert "h1_title" in extracted # Check keys based on schema
                assert "first_paragraph" in extracted
                found_llm_extraction = True
                print(f"LLM extracted from {result['url']}: Title='{extracted.get('h1_title')}'")
            except (json.JSONDecodeError, AssertionError, IndexError, TypeError) as e:
                pytest.fail(f"LLM extraction validation failed for {result['url']}: {e}\nContent: {result['extracted_content']}")

        assert found_llm_extraction, "LLM extraction did not yield expected data on any crawled page."


    # 6. Deep Crawl with SSL Certificate Fetching
    async def test_deep_crawl_with_ssl(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with fetch_ssl_certificate enabled."""
        max_depth = 0 # Only fetch for start URL to keep test fast
        max_pages = 1
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "fetch_ssl_certificate": True, # <-- Enable SSL fetching
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                        }
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

        await assert_crawl_result_structure(result, check_ssl=True) # <-- Tell helper to check SSL field
        assert result["success"] is True
                # Check if SSL info was actually retrieved
        if result["ssl_certificate"]:
            # Assert directly using dictionary keys
            assert isinstance(result["ssl_certificate"], dict) # Verify it's a dict
            assert "issuer" in result["ssl_certificate"]
            assert "subject" in result["ssl_certificate"]
            # --- MODIFIED ASSERTIONS ---
            assert "not_before" in result["ssl_certificate"] # Check for the actual key
            assert "not_after" in result["ssl_certificate"]  # Check for the actual key
            # --- END MODIFICATIONS ---
            assert "fingerprint" in result["ssl_certificate"] # Check another key

            # This print statement using .get() already works correctly with dictionaries
            print(f"SSL Issuer Org: {result['ssl_certificate'].get('issuer', {}).get('O', 'N/A')}")
            print(f"SSL Valid From: {result['ssl_certificate'].get('not_before', 'N/A')}")
        else:
            # This part remains the same
            print("SSL Certificate was null in the result.")


    # 7. Deep Crawl with Proxy Rotation (Requires PROXIES env var)
    async def test_deep_crawl_with_proxies(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl using proxy rotation."""
        proxies = load_proxies_from_env()
        if not proxies:
            pytest.skip("Skipping proxy test: PROXIES environment variable not set or empty.")

        print(f"\nTesting with {len(proxies)} proxies loaded from environment.")

        max_depth = 1
        max_pages = 3
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL], # Use the dummy site
             # Use a BrowserConfig that *might* pick up proxy if set, but rely on CrawlerRunConfig
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "proxy_rotation_strategy": { # <-- Define the strategy
                        "type": "RoundRobinProxyStrategy",
                        "params": {
                             # Convert ProxyConfig dicts back to the serialized format expected by server
                             "proxies": [{"type": "ProxyConfig", "params": p} for p in proxies]
                        }
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": { "filters": [{"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}}]}
                            }
                        }
                    }
                }
            }
        }
        try:
            response = await async_client.post("/crawl", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            # Proxies often cause connection errors, catch them
            pytest.fail(f"Proxy deep crawl failed: {e}. Response: {e.response.text}. Are proxies valid and accessible by the server?")
        except httpx.RequestError as e:
             pytest.fail(f"Proxy deep crawl request failed: {e}. Are proxies valid and accessible?")

        assert data["success"] is True
        assert len(data["results"]) > 0
        assert len(data["results"]) <= max_pages
        # Primary assertion is that the crawl succeeded *with* proxy config
        print(f"Proxy deep crawl completed successfully for {len(data['results'])} pages.")

        # Verifying specific proxy usage requires server logs or custom headers/responses


# --- Main Execution Block (for running script directly) ---
if __name__ == "__main__":
    pytest_args = ["-v", "-s", __file__]
    # Example: Run only proxy test
    # pytest_args.append("-k test_deep_crawl_with_proxies")
    print(f"Running pytest with args: {pytest_args}")
    exit_code = pytest.main(pytest_args)
    print(f"Pytest finished with exit code: {exit_code}")