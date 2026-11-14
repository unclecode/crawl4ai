"""The client's HTTP timeout is independent of the server-side hook timeout."""

import json

import httpx
import pytest

from crawl4ai import Crawl4aiDockerClient, CrawlerRunConfig


@pytest.fixture
def recorded_requests(monkeypatch):
    requests = []
    result = {"url": "https://example.com", "html": "<p>Example</p>", "success": True}

    def handler(request):
        requests.append(request)
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/crawl":
            return httpx.Response(200, json={"success": True, "results": [result]})
        if request.url.path == "/crawl/stream":
            return httpx.Response(
                200,
                text=json.dumps(result) + '\n{"status": "completed"}\n',
                headers={"Content-Type": "application/x-ndjson"},
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async_client = httpx.AsyncClient

    def mock_client(*args, **kwargs):
        return async_client(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_client)
    return requests


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["batch", "stream"])
@pytest.mark.parametrize("hooks_timeout", [None, 7], ids=["default-hook", "short-hook"])
@pytest.mark.parametrize("with_hooks", [False, True], ids=["no-hooks", "hooks"])
@pytest.mark.parametrize(
    "timeout", [120.0, 1.0, None], ids=["long", "short", "default"]
)
async def test_crawl_uses_client_timeout(
    recorded_requests, timeout, with_hooks, hooks_timeout, stream
):
    client_kwargs = {"base_url": "http://crawl4ai.test", "verbose": False}
    if timeout is not None:
        client_kwargs["timeout"] = timeout

    crawl_kwargs = {"crawler_config": CrawlerRunConfig(stream=stream)}
    hooks = {"before_goto": "async def before_goto(page, **kwargs):\n    return page"}
    if with_hooks:
        crawl_kwargs["hooks"] = hooks
    if hooks_timeout is not None:
        crawl_kwargs["hooks_timeout"] = hooks_timeout

    async with Crawl4aiDockerClient(**client_kwargs) as client:
        result = await client.crawl(["https://example.com"], **crawl_kwargs)
        if stream:
            results = [item async for item in result]
            assert len(results) == 1
            result = results[0]
        assert result.success
        assert result.url == "https://example.com"

    endpoint = "/crawl/stream" if stream else "/crawl"
    assert [(request.method, request.url.path) for request in recorded_requests] == [
        ("GET", "/health"),
        ("POST", endpoint),
    ]

    payload = json.loads(recorded_requests[1].content)
    if with_hooks:
        assert payload["hooks"] == {
            "code": hooks,
            "timeout": hooks_timeout if hooks_timeout is not None else 30,
        }
    else:
        assert "hooks" not in payload

    expected_timeout = timeout if timeout is not None else 30.0
    for request in recorded_requests:
        assert request.extensions["timeout"] == {
            phase: expected_timeout for phase in ("connect", "read", "write", "pool")
        }
