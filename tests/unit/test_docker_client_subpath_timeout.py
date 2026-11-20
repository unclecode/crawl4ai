"""Crawl4aiDockerClient: subpath base_url, crawl timeout preservation, and JSON error handling."""

import json

import httpx
import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.docker_client import Crawl4aiDockerClient, RequestError

RESULT = {"url": "https://example.com", "html": "<html></html>", "success": True}


@pytest.mark.asyncio
async def test_subpath_base_url_is_preserved_across_all_endpoints(monkeypatch):
    seen_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "tok"})
        if request.url.path.endswith("/health") or request.url.path.endswith("/schema"):
            return httpx.Response(200, json={})
        if request.url.path.endswith("/crawl/stream"):
            body = json.dumps(RESULT) + "\n" + json.dumps({"status": "completed"})
            return httpx.Response(200, text=body)
        return httpx.Response(200, json={"success": True, "results": [RESULT]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    async with Crawl4aiDockerClient(
        base_url="http://server/crawl4ai/", verbose=False
    ) as client:
        await client.authenticate("user@example.com")
        await client.crawl(["https://example.com"])
        async for _ in await client.crawl(
            ["https://example.com"], crawler_config=CrawlerRunConfig(stream=True)
        ):
            pass
        await client.get_schema()

    assert seen_paths == [
        "/crawl4ai/token",
        "/crawl4ai/health",
        "/crawl4ai/crawl",
        "/crawl4ai/health",
        "/crawl4ai/crawl/stream",
        "/crawl4ai/schema",
    ]


@pytest.mark.asyncio
async def test_crawl_preserves_client_timeout(monkeypatch):
    crawl_timeouts = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/crawl":
            crawl_timeouts.append(request.extensions["timeout"]["read"])
        if request.url.path == "/health":
            return httpx.Response(200, json={})
        return httpx.Response(200, json={"success": True, "results": [RESULT]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    hooks = [{"action": "block_resources", "params": {"resource_types": ["image"]}}]
    async with Crawl4aiDockerClient(
        base_url="http://server", timeout=120.0, verbose=False
    ) as client:
        await client.crawl(["https://example.com"])
        await client.crawl(["https://example.com"], hooks=hooks, hooks_timeout=15)

    async with Crawl4aiDockerClient(
        base_url="http://server", timeout=30.0, verbose=False
    ) as default_client:
        await default_client.crawl(
            ["https://example.com"], hooks=hooks, hooks_timeout=90
        )

    assert crawl_timeouts == [120.0, 120.0, 90.0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, body",
    [
        (502, b"Bad Gateway"),
        (422, b'["invalid payload"]'),
    ],
)
async def test_malformed_or_non_dict_json_error_raises_request_error(
    monkeypatch, status, body
):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            content=body,
            headers={"content-type": "application/json"},
        )

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )

    async with Crawl4aiDockerClient(base_url="http://server", verbose=False) as client:
        with pytest.raises(RequestError, match=f"Server error {status}"):
            await client.get_schema()
