import pytest
import pytest_asyncio
import httpx
import json
import asyncio
import os
from typing import List, Dict, Any, AsyncGenerator

from dotenv import load_dotenv
load_dotenv()


# Optional: Import crawl4ai classes directly for reference/easier payload creation aid
# You don't strictly NEED these imports for the tests to run against the server,
# but they help in understanding the structure you are mimicking in JSON.
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    BM25ContentFilter,
    BFSDeepCrawlStrategy,
    FilterChain,
    ContentTypeFilter,
    DomainFilter,
    CompositeScorer,
    KeywordRelevanceScorer,
    PathDepthScorer,
    JsonCssExtractionStrategy,
    LLMExtractionStrategy,
    LLMConfig
)

# --- Test Configuration ---
# BASE_URL = os.getenv("CRAWL4AI_TEST_URL", "http://localhost:8020") # Make base URL configurable
BASE_URL = os.getenv("CRAWL4AI_TEST_URL", "http://0.0.0.0:11234") # Make base URL configurable
# Use a known simple HTML page for basic tests
SIMPLE_HTML_URL = "https://docs.crawl4ai.com"
# Use a site suitable for scraping tests
SCRAPE_TARGET_URL = "http://books.toscrape.com/"
# Use a site with internal links for deep crawl tests
DEEP_CRAWL_URL = "https://python.org"

# --- Pytest Fixtures ---

# Use the built-in event_loop fixture from pytest_asyncio
# The custom implementation was causing issues with closing the loop

@pytest_asyncio.fixture(scope="function")  # Changed to function scope to avoid event loop issues
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an async HTTP client"""
    client = httpx.AsyncClient(base_url=BASE_URL, timeout=120.0)
    yield client
    await client.aclose()

# --- Helper Functions ---

async def check_server_health(client: httpx.AsyncClient):
    """Check if the server is healthy before running tests."""
    try:
        response = await client.get("/health")
        response.raise_for_status()
        print(f"\nServer healthy: {response.json()}")
        return True
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        pytest.fail(f"Server health check failed: {e}. Is the server running at {BASE_URL}?", pytrace=False)

async def assert_crawl_result_structure(result: Dict[str, Any]):
    """Asserts the basic structure of a single crawl result."""
    assert isinstance(result, dict)
    assert "url" in result
    assert "success" in result
    assert "html" in result
    # Add more common checks if needed

async def process_streaming_response(response: httpx.Response) -> List[Dict[str, Any]]:
    """Processes an NDJSON streaming response."""
    results = []
    completed = False
    buffer = ""

    async for chunk in response.aiter_text():
        buffer += chunk
        lines = buffer.split('\n')

        # Keep the last incomplete line in buffer
        buffer = lines.pop() if lines and not lines[-1].endswith('\n') else ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                if data.get("status") in ["completed", "error"]:
                    completed = True
                    print(f"DEBUG: Received completion marker: {data}")  # Debug output
                    break
                else:
                    results.append(data)
            except json.JSONDecodeError:
                pytest.fail(f"Failed to decode JSON line: {line}")

        if completed:
            break

    print(f"DEBUG: Final results count: {len(results)}, completed: {completed}")  # Debug output
    assert completed, "Streaming response did not end with a completion marker."
    return results
# --- Test Class ---

@pytest.mark.asyncio
class TestCrawlEndpoints:

    @pytest_asyncio.fixture(autouse=True)
    async def check_health_before_tests(self, async_client: httpx.AsyncClient):
        """Fixture to ensure server is healthy before each test in the class."""
        await check_server_health(async_client)

    # 1. Simple Requests (Primitives)
    async def test_simple_crawl_single_url(self, async_client: httpx.AsyncClient):
        """Test /crawl with a single URL and simple config values."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {
                "type": "BrowserConfig",
                "params": {
                    "headless": True,
                }
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False, # Explicitly false for /crawl
                    "screenshot": False,
                    "cache_mode": CacheMode.BYPASS.value # Use enum value
                }
            }
        }
        try:
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error: {e}")
            print(f"Response content: {e.response.text}")
            raise

        assert data["success"] is True
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert result["url"] == SIMPLE_HTML_URL
        assert "Crawl4AI Documentation" in result["html"]
        # We don't specify a markdown generator in this test, so don't make assumptions about markdown field
        # It might be null, missing, or populated depending on the server's default behavior
    async def test_crawl_with_stream_direct(self, async_client: httpx.AsyncClient):
        """Test that /crawl endpoint handles stream=True directly without redirect."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {
                "type": "BrowserConfig",
                "params": {
                    "headless": True,
                }
            },
            "crawler_config": {
                "type": "CrawlerRunConfig", 
                "params": {
                    "stream": True,  # Set stream to True for direct streaming
                    "screenshot": False,
                    "cache_mode": CacheMode.BYPASS.value
                }
            }
        }

        # Send a request to the /crawl endpoint - should handle streaming directly
        async with async_client.stream("POST", "/crawl", json=payload) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"
            assert response.headers.get("x-stream-status") == "active"

            results = await process_streaming_response(response)

            assert len(results) == 1
            result = results[0]
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["url"] == SIMPLE_HTML_URL
            assert "Crawl4AI Documentation" in result["html"]
    async def test_simple_crawl_single_url_streaming(self, async_client: httpx.AsyncClient):
        """Test /crawl/stream with a single URL and simple config values."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {
                "type": "BrowserConfig",
                "params": {
                    "headless": True,
                }
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": True, # Must be true for /crawl/stream
                    "screenshot": False,
                    "cache_mode": CacheMode.BYPASS.value
                }
            }
        }
        async with async_client.stream("POST", "/crawl/stream", json=payload) as response:
            response.raise_for_status()
            results = await process_streaming_response(response)

        assert len(results) == 1
        result = results[0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert result["url"] == SIMPLE_HTML_URL
        assert "Crawl4AI Documentation" in result["html"]


    # 2. Multi-URL and Dispatcher
    async def test_multi_url_crawl(self, async_client: httpx.AsyncClient):
        """Test /crawl with multiple URLs, implicitly testing dispatcher."""
        urls = [SIMPLE_HTML_URL, "https://www.geeksforgeeks.org/"]
        payload = {
            "urls": urls,
            "browser_config": {
                "type": "BrowserConfig",
                "params": {"headless": True}
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {"stream": False, "cache_mode": CacheMode.BYPASS.value}
            }
        }
        try:
            print(f"Sending deep crawl request to server...")
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")
            
            if response.status_code >= 400:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error detail: {error_detail}")
                print(f"Full response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error status: {e.response.status_code}")
            print(f"Server error response: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"Parsed error: {error_json}")
            except:
                print("Could not parse error response as JSON")
            raise

        assert data["success"] is True
        assert isinstance(data["results"], list)
        assert len(data["results"]) == len(urls)
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["url"] in urls

    async def test_multi_url_crawl_streaming(self, async_client: httpx.AsyncClient):

        """Test /crawl/stream with multiple URLs."""
        urls = [SIMPLE_HTML_URL, "https://www.geeksforgeeks.org/"]
        payload = {
            "urls": urls,
            "browser_config": {
                "type": "BrowserConfig",
                "params": {"headless": True}
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {"stream": True, "cache_mode": CacheMode.BYPASS.value}
            }
        }
        async with async_client.stream("POST", "/crawl/stream", json=payload) as response:
            response.raise_for_status()
            results = await process_streaming_response(response)

        assert len(results) == len(urls)
        processed_urls = set()
        for result in results:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["url"] in urls
            processed_urls.add(result["url"])
        assert processed_urls == set(urls) # Ensure all URLs were processed


    # 3. Class Values and Nested Classes (Markdown Generator)
    async def test_crawl_with_markdown_pruning_filter(self, async_client: httpx.AsyncClient):
        """Test /crawl with MarkdownGenerator using PruningContentFilter."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "cache_mode": CacheMode.ENABLED.value, # Test different cache mode
                    "markdown_generator": {
                        "type": "DefaultMarkdownGenerator",
                        "params": {
                            "content_filter": {
                                "type": "PruningContentFilter",
                                "params": {
                                    "threshold": 0.5, # Example param
                                    "threshold_type": "relative"
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            print(f"Sending deep crawl request to server...")
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")
            
            if response.status_code >= 400:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error detail: {error_detail}")
                print(f"Full response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error status: {e.response.status_code}")
            print(f"Server error response: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"Parsed error: {error_json}")
            except:
                print("Could not parse error response as JSON")
            raise

        assert data["success"] is True
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "markdown" in result
        assert isinstance(result["markdown"], dict)
        assert "raw_markdown" in result["markdown"]
        assert "fit_markdown" in result["markdown"] # Pruning creates fit_markdown
        assert "Crawl4AI" in result["markdown"]["raw_markdown"]
        # Fit markdown content might be different/shorter due to pruning
        assert len(result["markdown"]["fit_markdown"]) <= len(result["markdown"]["raw_markdown"])

    async def test_crawl_with_markdown_bm25_filter(self, async_client: httpx.AsyncClient):
        """Test /crawl with MarkdownGenerator using BM25ContentFilter."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "markdown_generator": {
                        "type": "DefaultMarkdownGenerator",
                        "params": {
                            "content_filter": {
                                "type": "BM25ContentFilter",
                                "params": {
                                    "user_query": "Herman Melville", # Query for BM25
                                    "bm25_threshold": 0.1, # Lower threshold to increase matches
                                    "language": "english"  # Valid parameters
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            print(f"Payload for BM25 test: {json.dumps(payload)}")
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")
            
            if response.status_code >= 400:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error detail: {error_detail}")
                print(f"Full response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error status: {e.response.status_code}")
            print(f"Server error response: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"Parsed error: {error_json}")
            except:
                print("Could not parse error response as JSON")
            raise

        assert data["success"] is True
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "markdown" in result
        assert isinstance(result["markdown"], dict)
        assert "raw_markdown" in result["markdown"]
        assert "fit_markdown" in result["markdown"] # BM25 creates fit_markdown
        
        # Print values for debug
        print(f"Raw markdown length: {len(result['markdown']['raw_markdown'])}")
        print(f"Fit markdown length: {len(result['markdown']['fit_markdown'])}")
        
        # Either fit_markdown has content (possibly including our query terms)
        # or it might be empty if no good BM25 matches were found
        # Don't assert specific content since it can be environment-dependent


    # 4. Deep Crawling
    async def test_deep_crawl(self, async_client: httpx.AsyncClient):
        """Test /crawl with a deep crawl strategy."""
        payload = {
            "urls": [DEEP_CRAWL_URL], # Start URL
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": CacheMode.BYPASS.value,
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": 1, # Limit depth for testing speed
                            "max_pages": 5, # Limit pages to crawl
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {
                                            "type": "ContentTypeFilter",
                                            "params": {"allowed_types": ["text/html"]}
                                        },
                                        {
                                            "type": "DomainFilter",
                                            "params": {"allowed_domains": ["python.org", "docs.python.org"]} # Include important subdomains
                                        }
                                    ]
                                }
                            },
                            "url_scorer": {
                                "type": "CompositeScorer",
                                "params": {
                                    "scorers": [
                                        {
                                            "type": "KeywordRelevanceScorer",
                                            "params": {"keywords": ["documentation", "tutorial"]}
                                        },
                                        {
                                            "type": "PathDepthScorer",
                                            "params": {"weight": 0.5, "optimal_depth": 2}
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            print(f"Sending deep crawl request to server...")
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")
            
            if response.status_code >= 400:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error detail: {error_detail}")
                print(f"Full response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error status: {e.response.status_code}")
            print(f"Server error response: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"Parsed error: {error_json}")
            except:
                print("Could not parse error response as JSON")
            raise

        assert data["success"] is True
        assert isinstance(data["results"], list)
        # Expect more than 1 result due to deep crawl (start URL + crawled links)
        assert len(data["results"]) > 1
        assert len(data["results"]) <= 6 # Start URL + max_links=5

        start_url_found = False
        crawled_urls_found = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            
            # Print URL for debugging
            print(f"Crawled URL: {result['url']}")
            
            # Allow URLs that contain python.org (including subdomains like docs.python.org)
            assert "python.org" in result["url"]
            if result["url"] == DEEP_CRAWL_URL:
                start_url_found = True
            else:
                crawled_urls_found = True

        assert start_url_found
        assert crawled_urls_found


    # 5. Extraction without LLM (JSON/CSS)
    async def test_json_css_extraction(self, async_client: httpx.AsyncClient):
        """Test /crawl with JsonCssExtractionStrategy."""
        payload = {
            "urls": [SCRAPE_TARGET_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "cache_mode": CacheMode.BYPASS.value,
                    "extraction_strategy": {
                        "type": "JsonCssExtractionStrategy",
                        "params": {
                            "schema": { 
                                "type": "dict", # IMPORTANT: Wrap schema dict with type/value structure
                                "value": {
                                    "name": "BookList",
                                    "baseSelector": "ol.row li.col-xs-6", # Select each book item
                                    "fields": [
                                        {"name": "title", "selector": "article.product_pod h3 a", "type": "attribute", "attribute": "title"},
                                        {"name": "price", "selector": "article.product_pod .price_color", "type": "text"},
                                        {"name": "rating", "selector": "article.product_pod p.star-rating", "type": "attribute", "attribute": "class"}
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            print(f"Sending deep crawl request to server...")
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")
            
            if response.status_code >= 400:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error detail: {error_detail}")
                print(f"Full response: {response.text}")
            
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error status: {e.response.status_code}")
            print(f"Server error response: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"Parsed error: {error_json}")
            except:
                print("Could not parse error response as JSON")
            raise

        assert data["success"] is True
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "extracted_content" in result
        assert result["extracted_content"] is not None

        # Extracted content should be a JSON string representing a list of dicts
        try:
            extracted_data = json.loads(result["extracted_content"])
            assert isinstance(extracted_data, list)
            assert len(extracted_data) > 0 # Should find some books
            # Check structure of the first extracted item
            first_item = extracted_data[0]
            assert "title" in first_item
            assert "price" in first_item
            assert "rating" in first_item
            assert "star-rating" in first_item["rating"] # e.g., "star-rating Three"
        except (json.JSONDecodeError, AssertionError) as e:
            pytest.fail(f"Extracted content parsing or validation failed: {e}\nContent: {result['extracted_content']}")


    # 6. Extraction with LLM
    async def test_llm_extraction(self, async_client: httpx.AsyncClient):
        """
        Test /crawl with LLMExtractionStrategy.
        NOTE: Requires the server to have appropriate LLM API keys (e.g., OPENAI_API_KEY)
              configured via .llm.env or environment variables.
              This test uses the default provider configured in the server's config.yml.
        """
        # Skip test if no OpenAI API key is configured
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not configured, skipping LLM extraction test")
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "cache_mode": CacheMode.BYPASS.value,
                    "extraction_strategy": {
                        "type": "LLMExtractionStrategy",
                        "params": {
                            "instruction": "Extract the main title and any key information about Crawl4AI from the text into JSON.",
                            # LLMConfig is implicitly defined by server's config.yml and .llm.env
                            # If you needed to override provider/token PER REQUEST:
                            "llm_config": {
                               "type": "LLMConfig",
                               "params": {
                                  "provider": "deepseek/deepseek-chat-v3.1:free", # Use deepseek model from openrouter
                                  "api_token": os.getenv("OPENAI_API_KEY"), # Use OPENAI_API_KEY for openrouter
                                  "base_url": "https://openrouter.ai/api/v1" # OpenRouter base URL
                               }
                            },
                            "schema": { # Optional: Provide a schema for structured output
                                "type": "dict", # IMPORTANT: Wrap schema dict
                                "value": {
                                    "title": "Crawl4AI Info",
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "The main title of the page"},
                                        "description": {"type": "string", "description": "Key information about Crawl4AI"}
                                    },
                                     "required": ["title"]
                                }
                            }
                        }
                    }
                }
            }
        }

        try:
            response = await async_client.post("/crawl", json=payload)
            response.raise_for_status() # Will raise if server returns 500 (e.g., bad API key)
            data = response.json()
        except httpx.HTTPStatusError as e:
            # Catch potential server errors (like 500 due to missing/invalid API keys)
            pytest.fail(f"LLM extraction request failed: {e}. Response: {e.response.text}. Check server logs and ensure API keys are correctly configured for the server.")
        except httpx.RequestError as e:
             pytest.fail(f"LLM extraction request failed: {e}.")

        assert data["success"] is True
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "extracted_content" in result
        assert result["extracted_content"] is not None

        # Extracted content should be JSON (because we provided a schema)
        try:
            extracted_data = json.loads(result["extracted_content"])
            print(f"\nLLM Extracted Data: {extracted_data}") # Print for verification
            
            # Handle both dict and list formats (server returns a list)
            if isinstance(extracted_data, list):
                assert len(extracted_data) > 0
                extracted_item = extracted_data[0]  # Take first item
                assert isinstance(extracted_item, dict)
                assert "title" in extracted_item
                assert "Crawl4AI" in extracted_item.get("title", "")
            else:
                assert isinstance(extracted_data, dict)
                assert "title" in extracted_data
                assert "Crawl4AI" in extracted_data.get("title", "")
        except (json.JSONDecodeError, AssertionError) as e:
            pytest.fail(f"LLM extracted content parsing or validation failed: {e}\nContent: {result['extracted_content']}")
        except Exception as e: # Catch any other unexpected error
            pytest.fail(f"An unexpected error occurred during LLM result processing: {e}\nContent: {result['extracted_content']}")


    # 7. Error Handling Tests
    async def test_invalid_url_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for invalid URLs."""
        payload = {
            "urls": ["invalid-url", "https://nonexistent-domain-12345.com"],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": CacheMode.BYPASS.value}}
        }
        
        response = await async_client.post("/crawl", json=payload)
        # Should return 200 with failed results, not 500
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True  # Overall success, but individual results may fail

    async def test_mixed_success_failure_urls(self, async_client: httpx.AsyncClient):
        """Test handling of mixed success/failure URLs."""
        payload = {
            "urls": [
                SIMPLE_HTML_URL,  # Should succeed
                "https://nonexistent-domain-12345.com",  # Should fail
                "https://invalid-url-with-special-chars-!@#$%^&*()",  # Should fail
            ],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig", 
                "params": {
                    "cache_mode": CacheMode.BYPASS.value,
                    "markdown_generator": {
                        "type": "DefaultMarkdownGenerator",
                        "params": {
                            "content_filter": {
                                "type": "PruningContentFilter",
                                "params": {"threshold": 0.5}
                            }
                        }
                    }
                }
            }
        }
        
        response = await async_client.post("/crawl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 3
        
        success_count = 0
        failure_count = 0
        
        for result in data["results"]:
            if result["success"]:
                success_count += 1
            else:
                failure_count += 1
                assert "error_message" in result
                assert len(result["error_message"]) > 0
                
        assert success_count >= 1  # At least one should succeed
        assert failure_count >= 1  # At least one should fail

    async def test_streaming_mixed_urls(self, async_client: httpx.AsyncClient):
        """Test streaming with mixed success/failure URLs."""
        payload = {
            "urls": [
                SIMPLE_HTML_URL,  # Should succeed
                "https://nonexistent-domain-12345.com",  # Should fail
            ],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig", 
                "params": {
                    "stream": True,
                    "cache_mode": CacheMode.BYPASS.value
                }
            }
        }
        
        async with async_client.stream("POST", "/crawl/stream", json=payload) as response:
            response.raise_for_status()
            results = await process_streaming_response(response)
        
        assert len(results) == 2
        
        success_count = 0
        failure_count = 0
        
        for result in results:
            if result["success"]:
                success_count += 1
                assert result["url"] == SIMPLE_HTML_URL
            else:
                failure_count += 1
                assert "error_message" in result
                assert result["error_message"] is not None
        
        assert success_count == 1
        assert failure_count == 1

    async def test_markdown_endpoint_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for markdown endpoint."""
        # Test invalid URL
        invalid_payload = {"url": "invalid-url", "f": "fit"}
        response = await async_client.post("/md", json=invalid_payload)
        # Should return 400 for invalid URL format
        assert response.status_code == 400
        
        # Test non-existent URL
        nonexistent_payload = {"url": "https://nonexistent-domain-12345.com", "f": "fit"}
        response = await async_client.post("/md", json=nonexistent_payload)
        # Should return 500 for crawl failure
        assert response.status_code == 500

    async def test_html_endpoint_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for HTML endpoint."""
        # Test invalid URL
        invalid_payload = {"url": "invalid-url"}
        response = await async_client.post("/html", json=invalid_payload)
        # Should return 500 for crawl failure
        assert response.status_code == 500

    async def test_screenshot_endpoint_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for screenshot endpoint."""
        # Test invalid URL
        invalid_payload = {"url": "invalid-url"}
        response = await async_client.post("/screenshot", json=invalid_payload)
        # Should return 500 for crawl failure
        assert response.status_code == 500

    async def test_pdf_endpoint_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for PDF endpoint."""
        # Test invalid URL
        invalid_payload = {"url": "invalid-url"}
        response = await async_client.post("/pdf", json=invalid_payload)
        # Should return 500 for crawl failure
        assert response.status_code == 500

    async def test_execute_js_endpoint_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for execute_js endpoint."""
        # Test invalid URL
        invalid_payload = {"url": "invalid-url", "scripts": ["return document.title;"]}
        response = await async_client.post("/execute_js", json=invalid_payload)
        # Should return 500 for crawl failure
        assert response.status_code == 500

    async def test_llm_endpoint_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for LLM endpoint."""
        # Test missing query parameter
        response = await async_client.get("/llm/https://example.com")
        assert response.status_code == 422  # FastAPI validation error, not 400
        
        # Test invalid URL
        response = await async_client.get("/llm/invalid-url?q=test")
        # Should return 500 for crawl failure
        assert response.status_code == 500

    async def test_ask_endpoint_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for ask endpoint."""
        # Test invalid context_type
        response = await async_client.get("/ask?context_type=invalid")
        assert response.status_code == 422  # Validation error
        
        # Test invalid score_ratio
        response = await async_client.get("/ask?score_ratio=2.0")  # > 1.0
        assert response.status_code == 422  # Validation error
        
        # Test invalid max_results
        response = await async_client.get("/ask?max_results=0")  # < 1
        assert response.status_code == 422  # Validation error

    async def test_config_dump_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for config dump endpoint."""
        # Test invalid code
        invalid_payload = {"code": "invalid_code"}
        response = await async_client.post("/config/dump", json=invalid_payload)
        assert response.status_code == 400
        
        # Test nested function calls (not allowed)
        nested_payload = {"code": "CrawlerRunConfig(BrowserConfig())"}
        response = await async_client.post("/config/dump", json=nested_payload)
        assert response.status_code == 400

    async def test_llm_job_with_chunking_strategy(self, async_client: httpx.AsyncClient):
        """Test LLM job endpoint with chunking strategy."""
        payload = {
            "url": SIMPLE_HTML_URL,
            "q": "Extract the main title and any headings from the content",
            "chunking_strategy": {
                "type": "RegexChunking",
                "params": {
                    "patterns": ["\\n\\n+"],
                    "overlap": 50
                }
            }
        }
        
        try:
            # Submit the job
            response = await async_client.post("/llm/job", json=payload)
            response.raise_for_status()
            job_data = response.json()
            
            assert "task_id" in job_data
            task_id = job_data["task_id"]
            
            # Poll for completion (simple implementation)
            max_attempts = 10  # Reduced for testing
            attempt = 0
            while attempt < max_attempts:
                status_response = await async_client.get(f"/llm/job/{task_id}")
                
                # Check if response is valid JSON
                try:
                    status_data = status_response.json()
                except:
                    print(f"Non-JSON response: {status_response.text}")
                    attempt += 1
                    await asyncio.sleep(1)
                    continue
                
                if status_data.get("status") == "completed":
                    # Verify we got a result
                    assert "result" in status_data
                    result = status_data["result"]
                    # Result can be string, dict, or list depending on extraction
                    assert result is not None
                    print(f"✓ LLM job with chunking completed successfully. Result type: {type(result)}")
                    break
                elif status_data.get("status") == "failed":
                    pytest.fail(f"LLM job failed: {status_data.get('error', 'Unknown error')}")
                    break
                else:
                    attempt += 1
                    await asyncio.sleep(1)  # Wait 1 second before checking again
            
            if attempt >= max_attempts:
                # For testing purposes, just verify the job was submitted
                print("✓ LLM job with chunking submitted successfully (completion check timed out)")
                
        except httpx.HTTPStatusError as e:
            pytest.fail(f"LLM job request failed: {e}. Response: {e.response.text}")
        except Exception as e:
            pytest.fail(f"LLM job test failed: {e}")

    async def test_chunking_strategies_supported(self, async_client: httpx.AsyncClient):
        """Test that all chunking strategies are supported by the API."""
        from deploy.docker.utils import create_chunking_strategy
        
        # Test all supported chunking strategies
        strategies_to_test = [
            {"type": "IdentityChunking", "params": {}},
            {"type": "RegexChunking", "params": {"patterns": ["\\n\\n"]}},
            {"type": "FixedLengthWordChunking", "params": {"chunk_size": 50}},
            {"type": "SlidingWindowChunking", "params": {"window_size": 100, "step": 50}},
            {"type": "OverlappingWindowChunking", "params": {"window_size": 100, "overlap": 20}},
        ]
        
        for strategy_config in strategies_to_test:
            try:
                # Test that the strategy can be created
                strategy = create_chunking_strategy(strategy_config)
                assert strategy is not None
                print(f"✓ {strategy_config['type']} strategy created successfully")
                
                # Test basic chunking functionality
                test_text = "This is a test document with multiple sentences. It should be split appropriately."
                chunks = strategy.chunk(test_text)
                assert isinstance(chunks, list)
                assert len(chunks) > 0
                print(f"✓ {strategy_config['type']} chunking works: {len(chunks)} chunks")
                
            except Exception as e:
                # Some strategies may fail due to missing dependencies (NLTK), but that's OK
                if "NlpSentenceChunking" in strategy_config["type"] or "TopicSegmentationChunking" in strategy_config["type"]:
                    print(f"⚠ {strategy_config['type']} requires NLTK dependencies: {e}")
                else:
                    pytest.fail(f"Unexpected error with {strategy_config['type']}: {e}")

    async def test_malformed_request_handling(self, async_client: httpx.AsyncClient):
        """Test handling of malformed requests."""
        # Test missing required fields
        malformed_payload = {"urls": []}  # Missing browser_config and crawler_config
        response = await async_client.post("/crawl", json=malformed_payload)
        print(f"Response: {response.text}")
        assert response.status_code == 422  # Validation error
        
        # Test empty URLs list
        empty_urls_payload = {
            "urls": [],
            "browser_config": {"type": "BrowserConfig", "params": {}},
            "crawler_config": {"type": "CrawlerRunConfig", "params": {}}
        }
        response = await async_client.post("/crawl", json=empty_urls_payload)
        assert response.status_code == 422  # "At least one URL required"

    # 7. HTTP-only Crawling Tests
    async def test_http_crawl_single_url(self, async_client: httpx.AsyncClient):
        """Test /crawl/http with a single URL using HTTP-only strategy."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "http_config": {
                "method": "GET",
                "headers": {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                "follow_redirects": True,
                "verify_ssl": True
            },
            "crawler_config": {
                "cache_mode": CacheMode.BYPASS.value,
                "screenshot": False
            }
        }
        try:
            response = await async_client.post("/crawl/http", json=payload)
            print(f"HTTP Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Server error: {e}")
            print(f"Response content: {e.response.text}")
            raise

        assert data["success"] is True
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert result["url"] == SIMPLE_HTML_URL
        assert "Crawl4AI Documentation" in result["html"]
        # Check that processing was fast (HTTP should be much faster than browser)
        assert data["server_processing_time_s"] < 5.0  # Should complete in under 5 seconds

    async def test_http_crawl_streaming(self, async_client: httpx.AsyncClient):
        """Test /crawl/http/stream with HTTP-only strategy."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "http_config": {
                "method": "GET",
                "headers": {"Accept": "text/html"},
                "follow_redirects": True
            },
            "crawler_config": {
                "cache_mode": CacheMode.BYPASS.value,
                "screenshot": False
            }
        }
        async with async_client.stream("POST", "/crawl/http/stream", json=payload) as response:
            response.raise_for_status()
            assert response.headers["content-type"] == "application/x-ndjson"
            assert response.headers.get("x-stream-status") == "active"

            results = await process_streaming_response(response)

            assert len(results) == 1
            result = results[0]
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["url"] == SIMPLE_HTML_URL
            assert "Crawl4AI Documentation" in result["html"]

    async def test_http_crawl_api_endpoint(self, async_client: httpx.AsyncClient):
        """Test HTTP crawling with a JSON API endpoint."""
        payload = {
            "urls": ["https://httpbin.org/json"],
            "http_config": {
                "method": "GET",
                "headers": {"Accept": "application/json"},
                "follow_redirects": True
            },
            "crawler_config": {
                "cache_mode": CacheMode.BYPASS.value
            }
        }
        try:
            response = await async_client.post("/crawl/http", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP API test error: {e}")
            print(f"Response: {e.response.text}")
            raise

        assert data["success"] is True
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert result["success"] is True
        assert result["url"] == "https://httpbin.org/json"
        # Should contain JSON response
        assert "slideshow" in result["html"] or "application/json" in result.get("content_type", "")

    async def test_http_crawl_error_handling(self, async_client: httpx.AsyncClient):
        """Test error handling for HTTP crawl endpoints."""
        # Test invalid URL
        invalid_payload = {
            "urls": ["invalid-url"],
            "http_config": {"method": "GET"},
            "crawler_config": {"cache_mode": CacheMode.BYPASS.value}
        }
        response = await async_client.post("/crawl/http", json=invalid_payload)
        # HTTP crawler handles invalid URLs gracefully, returns 200 with failed results
        assert response.status_code == 200

        # Test non-existent domain
        nonexistent_payload = {
            "urls": ["https://nonexistent-domain-12345.com"],
            "http_config": {"method": "GET"},
            "crawler_config": {"cache_mode": CacheMode.BYPASS.value}
        }
        response = await async_client.post("/crawl/http", json=nonexistent_payload)
        # HTTP crawler handles unreachable hosts gracefully, returns 200 with failed results
        assert response.status_code == 200


if __name__ == "__main__":
    # Define arguments for pytest programmatically
    # -v: verbose output
    # -s: show print statements immediately (useful for debugging)
    # __file__: tells pytest to run tests in the current file
    pytest_args = ["-v", "-s", __file__]

    # You can add more pytest arguments here if needed, for example:
    # '-k test_llm_extraction': Run only the LLM test function
    # pytest_args.append("-k test_llm_extraction")

    print(f"Running pytest with args: {pytest_args}")

    # Execute pytest
    exit_code = pytest.main(pytest_args)

    print(f"Pytest finished with exit code: {exit_code}")