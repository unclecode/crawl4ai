import asyncio
import json
import sys
from typing import Optional, Union
from urllib.parse import quote

import aiohttp
import pytest
from httpx import Response, codes

from .common import TEST_URLS, async_client, markdown_params

EndpointResponse = Optional[Union[dict, str]]


async def endpoint(
    endpoint: str, url: str, params: Optional[dict] = None, expected_status: int = codes.OK
) -> EndpointResponse:
    """Test an endpoint and print results"""
    params = params or {}
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    path = f"/{endpoint}/{quote(url)}"
    if param_str:
        path += f"?{param_str}"

    print(f"\nTesting: {path}")

    async with async_client() as session:
        response: Response = await session.get(path)
        content_type: str = response.headers.get(
            aiohttp.hdrs.CONTENT_TYPE, ""
        ).lower()
        data: Union[dict, str] = (
            response.json() if content_type == "application/json" else response.text
        )

        print(f"Status: {response.status_code} (Expected: {expected_status})")
        if isinstance(data, dict):
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {data[:500]}...")  # First 500 chars
        assert response.status_code == expected_status
        return data


async def llm_task_completion(task_id: str) -> Optional[dict]:
    """Poll task until completion"""
    for _ in range(10):  # Try 10 times
        result: EndpointResponse = await endpoint("llm", task_id)
        assert result, "Failed to process endpoint request"
        assert isinstance(result, dict), "Expected dict response"

        if result and result.get("status") in ["completed", "failed"]:
            return result
        print("Task still processing, waiting 5 seconds...")
        await asyncio.sleep(5)
    print("Task timed out")
    return None


@pytest.mark.asyncio
@pytest.mark.timeout(60) # LLM tasks can take a while.
@pytest.mark.parametrize("url,params", markdown_params())
async def test_markdown_endpoint(url: str, params: dict[str, str]):
    response: EndpointResponse = await endpoint("md", url, params)
    assert response, "Failed to process endpoint request"
    assert isinstance(response, str), "Expected str response"


@pytest.mark.asyncio
@pytest.mark.parametrize("url", TEST_URLS)
@pytest.mark.skip("LLM endpoint doesn't task based requests yet")
async def test_llm_endpoint_no_schema(url: str):
    result: EndpointResponse = await endpoint(
        "llm", url, {"q": "Extract title and main content"}
    )
    assert result, "Failed to process endpoint request"
    assert isinstance(result, dict), "Expected dict response"
    assert "task_id" in result

    print("\nChecking task completion...")
    await llm_task_completion(result["task_id"])


@pytest.mark.asyncio
@pytest.mark.parametrize("url", TEST_URLS)
@pytest.mark.skip("LLM endpoint doesn't task based or schema requests yet")
async def test_llm_endpoint_schema(url: str):
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "links": {"type": "array", "items": {"type": "string"}},
        },
    }
    result: EndpointResponse = await endpoint(
        "llm",
        url,
        {
            "q": "Extract content with links",
            "s": json.dumps(schema),
            "c": "1",  # Test with cache
        },
    )
    assert result, "Failed to process endpoint request"
    assert isinstance(result, dict), "Expected dict response"
    assert "task_id" in result
    print("\nChecking schema task completion...")
    await llm_task_completion(result["task_id"])


@pytest.mark.asyncio
async def test_invalid_url():
    await endpoint("md", "not_a_real_url", expected_status=codes.INTERNAL_SERVER_ERROR)


@pytest.mark.asyncio
async def test_invalid_filter():
    await endpoint("md", "example.com", {"f": "invalid"}, expected_status=codes.UNPROCESSABLE_ENTITY)


@pytest.mark.asyncio
async def test_llm_without_query():
    await endpoint("llm", "example.com", expected_status=codes.BAD_REQUEST)


@pytest.mark.asyncio
async def test_invalid_task():
    await endpoint("llm", "llm_invalid_task", expected_status=codes.BAD_REQUEST)


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
