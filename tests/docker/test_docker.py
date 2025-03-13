import requests
import time
import httpx
import asyncio
from typing import Dict, Any
from crawl4ai import (
    BrowserConfig, CrawlerRunConfig, DefaultMarkdownGenerator,
    PruningContentFilter, JsonCssExtractionStrategy, LLMContentFilter, CacheMode
)
from crawl4ai import LLMConfig
from crawl4ai.docker_client import Crawl4aiDockerClient

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

async def test_direct_api():
    """Test direct API endpoints without using the client SDK"""
    print("\n=== Testing Direct API Calls ===")
    
    # Test 1: Basic crawl with content filtering
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1200,
        viewport_height=800
    )
    
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=0
            ),
            options={"ignore_links": True}
        )
    )

    request_data = {
        "urls": ["https://example.com"],
        "browser_config": browser_config.dump(),
        "crawler_config": crawler_config.dump()
    }

    # Make direct API call
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/crawl",
            json=request_data,
            timeout=300
        )
        assert response.status_code == 200
        result = response.json()
        print("Basic crawl result:", result["success"])

    # Test 2: Structured extraction with JSON CSS
    schema = {
        "baseSelector": "article.post",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".content", "type": "html"}
        ]
    }

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema=schema)
    )

    request_data["crawler_config"] = crawler_config.dump()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/crawl",
            json=request_data
        )
        assert response.status_code == 200
        result = response.json()
        print("Structured extraction result:", result["success"])

    # Test 3: Get schema
    # async with httpx.AsyncClient() as client:
    #     response = await client.get("http://localhost:8000/schema")
    #     assert response.status_code == 200
    #     schemas = response.json()
    #     print("Retrieved schemas for:", list(schemas.keys()))

async def test_with_client():
    """Test using the Crawl4AI Docker client SDK"""
    print("\n=== Testing Client SDK ===")
    
    async with Crawl4aiDockerClient(verbose=True) as client:
        # Test 1: Basic crawl
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48,
                    threshold_type="fixed"
                )
            )
        )

        result = await client.crawl(
            urls=["https://example.com"],
            browser_config=browser_config,
            crawler_config=crawler_config
        )
        print("Client SDK basic crawl:", result.success)

        # Test 2: LLM extraction with streaming
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=LLMContentFilter(
                    llm_config=LLMConfig(provider="openai/gpt-40"),
                    instruction="Extract key technical concepts"
                )
            ),
            stream=True
        )

        async for result in await client.crawl(
            urls=["https://example.com"],
            browser_config=browser_config,
            crawler_config=crawler_config
        ):
            print(f"Streaming result for: {result.url}")

        # # Test 3: Get schema
        # schemas = await client.get_schema()
        # print("Retrieved client schemas for:", list(schemas.keys()))

async def main():
    """Run all tests"""
    # Test direct API
    print("Testing direct API calls...")
    await test_direct_api()

    # Test client SDK
    print("\nTesting client SDK...")
    await test_with_client()

if __name__ == "__main__":
    asyncio.run(main())