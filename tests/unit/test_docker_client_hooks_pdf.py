"""Crawl4aiDockerClient: declarative hooks, server hook warnings, and PDF decoding."""
import base64
import json

import httpx
import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.docker_client import Crawl4aiDockerClient

PDF = b"%PDF-1.4 fake"
RESULT = {"url": "https://example.com", "html": "<html></html>", "success": True,
          "pdf": base64.b64encode(PDF).decode()}
WARNING = "hook code was NOT executed"
STREAM = CrawlerRunConfig(stream=True)


def _client(monkeypatch, sent, response_json=None, headers=None):
    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={})
        sent.append(json.loads(request.content))
        if request.url.path == "/crawl/stream":
            body = json.dumps(RESULT) + "\n" + json.dumps({"status": "completed"})
            return httpx.Response(200, text=body, headers=headers)
        return httpx.Response(200, json=response_json or {"success": True, "results": [RESULT]})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )
    return Crawl4aiDockerClient(base_url="http://server", verbose=False)


@pytest.mark.asyncio
async def test_hooks_are_sent(monkeypatch):
    sent = []
    hooks = [{"action": "block_resources", "params": {"resource_types": ["image"]}}]
    legacy = {"before_goto": "async def hook(page, **kw): return page"}
    async with _client(monkeypatch, sent) as client:
        await client.crawl(["https://example.com"], hooks=hooks, hooks_timeout=15)
        await client.crawl(["https://example.com"], hooks=[])
        await client.crawl(["https://example.com"], hooks=legacy)
    assert sent[0]["hooks"] == {"hooks": hooks, "timeout": 15}
    assert "hooks" not in sent[1]
    assert sent[2]["hooks"] == {"code": legacy, "timeout": 30}


@pytest.mark.asyncio
async def test_hooks_warning_is_raised(monkeypatch):
    response = {"success": True, "results": [RESULT], "hooks": {"warning": WARNING}}
    async with _client(monkeypatch, [], response_json=response, headers={"X-Hooks-Warning": WARNING}) as client:
        with pytest.warns(UserWarning, match="NOT executed"):
            await client.crawl(["https://example.com"])
        with pytest.warns(UserWarning, match="NOT executed"):
            async for _ in await client.crawl(["https://example.com"], crawler_config=STREAM):
                pass


@pytest.mark.asyncio
async def test_pdf_is_decoded(monkeypatch):
    async with _client(monkeypatch, []) as client:
        result = await client.crawl(["https://example.com"])
        streamed = [r async for r in await client.crawl(["https://example.com"], crawler_config=STREAM)]
    assert result.pdf == PDF
    assert streamed[0].pdf == PDF
    assert Crawl4aiDockerClient._to_result({**RESULT, "pdf": "QUJD!"}).pdf == b"QUJD!"
