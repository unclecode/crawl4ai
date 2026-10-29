"""Unit tests for DomainMapper: soft-404, robots.txt, feeds, normalization, nonsense filter."""
import asyncio
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from crawl4ai.domain_mapper import (
    DomainMapper,
    Soft404Fingerprint,
    _NONSENSE_SUFFIXES,
    _ASSET_EXTENSIONS,
)


# ════════════════════════════════════════════════════════════════════════
#  Soft-404 Detection
# ════════════════════════════════════════════════════════════════════════

class TestSoft404Detection:

    def test_is_soft_404_title_match(self):
        mapper = DomainMapper.__new__(DomainMapper)
        fp = Soft404Fingerprint(
            status_code=200, title="Page Not Found",
            content_length=1234, body_hash="abc123",
        )
        body = b"<html><title>Page Not Found</title><body>Oops</body></html>"
        assert mapper._is_soft_404(200, body, fp) is True

    def test_is_soft_404_hash_match(self):
        mapper = DomainMapper.__new__(DomainMapper)
        body = b"<html><title>Different Title</title><body>Error content</body></html>"
        body_hash = hashlib.md5(body[:2048]).hexdigest()
        fp = Soft404Fingerprint(
            status_code=200, title="Other Title",
            content_length=len(body), body_hash=body_hash,
        )
        assert mapper._is_soft_404(200, body, fp) is True

    def test_is_soft_404_real_404(self):
        mapper = DomainMapper.__new__(DomainMapper)
        fp = Soft404Fingerprint(
            status_code=200, title="Not Found",
            content_length=100, body_hash="abc",
        )
        body = b"<html><title>Not Found</title></html>"
        # Real 404 status — NOT a soft-404
        assert mapper._is_soft_404(404, body, fp) is False

    def test_is_soft_404_no_fingerprint(self):
        mapper = DomainMapper.__new__(DomainMapper)
        body = b"<html><title>Anything</title></html>"
        assert mapper._is_soft_404(200, body, None) is False

    def test_is_soft_404_different_content(self):
        mapper = DomainMapper.__new__(DomainMapper)
        fp = Soft404Fingerprint(
            status_code=200, title="Not Found",
            content_length=100, body_hash="abc123",
        )
        body = b"<html><title>Real Page</title><body>Actual content here</body></html>"
        assert mapper._is_soft_404(200, body, fp) is False

    def test_is_soft_404_no_title_in_body(self):
        mapper = DomainMapper.__new__(DomainMapper)
        fp = Soft404Fingerprint(
            status_code=200, title="Not Found",
            content_length=100, body_hash="abc123",
        )
        body = b"<html><body>No title tag</body></html>"
        assert mapper._is_soft_404(200, body, fp) is False


# ════════════════════════════════════════════════════════════════════════
#  robots.txt Parsing
# ════════════════════════════════════════════════════════════════════════

class TestRobotsTxtParsing:

    @pytest.mark.asyncio
    async def test_parse_sitemap_directives(self):
        robots_text = (
            "User-agent: *\n"
            "Disallow: /private/\n"
            "Sitemap: https://example.com/sitemap.xml\n"
            "Sitemap: https://example.com/sitemap-posts.xml\n"
        )
        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.text = robots_text
        mapper.client.get = AsyncMock(return_value=resp)

        from crawl4ai.async_configs import DomainMapperConfig
        config = DomainMapperConfig()

        sitemap_urls, disallow_paths = await mapper._scan_robots_txt("example.com", config)
        assert len(sitemap_urls) == 2
        assert "https://example.com/sitemap.xml" in sitemap_urls
        assert "/private/" in disallow_paths

    @pytest.mark.asyncio
    async def test_parse_disallow_ignores_wildcards(self):
        robots_text = (
            "User-agent: *\n"
            "Disallow: /admin/\n"
            "Disallow: /search?*\n"
            "Disallow: /\n"
            "Allow: /public/\n"
        )
        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.text = robots_text
        mapper.client.get = AsyncMock(return_value=resp)

        from crawl4ai.async_configs import DomainMapperConfig
        config = DomainMapperConfig()

        _, paths = await mapper._scan_robots_txt("example.com", config)
        assert "/admin/" in paths
        assert "/public/" in paths
        # Wildcards should be skipped
        assert "/search?*" not in paths
        # Single "/" is too short (len <= 1)
        assert "/" not in paths

    @pytest.mark.asyncio
    async def test_empty_robots(self):
        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        resp = MagicMock()
        resp.status_code = 404
        mapper.client.get = AsyncMock(return_value=resp)

        from crawl4ai.async_configs import DomainMapperConfig
        config = DomainMapperConfig()

        sitemap_urls, paths = await mapper._scan_robots_txt("example.com", config)
        assert sitemap_urls == []
        assert paths == []


# ════════════════════════════════════════════════════════════════════════
#  Feed Parsing
# ════════════════════════════════════════════════════════════════════════

class TestFeedParsing:

    def test_parse_rss_feed(self):
        rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <item><link>https://example.com/post-1</link></item>
            <item><link>https://example.com/post-2</link></item>
          </channel>
        </rss>"""
        mapper = DomainMapper.__new__(DomainMapper)
        urls = mapper._parse_feed_xml(rss, "https://example.com/feed")
        assert len(urls) == 2
        assert "https://example.com/post-1" in urls
        assert "https://example.com/post-2" in urls

    def test_parse_atom_feed(self):
        atom = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <link href="https://example.com/entry-1" rel="alternate"/>
          </entry>
          <entry>
            <link href="https://example.com/entry-2"/>
          </entry>
        </feed>"""
        mapper = DomainMapper.__new__(DomainMapper)
        urls = mapper._parse_feed_xml(atom, "https://example.com/atom.xml")
        assert len(urls) == 2
        assert "https://example.com/entry-1" in urls

    def test_parse_rss_guid_fallback(self):
        rss = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <guid isPermaLink="true">https://example.com/guid-post</guid>
            </item>
          </channel>
        </rss>"""
        mapper = DomainMapper.__new__(DomainMapper)
        urls = mapper._parse_feed_xml(rss, "https://example.com/feed")
        assert "https://example.com/guid-post" in urls

    def test_malformed_feed(self):
        mapper = DomainMapper.__new__(DomainMapper)
        urls = mapper._parse_feed_xml("not xml at all <><>", "https://example.com/feed")
        assert urls == []


# ════════════════════════════════════════════════════════════════════════
#  URL Normalization & Dedup
# ════════════════════════════════════════════════════════════════════════

class TestNormalizationDedup:

    def test_trailing_slash_dedup(self):
        mapper = DomainMapper.__new__(DomainMapper)
        results = [
            {"url": "https://example.com/about", "host": "example.com", "source": "sitemap", "status": "valid", "head_data": {}},
            {"url": "https://example.com/about/", "host": "example.com", "source": "probe", "status": "valid", "head_data": {}},
        ]
        deduped = mapper._normalize_and_dedup(results, "example.com")
        assert len(deduped) == 1
        assert "probe" in deduped[0]["source"] or "sitemap" in deduped[0]["source"]

    def test_source_merging(self):
        mapper = DomainMapper.__new__(DomainMapper)
        results = [
            {"url": "https://example.com/page", "host": "example.com", "source": "sitemap", "status": "valid", "head_data": {}},
            {"url": "https://example.com/page", "host": "example.com", "source": "homepage", "status": "valid", "head_data": {}},
        ]
        deduped = mapper._normalize_and_dedup(results, "example.com")
        assert len(deduped) == 1
        sources = set(deduped[0]["source"].split("+"))
        assert "sitemap" in sources
        assert "homepage" in sources


# ════════════════════════════════════════════════════════════════════════
#  Nonsense Filter
# ════════════════════════════════════════════════════════════════════════

class TestNonsenseFilter:

    def test_filters_robots_txt(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/robots.txt") is True

    def test_filters_sitemap_xml(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/sitemap.xml") is True

    def test_filters_js_assets(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/app.bundle.js") is True

    def test_filters_css_assets(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/style.css") is True

    def test_filters_images(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/logo.png") is True
        assert mapper._is_nonsense("https://example.com/photo.jpg") is True

    def test_filters_next_js_chunks(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/_next/static/chunks/main.js") is True

    def test_filters_wayback_garbage(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/%5Cn-") is True
        assert mapper._is_nonsense("https://example.com/%5CnJoin") is True

    def test_keeps_login(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/login") is False

    def test_keeps_dashboard(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/dashboard") is False

    def test_keeps_docs(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/docs") is False

    def test_keeps_api_docs(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/api-docs") is False

    def test_filters_dotfiles(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/.env") is True
        assert mapper._is_nonsense("https://example.com/.git/config") is True

    def test_filters_fonts(self):
        mapper = DomainMapper.__new__(DomainMapper)
        assert mapper._is_nonsense("https://example.com/fonts/arial.woff2") is True


# ════════════════════════════════════════════════════════════════════════
#  crt.sh Response Parsing
# ════════════════════════════════════════════════════════════════════════

class TestCrtShParsing:

    @pytest.mark.asyncio
    async def test_parse_crt_response(self):
        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [
            {"common_name": "example.com", "name_value": "example.com"},
            {"common_name": "docs.example.com", "name_value": "docs.example.com\napi.example.com"},
            {"common_name": "*.example.com", "name_value": "*.example.com"},
        ]
        mapper.client.get = AsyncMock(return_value=resp)

        from crawl4ai.async_configs import DomainMapperConfig
        hosts = await mapper._discover_via_crt("example.com", DomainMapperConfig())
        assert "example.com" in hosts
        assert "docs.example.com" in hosts
        assert "api.example.com" in hosts
        # Wildcards should be resolved to base
        assert "*.example.com" not in hosts

    @pytest.mark.asyncio
    async def test_crt_filters_unrelated_domains(self):
        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [
            {"common_name": "example.com", "name_value": "example.com"},
            {"common_name": "evil.com", "name_value": "evil.com"},
        ]
        mapper.client.get = AsyncMock(return_value=resp)

        from crawl4ai.async_configs import DomainMapperConfig
        hosts = await mapper._discover_via_crt("example.com", DomainMapperConfig())
        assert "example.com" in hosts
        assert "evil.com" not in hosts

    @pytest.mark.asyncio
    async def test_crt_handles_failure(self):
        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        mapper.client.get = AsyncMock(side_effect=Exception("timeout"))

        from crawl4ai.async_configs import DomainMapperConfig
        hosts = await mapper._discover_via_crt("example.com", DomainMapperConfig())
        assert hosts == set()


# ════════════════════════════════════════════════════════════════════════
#  Homepage Link Extraction
# ════════════════════════════════════════════════════════════════════════

class TestHomepageLinkExtraction:

    @pytest.mark.asyncio
    async def test_extract_internal_links(self):
        html = """<html>
        <head><title>Test</title></head>
        <body>
            <a href="/about">About</a>
            <a href="/blog">Blog</a>
            <a href="https://external.com/page">External</a>
        </body></html>"""

        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.text = html
        resp.url = "https://example.com/"
        mapper.client.get = AsyncMock(return_value=resp)

        from crawl4ai.async_configs import DomainMapperConfig
        urls = await mapper._scan_homepage("example.com", "example.com", DomainMapperConfig())
        # Should have internal links, not external
        assert any("/about" in u for u in urls)
        assert any("/blog" in u for u in urls)
        assert not any("external.com" in u for u in urls)

    @pytest.mark.asyncio
    async def test_extract_link_tags(self):
        html = """<html>
        <head>
            <title>Test</title>
            <link rel="alternate" hreflang="es" href="/es/">
            <link rel="preload" href="/features">
        </head>
        <body><a href="/page">Link</a></body></html>"""

        mapper = DomainMapper.__new__(DomainMapper)
        mapper.logger = None
        mapper.client = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.text = html
        resp.url = "https://example.com/"
        mapper.client.get = AsyncMock(return_value=resp)

        from crawl4ai.async_configs import DomainMapperConfig
        urls = await mapper._scan_homepage("example.com", "example.com", DomainMapperConfig())
        # Should include link tags
        assert any("/es/" in u for u in urls)
        assert any("/features" in u for u in urls)
