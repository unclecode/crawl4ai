import base64
import io
import json
import os
import sys
import time
from typing import Any, Dict

import pytest
import requests
from PIL import Image, ImageFile

from crawl4ai import (
    CosineStrategy,
    JsonCssExtractionStrategy,
    LLMConfig,
    LLMExtractionStrategy,
)
from crawl4ai.async_configs import BrowserConfig
from crawl4ai.async_webcrawler import CrawlerRunConfig

from .common import async_client


class Crawl4AiTester:
    def __init__(self):
        self.client = async_client()

    async def submit_and_validate(
        self, request_data: Dict[str, Any], timeout: int = 300
    ) -> Dict[str, Any]:
        """Submit a crawl request and validate for the result.

        The response is validated to ensure that it is successful and contains at least one result.

        :param request_data: The request data to submit.
        :type request_data: Dict[str, Any]
        :param timeout: The maximum time to wait for the response, defaults to 300.
        :type timeout: int, optional
        :return: The response of the crawl decoded from JSON.
        :rtype: Dict[str, Any]
        """
        response = await self.client.post("/crawl", json=request_data)
        return self.assert_valid_response(response.json())

    async def check_health(self) -> None:
        """Check the health of the service.

        Check the health of the service and wait for it to be ready.
        If the service is not ready after a few retries, the test will fail."""
        max_retries = 5
        for i in range(max_retries):
            try:
                health = await self.client.get("/health", timeout=10)
                print("Health check:", health.json())
                return
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    assert False, f"Failed to connect after {max_retries} attempts"

                print(
                    f"Waiting for service to start (attempt {i + 1}/{max_retries})..."
                )
                time.sleep(5)

        pytest.fail(f"Failed to connect to service after {max_retries} retries")

    def assert_valid_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Assert that the response is valid and returns the first result.

        :param result: The response from the API
        :type result: Dict[str, Any]
        :return: The first result
        :rtype: dict[str, Any]
        """
        assert result["success"]
        assert result["results"]
        assert len(result["results"]) > 0
        assert result["results"][0]["url"]
        assert result["results"][0]["html"]
        return result["results"][0]


@pytest.fixture
def tester() -> Crawl4AiTester:
    return Crawl4AiTester()


@pytest.mark.asyncio
async def test_basic_crawl(tester: Crawl4AiTester):
    request = {"urls": ["https://www.nbcnews.com/business"], "priority": 10}

    await tester.submit_and_validate(request)


@pytest.mark.asyncio
async def test_js_execution(tester: Crawl4AiTester):
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 8,
        "js_code": [
            "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
        ],
        "wait_for": "article.tease-card:nth-child(10)",
        "crawler_params": {"headless": True},
    }

    await tester.submit_and_validate(request)


@pytest.mark.asyncio
async def test_css_selector(tester: Crawl4AiTester):
    print("\n=== Testing CSS Selector ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 7,
        "css_selector": ".wide-tease-item__description",
        "crawler_params": {"headless": True},
        "extra": {"word_count_threshold": 10},
    }

    await tester.submit_and_validate(request)


@pytest.mark.asyncio
async def test_structured_extraction(tester: Crawl4AiTester):
    schema = {
        "name": "Coinbase Crypto Prices",
        "baseSelector": "table > tbody > tr",
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
    crawler_config: CrawlerRunConfig = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema),
    )
    request = {
        "urls": ["https://www.coinbase.com/explore"],
        "priority": 9,
        "crawler_config": crawler_config.dump(),
    }

    result = await tester.submit_and_validate(request)

    extracted = json.loads(result["extracted_content"])
    print(f"Extracted {len(extracted)} items")
    print("Sample item:", json.dumps(extracted[0], indent=2))

    assert len(extracted) > 0


@pytest.mark.asyncio
async def test_llm_extraction(tester: Crawl4AiTester):
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

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

    crawler_config: CrawlerRunConfig = CrawlerRunConfig(
        extraction_strategy=LLMExtractionStrategy(
            schema=schema,
            llm_config=LLMConfig(
                provider="openai/gpt-4o-mini",
                api_token=os.getenv("OPENAI_API_KEY"),
            ),
            extraction_type="schema",
            instruction="From the crawled content, extract all mentioned model names along with their fees for input and output tokens.",
        ),
        word_count_threshold=1,
    )
    request = {
        "urls": ["https://openai.com/api/pricing"],
        "priority": 8,
        "crawler_config": crawler_config.dump(),
    }

    result = await tester.submit_and_validate(request)
    extracted = json.loads(result["extracted_content"])
    print(f"Extracted {len(extracted)} model pricing entries")
    print("Sample entry:", json.dumps(extracted[0], indent=2))
    assert result["success"]
    assert len(extracted) > 0, "No model pricing entries found"


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_llm_with_ollama(tester: Crawl4AiTester):
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

    crawler_config: CrawlerRunConfig = CrawlerRunConfig(
        extraction_strategy=LLMExtractionStrategy(
            schema=schema,
            llm_config=LLMConfig(
                provider="ollama/llama2",
            ),
            extraction_type="schema",
            instruction="Extract the main article information including title, summary, and main topics.",
        ),
        word_count_threshold=1,
    )

    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 8,
        "crawler_config": crawler_config.dump(),
    }

    result = await tester.submit_and_validate(request)
    extracted = json.loads(result["extracted_content"])
    print("Extracted content:", json.dumps(extracted, indent=2))
    assert result["success"]
    assert len(extracted) > 0, "No content extracted"


@pytest.mark.asyncio
async def test_cosine_extraction(tester: Crawl4AiTester):
    print("\n=== Testing Cosine Extraction ===")
    crawler_config: CrawlerRunConfig = CrawlerRunConfig(
        extraction_strategy=CosineStrategy(
            semantic_filter="business finance economy",
            word_count_threshold=10,
            max_dist=0.2,
            top_k=3,
        ),
        word_count_threshold=1,
        verbose=True,
    )

    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 8,
        "crawler_config": crawler_config.dump(),
    }

    result = await tester.submit_and_validate(request)
    extracted = json.loads(result["extracted_content"])
    print(f"Extracted {len(extracted)} text clusters")
    print("First cluster tags:", extracted[0]["tags"])
    assert result["success"]
    assert len(extracted) > 0, "No clusters found"


@pytest.mark.asyncio
async def test_screenshot(tester: Crawl4AiTester):
    crawler_config: CrawlerRunConfig = CrawlerRunConfig(
        screenshot=True,
        word_count_threshold=1,
        verbose=True,
    )

    browser_config: BrowserConfig = BrowserConfig(headless=True)

    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 5,
        "screenshot": True,
        "crawler_config": crawler_config.dump(),
        "browser_config": browser_config.dump(),
    }

    result = await tester.submit_and_validate(request)
    assert result.get("screenshot")
    image: ImageFile.ImageFile = Image.open(
        io.BytesIO(base64.b64decode(result["screenshot"]))
    )

    assert image.format == "BMP"


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
