from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api import _raise_for_crawl_failure


def test_crawl_failure_is_reported_as_bad_gateway():
    result = SimpleNamespace(success=False, error_message="Blocked by anti-bot protection: challenge")

    with pytest.raises(HTTPException) as raised:
        _raise_for_crawl_failure(result)

    assert raised.value.status_code == 502
    assert raised.value.detail == result.error_message


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/md", {"url": "https://example.com", "f": "raw"}),
        ("get", "/llm/example.com?q=summarize", None),
    ],
)
def test_single_url_crawl_failure_reaches_client(
    stock_client, server_module, monkeypatch, method, path, payload
):
    error_message = "Blocked by anti-bot protection: challenge"
    failed_result = SimpleNamespace(success=False, error_message=error_message)

    class FailedCrawler:
        async def arun(self, *args, **kwargs):
            return failed_result

    async def get_failed_crawler(*args, **kwargs):
        return FailedCrawler()

    async def release_crawler(*args, **kwargs):
        return None

    import api
    import crawler_pool
    from auth import create_access_token

    monkeypatch.setattr(api, "validate_url_destination", lambda url: None)
    monkeypatch.setattr(crawler_pool, "get_crawler", get_failed_crawler)
    monkeypatch.setattr(crawler_pool, "release_crawler", release_crawler)

    token = create_access_token({"sub": "test@example.com"})
    request = getattr(stock_client, method)
    kwargs = {"json": payload} if payload is not None else {}
    response = request(
        path, headers={"Authorization": f"Bearer {token}"}, **kwargs
    )

    assert response.status_code == 502
    assert response.json() == {"detail": error_message}
