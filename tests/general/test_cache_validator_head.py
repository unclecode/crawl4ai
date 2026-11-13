"""CacheValidator._fetch_head must never fingerprint something that is not a head."""

import asyncio

import httpx

from crawl4ai.cache_validator import CacheValidator


def _client_for(body: bytes, headers: dict[str, str] | None = None) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body, headers=headers or {})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)


def _fetch_head(body: bytes, headers: dict[str, str] | None = None):
    async def run():
        validator = CacheValidator()
        validator._client = _client_for(body, headers)
        try:
            return await validator._fetch_head("https://example.com/page")
        finally:
            await validator.close()

    return asyncio.run(run())


def test_returns_the_head_section_only():
    body = b"<html><head><title>x</title></head><body><p>body</p></body></html>"
    html, _, _ = _fetch_head(body)
    assert html == "<html><head><title>x</title></head>"


def test_close_tag_is_case_insensitive():
    body = b"<html><HEAD><title>x</title></HEAD><body><p>body</p></body></html>"
    html, _, _ = _fetch_head(body)
    assert html == "<html><HEAD><title>x</title></HEAD>"


def test_document_without_head_close_tag_reports_no_head():
    # Regression: the truncated buffer (here the whole body) used to be returned
    # as the head, so its fingerprint could never match the stored one.
    body = b"<html><body><p>no head element</p></body></html>"
    html, _, _ = _fetch_head(body)
    assert html is None


def test_empty_response_keeps_the_cached_validators():
    # Regression: `content` was only bound inside the stream loop, so an empty
    # body raised UnboundLocalError and the etag/last-modified were dropped.
    headers = {"etag": '"v1"', "last-modified": "Tue, 12 Nov 2026 10:00:00 GMT"}
    html, etag, last_modified = _fetch_head(b"", headers)
    assert html is None
    assert etag == '"v1"'
    assert last_modified == "Tue, 12 Nov 2026 10:00:00 GMT"
