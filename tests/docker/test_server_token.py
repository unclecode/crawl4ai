import json
import sys
from typing import AsyncGenerator, Optional, Union
from urllib.parse import quote

import aiohttp
import pytest
import pytest_asyncio
from httpx import AsyncClient, Response, codes

from tests.docker.common import TEST_URLS, async_client, markdown_params


async def get_token(client: AsyncClient, email: str = "test@example.com") -> str:
    """Fetch a JWT token from the /token endpoint."""
    path: str = "/token"
    payload: dict[str, str] = {"email": email}
    print(f"\nFetching token from {path} with email: {email}")
    response: Response = await client.post(path, json=payload)
    data = response.json()
    print(f"Token Response Status: {response.status_code}")
    print(f"Token Response: {json.dumps(data, indent=2)}")
    assert response.status_code == codes.OK
    return data["access_token"]


@pytest_asyncio.fixture(loop_scope="class")
async def setup_session() -> AsyncGenerator[tuple[AsyncClient, str], None]:
    async with async_client() as client:
        token: str = await get_token(client)
        assert token, "Failed to get token"

        yield client, token


@pytest.mark.asyncio(loop_scope="class")
class TestAPI:
    async def endpoint(
        self,
        client: AsyncClient,
        token: str,
        endpoint: str,
        url: str,
        params: Optional[dict] = None,
        expected_status: int = codes.OK,
    ) -> Union[dict, str]:
        """Test an endpoint with token and print results."""
        path = f"/{endpoint}/{quote(url)}"
        if params:
            path += "?" + "&".join(f"{k}={v}" for k, v in params.items())

        headers = {"Authorization": f"Bearer {token}"}
        print(f"\nTesting: {path}")

        response: Response = await client.get(path, headers=headers)
        content_type: str = response.headers.get(aiohttp.hdrs.CONTENT_TYPE, "").lower()
        data: Union[dict, str] = (
            response.json() if content_type == "application/json" else response.text
        )
        print(f"Status: {response.status_code} (Expected: {expected_status})")
        if isinstance(data, dict):
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {data[:500]}...")  # First 500 chars
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}"
        )
        return data

    async def stream_crawl(self, client: AsyncClient, token: str):
        """Test the /crawl/stream endpoint with multiple URLs."""
        url = "/crawl/stream"
        payload = {
            "urls": [
                "https://example.com",
                "https://example.com/page1",  # Replicated example.com with variation
                "https://example.com/page2",  # Replicated example.com with variation
                "https://example.com/page3",  # Replicated example.com with variation
            ],
            "browser_config": {"headless": True, "viewport": {"width": 1200}},
            "crawler_config": {"stream": True, "cache_mode": "aggressive"},
        }
        headers = {"Authorization": f"Bearer {token}"}
        print(f"\nTesting Streaming Crawl: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        async with client.stream(
            "POST", url, json=payload, headers=headers
        ) as response:
            print(f"Status: {response.status_code} (Expected: {codes.OK})")
            assert response.status_code == codes.OK, (
                f"Expected {codes.OK}, got {response.status_code}"
            )

            # Read streaming response line-by-line (NDJSON)
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line.strip())
                    print(f"Streamed Result: {json.dumps(data, indent=2)}")

    async def test_crawl_endpoint(self, setup_session: tuple[AsyncClient, str]):
        client, token = setup_session
        crawl_payload = {
            "urls": ["https://example.com"],
            "browser_config": {"headless": True},
            "crawler_config": {"stream": False},
        }
        response = await client.post(
            "/crawl",
            json=crawl_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        print(f"\nCrawl Endpoint Status: {response.status_code}")
        print(f"Crawl Response: {json.dumps(data, indent=2)}")

    @pytest.mark.asyncio
    async def test_stream_endpoint(self, setup_session: tuple[AsyncClient, str]):
        client, token = setup_session
        await self.stream_crawl(client, token)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("url,params", markdown_params())
    @pytest.mark.timeout(60) # LLM tasks can take a while.
    async def test_markdown_endpoint(
        self,
        url: str,
        params: dict[str, str],
        setup_session: tuple[AsyncClient, str],
    ):
        client, token = setup_session
        result: Union[dict, str] = await self.endpoint(client, token, "md", url, params)
        assert isinstance(result, str), "Expected str response"
        assert result, "Expected non-empty response"

    @pytest.mark.parametrize("url", TEST_URLS)
    async def test_llm_endpoint_no_schema(
        self, url: str, setup_session: tuple[AsyncClient, str]
    ):
        client, token = setup_session
        # Test basic extraction (direct response now)
        result = await self.endpoint(
            client,
            token,
            "llm",
            url,
            {"q": "Extract title and main content"},
        )
        assert isinstance(result, dict), "Expected dict response"
        assert "answer" in result, "Expected 'answer' key in response"

    # Currently the server handles LLM requests using handle_llm_qa
    # which doesn't use handle_llm_request which is where the schema
    # is processed.
    @pytest.mark.parametrize("url", TEST_URLS)
    @pytest.mark.skip("LLM endpoint doesn't schema request yet")
    async def test_llm_endpoint_schema(
        self, url: str, setup_session: tuple[AsyncClient, str]
    ):
        client, token = setup_session
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "links": {"type": "array", "items": {"type": "string"}},
            },
        }
        result = await self.endpoint(
            client,
            token,
            "llm",
            url,
            {
                "q": "Extract content with links",
                "s": json.dumps(schema),
                "c": "1",  # Test with cache
            },
        )
        assert isinstance(result, dict), "Expected dict response"
        assert "answer" in result, "Expected 'answer' key in response"
        print(result)

    async def test_invalid_url(self, setup_session: tuple[AsyncClient, str]):
        client, token = setup_session
        await self.endpoint(client, token, "md", "not_a_real_url", expected_status=codes.INTERNAL_SERVER_ERROR)

    async def test_invalid_filter(self, setup_session: tuple[AsyncClient, str]):
        client, token = setup_session
        await self.endpoint(
            client,
            token,
            "md",
            "example.com",
            {"f": "invalid"},
            expected_status=codes.UNPROCESSABLE_ENTITY,
        )

    async def test_missing_query(self, setup_session: tuple[AsyncClient, str]):
        client, token = setup_session
        # Test LLM without query (should fail per your server logic)
        await self.endpoint(client, token, "llm", "example.com", expected_status=codes.BAD_REQUEST)


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
