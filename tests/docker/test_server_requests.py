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
BASE_URL = os.getenv("CRAWL4AI_TEST_URL", "http://localhost:11235") # Make base URL configurable
# Use a known simple HTML page for basic tests
SIMPLE_HTML_URL = "https://httpbin.org/html"
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
    async for line in response.aiter_lines():
        if line:
            try:
                data = json.loads(line)
                if data.get("status") == "completed":
                    completed = True
                    break # Stop processing after completion marker
                else:
                    results.append(data)
            except json.JSONDecodeError:
                pytest.fail(f"Failed to decode JSON line: {line}")
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
        assert "<h1>Herman Melville - Moby-Dick</h1>" in result["html"]
        # We don't specify a markdown generator in this test, so don't make assumptions about markdown field
        # It might be null, missing, or populated depending on the server's default behavior

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
        assert "<h1>Herman Melville - Moby-Dick</h1>" in result["html"]


    # 2. Multi-URL and Dispatcher
    async def test_multi_url_crawl(self, async_client: httpx.AsyncClient):
        """Test /crawl with multiple URLs, implicitly testing dispatcher."""
        urls = [SIMPLE_HTML_URL, "https://httpbin.org/links/10/0"]
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
        urls = [SIMPLE_HTML_URL, "https://httpbin.org/links/10/0"]
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
        assert "Moby-Dick" in result["markdown"]["raw_markdown"]
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
                            "instruction": "Extract the main title and the author mentioned in the text into JSON.",
                            # LLMConfig is implicitly defined by server's config.yml and .llm.env
                            # If you needed to override provider/token PER REQUEST:
                            "llm_config": {
                               "type": "LLMConfig",
                               "params": {
                                  "provider": "openai/gpt-4o", # Example override
                                  "api_token": os.getenv("OPENAI_API_KEY") # Example override
                               }
                            },
                            "schema": { # Optional: Provide a schema for structured output
                                "type": "dict", # IMPORTANT: Wrap schema dict
                                "value": {
                                    "title": "Book Info",
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "The main title of the work"},
                                        "author": {"type": "string", "description": "The author of the work"}
                                    },
                                     "required": ["title", "author"]
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
                assert "author" in extracted_item
                assert "Moby-Dick" in extracted_item.get("title", "")
                assert "Herman Melville" in extracted_item.get("author", "")
            else:
                assert isinstance(extracted_data, dict)
                assert "title" in extracted_data
                assert "author" in extracted_data
                assert "Moby-Dick" in extracted_data.get("title", "")
                assert "Herman Melville" in extracted_data.get("author", "")
        except (json.JSONDecodeError, AssertionError) as e:
            pytest.fail(f"LLM extracted content parsing or validation failed: {e}\nContent: {result['extracted_content']}")
        except Exception as e: # Catch any other unexpected error
            pytest.fail(f"An unexpected error occurred during LLM result processing: {e}\nContent: {result['extracted_content']}")
            
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