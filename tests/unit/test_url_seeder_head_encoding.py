"""Exercise head decoding through the public seeder with an HTTP transport fixture."""

import httpx
import pytest

import crawl4ai.async_url_seeder as seeder_module
from crawl4ai.async_configs import SeedingConfig
from crawl4ai.async_url_seeder import AsyncUrlSeeder, _parse_head


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prefix", "declaration", "title", "description", "charset"),
    [
        pytest.param("", "", "Café 東京", "Résumé", None, id="no-html-charset"),
        pytest.param(
            "",
            '<meta charset="utf-8">',
            "Café 東京",
            "Résumé",
            "utf-8",
            id="meta-charset",
        ),
        pytest.param(
            "",
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">',
            "Café 東京",
            "Résumé",
            None,
            id="http-equiv-charset",
        ),
        pytest.param("\ufeff", "", "Café 東京", "Résumé", None, id="utf8-bom"),
        pytest.param(
            '<?xml version="1.0" encoding="UTF-8"?>',
            "",
            "Café 東京",
            "Résumé",
            None,
            id="xml-encoding-declaration",
        ),
        pytest.param("", "", "Plain title", "Plain description", None, id="ascii"),
    ],
)
async def test_public_seeder_preserves_decoded_head_text(
    tmp_path, prefix, declaration, title, description, charset
):
    page_url = "https://example.test/article"
    page = (
        f"{prefix}<html><head>{declaration}<title>{title}</title>"
        f'<meta name="description" content="{description}">'
        "</head><body>Article body</body></html>"
    ).encode("utf-8")
    sitemap = f"<urlset><url><loc>{page_url}</loc></url></urlset>".encode()
    requests = []

    def respond(request):
        requests.append((request.method, str(request.url)))
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, content=sitemap)
        assert request.method == "GET" and str(request.url) == page_url
        return httpx.Response(
            200, content=page, headers={"Content-Type": "text/html; charset=utf-8"}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        seeder = AsyncUrlSeeder(
            client=client,
            base_directory=tmp_path / "base",
            cache_root=tmp_path / "cache",
        )
        results = await seeder.urls(
            "example.test",
            SeedingConfig(
                source="sitemap",
                extract_head=True,
                concurrency=1,
                hits_per_sec=0,
                force=True,
            ),
        )

    assert requests == [
        ("HEAD", "https://example.test/sitemap.xml"),
        ("GET", "https://example.test/sitemap.xml"),
        ("GET", page_url),
    ]
    assert len(results) == 1
    assert results[0]["url"] == page_url
    assert results[0]["status"] == "valid"
    head = results[0]["head_data"]
    assert (head["title"], head["meta"]["description"]) == (title, description)
    assert head["charset"] == charset


@pytest.mark.parametrize(
    ("prefix", "declaration"),
    [
        pytest.param("", '<meta charset="iso-8859-1">', id="conflicting-meta"),
        pytest.param(
            '<?xml version="1.0" encoding="ISO-8859-1"?>',
            "",
            id="conflicting-xml-declaration",
        ),
    ],
)
def test_decoded_strings_keep_unicode_despite_charset_declarations(prefix, declaration):
    head = _parse_head(
        f"{prefix}<html><head>{declaration}<title>Café</title></head></html>"
    )

    assert head["title"] == "Café"
    if declaration:
        assert head["charset"] == "iso-8859-1"


@pytest.mark.parametrize(
    ("prefix", "declaration", "encoding"),
    [
        pytest.param("", '<meta charset="iso-8859-1">', "latin-1", id="latin1-meta"),
        pytest.param("\ufeff", "", "utf-8", id="utf8-bom"),
    ],
)
def test_byte_inputs_keep_encoding_autodetection(prefix, declaration, encoding):
    raw = (
        f"{prefix}<html><head>{declaration}<title>Café</title></head></html>"
    ).encode(encoding)

    assert _parse_head(raw)["title"] == "Café"


def test_empty_inputs_keep_the_parse_failure_result():
    assert _parse_head("") == {}
    assert _parse_head(b"") == {}


def test_regex_fallback_keeps_unicode(monkeypatch):
    monkeypatch.setattr(seeder_module, "LXML", False)

    head = _parse_head("<html><head><title>Café</title></head></html>")

    assert head["title"] == "Café"
