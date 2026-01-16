"""
Real-world tests for cache validation using actual HTTP requests.
No mocks - all tests hit real servers.
"""

import pytest
from crawl4ai.cache_validator import CacheValidator, CacheValidationResult
from crawl4ai.utils import compute_head_fingerprint


class TestRealDomainsConditionalSupport:
    """Test domains that support HTTP conditional requests (ETag/Last-Modified)."""

    @pytest.mark.asyncio
    async def test_docs_python_org_etag(self):
        """docs.python.org supports ETag - should return 304."""
        url = "https://docs.python.org/3/"

        async with CacheValidator(timeout=15.0) as validator:
            # First fetch to get ETag
            head_html, etag, last_modified = await validator._fetch_head(url)

            assert head_html is not None, "Should fetch head content"
            assert etag is not None, "docs.python.org should return ETag"

            # Validate with the ETag we just got
            result = await validator.validate(url=url, stored_etag=etag)

            assert result.status == CacheValidationResult.FRESH, f"Expected FRESH, got {result.status}: {result.reason}"
            assert "304" in result.reason

    @pytest.mark.asyncio
    async def test_docs_crawl4ai_etag(self):
        """docs.crawl4ai.com supports ETag - should return 304."""
        url = "https://docs.crawl4ai.com/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            assert etag is not None, "docs.crawl4ai.com should return ETag"

            result = await validator.validate(url=url, stored_etag=etag)

            assert result.status == CacheValidationResult.FRESH, f"Expected FRESH, got {result.status}: {result.reason}"

    @pytest.mark.asyncio
    async def test_wikipedia_last_modified(self):
        """Wikipedia supports Last-Modified - should return 304."""
        url = "https://en.wikipedia.org/wiki/Web_crawler"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            assert last_modified is not None, "Wikipedia should return Last-Modified"

            result = await validator.validate(url=url, stored_last_modified=last_modified)

            assert result.status == CacheValidationResult.FRESH, f"Expected FRESH, got {result.status}: {result.reason}"

    @pytest.mark.asyncio
    async def test_github_pages(self):
        """GitHub Pages supports conditional requests."""
        url = "https://pages.github.com/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            # GitHub Pages typically has at least one
            has_conditional = etag is not None or last_modified is not None
            assert has_conditional, "GitHub Pages should support conditional requests"

            result = await validator.validate(
                url=url,
                stored_etag=etag,
                stored_last_modified=last_modified,
            )

            assert result.status == CacheValidationResult.FRESH

    @pytest.mark.asyncio
    async def test_httpbin_etag(self):
        """httpbin.org/etag endpoint for testing ETag."""
        url = "https://httpbin.org/etag/test-etag-value"

        async with CacheValidator(timeout=15.0) as validator:
            result = await validator.validate(url=url, stored_etag='"test-etag-value"')

            # httpbin should return 304 for matching ETag
            assert result.status == CacheValidationResult.FRESH, f"Expected FRESH, got {result.status}: {result.reason}"


class TestRealDomainsNoConditionalSupport:
    """Test domains that may NOT support HTTP conditional requests."""

    @pytest.mark.asyncio
    async def test_dynamic_site_fingerprint_fallback(self):
        """Test fingerprint-based validation for sites without conditional support."""
        # Use a site that changes frequently but has stable head
        url = "https://example.com/"

        async with CacheValidator(timeout=15.0) as validator:
            # Get head and compute fingerprint
            head_html, etag, last_modified = await validator._fetch_head(url)

            assert head_html is not None
            fingerprint = compute_head_fingerprint(head_html)

            # Validate using fingerprint (not etag/last-modified)
            result = await validator.validate(
                url=url,
                stored_head_fingerprint=fingerprint,
            )

            # Should be FRESH since fingerprint should match
            assert result.status == CacheValidationResult.FRESH, f"Expected FRESH, got {result.status}: {result.reason}"
            assert "fingerprint" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_news_site_changes_frequently(self):
        """News sites change frequently - test that we can detect changes."""
        url = "https://www.bbc.com/news"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            # BBC News has ETag but it changes with content
            assert head_html is not None

            # Using a fake old ETag should return STALE (200 with different content)
            result = await validator.validate(
                url=url,
                stored_etag='"fake-old-etag-12345"',
            )

            # Should be STALE because the ETag doesn't match
            assert result.status == CacheValidationResult.STALE, f"Expected STALE, got {result.status}: {result.reason}"


class TestRealDomainsEdgeCases:
    """Edge cases with real domains."""

    @pytest.mark.asyncio
    async def test_nonexistent_domain(self):
        """Non-existent domain should return ERROR."""
        url = "https://this-domain-definitely-does-not-exist-xyz123.com/"

        async with CacheValidator(timeout=5.0) as validator:
            result = await validator.validate(url=url, stored_etag='"test"')

            assert result.status == CacheValidationResult.ERROR

    @pytest.mark.asyncio
    async def test_timeout_slow_server(self):
        """Test timeout handling with a slow endpoint."""
        # httpbin delay endpoint
        url = "https://httpbin.org/delay/10"

        async with CacheValidator(timeout=2.0) as validator:  # 2 second timeout
            result = await validator.validate(url=url, stored_etag='"test"')

            # Should timeout and return ERROR
            assert result.status == CacheValidationResult.ERROR
            assert "timeout" in result.reason.lower() or "timed out" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_redirect_handling(self):
        """Test that redirects are followed."""
        # httpbin redirect
        url = "https://httpbin.org/redirect/1"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            # Should follow redirect and get content
            # The final page might not have useful head content, but shouldn't error
            # This tests that redirects are handled

    @pytest.mark.asyncio
    async def test_https_only(self):
        """Test HTTPS connection."""
        url = "https://www.google.com/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            assert head_html is not None
            assert "<title" in head_html.lower()


class TestRealDomainsHeadFingerprint:
    """Test head fingerprint extraction with real domains."""

    @pytest.mark.asyncio
    async def test_python_docs_fingerprint(self):
        """Python docs has title and meta tags."""
        url = "https://docs.python.org/3/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, _, _ = await validator._fetch_head(url)

            assert head_html is not None
            fingerprint = compute_head_fingerprint(head_html)

            assert fingerprint != "", "Should extract fingerprint from Python docs"

            # Fingerprint should be consistent
            fingerprint2 = compute_head_fingerprint(head_html)
            assert fingerprint == fingerprint2

    @pytest.mark.asyncio
    async def test_github_fingerprint(self):
        """GitHub has og: tags."""
        url = "https://github.com/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, _, _ = await validator._fetch_head(url)

            assert head_html is not None
            assert "og:" in head_html.lower() or "title" in head_html.lower()

            fingerprint = compute_head_fingerprint(head_html)
            assert fingerprint != ""

    @pytest.mark.asyncio
    async def test_crawl4ai_docs_fingerprint(self):
        """Crawl4AI docs should have title and description."""
        url = "https://docs.crawl4ai.com/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, _, _ = await validator._fetch_head(url)

            assert head_html is not None
            fingerprint = compute_head_fingerprint(head_html)

            assert fingerprint != "", "Should extract fingerprint from Crawl4AI docs"


class TestRealDomainsFetchHead:
    """Test _fetch_head functionality with real domains."""

    @pytest.mark.asyncio
    async def test_fetch_stops_at_head_close(self):
        """Verify we stop reading after </head>."""
        url = "https://docs.python.org/3/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, _, _ = await validator._fetch_head(url)

            assert head_html is not None
            assert "</head>" in head_html.lower()
            # Should NOT contain body content
            assert "<body" not in head_html.lower() or head_html.lower().index("</head>") < head_html.lower().find("<body")

    @pytest.mark.asyncio
    async def test_extracts_both_headers(self):
        """Test extraction of both ETag and Last-Modified."""
        url = "https://docs.python.org/3/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            # Python docs should have both
            assert etag is not None, "Should have ETag"
            assert last_modified is not None, "Should have Last-Modified"

    @pytest.mark.asyncio
    async def test_handles_missing_head_tag(self):
        """Handle pages that might not have proper head structure."""
        # API endpoint that returns JSON (no HTML head)
        url = "https://httpbin.org/json"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)

            # Should not crash, may return partial content or None
            # The important thing is it doesn't error


class TestRealDomainsValidationCombinations:
    """Test various combinations of validation data."""

    @pytest.mark.asyncio
    async def test_etag_only(self):
        """Validate with only ETag."""
        url = "https://docs.python.org/3/"

        async with CacheValidator(timeout=15.0) as validator:
            _, etag, _ = await validator._fetch_head(url)

            result = await validator.validate(url=url, stored_etag=etag)
            assert result.status == CacheValidationResult.FRESH

    @pytest.mark.asyncio
    async def test_last_modified_only(self):
        """Validate with only Last-Modified."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

        async with CacheValidator(timeout=15.0) as validator:
            _, _, last_modified = await validator._fetch_head(url)

            if last_modified:
                result = await validator.validate(url=url, stored_last_modified=last_modified)
                assert result.status == CacheValidationResult.FRESH

    @pytest.mark.asyncio
    async def test_fingerprint_only(self):
        """Validate with only fingerprint."""
        url = "https://example.com/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, _, _ = await validator._fetch_head(url)
            fingerprint = compute_head_fingerprint(head_html)

            if fingerprint:
                result = await validator.validate(url=url, stored_head_fingerprint=fingerprint)
                assert result.status == CacheValidationResult.FRESH

    @pytest.mark.asyncio
    async def test_all_validation_data(self):
        """Validate with all available data."""
        url = "https://docs.python.org/3/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, etag, last_modified = await validator._fetch_head(url)
            fingerprint = compute_head_fingerprint(head_html)

            result = await validator.validate(
                url=url,
                stored_etag=etag,
                stored_last_modified=last_modified,
                stored_head_fingerprint=fingerprint,
            )

            assert result.status == CacheValidationResult.FRESH

    @pytest.mark.asyncio
    async def test_stale_etag_fresh_fingerprint(self):
        """When ETag is stale but fingerprint matches, should be FRESH."""
        url = "https://docs.python.org/3/"

        async with CacheValidator(timeout=15.0) as validator:
            head_html, _, _ = await validator._fetch_head(url)
            fingerprint = compute_head_fingerprint(head_html)

            # Use fake ETag but real fingerprint
            result = await validator.validate(
                url=url,
                stored_etag='"fake-stale-etag"',
                stored_head_fingerprint=fingerprint,
            )

            # Fingerprint should save us
            assert result.status == CacheValidationResult.FRESH
            assert "fingerprint" in result.reason.lower()
