"""Crawl4aiDockerClient sends the server's API token as a Bearer header."""
import httpx
import pytest

from crawl4ai.docker_client import Crawl4aiDockerClient


async def _auth_header(monkeypatch, **kwargs):
    seen = []
    transport = httpx.MockTransport(
        lambda request: seen.append(request.headers.get("Authorization")) or httpx.Response(200, json={})
    )
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real_client(transport=transport, **kw))
    async with Crawl4aiDockerClient(base_url="http://server", verbose=False, **kwargs) as client:
        await client.get_schema()
    return seen[0]


@pytest.mark.asyncio
async def test_api_token_is_sent(monkeypatch):
    assert await _auth_header(monkeypatch, api_token="t1") == "Bearer t1"


@pytest.mark.asyncio
async def test_no_token_sends_no_header(monkeypatch):
    assert await _auth_header(monkeypatch) is None
