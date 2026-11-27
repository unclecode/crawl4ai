"""Complex content-type patterns must reach the regular-expression matcher."""

import pytest

from crawl4ai.deep_crawling.scorers import ContentTypeScorer


@pytest.mark.parametrize(
    "pattern, path",
    [
        (".html?$", "/page.htm"),
        (".html?$", "/page.html"),
        (".(?:pdf|docx)$", "/report.pdf"),
        (".(?:pdf|docx)$", "/report.docx"),
        (r".*\.pdf$", "/report.pdf"),
        (r".tar\.gz$", "/archive.tar.gz"),
        (".ht[mt]l$", "/page.html"),
        (".(?i:pdf)$", "/report.PDF"),
    ],
)
def test_complex_extension_patterns_match(pattern, path):
    scorer = ContentTypeScorer({pattern: 0.8}, weight=2.0)

    assert scorer.score(f"https://example.com{path}") == pytest.approx(1.6)


@pytest.mark.parametrize(
    "path", ["/page.txt", "/page.html/child", "/page.htmll", "/page.HTML"]
)
def test_complex_extension_pattern_does_not_match_unrelated_paths(path):
    scorer = ContentTypeScorer({".html?$": 0.8})

    assert scorer.score(f"https://example.com{path}") == 0.0


def test_simple_extension_keeps_precedence_over_regex_fallback():
    scorer = ContentTypeScorer({".html$": 0.4, ".html?$": 0.8})

    assert scorer.score("https://example.com/page.html") == pytest.approx(0.4)
    assert scorer.score("https://example.com/page.htm") == pytest.approx(0.8)


@pytest.mark.parametrize("path", ["/page.html", "/page.HTML"])
def test_simple_extension_keeps_case_insensitive_lookup(path):
    scorer = ContentTypeScorer({".html$": 0.4})

    assert scorer.score(f"https://example.com{path}") == pytest.approx(0.4)


def test_regex_flags_keep_working_when_pattern_does_not_start_with_dot():
    scorer = ContentTypeScorer({r"(?i)\.pdf$": 0.8})

    assert scorer.score("https://example.com/report.PDF") == pytest.approx(0.8)
