import asyncio
import json
import os
import sys
import time
from typing import Any, Dict

import pytest
from httpx import AsyncClient, Response, codes

from crawl4ai.async_configs import CrawlerRunConfig

from .common import async_client


class NBCNewsAPITest:
    def __init__(self):
        self.client: AsyncClient = async_client()

    async def submit_crawl(self, request_data: Dict[str, Any]) -> str:
        if "crawler_config" not in request_data:
            request_data["crawler_config"] = CrawlerRunConfig(stream=True).dump()

        response: Response = await self.client.post("/crawl/stream", json=request_data)
        assert response.status_code == codes.OK, f"Error: {response.text}"
        result = response.json()
        assert "task_id" in result

        return result["task_id"]

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        response: Response = await self.client.get(f"/task/{task_id}")
        assert response.status_code == codes.OK
        result = response.json()
        assert "status" in result
        return result

    async def wait_for_task(
        self, task_id: str, timeout: int = 300, poll_interval: int = 2
    ) -> Dict[str, Any]:
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {timeout} seconds"
                )

            status = await self.get_task_status(task_id)
            if status["status"] in ["completed", "failed"]:
                return status

            await asyncio.sleep(poll_interval)

    async def check_health(self) -> Dict[str, Any]:
        response: Response = await self.client.get("/health")
        assert response.status_code == codes.OK
        return response.json()


@pytest.fixture
def api() -> NBCNewsAPITest:
    return NBCNewsAPITest()


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_basic_crawl(api: NBCNewsAPITest):
    print("\n=== Testing Basic Crawl ===")
    request = {"urls": ["https://www.nbcnews.com/business"], "priority": 10}
    task_id = await api.submit_crawl(request)
    result = await api.wait_for_task(task_id)
    print(f"Basic crawl result length: {len(result['result']['markdown'])}")
    assert result["status"] == "completed"
    assert "result" in result
    assert result["result"]["success"]


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_js_execution(api: NBCNewsAPITest):
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
    task_id = await api.submit_crawl(request)
    result = await api.wait_for_task(task_id)
    print(f"JS execution result length: {len(result['result']['markdown'])}")
    assert result["status"] == "completed"
    assert result["result"]["success"]


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_css_selector(api: NBCNewsAPITest):
    print("\n=== Testing CSS Selector ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 7,
        "css_selector": ".wide-tease-item__description",
    }
    task_id = await api.submit_crawl(request)
    result = await api.wait_for_task(task_id)
    print(f"CSS selector result length: {len(result['result']['markdown'])}")
    assert result["status"] == "completed"
    assert result["result"]["success"]


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_structured_extraction(api: NBCNewsAPITest):
    print("\n=== Testing Structured Extraction ===")
    schema = {
        "name": "NBC News Articles",
        "baseSelector": "article.tease-card",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {
                "name": "description",
                "selector": ".tease-card__description",
                "type": "text",
            },
            {
                "name": "link",
                "selector": "a",
                "type": "attribute",
                "attribute": "href",
            },
        ],
    }

    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 9,
        "extraction_config": {"type": "json_css", "params": {"schema": schema}},
    }
    task_id = await api.submit_crawl(request)
    result = await api.wait_for_task(task_id)
    extracted = json.loads(result["result"]["extracted_content"])
    print(f"Extracted {len(extracted)} articles")
    assert result["status"] == "completed"
    assert result["result"]["success"]
    assert len(extracted) > 0


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_batch_crawl(api: NBCNewsAPITest):
    print("\n=== Testing Batch Crawl ===")
    request = {
        "urls": [
            "https://www.nbcnews.com/business",
            "https://www.nbcnews.com/business/consumer",
            "https://www.nbcnews.com/business/economy",
        ],
        "priority": 6,
        "crawler_params": {"headless": True},
    }
    task_id = await api.submit_crawl(request)
    result = await api.wait_for_task(task_id)
    print(f"Batch crawl completed, got {len(result['results'])} results")
    assert result["status"] == "completed"
    assert "results" in result
    assert len(result["results"]) == 3


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_llm_extraction(api: NBCNewsAPITest):
    print("\n=== Testing LLM Extraction with Ollama ===")
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
        "required": ["article_title", "summary", "main_topics"],
    }

    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 8,
        "extraction_config": {
            "type": "llm",
            "params": {
                "provider": "openai/gpt-4o-mini",
                "api_key": os.getenv("OLLAMA_API_KEY"),
                "schema": schema,
                "extraction_type": "schema",
                "instruction": """Extract the main article information including title, a brief summary, and main topics discussed.
                Focus on the primary business news article on the page.""",
            },
        },
        "crawler_params": {"headless": True, "word_count_threshold": 1},
    }

    task_id = await api.submit_crawl(request)
    result = await api.wait_for_task(task_id)

    if result["status"] == "completed":
        extracted = json.loads(result["result"]["extracted_content"])
        print("Extracted article analysis:")
        print(json.dumps(extracted, indent=2))

    assert result["status"] == "completed"
    assert result["result"]["success"]


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_screenshot(api: NBCNewsAPITest):
    print("\n=== Testing Screenshot ===")
    request = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 5,
        "screenshot": True,
        "crawler_params": {"headless": True},
    }
    task_id = await api.submit_crawl(request)
    result = await api.wait_for_task(task_id)
    print("Screenshot captured:", bool(result["result"]["screenshot"]))
    assert result["status"] == "completed"
    assert result["result"]["success"]
    assert result["result"]["screenshot"] is not None


@pytest.mark.asyncio
@pytest.mark.skip("Crawl with task_id not implemented yet")
async def test_priority_handling(api: NBCNewsAPITest):
    print("\n=== Testing Priority Handling ===")
    # Submit low priority task first
    low_priority = {
        "urls": ["https://www.nbcnews.com/business"],
        "priority": 1,
        "crawler_params": {"headless": True},
    }
    low_task_id = await api.submit_crawl(low_priority)

    # Submit high priority task
    high_priority = {
        "urls": ["https://www.nbcnews.com/business/consumer"],
        "priority": 10,
        "crawler_params": {"headless": True},
    }
    high_task_id = await api.submit_crawl(high_priority)

    # Get both results
    high_result = await api.wait_for_task(high_task_id)
    low_result = await api.wait_for_task(low_task_id)

    print("Both tasks completed")
    assert high_result["status"] == "completed"
    assert low_result["status"] == "completed"


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
