"""#2288: one refused seed must not sink the whole /crawl or /crawl/stream batch."""
import json

import pytest
from fastapi import HTTPException

from crawl4ai import CrawlResult

GOOD = "https://example.com/"
BAD = "https://no-such-host.example/"


@pytest.fixture
def crawled(monkeypatch):
    """Refuse BAD, fake the crawler, and record which URLs reached it."""
    import api
    import crawler_pool

    seen = []

    def validate(url):
        if url == BAD:
            raise HTTPException(400, "URL blocked (SSRF protection): URL blocked")

    class FakeCrawler:
        async def arun(self, url, **kwargs):
            seen.append(url)
            return CrawlResult(url=url, html="ok", success=True)

        async def arun_many(self, urls, config=None, **kwargs):
            seen.extend(urls)
            results = [CrawlResult(url=u, html="ok", success=True) for u in urls]
            if not config.stream:
                return results

            async def gen():
                for r in results:
                    yield r
            return gen()

    async def get_crawler(*args, **kwargs):
        return FakeCrawler()

    async def release_crawler(*args, **kwargs):
        return None

    monkeypatch.setattr(api, "validate_url_destination", validate)
    monkeypatch.setattr(crawler_pool, "get_crawler", get_crawler)
    monkeypatch.setattr(crawler_pool, "release_crawler", release_crawler)
    return seen


def _auth():
    from auth import create_access_token
    return {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'})}"}


def test_batch_crawls_allowed_seeds_and_reports_refused(stock_client, crawled):
    r = stock_client.post("/crawl", json={"urls": [GOOD, BAD]}, headers=_auth())
    assert r.status_code == 200, r.text
    by_url = {res["url"]: res for res in r.json()["results"]}
    assert by_url[GOOD]["success"] is True
    assert by_url[BAD]["success"] is False
    assert by_url[BAD]["error_message"] == "URL blocked (SSRF protection): URL blocked"
    assert crawled == [GOOD]


def test_stream_crawls_allowed_seeds_and_reports_refused(stock_client, crawled):
    r = stock_client.post("/crawl/stream", json={"urls": [GOOD, BAD, GOOD]}, headers=_auth())
    assert r.status_code == 200, r.text
    lines = [json.loads(line) for line in r.text.splitlines() if line]
    results = [l for l in lines if "url" in l]
    assert [(l["url"], l["success"]) for l in results] == [(BAD, False), (GOOD, True), (GOOD, True)]
    assert crawled == [GOOD, GOOD]


@pytest.mark.parametrize("path", ["/crawl", "/crawl/stream"])
def test_all_refused_is_still_400(stock_client, crawled, path):
    r = stock_client.post(path, json={"urls": [BAD, BAD]}, headers=_auth())
    assert r.status_code == 400
    assert crawled == []
