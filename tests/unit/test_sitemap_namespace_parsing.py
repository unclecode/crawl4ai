import gzip
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
    def __init__(self, request_url: str, text: str | bytes):
        self.status_code = 200
        self._content = text if isinstance(text, bytes) else text.encode("utf-8")
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


GZ_CHILD_XML = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://example.com/posts/1</loc></url>
</urlset>
"""


def _index_for(child_url: str) -> str:
    return f"""<?xml version="1.0"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap><loc>{child_url}</loc></sitemap>
    </sitemapindex>
    """


async def _collect_from_index(child_url: str, child_body) -> list:
    seeder = AsyncUrlSeeder(
        client=DummyAsyncClient(
            {
                "https://example.com/sitemap.xml": _index_for(child_url),
                child_url: child_body,
            }
        )
    )
    return [u async for u in seeder._iter_sitemap("https://example.com/sitemap.xml")]


@pytest.mark.asyncio
async def test_iter_sitemap_decompresses_gzipped_sitemap():
    urls = await _collect_from_index(
        "https://example.com/posts.xml.gz", gzip.compress(GZ_CHILD_XML.encode())
    )

    assert urls == ["https://example.com/posts/1"]


@pytest.mark.asyncio
async def test_iter_sitemap_reads_gz_sitemap_already_decoded_by_the_client():
    urls = await _collect_from_index("https://example.com/posts.xml.gz", GZ_CHILD_XML)

    assert urls == ["https://example.com/posts/1"]


@pytest.mark.asyncio
async def test_iter_sitemap_decompresses_gzipped_sitemap_without_gz_suffix():
    urls = await _collect_from_index(
        "https://example.com/posts.xml.gz?v=2", gzip.compress(GZ_CHILD_XML.encode())
    )

    assert urls == ["https://example.com/posts/1"]
