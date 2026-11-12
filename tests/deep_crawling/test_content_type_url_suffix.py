"""Content-type scores must use the file extension, not URL suffixes."""

import pytest

from crawl4ai.deep_crawling import ContentTypeScorer


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        pytest.param("/report.pdf", 1.0, id="plain-extension"),
        pytest.param("/report.pdf?version=1.2", 1.0, id="dotted-query"),
        pytest.param("/report.pdf#section=1.2", 1.0, id="dotted-fragment"),
        pytest.param("/report.pdf;version=1.2", 1.0, id="dotted-path-parameter"),
        pytest.param(
            "/archive;version=1.2/report.PDF?next=/download.txt",
            1.0,
            id="parent-parameter-uppercase-extension-query-path",
        ),
        pytest.param("/archive.v1/report.pdf", 1.0, id="dotted-directory"),
        pytest.param("/archive.pdf/report", 0.0, id="directory-is-not-extension"),
        pytest.param("/download?filename=report.pdf", 0.0, id="query-is-not-extension"),
        pytest.param("/download", 0.0, id="no-extension"),
    ],
)
def test_content_type_scores_file_extension(path, expected):
    scorer = ContentTypeScorer({".pdf$": 1.0})

    assert scorer.score(f"https://example.test{path}") == expected


def test_regex_fallback_still_matches_the_original_url():
    scorer = ContentTypeScorer({".pdf$": 1.0, r"[?#]format=pdf$": 0.5})

    assert scorer.score("https://example.test/download?format=pdf") == 0.5
    assert scorer.score("https://example.test/download#format=pdf") == 0.5
    assert scorer.score("https://example.test/report.pdf?format=pdf") == 1.0


def test_repeated_scores_keep_weight_and_statistics():
    scorer = ContentTypeScorer({".pdf$": 1.0}, weight=0.5)
    url = "https://example.test/report.pdf?version=1.2"

    assert scorer.score(url) == 0.5
    assert scorer.score(url) == 0.5
    assert scorer.stats.get_average() == 0.5
