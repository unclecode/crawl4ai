"""Exercise the Docker SDK's public consumer against ordinary NDJSON frames."""

import json
from unittest.mock import Mock

import httpx
import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.docker_client import Crawl4aiDockerClient, RequestError

FIRST_URL = "https://example.test/first"
SECOND_URL = "https://example.test/second"
FAILED_URL = "https://example.test/failed"
UNSERIALIZABLE_URL = "https://example.test/unserializable"
SUCCESS = {"url": FIRST_URL, "html": "<p>One</p>", "success": True, "timing": 0.12}
TIMEOUT = {"status": "error", "error": "Crawl exceeded the time limit"}


class StreamBody(httpx.AsyncByteStream):
    def __init__(self, records):
        self.records = records
        self.closed = False

    async def __aiter__(self):
        for index, record in enumerate(self.records):
            line_ending = b"\n" if index < len(self.records) - 1 else b""
            yield json.dumps(record).encode() + line_ending

    async def aclose(self):
        self.closed = True


@pytest.fixture
def install_stream(monkeypatch):
    real_client = httpx.AsyncClient

    def install(records):
        body = StreamBody(records)

        def handler(request):
            if request.url.path == "/health":
                return httpx.Response(200, json={"status": "ok"})
            assert request.method == "POST"
            assert request.url.path == "/crawl/stream"
            return httpx.Response(
                200,
                headers={"Content-Type": "application/x-ndjson"},
                stream=body,
            )

        def client_with_mock_transport(**kwargs):
            return real_client(transport=httpx.MockTransport(handler), **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", client_with_mock_transport)
        return body

    return install


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_results", [[], [SUCCESS]], ids=["empty", "partial"])
async def test_stream_terminal_error_is_raised_and_response_is_closed(
    install_stream, initial_results
):
    body = install_stream([*initial_results, TIMEOUT])

    async with Crawl4aiDockerClient(verbose=False) as client:
        stream = await client.crawl(
            [FIRST_URL, SECOND_URL], crawler_config=CrawlerRunConfig(stream=True)
        )
        if initial_results:
            result = await anext(stream)
            assert (result.url, result.success) == (FIRST_URL, True)

        with pytest.raises(RequestError, match="Crawl exceeded the time limit"):
            await anext(stream)

        assert body.closed
        with pytest.raises(StopAsyncIteration):
            await anext(stream)


@pytest.mark.asyncio
async def test_stream_reports_each_result_and_keeps_completion_out_of_url_logs(
    install_stream, monkeypatch
):
    per_item_error = {"url": UNSERIALIZABLE_URL, "error": "Serialization failed"}
    failed_result = {
        "url": FAILED_URL,
        "html": "",
        "success": False,
        "error_message": "Failed to load",
        "timing": 0.24,
    }
    next_result = {"url": SECOND_URL, "html": "<p>Two</p>", "success": True}
    body = install_stream(
        [SUCCESS, per_item_error, failed_result, next_result, {"status": "completed"}]
    )

    async with Crawl4aiDockerClient(verbose=False) as client:
        url_status = Mock()
        error_status = Mock()
        monkeypatch.setattr(client.logger, "url_status", url_status)
        monkeypatch.setattr(client.logger, "error_status", error_status)
        results = [
            result
            async for result in await client.crawl(
                [FIRST_URL, UNSERIALIZABLE_URL, FAILED_URL, SECOND_URL],
                crawler_config=CrawlerRunConfig(stream=True),
            )
        ]

        assert body.closed
        assert [(result.url, result.success) for result in results] == [
            (FIRST_URL, True),
            (FAILED_URL, False),
            (SECOND_URL, True),
        ]
        assert results[1].error_message == "Failed to load"
        error_status.assert_called_once_with(
            url=UNSERIALIZABLE_URL, error="Serialization failed"
        )
        assert [call.kwargs for call in url_status.call_args_list] == [
            {"url": FIRST_URL, "success": True, "timing": 0.12},
            {"url": FAILED_URL, "success": False, "timing": 0.24},
            {"url": SECOND_URL, "success": True, "timing": 0.0},
        ]
