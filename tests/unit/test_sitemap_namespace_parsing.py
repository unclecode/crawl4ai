import sys
from types import SimpleNamespace

import pytest

# Provide a lightweight stub for rank_bm25 before importing the seeder to avoid
# optional dependency issues (e.g., incompatible wheels in CI).
class _FakeBM25:
    def __init__(self, corpus):
        self._scores = [1.0] * len(corpus)

    def get_scores(self, tokens):
        return self._scores


sys.modules.setdefault("rank_bm25", SimpleNamespace(BM25Okapi=_FakeBM25))

from crawl4ai.async_url_seeder import AsyncUrlSeeder


class DummyResponse:
    def __init__(self, request_url: str, text: str):
        self.status_code = 200
        self._content = text.encode("utf-8")
        self.url = request_url

    def raise_for_status(self):
        return None

    @property
    def content(self):
        return self._content

    @property
    def text(self):
        return self._content.decode("utf-8")


class DummyAsyncClient:
    def __init__(self, response_map):
        self._responses = response_map

    async def get(self, url, **kwargs):
        payload = self._responses[url]
        if callable(payload):
            payload = payload()
        return DummyResponse(url, payload)


@pytest.mark.asyncio
async def test_iter_sitemap_handles_namespace_less_sitemaps():
    xml = """<?xml version="1.0"?>
    <urlset>
        <url><loc>https://example.com/a</loc></url>
        <url><loc>https://example.com/b</loc></url>
    </urlset>
    """
    seeder = AsyncUrlSeeder(client=DummyAsyncClient({"https://example.com/sitemap.xml": xml}))

    urls = []
    async for u in seeder._iter_sitemap("https://example.com/sitemap.xml"):
        urls.append(u)

    assert urls == ["https://example.com/a", "https://example.com/b"]


@pytest.mark.asyncio
async def test_iter_sitemap_handles_custom_namespace():
    xml = """<?xml version="1.0"?>
    <urlset xmlns="https://custom.namespace/schema">
        <url><loc>https://example.com/ns</loc></url>
    </urlset>
    """
    seeder = AsyncUrlSeeder(client=DummyAsyncClient({"https://example.com/ns-sitemap.xml": xml}))

    urls = []
    async for u in seeder._iter_sitemap("https://example.com/ns-sitemap.xml"):
        urls.append(u)

    assert urls == ["https://example.com/ns"]


@pytest.mark.asyncio
async def test_iter_sitemap_handles_namespace_index_and_children():
    index_xml = """<?xml version="1.0"?>
    <sitemapindex xmlns="http://another.example/ns">
        <sitemap>
            <loc>https://example.com/child-1.xml</loc>
        </sitemap>
        <sitemap>
            <loc>https://example.com/child-2.xml</loc>
        </sitemap>
    </sitemapindex>
    """
    child_xml = """<?xml version="1.0"?>
    <urlset xmlns="http://irrelevant">
        <url><loc>https://example.com/page-{n}</loc></url>
    </urlset>
    """
    responses = {
        "https://example.com/index.xml": index_xml,
        "https://example.com/child-1.xml": child_xml.format(n=1),
        "https://example.com/child-2.xml": child_xml.format(n=2),
    }
    seeder = AsyncUrlSeeder(client=DummyAsyncClient(responses))

    urls = []
    async for u in seeder._iter_sitemap("https://example.com/index.xml"):
        urls.append(u)

    assert sorted(urls) == [
        "https://example.com/page-1",
        "https://example.com/page-2",
    ]


@pytest.mark.asyncio
async def test_iter_sitemap_normalizes_relative_locations():
    xml = """<?xml version="1.0"?>
    <urlset>
        <url><loc>/relative-path</loc></url>
        <url><loc>https://example.com/absolute</loc></url>
    </urlset>
    """
    seeder = AsyncUrlSeeder(client=DummyAsyncClient({"https://example.com/sitemap.xml": xml}))

    urls = []
    async for u in seeder._iter_sitemap("https://example.com/sitemap.xml"):
        urls.append(u)

    assert urls == [
        "https://example.com/relative-path",
        "https://example.com/absolute",
    ]
