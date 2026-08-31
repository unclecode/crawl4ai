"""
Comprehensive test suite for cloud-reported bug fixes:
  - Bug 1: Anti-bot false positives on browser-rendered JSON
  - Bug 2: URLPatternFilter PREFIX match using full URL instead of path
  - Bug 3: PDFContentScrapingStrategy not in ALLOWED_DESERIALIZE_TYPES

Tests include: unit, edge case, adversarial, and regression checks.
"""

import sys
import os
import re
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crawl4ai.antibot_detector import is_blocked, _looks_like_data, _structural_integrity_check
from crawl4ai.deep_crawling.filters import URLPatternFilter
from crawl4ai.async_configs import ALLOWED_DESERIALIZE_TYPES, to_serializable_dict, from_serializable_dict

PASS = 0
FAIL = 0

def check(name, actual, expected, detail=""):
    global PASS, FAIL
    ok = actual == expected
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {name}")
        print(f"         got: {actual!r}")
        print(f"         expected: {expected!r}")
        if detail:
            print(f"         detail: {detail}")


# =====================================================================
# BUG 1: Anti-bot false positives on browser-rendered JSON
# =====================================================================
print("\n" + "=" * 70)
print("BUG 1: Anti-bot false positives on browser-rendered JSON")
print("=" * 70)

# --- 1A: _looks_like_data() unit tests ---
print("\n--- _looks_like_data() ---")

check("raw JSON object", _looks_like_data('{"origin": "1.2.3.4"}'), True)
check("raw JSON array", _looks_like_data('[1, 2, 3]'), True)
check("raw XML", _looks_like_data('<?xml version="1.0"?><root/>'), True)
check("empty string", _looks_like_data(''), False)
check("whitespace only", _looks_like_data('   \n  '), False)
check("normal HTML page", _looks_like_data('<html><body><p>Hello</p></body></html>'), False)
check("<!DOCTYPE html>", _looks_like_data('<!DOCTYPE html><html><body></body></html>'), False)
check("<HTML uppercase>", _looks_like_data('<HTML><BODY></BODY></HTML>'), False)

# Browser-wrapped JSON (the core bug)
check("browser-wrapped JSON object",
    _looks_like_data('<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"origin": "1.2.3.4"}</pre></body></html>'),
    True)

check("browser-wrapped JSON array",
    _looks_like_data('<html><head></head><body><pre>[{"id": 1}, {"id": 2}]</pre></body></html>'),
    True)

check("browser-wrapped JSON (uppercase HTML)",
    _looks_like_data('<HTML><HEAD></HEAD><BODY><PRE>{"key": "val"}</PRE></BODY></HTML>'),
    True)

check("browser-wrapped JSON (DOCTYPE)",
    _looks_like_data('<!DOCTYPE html><html><head></head><body><pre>{"x": 1}</pre></body></html>'),
    True)

check("browser-wrapped JSON with whitespace before pre",
    _looks_like_data('<html><head></head><body>  \n  <pre>{"x": 1}</pre></body></html>'),
    True)

# Should NOT detect as data — normal HTML with <pre>
check("HTML page with code block (not JSON in pre)",
    _looks_like_data('<html><body><h1>Tutorial</h1><pre>def hello():\n    print("hi")</pre></body></html>'),
    False)

check("HTML with <pre> but text content, not JSON",
    _looks_like_data('<html><body><pre>This is just preformatted text, not JSON.</pre></body></html>'),
    False)

# --- 1B: is_blocked() integration tests for browser-wrapped JSON ---
print("\n--- is_blocked() with browser-rendered JSON ---")

# httpbin.org /ip response (tiny — ~90 bytes HTML)
httpbin_ip = '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"origin": "203.0.113.42"}</pre></body></html>'
blocked, reason = is_blocked(200, httpbin_ip)
check("httpbin /ip (200, small browser-wrapped JSON)", blocked, False, reason)

# httpbin.org /anything response (medium)
httpbin_anything = '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"args": {}, "data": "", "files": {}, "form": {}, "headers": {"Accept": "*/*", "Host": "httpbin.org", "User-Agent": "Mozilla/5.0"}, "json": null, "method": "GET", "origin": "203.0.113.42", "url": "https://httpbin.org/anything"}</pre></body></html>'
blocked, reason = is_blocked(200, httpbin_anything)
check("httpbin /anything (200, medium browser-wrapped JSON)", blocked, False, reason)

# httpbin.org /delay/N response
httpbin_delay = '<html><head></head><body><pre>{"args": {}, "data": "", "headers": {"Host": "httpbin.org"}, "origin": "1.2.3.4", "url": "https://httpbin.org/delay/2"}</pre></body></html>'
blocked, reason = is_blocked(200, httpbin_delay)
check("httpbin /delay/2 (200, browser-wrapped JSON)", blocked, False, reason)

# httpbin.org /headers response
httpbin_headers = '<html><head></head><body><pre>{"headers": {"Accept": "text/html", "Accept-Encoding": "gzip", "Host": "httpbin.org", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "X-Forwarded-For": "1.2.3.4", "X-Forwarded-Proto": "https"}}</pre></body></html>'
blocked, reason = is_blocked(200, httpbin_headers)
check("httpbin /headers (200, browser-wrapped JSON)", blocked, False, reason)

# Browser-wrapped JSON array
json_array_page = '<html><head></head><body><pre>[{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]</pre></body></html>'
blocked, reason = is_blocked(200, json_array_page)
check("browser-wrapped JSON array (200)", blocked, False, reason)

# --- 1C: Ensure real block pages still detected ---
print("\n--- Regression: real block pages still detected ---")

# Empty shell (should still be blocked)
blocked, reason = is_blocked(200, '<html><body></body></html>')
check("empty shell (200, no content)", blocked, True, reason)

# Anti-bot redirect page
blocked, reason = is_blocked(200, '<html><head></head><body><script>window.location="/challenge"</script></body></html>')
check("script-only redirect (200)", blocked, True, reason)

# Small page with no content elements (not JSON)
blocked, reason = is_blocked(200, '<html><body><div>x</div></body></html>')
check("tiny div-only page (200)", blocked, True, reason)

# 403 with browser-wrapped JSON should NOT be blocked (it's data)
blocked, reason = is_blocked(403, '{"error": "forbidden", "code": 403}')
check("403 raw JSON (data response)", blocked, False, reason)

# 403 with HTML should still be blocked
blocked, reason = is_blocked(403, '<html><body><p>Forbidden</p></body></html>')
check("403 HTML page (blocked)", blocked, True, reason)

# --- 1D: <pre> now counts as content element ---
print("\n--- <pre> as content element ---")

# Page with only <pre> (code block) should not be flagged as "no content elements"
html_with_pre = '<html><body><pre>function hello() {\n  console.log("world");\n}\n\nThis is a code example that demonstrates JavaScript functions. It shows how to define and use basic functions with console output for debugging purposes.</pre></body></html>'
blocked, reason = is_blocked(200, html_with_pre)
check("page with <pre> code block (200)", blocked, False, reason)

# Page with <pre> containing log output
html_pre_logs = '<html><body><pre>2024-01-15 10:30:45 INFO  Starting server on port 8080\n2024-01-15 10:30:46 INFO  Database connected successfully\n2024-01-15 10:30:47 INFO  Application ready to accept connections on all interfaces</pre></body></html>'
blocked, reason = is_blocked(200, html_pre_logs)
check("page with <pre> log output (200)", blocked, False, reason)

# --- 1E: Adversarial: attacker tries to bypass detection using <pre> ---
print("\n--- Adversarial: <pre> shouldn't defeat real block detection ---")

# Tier 1 pattern in page with <pre> should still be detected
blocked, reason = is_blocked(403, '<html><body><pre>Reference #18.2d351ab8.1557333295.a4e16ab</pre></body></html>')
check("Akamai ref in <pre> (403)", blocked, True, reason)

blocked, reason = is_blocked(200, '<html><body><pre>window._pxAppId = "PX123";</pre></body></html>')
check("PerimeterX in <pre> (200)", blocked, True, reason)

# Empty <pre> should still trigger
blocked, reason = is_blocked(200, '<html><body><pre></pre></body></html>')
check("empty <pre> (200, minimal text)", blocked, True, reason)

# <pre> with whitespace only
blocked, reason = is_blocked(200, '<html><body><pre>   </pre></body></html>')
check("<pre> with only whitespace (200)", blocked, True, reason)


# =====================================================================
# BUG 2: URLPatternFilter PREFIX match
# =====================================================================
print("\n" + "=" * 70)
print("BUG 2: URLPatternFilter PREFIX match")
print("=" * 70)

# --- 2A: Path-only prefix patterns (the original bug) ---
print("\n--- Path-only prefix patterns ---")

f = URLPatternFilter(patterns=["/docs/*"])
check("/docs/* matches /docs/page1", f.apply("https://example.com/docs/page1"), True)
check("/docs/* matches /docs/", f.apply("https://example.com/docs/"), True)
check("/docs/* matches /docs/sub/page", f.apply("https://example.com/docs/sub/page"), True)
f2 = URLPatternFilter(patterns=["/docs/*"])  # fresh filter (lru_cache)
check("/docs/* no match /api/docs", f2.apply("https://example.com/api/docs"), False)
f3 = URLPatternFilter(patterns=["/docs/*"])
check("/docs/* no match /other", f3.apply("https://example.com/other"), False)

# --- 2B: Full-URL prefix patterns (must still work) ---
print("\n--- Full-URL prefix patterns ---")

f4 = URLPatternFilter(patterns=["https://example.com/blog/*"])
check("full URL prefix matches", f4.apply("https://example.com/blog/post-1"), True)
check("full URL prefix matches subpath", f4.apply("https://example.com/blog/2024/post-1"), True)
f5 = URLPatternFilter(patterns=["https://example.com/blog/*"])
check("full URL prefix no match different domain", f5.apply("https://other.com/blog/post-1"), False)
f6 = URLPatternFilter(patterns=["https://example.com/blog/*"])
check("full URL prefix no match blogxx", f6.apply("https://example.com/blogxx/post-1"), False)

# --- 2C: Path prefix with query strings ---
print("\n--- Prefix with query strings ---")

f7 = URLPatternFilter(patterns=["/api/*"])
check("/api/* matches /api/v1", f7.apply("https://example.com/api/v1"), True)
check("/api/* matches /api/v1?key=123", f7.apply("https://example.com/api/v1?key=123"), True)
f8 = URLPatternFilter(patterns=["/api/*"])
check("/api/* no match /apiv2/", f8.apply("https://example.com/apiv2/"), False)

# --- 2D: Suffix patterns still work ---
print("\n--- Suffix patterns ---")

f9 = URLPatternFilter(patterns=["*.pdf"])
check("*.pdf matches report.pdf", f9.apply("https://example.com/report.pdf"), True)
check("*.pdf matches nested pdf", f9.apply("https://example.com/docs/report.pdf"), True)
f10 = URLPatternFilter(patterns=["*.pdf"])
check("*.pdf no match .html", f10.apply("https://example.com/page.html"), False)

# --- 2E: Reverse mode ---
print("\n--- Reverse mode ---")

f11 = URLPatternFilter(patterns=["/private/*"], reverse=True)
check("reverse: /private/* excludes /private/page", f11.apply("https://example.com/private/page"), False)
f12 = URLPatternFilter(patterns=["/private/*"], reverse=True)
check("reverse: /private/* allows /public/page", f12.apply("https://example.com/public/page"), True)

# --- 2F: Adversarial URL patterns ---
print("\n--- Adversarial URL edge cases ---")

f13 = URLPatternFilter(patterns=["/docs/*"])
check("prefix with port in URL", f13.apply("https://example.com:8080/docs/page"), True)
f14 = URLPatternFilter(patterns=["/docs/*"])
check("prefix with auth in URL", f14.apply("https://user:pass@example.com/docs/page"), True)
f15 = URLPatternFilter(patterns=["/docs/*"])
check("prefix with fragment", f15.apply("https://example.com/docs#section"), True)

# URL-encoded path
f16 = URLPatternFilter(patterns=["/docs/*"])
check("prefix with encoded path", f16.apply("https://example.com/docs/my%20page"), True)

# Multiple prefix patterns
f17 = URLPatternFilter(patterns=["/docs/*", "/api/*"])
check("multi-prefix: /docs/ matches", f17.apply("https://example.com/docs/page"), True)
check("multi-prefix: /api/ matches", f17.apply("https://example.com/api/v1"), True)
f18 = URLPatternFilter(patterns=["/docs/*", "/api/*"])
check("multi-prefix: /other/ no match", f18.apply("https://example.com/other/page"), False)

# --- 2G: Complex (PATH) patterns still work ---
print("\n--- Complex glob patterns ---")

f19 = URLPatternFilter(patterns=["*/docs/*/guide"])
check("glob */docs/*/guide matches", f19.apply("https://example.com/docs/v2/guide"), True)
f20 = URLPatternFilter(patterns=["*/docs/*/guide"])
check("glob */docs/*/guide no match", f20.apply("https://example.com/docs/v2/tutorial"), False)

# --- 2H: Domain patterns still work ---
print("\n--- Domain patterns ---")

# Note: *.example.com (without ://) is classified as SUFFIX, not DOMAIN.
# Use http://*.example.com for domain matching.
f21 = URLPatternFilter(patterns=["http://*.example.com/*"])
check("domain http://*.example.com/* matches sub.example.com", f21.apply("http://sub.example.com/page"), True)
f22 = URLPatternFilter(patterns=["http://*.example.com/*"])
check("domain http://*.example.com/* no match other.com", f22.apply("http://other.com/page"), False)

# --- 2I: Regex patterns still work ---
print("\n--- Regex patterns ---")

f23 = URLPatternFilter(patterns=[r"^https://example\.com/v\d+/"])
check("regex matches /v1/", f23.apply("https://example.com/v1/page"), True)
f24 = URLPatternFilter(patterns=[r"^https://example\.com/v\d+/"])
check("regex no match /vx/", f24.apply("https://example.com/vx/page"), False)


# =====================================================================
# BUG 3: PDFContentScrapingStrategy deserialization
# =====================================================================
print("\n" + "=" * 70)
print("BUG 3: PDFContentScrapingStrategy deserialization")
print("=" * 70)

# --- 3A: Type is in allowlist ---
print("\n--- Allowlist check ---")

check("PDFContentScrapingStrategy in ALLOWED_DESERIALIZE_TYPES",
    "PDFContentScrapingStrategy" in ALLOWED_DESERIALIZE_TYPES, True)

# --- 3B: Roundtrip serialization ---
print("\n--- Serialization roundtrip ---")

try:
    from crawl4ai.processors.pdf import PDFContentScrapingStrategy

    strategy = PDFContentScrapingStrategy(extract_images=False, batch_size=8)
    serialized = to_serializable_dict(strategy)
    check("serialization type field", serialized.get("type"), "PDFContentScrapingStrategy")
    check("serialization has params", "params" in serialized, True)

    # Deserialize back — verifies it resolves to the correct class (the original bug)
    deserialized = from_serializable_dict(serialized)
    check("deserialization type", type(deserialized).__name__, "PDFContentScrapingStrategy")
    # The strategy passes params to NaivePDFProcessorStrategy internally,
    # so verify via the inner processor
    check("deserialization creates valid processor",
        hasattr(deserialized, 'pdf_processor'), True)

    print("  (roundtrip OK)")
except ImportError as e:
    print(f"  SKIP: PDFContentScrapingStrategy import failed: {e}")
except Exception as e:
    FAIL += 1
    print(f"  FAIL: Serialization roundtrip failed: {e}")

# --- 3C: CrawlerRunConfig with PDFContentScrapingStrategy ---
print("\n--- CrawlerRunConfig with PDFContentScrapingStrategy ---")

try:
    from crawl4ai import CrawlerRunConfig
    from crawl4ai.processors.pdf import PDFContentScrapingStrategy

    config = CrawlerRunConfig(
        scraping_strategy=PDFContentScrapingStrategy(extract_images=False, batch_size=4)
    )
    serialized = to_serializable_dict(config)
    deserialized = from_serializable_dict(serialized)
    check("CrawlerRunConfig roundtrip with PDF strategy",
        type(deserialized.scraping_strategy).__name__, "PDFContentScrapingStrategy")
    check("PDF strategy has processor after roundtrip",
        hasattr(deserialized.scraping_strategy, 'pdf_processor'), True)

    print("  (config roundtrip OK)")
except ImportError as e:
    print(f"  SKIP: Import failed: {e}")
except Exception as e:
    FAIL += 1
    print(f"  FAIL: Config roundtrip failed: {e}")

# --- 3D: Other types still deserialize correctly (regression) ---
print("\n--- Regression: other types still work ---")

try:
    from crawl4ai import CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator
    from crawl4ai import LXMLWebScrapingStrategy, RegexChunking

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(),
        scraping_strategy=LXMLWebScrapingStrategy(),
        chunking_strategy=RegexChunking(),
    )
    serialized = to_serializable_dict(config)
    deserialized = from_serializable_dict(serialized)
    check("CrawlerRunConfig basic roundtrip type", type(deserialized).__name__, "CrawlerRunConfig")
    check("CrawlerRunConfig cache_mode preserved", deserialized.cache_mode, CacheMode.BYPASS)

    print("  (regression OK)")
except Exception as e:
    FAIL += 1
    print(f"  FAIL: Regression roundtrip failed: {e}")


# =====================================================================
# ADVERSARIAL / EDGE CASES — Cross-cutting
# =====================================================================
print("\n" + "=" * 70)
print("ADVERSARIAL / EDGE CASES")
print("=" * 70)

# --- Antibot: various browser JSON wrapping styles ---
print("\n--- Browser JSON wrapping variants ---")

# Chrome style
chrome_json = '<html><head></head><body><pre style="word-wrap: break-word; white-space: pre-wrap;">{"origin": "1.2.3.4"}</pre></body></html>'
blocked, reason = is_blocked(200, chrome_json)
check("Chrome-style JSON wrap", blocked, False, reason)

# Firefox style (no inline style on pre)
firefox_json = '<html><head></head><body><pre>{"origin": "1.2.3.4"}</pre></body></html>'
blocked, reason = is_blocked(200, firefox_json)
check("Firefox-style JSON wrap", blocked, False, reason)

# With extra whitespace/newlines
whitespace_json = '<html>\n<head>\n</head>\n<body>\n  <pre>\n{"origin": "1.2.3.4"}</pre>\n</body>\n</html>'
blocked, reason = is_blocked(200, whitespace_json)
check("JSON wrap with newlines", blocked, False, reason)

# Deeply nested JSON
big_json = '<html><head></head><body><pre>' + json.dumps({"data": [{"id": i, "name": f"item_{i}", "values": list(range(10))} for i in range(100)]}) + '</pre></body></html>'
blocked, reason = is_blocked(200, big_json)
check("large nested JSON in browser wrap", blocked, False, reason)

# JSON with special chars
special_json = '<html><head></head><body><pre>{"html": "<p>hello</p>", "url": "https://example.com?a=1&b=2"}</pre></body></html>'
blocked, reason = is_blocked(200, special_json)
check("JSON with embedded HTML/URL", blocked, False, reason)

# --- Antibot: responses that look similar but should still be blocked ---
print("\n--- Similar-looking pages that SHOULD be blocked ---")

# HTML page that happens to have <pre> but isn't JSON
blocked, reason = is_blocked(200, '<html><body><pre>Access Denied</pre></body></html>')
check("<pre>Access Denied</pre> (200, small)", blocked, True, reason)

# Empty body with <pre> but no JSON
blocked, reason = is_blocked(200, '<html><body><pre>   </pre></body></html>')
check("<pre> with whitespace (200)", blocked, True, reason)

# <pre> with non-JSON that starts with { but invalid
blocked, reason = is_blocked(200, '<html><body><pre>{not valid json at all, this is just text</pre></body></html>')
# This is ambiguous — looks like it could be data. Our check just looks at { or [ prefix.
# It will be detected as data and NOT blocked, which is the safer choice.
check("<pre>{non-json text} treated as data (200)", blocked, False, reason)

# --- URLPatternFilter: empty and edge-case inputs ---
print("\n--- URLPatternFilter edge cases ---")

# Empty URL
f_edge = URLPatternFilter(patterns=["/docs/*"])
check("empty URL no match", f_edge.apply(""), False)

# URL with no path
f_edge2 = URLPatternFilter(patterns=["/docs/*"])
check("domain-only URL no match", f_edge2.apply("https://example.com"), False)

# Root path
f_edge3 = URLPatternFilter(patterns=["/*"])
check("/* matches any path", f_edge3.apply("https://example.com/anything"), True)

# Exact prefix match (path equals prefix exactly)
f_edge4 = URLPatternFilter(patterns=["/docs/*"])
check("/docs/* matches /docs exactly (prefix == path)", f_edge4.apply("https://example.com/docs"), True)
# /docs without trailing / matches because len(url_path) == len(prefix) is the exact-match case

# Very long URL
long_path = "/docs/" + "a" * 2000
f_edge5 = URLPatternFilter(patterns=["/docs/*"])
check("very long path matches", f_edge5.apply(f"https://example.com{long_path}"), True)

# Unicode in path
f_edge6 = URLPatternFilter(patterns=["/docs/*"])
check("unicode path matches", f_edge6.apply("https://example.com/docs/页面"), True)

# --- Deserialization: security edge cases ---
print("\n--- Deserialization security ---")

# Ensure disallowed types still raise
try:
    from_serializable_dict({"type": "os.system", "params": {"command": "whoami"}})
    FAIL += 1
    print("  FAIL: should have raised ValueError for disallowed type")
except (ValueError, AttributeError):
    PASS += 1
    print("  PASS: disallowed type 'os.system' correctly rejected")
except Exception as e:
    PASS += 1  # Any error is fine, as long as it doesn't execute
    print(f"  PASS: disallowed type rejected with {type(e).__name__}")

try:
    from_serializable_dict({"type": "__import__", "params": {"name": "os"}})
    FAIL += 1
    print("  FAIL: should have raised for __import__")
except (ValueError, AttributeError):
    PASS += 1
    print("  PASS: disallowed type '__import__' correctly rejected")
except Exception as e:
    PASS += 1
    print(f"  PASS: disallowed type rejected with {type(e).__name__}")


# =====================================================================
# SUMMARY
# =====================================================================
print(f"\n{'=' * 70}")
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
print(f"{'=' * 70}")
if FAIL > 0:
    print("SOME TESTS FAILED!")
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
