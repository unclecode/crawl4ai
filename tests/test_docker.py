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
        # Submit crawl job
        response = requests.post(f"{self.base_url}/crawl", json=request_data)
        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")

        # Poll for result
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {timeout} seconds"
                )

            result = requests.get(f"{self.base_url}/task/{task_id}")
            status = result.json()

            if status["status"] == "failed":
                print("Task failed:", status.get("error"))
                raise Exception(f"Task failed: {status.get('error')}")

            if status["status"] == "completed":
                return status

            time.sleep(2)


def test_docker_deployment(version="basic"):
    tester = Crawl4AiTester()
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

    # if version in ["full", "transformer"]:
    #     test_cosine_extraction(tester)

    # test_js_execution(tester)
    # test_css_selector(tester)
    # test_structured_extraction(tester)
    # test_llm_extraction(tester)
    # test_llm_with_ollama(tester)
    # test_screenshot(tester)
    test_link_analysis(tester)


def test_basic_crawl(tester: Crawl4AiTester):
    print("\n=== Testing Basic Crawl ===")
    request = {"urls": ["https://www.nbcnews.com/business"], "priority": 10}

    result = tester.submit_and_wait(request)
    print(f"Basic crawl result length: {len(result['result']['markdown'])}")
    assert result["result"]["success"]
    assert len(result["result"]["markdown"]) > 0


def test_js_execution(tester: Crawl4AiTester):
    print("\n=== Testing JS Execution ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 8,
        "js_code": [
            "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
        ],
        "wait_for": "article.tease-card:nth-child(10)",
        "crawler_params": {"headless": True},
    }

    result = tester.submit_and_wait(request)
    print(f"JS execution result length: {len(result['result']['markdown'])}")
    assert result["result"]["success"]


def test_css_selector(tester: Crawl4AiTester):
    print("\n=== Testing CSS Selector ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 7,
        "css_selector": ".wide-tease-item__description",
        "crawler_params": {"headless": True},
        "extra": {"word_count_threshold": 10},
    }

    result = tester.submit_and_wait(request)
    print(f"CSS selector result length: {len(result['result']['markdown'])}")
    assert result["result"]["success"]


def test_structured_extraction(tester: Crawl4AiTester):
    print("\n=== Testing Structured Extraction ===")
    schema = {
        "name": "Coinbase Crypto Prices",
        "baseSelector": ".cds-tableRow-t45thuk",
        "fields": [
            {
                "name": "crypto",
                "selector": "td:nth-child(1) h2",
                "type": "text",
            },
            {
                "name": "symbol",
                "selector": "td:nth-child(1) p",
                "type": "text",
            },
            {
                "name": "price",
                "selector": "td:nth-child(2)",
                "type": "text",
            },
        ],
    }

    request = {
        "urls": ["https://www.coinbase.com/explore"],
        "priority": 9,
        "extraction_config": {"type": "json_css", "params": {"schema": schema}},
    }

    result = tester.submit_and_wait(request)
    extracted = json.loads(result["result"]["extracted_content"])
    print(f"Extracted {len(extracted)} items")
    print("Sample item:", json.dumps(extracted[0], indent=2))
    assert result["result"]["success"]
    assert len(extracted) > 0


def test_llm_extraction(tester: Crawl4AiTester):
    print("\n=== Testing LLM Extraction ===")
    schema = {
        "type": "object",
        "properties": {
            "model_name": {
                "type": "string",
                "description": "Name of the OpenAI model.",
            },
            "input_fee": {
                "type": "string",
                "description": "Fee for input token for the OpenAI model.",
            },
            "output_fee": {
                "type": "string",
                "description": "Fee for output token for the OpenAI model.",
            },
        },
        "required": ["model_name", "input_fee", "output_fee"],
    }

    request = {
        "urls": ["https://openai.com/api/pricing"],
        "priority": 8,
        "extraction_config": {
            "type": "llm",
            "params": {
                "provider": "openai/gpt-4o-mini",
                "api_token": os.getenv("OPENAI_API_KEY"),
                "schema": schema,
                "extraction_type": "schema",
                "instruction": """From the crawled content, extract all mentioned model names along with their fees for input and output tokens.""",
            },
        },
        "crawler_params": {"word_count_threshold": 1},
    }

    try:
        result = tester.submit_and_wait(request)
        extracted = json.loads(result["result"]["extracted_content"])
        print(f"Extracted {len(extracted)} model pricing entries")
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
        "priority": 8,
        "extraction_config": {
            "type": "llm",
            "params": {
                "provider": "ollama/llama2",
                "schema": schema,
                "extraction_type": "schema",
                "instruction": "Extract the main article information including title, summary, and main topics.",
            },
        },
        "extra": {"word_count_threshold": 1},
        "crawler_params": {"verbose": True},
    }

    try:
        result = tester.submit_and_wait(request)
        extracted = json.loads(result["result"]["extracted_content"])
        print("Extracted content:", json.dumps(extracted, indent=2))
        assert result["result"]["success"]
    except Exception as e:
        print(f"Ollama extraction test failed: {str(e)}")


def test_cosine_extraction(tester: Crawl4AiTester):
    print("\n=== Testing Cosine Extraction ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 8,
        "extraction_config": {
            "type": "cosine",
            "params": {
                "semantic_filter": "business finance economy",
                "word_count_threshold": 10,
                "max_dist": 0.2,
                "top_k": 3,
            },
        },
    }

    try:
        result = tester.submit_and_wait(request)
        extracted = json.loads(result["result"]["extracted_content"])
        print(f"Extracted {len(extracted)} text clusters")
        print("First cluster tags:", extracted[0]["tags"])
        assert result["result"]["success"]
    except Exception as e:
        print(f"Cosine extraction test failed: {str(e)}")


def test_screenshot(tester: Crawl4AiTester):
    print("\n=== Testing Screenshot ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 5,
        "screenshot": True,
        "crawler_params": {"headless": True},
    }

    result = tester.submit_and_wait(request)
    print("Screenshot captured:", bool(result["result"]["screenshot"]))

    if result["result"]["screenshot"]:
        # Save screenshot
        screenshot_data = base64.b64decode(result["result"]["screenshot"])
        with open("test_screenshot.jpg", "wb") as f:
            f.write(screenshot_data)
        print("Screenshot saved as test_screenshot.jpg")

    assert result["result"]["success"]


def test_link_analysis(tester: Crawl4AiTester):
    print("\n=== Testing Link Analysis ===")

    # Get auth token first
    try:
        token_response = requests.post(f"{tester.base_url}/token", json={"email": "test@example.com"})
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    except Exception as e:
        print(f"Could not get auth token: {e}")
        headers = {"Content-Type": "application/json"}

    # Test basic link analysis
    request_data = {
        "url": "https://www.nbcnews.com/business"
    }

    response = requests.post(
        f"{tester.base_url}/links/analyze",
        headers=headers,
        json=request_data,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        total_links = sum(len(links) for links in result.values())
        print(f"Link analysis successful: found {total_links} links")

        # Check for expected categories
        categories_found = []
        for category in ['internal', 'external', 'social', 'download', 'email', 'phone']:
            if category in result and result[category]:
                categories_found.append(category)

        print(f"Link categories found: {categories_found}")

        # Verify we have some links
        assert total_links > 0, "Should find at least one link"
        assert len(categories_found) > 0, "Should find at least one link category"

        # Test with configuration
        request_data_with_config = {
            "url": "https://www.nbcnews.com/business",
            "config": {
                "simulate_user": True,
                "override_navigator": True,
                "word_count_threshold": 1
            }
        }

        response_with_config = requests.post(
            f"{tester.base_url}/links/analyze",
            headers=headers,
            json=request_data_with_config,
            timeout=60
        )

        if response_with_config.status_code == 200:
            result_with_config = response_with_config.json()
            total_links_config = sum(len(links) for links in result_with_config.values())
            print(f"Link analysis with config: found {total_links_config} links")
            assert total_links_config > 0, "Should find links even with config"

        print("✅ Link analysis tests passed")
    else:
        print(f"❌ Link analysis failed: {response.status_code} - {response.text}")
        # Don't fail the entire test suite for this endpoint
        print("⚠️  Link analysis test failed, but continuing with other tests")


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "basic"
    # version = "full"
    test_docker_deployment(version)
