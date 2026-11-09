"""Exercise Atom element identity through public DomainMapper feed discovery."""

import asyncio

import httpx
import pytest

from crawl4ai import DomainMapper, DomainMapperConfig, domain_mapper

ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"


@pytest.mark.parametrize("use_lxml", [True, False], ids=["lxml", "stdlib"])
@pytest.mark.parametrize(
    "feed",
    [
        pytest.param(
            f'<feed xmlns="{ATOM_NAMESPACE}" xmlns:ext="urn:extension">'
            '<entry><ext:link href="/foreign"/><link href="/article"/></entry></feed>',
            id="foreign-link-first",
        ),
        pytest.param(
            f'<feed xmlns="{ATOM_NAMESPACE}" xmlns:ext="urn:extension">'
            '<ext:entry><link href="/foreign"/></ext:entry>'
            '<entry><link href="/article"/></entry></feed>',
            id="foreign-entry",
        ),
        pytest.param(
            f'<feed xmlns="{ATOM_NAMESPACE}">'
            '<entry xmlns=""><link href="/foreign"/></entry>'
            '<entry><link href="/article"/></entry></feed>',
            id="namespace-reset-in-atom",
        ),
        pytest.param(
            f'<feed xmlns="{ATOM_NAMESPACE}" xmlns:ext="urn:extension">'
            "<ext:item><ext:link>/foreign</ext:link></ext:item>"
            "<ext:item><ext:guid>https://example.org/foreign-guid</ext:guid></ext:item>"
            '<entry><link href="/article"/></entry></feed>',
            id="rss-lookalike-extension",
        ),
        pytest.param(
            f'<feed xmlns="{ATOM_NAMESPACE}" xmlns:ext="urn:extension">'
            '<ext:container><entry><link href="/foreign"/></entry></ext:container>'
            '<entry><link href="/article"/></entry></feed>',
            id="nested-entry-extension",
        ),
        pytest.param(
            '<feed xmlns="http://purl.org/atom/ns#" xmlns:ext="urn:extension">'
            '<entry><ext:link href="/foreign"/><link href="/article"/></entry></feed>',
            id="legacy-atom-03",
        ),
        pytest.param(
            f'<a:feed xmlns:a="{ATOM_NAMESPACE}" xmlns:b="{ATOM_NAMESPACE}">'
            '<a:entry><b:link href="/article"/></a:entry></a:feed>',
            id="same-uri-prefix-alias",
        ),
        pytest.param(
            '<feed><entry><link href="/article"/></entry></feed>',
            id="legacy-unqualified-atom",
        ),
        pytest.param(
            '<rss xmlns="urn:rss"><channel>'
            "<item><link>/article</link></item></channel></rss>",
            id="legacy-namespaced-rss",
        ),
    ],
)
def test_scan_feed_element_namespaces(feed, use_lxml, monkeypatch, tmp_path):
    if use_lxml and not domain_mapper.LXML:
        pytest.skip("lxml is not installed")
    monkeypatch.setattr(domain_mapper, "LXML", use_lxml)
    monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(tmp_path))

    def respond(request):
        if request.url.path == "/":
            return httpx.Response(200)
        if request.url.path == "/feed":
            return httpx.Response(
                200, text=feed, headers={"Content-Type": "application/xml"}
            )
        return httpx.Response(404)

    async def scan():
        config = DomainMapperConfig(
            source="feed",
            include_subdomains=False,
            extract_head=False,
            soft_404_detection=False,
            verbose=False,
        )
        transport = httpx.MockTransport(respond)
        async with httpx.AsyncClient(transport=transport) as client:
            async with DomainMapper(client=client, base_directory=tmp_path) as mapper:
                return await mapper.scan("example.org", config)

    results = asyncio.run(scan())
    assert [(row["url"], row["source"]) for row in results] == [
        ("https://example.org/article", "feed")
    ]


@pytest.mark.parametrize("use_lxml", [True, False], ids=["lxml", "stdlib"])
def test_atom_entry_document_keeps_existing_parser_policy(use_lxml, monkeypatch):
    if use_lxml and not domain_mapper.LXML:
        pytest.skip("lxml is not installed")
    monkeypatch.setattr(domain_mapper, "LXML", use_lxml)
    mapper = DomainMapper.__new__(DomainMapper)
    body = f'<entry xmlns="{ATOM_NAMESPACE}"><link href="/article"/></entry>'

    expected = ["https://example.org/article"] if use_lxml else []
    assert mapper._parse_feed_xml(body, "https://example.org/feed") == expected


@pytest.mark.parametrize("use_lxml", [True, False], ids=["lxml", "stdlib"])
def test_atom_extension_cannot_trigger_rss_guid_fallback(use_lxml, monkeypatch):
    if use_lxml and not domain_mapper.LXML:
        pytest.skip("lxml is not installed")
    monkeypatch.setattr(domain_mapper, "LXML", use_lxml)
    mapper = DomainMapper.__new__(DomainMapper)
    body = (
        f'<feed xmlns="{ATOM_NAMESPACE}" xmlns:ext="urn:extension">'
        "<ext:item><ext:guid>https://example.org/foreign</ext:guid></ext:item>"
        "</feed>"
    )
    assert mapper._parse_feed_xml(body, "https://example.org/feed") == []
