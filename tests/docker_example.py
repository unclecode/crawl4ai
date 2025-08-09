import requests
import json
import time
import sys
import base64
import os
from typing import Dict, Any

class Crawl4AiTester:
    def __init__(self, base_url: str = "http://localhost:11235"):
        self.base_url = base_url


    def submit_and_wait(
        self, request_data: Dict[str, Any], timeout: int = 300
    ) -> Dict[str, Any]:
        # Submit crawl job using async endpoint
        response = requests.post(
            f"{self.base_url}/crawl/job", json=request_data
        )
        response.raise_for_status()
        job_response = response.json()
        task_id = job_response["task_id"]
        print(f"Submitted job with task_id: {task_id}")

        # Poll for result
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {timeout} seconds"
                )

            result = requests.get(
                f"{self.base_url}/crawl/job/{task_id}"
            )
            result.raise_for_status()
            status = result.json()

            if status["status"] == "failed":
                print("Task failed:", status.get("error"))
                raise Exception(f"Task failed: {status.get('error')}")

            if status["status"] == "completed":
                return status

            time.sleep(2)

    def submit_sync(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # Use synchronous crawl endpoint
        response = requests.post(
            f"{self.base_url}/crawl",
            json=request_data,
            timeout=60,
        )
        if response.status_code == 408:
            raise TimeoutError("Task did not complete within server timeout")
        response.raise_for_status()
        return response.json()


def test_docker_deployment(version="basic"):
    tester = Crawl4AiTester(
        base_url="http://localhost:11235",
        #base_url="https://crawl4ai-sby74.ondigitalocean.app",
    )
    print(f"Testing Crawl4AI Docker {version} version")

    # Health check with timeout and retry
    max_retries = 5
    for i in range(max_retries):
        try:
            health = requests.get(f"{tester.base_url}/health", timeout=10)
            print("Health check:", health.json())
            break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                print(f"Failed to connect after {max_retries} attempts")
                sys.exit(1)
            print(f"Waiting for service to start (attempt {i+1}/{max_retries})...")
            time.sleep(5)

    # Test cases based on version
    test_basic_crawl(tester)
    test_basic_crawl_sync(tester)

    if version in ["full", "transformer"]:
        test_cosine_extraction(tester)

    test_js_execution(tester)
    test_css_selector(tester)
    test_structured_extraction(tester)
    test_llm_extraction(tester)
    test_llm_with_ollama(tester)
    test_screenshot(tester)


def test_basic_crawl(tester: Crawl4AiTester):
    print("\n=== Testing Basic Crawl (Async) ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
    }

    result = tester.submit_and_wait(request)
    print(f"Basic crawl result count: {len(result['result']['results'])}")
    assert result["result"]["success"]
    assert len(result["result"]["results"]) > 0
    assert len(result["result"]["results"][0]["markdown"]) > 0


def test_basic_crawl_sync(tester: Crawl4AiTester):
    print("\n=== Testing Basic Crawl (Sync) ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
    }

    result = tester.submit_sync(request)
    print(f"Basic crawl result count: {len(result['results'])}")
    assert result["success"]
    assert len(result["results"]) > 0
    assert len(result["results"][0]["markdown"]) > 0


def test_js_execution(tester: Crawl4AiTester):
    print("\n=== Testing JS Execution ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "browser_config": {"headless": True},
        "crawler_config": {
            "js_code": [
                "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); if(loadMoreButton) loadMoreButton.click();"
            ],
            "wait_for": "wide-tease-item__wrapper df flex-column flex-row-m flex-nowrap-m enable-new-sports-feed-mobile-design(10)"
        }
    }

    result = tester.submit_and_wait(request)
    print(f"JS execution result count: {len(result['result']['results'])}")
    assert result["result"]["success"]


def test_css_selector(tester: Crawl4AiTester):
    print("\n=== Testing CSS Selector ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "browser_config": {"headless": True},
        "crawler_config": {
            "css_selector": ".wide-tease-item__description",
            "word_count_threshold": 10
        }
    }

    result = tester.submit_and_wait(request)
    print(f"CSS selector result count: {len(result['result']['results'])}")
    assert result["result"]["success"]


def test_structured_extraction(tester: Crawl4AiTester):
    print("\n=== Testing Structured Extraction ===")
    schema = {
  "name": "Cryptocurrency Prices",
  "baseSelector": "table[data-testid=\"prices-table\"] tbody tr",
  "fields": [
    {
      "name": "asset_name",
      "selector": "td:nth-child(2) p.cds-headline-h4steop",
      "type": "text"
    },
    {
      "name": "asset_symbol",
      "selector": "td:nth-child(2) p.cds-label2-l1sm09ec",
      "type": "text"
    },
    {
      "name": "asset_image_url",
      "selector": "td:nth-child(2) img[alt=\"Asset Symbol\"]",
      "type": "attribute",
      "attribute": "src"
    },
    {
      "name": "asset_url",
      "selector": "td:nth-child(2) a[aria-label^=\"Asset page for\"]",
      "type": "attribute",
      "attribute": "href"
    },
    {
      "name": "price",
      "selector": "td:nth-child(3) div.cds-typographyResets-t6muwls.cds-body-bwup3gq",
      "type": "text"
    },
    {
      "name": "change",
      "selector": "td:nth-child(7) p.cds-body-bwup3gq",
      "type": "text"
    }
  ]
}


    request = {
        "urls": ["https://www.coinbase.com/explore"],
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "JsonCssExtractionStrategy",
                    "params": {"schema": schema}
                }
            }
        }
    }

    result = tester.submit_and_wait(request)
    extracted = json.loads(result["result"]["results"][0]["extracted_content"])
    print(f"Extracted {len(extracted)} items")
    if extracted:
        print("Sample item:", json.dumps(extracted[0], indent=2))
    assert result["result"]["success"]
    assert len(extracted) > 0


def test_llm_extraction(tester: Crawl4AiTester):
    print("\n=== Testing LLM Extraction ===")
    schema = {
        "type": "object",
        "properties": {
            "asset_name": {
                "type": "string",
                "description": "Name of the asset.",
            },
            "price": {
                "type": "string",
                "description": "Price of the asset.",
            },
            "change": {
                "type": "string",
                "description": "Change in price of the asset.",
            },
        },
        "required": ["asset_name", "price", "change"],
    }

    request = {
        "urls": ["https://www.coinbase.com/en-in/explore"],
        "browser_config": {},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "LLMExtractionStrategy",
                    "params": {
                        "llm_config": {
                            "type": "LLMConfig",
                            "params": {
                                "provider": "gemini/gemini-2.5-flash",
                                "api_token": os.getenv("GEMINI_API_KEY")
                            }
                        },
                        "schema": schema,
                        "extraction_type": "schema",
                        "instruction": "From the crawled content    tioned asset names along with their prices and change in price.",
                    }
                },
                "word_count_threshold": 1
            }
        }
    }

    try:
        result = tester.submit_and_wait(request)
        extracted = json.loads(result["result"]["results"][0]["extracted_content"])
        print(f"Extracted {len(extracted)} model pricing entries")
        if extracted:
            print("Sample entry:", json.dumps(extracted[0], indent=2))
        assert result["result"]["success"]
    except Exception as e:
        print(f"LLM extraction test failed (might be due to missing API key): {str(e)}")


def test_llm_with_ollama(tester: Crawl4AiTester):
    print("\n=== Testing LLM with Ollama ===")
    schema = {
        "type": "object",
        "properties": {
            "article_title": {
                "type": "string",
                "description": "The main title of the news article",
            },
            "summary": {
                "type": "string",
                "description": "A brief summary of the article content",
            },
            "main_topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Main topics or themes discussed in the article",
            },
        },
    }

    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "browser_config": {"verbose": True},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "LLMExtractionStrategy",
                    "params": {
                        "llm_config": {
                            "type": "LLMConfig",
                            "params": {
                                "provider": "ollama/llama3.2:latest",
                            }
                        },
                        "schema": schema,
                        "extraction_type": "schema",
                        "instruction": "Extract the main article information including title, summary, and main topics.",
                    }
                },
                "word_count_threshold": 1
            }
        }
    }

    try:
        result = tester.submit_and_wait(request)
        extracted = json.loads(result["result"]["results"][0]["extracted_content"])
        print("Extracted content:", json.dumps(extracted, indent=2))
        assert result["result"]["success"]
    except Exception as e:
        print(f"Ollama extraction test failed: {str(e)}")


def test_cosine_extraction(tester: Crawl4AiTester):
    print("\n=== Testing Cosine Extraction ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "browser_config": {},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "CosineStrategy",
                    "params": {
                        "semantic_filter": "business finance economy",
                        "word_count_threshold": 10,
                        "max_dist": 0.2,
                        "top_k": 3,
                    }
                }
            }
        }
    }

    try:
        result = tester.submit_and_wait(request)
        extracted = json.loads(result["result"]["results"][0]["extracted_content"])
        print(f"Extracted {len(extracted)} text clusters")
        if extracted:
            print("First cluster tags:", extracted[0]["tags"])
        assert result["result"]["success"]
    except Exception as e:
        print(f"Cosine extraction test failed: {str(e)}")


def test_screenshot(tester: Crawl4AiTester):
    print("\n=== Testing Screenshot ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "browser_config": {"headless": True},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "screenshot": True
            }
        }
    }

    result = tester.submit_and_wait(request)
    screenshot_data = result["result"]["results"][0]["screenshot"]
    print("Screenshot captured:", bool(screenshot_data))

    if screenshot_data:
        # Save screenshot
        screenshot_bytes = base64.b64decode(screenshot_data)
        with open("test_screenshot.jpg", "wb") as f:
            f.write(screenshot_bytes)
        print("Screenshot saved as test_screenshot.jpg")

    assert result["result"]["success"]


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "basic"
    # version = "full"
    test_docker_deployment(version)
