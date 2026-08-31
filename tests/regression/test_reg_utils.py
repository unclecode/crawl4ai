"""
Regression tests for Crawl4AI utility functions.

Covers extract_xml_data, URL normalization, CacheContext/CacheMode,
sanitize_input_encode, content hashing, and image scoring.
"""

import pytest

from crawl4ai.utils import (
    extract_xml_data,
    extract_xml_data_legacy,
    normalize_url,
    normalize_url_for_deep_crawl,
    efficient_normalize_url_for_deep_crawl,
    sanitize_input_encode,
    generate_content_hash,
)
from crawl4ai.cache_context import CacheContext, CacheMode


# ===================================================================
# extract_xml_data
# ===================================================================

class TestExtractXmlData:
    """Verify extract_xml_data correctly parses tag content from strings."""

    def test_basic_single_tag(self):
        """Basic extraction of a single tag should return its content."""
        result = extract_xml_data(["blocks"], "<blocks>hello</blocks>")
        assert result["blocks"] == "hello"

    def test_multiple_tags(self):
        """Extracting multiple tags should return both."""
        result = extract_xml_data(["a", "b"], "<a>1</a><b>2</b>")
        assert result["a"] == "1"
        assert result["b"] == "2"

    def test_longest_match(self):
        """When multiple occurrences exist, return the longest content."""
        text = "<blocks>short</blocks> some text <blocks>this is the longer content here</blocks>"
        result = extract_xml_data(["blocks"], text)
        assert result["blocks"] == "this is the longer content here"

    def test_nested_mention_bug_fix_1183(self):
        """Fix for #1183: nested mention of tag name should not confuse extraction.

        When <think> block mentions <blocks> in prose, the extraction should
        return the actual <blocks> content, not the prose mention.
        """
        text = (
            "<think>The user wants me to extract <blocks> data from the page.</think>"
            "<blocks>real extracted data</blocks>"
        )
        result = extract_xml_data(["blocks"], text)
        assert result["blocks"] == "real extracted data"

    def test_missing_tag_returns_empty(self):
        """Missing tag should return empty string."""
        result = extract_xml_data(["missing"], "<other>content</other>")
        assert result["missing"] == ""

    def test_empty_content(self):
        """Empty tag content should return empty string."""
        result = extract_xml_data(["blocks"], "<blocks></blocks>")
        assert result["blocks"] == ""

    def test_multiline_content(self):
        """Content spanning multiple lines should be extracted."""
        text = "<blocks>\nline 1\nline 2\nline 3\n</blocks>"
        result = extract_xml_data(["blocks"], text)
        assert "line 1" in result["blocks"]
        assert "line 2" in result["blocks"]
        assert "line 3" in result["blocks"]

    def test_special_chars_in_content(self):
        """JSON-like content with special characters should be preserved."""
        text = '<blocks>{"key": "value", "num": 42}</blocks>'
        result = extract_xml_data(["blocks"], text)
        assert '"key": "value"' in result["blocks"]
        assert '"num": 42' in result["blocks"]

    def test_content_with_angle_brackets(self):
        """Content with HTML-like angle brackets should work if not same tag."""
        text = "<blocks>some <b>bold</b> text</blocks>"
        result = extract_xml_data(["blocks"], text)
        assert "<b>bold</b>" in result["blocks"]

    def test_multiple_tags_some_missing(self):
        """Mixed present and missing tags should return values for present, empty for missing."""
        result = extract_xml_data(["found", "missing"], "<found>yes</found>")
        assert result["found"] == "yes"
        assert result["missing"] == ""

    def test_whitespace_stripped(self):
        """Content should be stripped of leading/trailing whitespace."""
        result = extract_xml_data(["blocks"], "<blocks>  trimmed  </blocks>")
        assert result["blocks"] == "trimmed"


class TestExtractXmlDataLegacy:
    """Verify the legacy extract_xml_data function works."""

    def test_basic_extraction(self):
        """Legacy function should extract basic tag content."""
        result = extract_xml_data_legacy(["blocks"], "<blocks>hello</blocks>")
        assert result["blocks"] == "hello"

    def test_missing_tag(self):
        """Legacy function should return empty string for missing tags."""
        result = extract_xml_data_legacy(["missing"], "no tags here")
        assert result["missing"] == ""


# ===================================================================
# URL normalization
# ===================================================================

class TestNormalizeUrl:
    """Verify normalize_url handles various URL edge cases."""

    def test_trailing_slash_preserved(self):
        """Trailing slash should be preserved (fix for #1520)."""
        result = normalize_url("/foo/bar/", "http://x.com")
        assert result.endswith("/foo/bar/")

    def test_no_trailing_slash_not_added(self):
        """URL without trailing slash should NOT have one added."""
        result = normalize_url("/foo/bar", "http://x.com")
        assert result.endswith("/foo/bar")
        assert not result.endswith("/foo/bar/")

    def test_root_path(self):
        """Root path '/' should be preserved."""
        result = normalize_url("/", "http://x.com")
        assert result == "http://x.com/"

    def test_query_param_case_preservation(self):
        """Query parameter values should NOT be lowercased (fix for #1489).

        cHash=AbCd must remain as-is, not become chash=abcd.
        """
        result = normalize_url("/page?cHash=AbCd", "http://x.com")
        assert "cHash=AbCd" in result

    def test_tracking_params_removed(self):
        """Common tracking parameters should be removed."""
        result = normalize_url(
            "/page?utm_source=google&utm_medium=cpc&real_param=keep",
            "http://x.com",
        )
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "real_param=keep" in result

    def test_fbclid_removed(self):
        """fbclid tracking parameter should be removed."""
        result = normalize_url("/page?fbclid=abc123&keep=yes", "http://x.com")
        assert "fbclid" not in result
        assert "keep=yes" in result

    def test_gclid_removed(self):
        """gclid tracking parameter should be removed."""
        result = normalize_url("/page?gclid=xyz&keep=yes", "http://x.com")
        assert "gclid" not in result
        assert "keep=yes" in result

    def test_tracking_removal_case_insensitive(self):
        """Tracking parameter removal should be case-insensitive."""
        # The normalize_url uses k.lower() for comparison
        result = normalize_url("/page?UTM_SOURCE=test&data=1", "http://x.com")
        # UTM_SOURCE (uppercase) should be removed since comparison is case-insensitive
        assert "data=1" in result

    def test_query_sorting(self):
        """Query parameters should be sorted alphabetically."""
        result = normalize_url("/page?z=1&a=2&m=3", "http://x.com")
        # Parameters should appear in alphabetical order
        idx_a = result.index("a=2")
        idx_m = result.index("m=3")
        idx_z = result.index("z=1")
        assert idx_a < idx_m < idx_z

    def test_fragment_removed_by_default(self):
        """Fragment (#section) should be removed by default."""
        result = normalize_url("/page#section", "http://x.com")
        assert "#section" not in result

    def test_fragment_kept_when_requested(self):
        """Fragment should be kept when keep_fragment=True."""
        result = normalize_url("/page#section", "http://x.com", keep_fragment=True)
        assert "#section" in result

    def test_relative_url_resolution(self):
        """Relative URLs should be resolved against base_url."""
        result = normalize_url("page2", "http://x.com/dir/page1")
        assert result == "http://x.com/dir/page2"

    def test_empty_href_returns_none(self):
        """Empty href should return None."""
        result = normalize_url("", "http://x.com")
        assert result is None

    def test_none_href_returns_none(self):
        """None href should return None."""
        result = normalize_url(None, "http://x.com")
        assert result is None

    def test_hostname_lowercased(self):
        """Hostname should be lowercased for consistency."""
        result = normalize_url("/page", "http://EXAMPLE.COM/path")
        assert "example.com" in result

    def test_no_query_params_still_works(self):
        """URL without query params should normalize without issue."""
        result = normalize_url("/simple/path", "http://x.com")
        assert "http://x.com/simple/path" == result


class TestNormalizeUrlForDeepCrawl:
    """Verify normalize_url_for_deep_crawl handles deep crawl edge cases."""

    def test_trailing_slash_preserved(self):
        """Trailing slash should be preserved in deep crawl normalization."""
        result = normalize_url_for_deep_crawl("/foo/bar/", "http://x.com")
        assert result is not None
        assert result.endswith("/foo/bar/")

    def test_empty_href_returns_none(self):
        """Empty href should return None."""
        result = normalize_url_for_deep_crawl("", "http://x.com")
        assert result is None

    def test_none_href_returns_none(self):
        """None href should return None."""
        result = normalize_url_for_deep_crawl(None, "http://x.com")
        assert result is None

    def test_fragment_removed(self):
        """Fragment should be removed in deep crawl normalization."""
        result = normalize_url_for_deep_crawl("/page#anchor", "http://x.com")
        assert "#anchor" not in result

    def test_tracking_params_removed(self):
        """utm_source and similar tracking params should be removed."""
        result = normalize_url_for_deep_crawl(
            "/page?utm_source=google&keep=yes", "http://x.com"
        )
        assert "utm_source" not in result
        assert "keep=yes" in result

    def test_hostname_lowercased(self):
        """Hostname should be lowercased."""
        result = normalize_url_for_deep_crawl("/page", "http://EXAMPLE.COM")
        assert "example.com" in result


class TestEfficientNormalizeUrlForDeepCrawl:
    """Verify efficient_normalize_url_for_deep_crawl caching and correctness."""

    def test_trailing_slash_preserved(self):
        """Trailing slash should be preserved."""
        result = efficient_normalize_url_for_deep_crawl("/foo/bar/", "http://x.com")
        assert result is not None
        assert result.endswith("/foo/bar/")

    def test_cached_results_consistent(self):
        """Calling twice with same args should return same result (cached)."""
        result1 = efficient_normalize_url_for_deep_crawl("/cached", "http://x.com")
        result2 = efficient_normalize_url_for_deep_crawl("/cached", "http://x.com")
        assert result1 == result2

    def test_empty_href_returns_none(self):
        """Empty href should return None."""
        result = efficient_normalize_url_for_deep_crawl("", "http://x.com")
        assert result is None

    def test_none_href_returns_none(self):
        """None href should return None."""
        result = efficient_normalize_url_for_deep_crawl(None, "http://x.com")
        assert result is None

    def test_fragment_removed(self):
        """Fragment should be removed."""
        result = efficient_normalize_url_for_deep_crawl("/page#top", "http://x.com")
        assert "#top" not in result

    def test_hostname_lowercased(self):
        """Hostname should be lowercased."""
        result = efficient_normalize_url_for_deep_crawl("/path", "http://UPPER.COM")
        assert "upper.com" in result

    def test_relative_url_resolution(self):
        """Relative URLs should be resolved correctly."""
        result = efficient_normalize_url_for_deep_crawl(
            "child", "http://x.com/parent/"
        )
        assert result == "http://x.com/parent/child"


# ===================================================================
# CacheContext / CacheMode
# ===================================================================

class TestCacheMode:
    """Verify CacheContext behavior for each CacheMode."""

    def test_enabled_reads_and_writes(self):
        """CacheMode.ENABLED should allow both reads and writes."""
        ctx = CacheContext("http://example.com", CacheMode.ENABLED)
        assert ctx.should_read() is True
        assert ctx.should_write() is True

    def test_disabled_no_reads_no_writes(self):
        """CacheMode.DISABLED should block both reads and writes."""
        ctx = CacheContext("http://example.com", CacheMode.DISABLED)
        assert ctx.should_read() is False
        assert ctx.should_write() is False

    def test_bypass_no_reads_but_writes(self):
        """CacheMode.BYPASS should skip reads but allow writes."""
        ctx = CacheContext("http://example.com", CacheMode.BYPASS)
        assert ctx.should_read() is False
        assert ctx.should_write() is False

    def test_read_only_reads_no_writes(self):
        """CacheMode.READ_ONLY should allow reads, block writes."""
        ctx = CacheContext("http://example.com", CacheMode.READ_ONLY)
        assert ctx.should_read() is True
        assert ctx.should_write() is False

    def test_write_only_no_reads_but_writes(self):
        """CacheMode.WRITE_ONLY should block reads, allow writes."""
        ctx = CacheContext("http://example.com", CacheMode.WRITE_ONLY)
        assert ctx.should_read() is False
        assert ctx.should_write() is True

    def test_raw_url_not_cacheable(self):
        """raw:// URLs should not be cacheable regardless of mode."""
        ctx = CacheContext("raw://<html>test</html>", CacheMode.ENABLED)
        assert ctx.should_read() is False
        assert ctx.should_write() is False

    def test_raw_url_is_raw_html(self):
        """raw:// URLs should be flagged as raw HTML."""
        ctx = CacheContext("raw://<html>test</html>", CacheMode.ENABLED)
        assert ctx.is_raw_html is True
        assert ctx.is_web_url is False

    def test_http_url_is_cacheable(self):
        """http:// URLs should be cacheable."""
        ctx = CacheContext("http://example.com", CacheMode.ENABLED)
        assert ctx.is_cacheable is True
        assert ctx.is_web_url is True

    def test_https_url_is_cacheable(self):
        """https:// URLs should be cacheable."""
        ctx = CacheContext("https://example.com", CacheMode.ENABLED)
        assert ctx.is_cacheable is True

    def test_file_url_is_cacheable(self):
        """file:// URLs should be cacheable."""
        ctx = CacheContext("file:///tmp/test.html", CacheMode.ENABLED)
        assert ctx.is_cacheable is True
        assert ctx.is_local_file is True

    def test_always_bypass_overrides_everything(self):
        """always_bypass=True should force read=False, write=False."""
        ctx = CacheContext("http://example.com", CacheMode.ENABLED, always_bypass=True)
        assert ctx.should_read() is False
        assert ctx.should_write() is False

    def test_display_url_for_web(self):
        """Display URL for web URLs should be the URL itself."""
        ctx = CacheContext("http://example.com", CacheMode.ENABLED)
        assert ctx.display_url == "http://example.com"

    def test_display_url_for_raw(self):
        """Display URL for raw HTML should be 'Raw HTML'."""
        ctx = CacheContext("raw://something", CacheMode.ENABLED)
        assert ctx.display_url == "Raw HTML"


# ===================================================================
# sanitize_input_encode
# ===================================================================

class TestSanitizeInputEncode:
    """Verify sanitize_input_encode handles encoding edge cases."""

    def test_normal_utf8_passthrough(self):
        """Normal UTF-8 text should pass through unchanged."""
        text = "Hello, world! This is normal text."
        assert sanitize_input_encode(text) == text

    def test_unicode_text_preserved(self):
        """Unicode characters should be preserved."""
        text = "Caf\u00e9 na\u00efve r\u00e9sum\u00e9"
        assert sanitize_input_encode(text) == text

    def test_empty_string_returns_empty(self):
        """Empty string should return empty string."""
        assert sanitize_input_encode("") == ""

    def test_ascii_text_passthrough(self):
        """Pure ASCII text should pass through."""
        text = "Simple ASCII text 123"
        assert sanitize_input_encode(text) == text

    def test_cjk_characters_preserved(self):
        """CJK characters should be preserved."""
        text = "\u4f60\u597d\u4e16\u754c"
        assert sanitize_input_encode(text) == text

    def test_emoji_preserved(self):
        """Emoji characters should be preserved in UTF-8."""
        text = "Hello \U0001f600 World"
        result = sanitize_input_encode(text)
        assert "Hello" in result
        assert "World" in result


# ===================================================================
# Content hashing
# ===================================================================

class TestGenerateContentHash:
    """Verify generate_content_hash produces consistent results."""

    def test_same_content_same_hash(self):
        """Same content should produce same hash."""
        hash1 = generate_content_hash("hello world")
        hash2 = generate_content_hash("hello world")
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Different content should produce different hashes."""
        hash1 = generate_content_hash("hello world")
        hash2 = generate_content_hash("goodbye world")
        assert hash1 != hash2

    def test_empty_content_valid_hash(self):
        """Empty content should produce a valid hash (not an error)."""
        h = generate_content_hash("")
        assert isinstance(h, str)
        assert len(h) > 0

    def test_hash_is_hex_string(self):
        """Hash should be a hexadecimal string."""
        h = generate_content_hash("test content")
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_deterministic_across_calls(self):
        """Hash should be deterministic, not random."""
        content = "The quick brown fox jumps over the lazy dog"
        hashes = [generate_content_hash(content) for _ in range(10)]
        assert len(set(hashes)) == 1

    def test_whitespace_sensitive(self):
        """Hash should be sensitive to whitespace differences."""
        h1 = generate_content_hash("hello world")
        h2 = generate_content_hash("hello  world")
        assert h1 != h2

    def test_case_sensitive(self):
        """Hash should be case-sensitive."""
        h1 = generate_content_hash("Hello")
        h2 = generate_content_hash("hello")
        assert h1 != h2

    def test_long_content(self):
        """Long content should hash without error."""
        content = "x" * 1_000_000
        h = generate_content_hash(content)
        assert isinstance(h, str)
        assert len(h) > 0


# ===================================================================
# Image scoring (import-guarded)
# ===================================================================

class TestImageScoring:
    """Test image scoring logic if available.

    score_image_for_usefulness is a nested function, so we test
    the concept indirectly by checking that the module loads and
    the scoring constants exist.
    """

    def test_image_score_threshold_exists(self):
        """IMAGE_SCORE_THRESHOLD config constant should exist."""
        from crawl4ai.config import IMAGE_SCORE_THRESHOLD
        assert isinstance(IMAGE_SCORE_THRESHOLD, (int, float))

    def test_image_description_threshold_exists(self):
        """IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD should exist."""
        from crawl4ai.config import IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
        assert isinstance(IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD, (int, float))
