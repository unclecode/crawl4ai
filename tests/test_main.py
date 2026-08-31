import asyncio
import aiohttp
import json
import time
import os
from typing import Dict, Any


class NBCNewsAPITest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def submit_crawl(self, request_data: Dict[str, Any]) -> str:
        async with self.session.post(
            f"{self.base_url}/crawl", json=request_data
        ) as response:
            result = await response.json()
            return result["task_id"]

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        async with self.session.get(f"{self.base_url}/task/{task_id}") as response:
            return await response.json()

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
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()


async def test_basic_crawl():
    print("\n=== Testing Basic Crawl ===")
    async with NBCNewsAPITest() as api:
        request = {"urls": ["https://www.nbcnews.com/business"], "priority": 10}
        task_id = await api.submit_crawl(request)
        result = await api.wait_for_task(task_id)
        print(f"Basic crawl result length: {len(result['result']['markdown'])}")
        assert result["status"] == "completed"
        assert "result" in result
        assert result["result"]["success"]


async def test_js_execution():
    print("\n=== Testing JS Execution ===")
    async with NBCNewsAPITest() as api:
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


async def test_css_selector():
    print("\n=== Testing CSS Selector ===")
    async with NBCNewsAPITest() as api:
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


async def test_structured_extraction():
    print("\n=== Testing Structured Extraction ===")
    async with NBCNewsAPITest() as api:
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


async def test_batch_crawl():
    print("\n=== Testing Batch Crawl ===")
    async with NBCNewsAPITest() as api:
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


async def test_llm_extraction():
    print("\n=== Testing LLM Extraction with Ollama ===")
    async with NBCNewsAPITest() as api:
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


async def test_screenshot():
    print("\n=== Testing Screenshot ===")
    async with NBCNewsAPITest() as api:
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


async def test_priority_handling():
    print("\n=== Testing Priority Handling ===")
    async with NBCNewsAPITest() as api:
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


async def main():
    try:
        # Start with health check
        async with NBCNewsAPITest() as api:
            health = await api.check_health()
            print("Server health:", health)

        # Run all tests
        # await test_basic_crawl()
        # await test_js_execution()
        # await test_css_selector()
        # await test_structured_extraction()
        await test_llm_extraction()
        # await test_batch_crawl()
        # await test_screenshot()
        # await test_priority_handling()

    except Exception as e:
        print(f"Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
