"""Unit tests for robots.txt rules ending in a bare '?' (e.g. 'Disallow: /*?').

urllib drops the trailing '?', which the wildcard patch in crawl4ai.utils turns
into the regex '^/.*' - disallowing the whole site. _preserve_bare_query rewrites
the rule to the equivalent '/*?*', which survives the round trip.
"""

import asyncio

import pytest

from crawl4ai.utils import RobotsParser, _preserve_bare_query

QUERY_RULES = "User-agent: *\nDisallow: /*?\n"


@pytest.mark.parametrize(
    "line, expected",
    [
        # A bare trailing '?' gains an explicit '*'
        ("Disallow: /*?", "Disallow: /*?*"),
        ("Allow: /*?", "Allow: /*?*"),
        ("Disallow: /search?", "Disallow: /search?*"),
        # Case and spacing are normalised, not required
        ("disallow: /*?", "disallow: /*?*"),
        ("DISALLOW:/*?", "DISALLOW: /*?*"),
        ("Disallow:   /*?   ", "Disallow: /*?*"),
        # Already explicit, or no trailing '?': left alone
        ("Disallow: /*?*", "Disallow: /*?*"),
        ("Disallow: /private/", "Disallow: /private/"),
        ("Allow: /public/", "Allow: /public/"),
        # Non-rule directives are never rewritten, even ending in '?'
        ("User-agent: *", "User-agent: *"),
        ("Sitemap: https://example.com/sitemap.xml?", "Sitemap: https://example.com/sitemap.xml?"),
        ("", ""),
        ("# just a comment", "# just a comment"),
    ],
)
def test_preserve_bare_query_line_rewriting(line, expected):
    assert _preserve_bare_query(line) == expected


def test_preserve_bare_query_keeps_document_structure():
    """Untouched lines, blank lines and ordering survive verbatim.

    The rewrite is splitlines()-based, so a trailing newline is not preserved.
    That is harmless: the only caller re-splits the result immediately.
    """
    source = "User-agent: *\nDisallow: /private/\n\nDisallow: /*?\nAllow: /public/\n"
    assert _preserve_bare_query(source) == (
        "User-agent: *\nDisallow: /private/\n\nDisallow: /*?*\nAllow: /public/"
    )
    # What the caller actually consumes is unaffected by the missing newline.
    assert _preserve_bare_query(source).splitlines() == [
        "User-agent: *", "Disallow: /private/", "", "Disallow: /*?*", "Allow: /public/",
    ]


def test_preserve_bare_query_is_idempotent():
    once = _preserve_bare_query(QUERY_RULES)
    assert _preserve_bare_query(once) == once


def _can_fetch(rules, path, tmp_path):
    """Answer can_fetch for a host whose rules are pre-seeded in the cache.

    Nothing listens on the host, and can_fetch falls back to 'allowed' whenever a
    fetch fails, so any denial below can only have come from the cached rules.
    """
    host = "localhost:8098"
    parser = RobotsParser(cache_dir=str(tmp_path))
    parser._cache_rules(host, rules)
    assert parser._get_cached_rules(host)[1], "seeded rules should be fresh"
    return asyncio.run(parser.can_fetch(f"http://{host}{path}", "bot"))


@pytest.mark.parametrize("path", ["/", "/article", "/a/b/c"])
def test_query_disallow_keeps_plain_urls_crawlable(path, tmp_path):
    """'Disallow: /*?' must not take the whole site down."""
    assert _can_fetch(QUERY_RULES, path, tmp_path) is True


@pytest.mark.parametrize("path", ["/?page=2", "/article?ref=x", "/a/b?x=1&y=2"])
def test_query_disallow_denies_query_urls(path, tmp_path):
    assert _can_fetch(QUERY_RULES, path, tmp_path) is False


def test_ordinary_rules_still_apply(tmp_path):
    """The rewrite must not disturb rules that never had a trailing '?'."""
    rules = "User-agent: *\nDisallow: /private/\nAllow: /public/\n"
    assert _can_fetch(rules, "/public/page", tmp_path) is True
    assert _can_fetch(rules, "/private/secret", tmp_path) is False
