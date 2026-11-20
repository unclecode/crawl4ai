"""Sitemap index following must stay bounded on hostile sitemaps.

A seeded site controls its own sitemaps. An index that lists itself, an endless
chain of distinct indexes, or a small body that inflates to gigabytes must not
stall the seeding job or exhaust memory.
"""
import asyncio
import gzip
import io
import sys
from types import SimpleNamespace

import httpx
import pytest

sys.modules.setdefault("rank_bm25", SimpleNamespace(BM25Okapi=object))

import crawl4ai.async_url_seeder as seeder_mod
from crawl4ai.async_url_seeder import AsyncUrlSeeder

NS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'


def _index(*locs):
    body = "".join(f"<sitemap><loc>{u}</loc></sitemap>" for u in locs)
    return f'<?xml version="1.0"?><sitemapindex {NS}>{body}</sitemapindex>'.encode()


def _urlset(*locs, pad=0):
    body = "".join(f"<url><loc>{u}</loc></url>" for u in locs)
    return f'<?xml version="1.0"?><urlset {NS}>{body}'.encode() + b" " * pad + b"</urlset>"


def _gzip(data):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as g:
        g.write(data)
    return buf.getvalue()


def _seeder(handler):
    return AsyncUrlSeeder(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


async def _collect(agen):
    return [u async for u in agen]


@pytest.mark.asyncio
async def test_self_referencing_index_is_fetched_once():
    hits = []

    def handler(req):
        hits.append(str(req.url))
        if req.url.path == "/index.xml":
            return httpx.Response(200, content=_index("http://evil.test/index.xml",
                                                      "http://evil.test/index.xml",
                                                      "http://evil.test/page.xml"))
        return httpx.Response(200, content=_urlset("http://evil.test/a"))

    urls = await asyncio.wait_for(
        _collect(_seeder(handler)._iter_sitemap("http://evil.test/index.xml")), 5)
    assert urls == ["http://evil.test/a"]
    assert hits.count("http://evil.test/index.xml") == 1


@pytest.mark.asyncio
async def test_self_referencing_index_from_prefetched_content():
    def handler(req):
        return httpx.Response(200, content=_index("http://evil.test/index.xml"))

    s = _seeder(handler)
    urls = await asyncio.wait_for(
        _collect(s._iter_sitemap_content("http://evil.test/index.xml",
                                         _index("http://evil.test/index.xml"))), 5)
    assert urls == []


@pytest.mark.asyncio
async def test_endless_chain_of_distinct_indexes_stops_at_depth_limit():
    hits = []

    def handler(req):
        n = int(req.url.params.get("n", "0"))
        hits.append(n)
        return httpx.Response(200, content=_index(f"http://evil.test/i.xml?n={n + 1}"))

    await asyncio.wait_for(
        _collect(_seeder(handler)._iter_sitemap("http://evil.test/i.xml?n=0")), 5)
    assert max(hits) <= seeder_mod._SITEMAP_MAX_DEPTH


@pytest.mark.asyncio
async def test_wide_fanout_stops_at_file_budget(monkeypatch):
    monkeypatch.setattr(seeder_mod, "_SITEMAP_MAX_FILES", 20, raising=False)
    hits = []

    def handler(req):
        hits.append(str(req.url))
        n = req.url.params.get("n", "")
        return httpx.Response(200, content=_index(*(f"http://evil.test/i.xml?n={n}{k}" for k in range(10))))

    await asyncio.wait_for(
        _collect(_seeder(handler)._iter_sitemap("http://evil.test/i.xml")), 5)
    assert len(hits) <= 20


@pytest.mark.asyncio
async def test_gzip_bomb_sitemap_is_refused(monkeypatch):
    monkeypatch.setattr(seeder_mod, "_SITEMAP_MAX_BYTES", 1 << 20, raising=False)
    bomb = _gzip(_urlset("http://evil.test/a", pad=2 << 20))
    assert len(bomb) < (1 << 20)

    def handler(req):
        return httpx.Response(200, content=bomb)

    s = _seeder(handler)
    assert await _collect(s._iter_sitemap("http://evil.test/s.xml.gz")) == []
    assert await _collect(s._iter_sitemap_content("http://evil.test/s.xml.gz", bomb)) == []


@pytest.mark.asyncio
async def test_content_encoding_bomb_is_refused(monkeypatch):
    monkeypatch.setattr(seeder_mod, "_SITEMAP_MAX_BYTES", 1 << 20, raising=False)
    bomb = _gzip(_urlset("http://evil.test/a", pad=2 << 20))

    def handler(req):
        return httpx.Response(200, content=bomb, headers={"Content-Encoding": "gzip"})

    assert await _collect(_seeder(handler)._iter_sitemap("http://evil.test/s.xml")) == []


@pytest.mark.asyncio
async def test_oversized_raw_sitemap_is_refused(monkeypatch):
    monkeypatch.setattr(seeder_mod, "_SITEMAP_MAX_BYTES", 1 << 20, raising=False)

    def handler(req):
        return httpx.Response(200, content=_urlset("http://evil.test/a", pad=2 << 20))

    assert await _collect(_seeder(handler)._iter_sitemap("http://evil.test/s.xml")) == []


@pytest.mark.asyncio
async def test_normal_index_still_works():
    def handler(req):
        if req.url.path == "/index.xml.gz":
            return httpx.Response(200, content=_gzip(_index("http://ok.test/a.xml", "http://ok.test/b.xml")))
        return httpx.Response(200, content=_urlset(f"http://ok.test{req.url.path}.page"))

    urls = await _collect(_seeder(handler)._iter_sitemap("http://ok.test/index.xml.gz"))
    assert sorted(urls) == ["http://ok.test/a.xml.page", "http://ok.test/b.xml.page"]


# ── behaviour that must not change ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_multi_member_gzip_sitemap_reads_every_member():
    data = _urlset("http://ok.test/a", "http://ok.test/b")
    half = len(data) // 2
    two_members = _gzip(data[:half]) + _gzip(data[half:])

    def handler(req):
        return httpx.Response(200, content=two_members)

    urls = await _collect(_seeder(handler)._iter_sitemap("http://ok.test/s.xml.gz"))
    assert urls == ["http://ok.test/a", "http://ok.test/b"]


@pytest.mark.asyncio
async def test_relative_locs_and_redirects_resolve_against_final_url():
    def handler(req):
        if req.url.path == "/old.xml":
            return httpx.Response(301, headers={"Location": "http://ok.test/new/index.xml"})
        if req.url.path == "/new/index.xml":
            return httpx.Response(200, content=_index("child.xml"))
        if req.url.path == "/new/child.xml":
            return httpx.Response(200, content=_urlset("page"))
        return httpx.Response(404)

    urls = await _collect(_seeder(handler)._iter_sitemap("http://ok.test/old.xml"))
    assert urls == ["http://ok.test/new/page"]


@pytest.mark.asyncio
async def test_failed_child_does_not_stop_siblings():
    def handler(req):
        if req.url.path == "/index.xml":
            return httpx.Response(200, content=_index("http://ok.test/bad.xml", "http://ok.test/good.xml"))
        if req.url.path == "/bad.xml":
            return httpx.Response(500)
        return httpx.Response(200, content=_urlset("http://ok.test/a"))

    assert await _collect(_seeder(handler)._iter_sitemap("http://ok.test/index.xml")) == ["http://ok.test/a"]


@pytest.mark.asyncio
async def test_separate_calls_do_not_share_a_budget():
    def handler(req):
        return httpx.Response(200, content=_urlset("http://ok.test/a"))

    s = _seeder(handler)
    assert await _collect(s._iter_sitemap("http://ok.test/s.xml")) == ["http://ok.test/a"]
    assert await _collect(s._iter_sitemap("http://ok.test/s.xml")) == ["http://ok.test/a"]


@pytest.mark.asyncio
async def test_sitemap_at_exactly_the_size_limit_is_accepted(monkeypatch):
    monkeypatch.setattr(seeder_mod, "_SITEMAP_MAX_BYTES", 1 << 20)
    head = _urlset("http://ok.test/a")
    body = head[:-len(b"</urlset>")] + b" " * ((1 << 20) - len(head)) + b"</urlset>"
    assert len(body) == 1 << 20

    def handler(req):
        return httpx.Response(200, content=_gzip(body) if req.url.path.endswith(".gz") else body)

    s = _seeder(handler)
    assert await _collect(s._iter_sitemap("http://ok.test/s.xml")) == ["http://ok.test/a"]
    assert await _collect(s._iter_sitemap("http://ok.test/s.xml.gz")) == ["http://ok.test/a"]
