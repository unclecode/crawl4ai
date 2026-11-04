"""FreshnessScorer scores against the current year by default.

The default used to be a hard-coded 2024, and years after current_year are
discarded as invalid, so from 2025 on current content scored like an undated
URL (0.5) and 2024 content scored highest.
"""

from datetime import date

from crawl4ai.deep_crawling.scorers import FreshnessScorer


def test_default_scores_this_year_highest():
    this_year = date.today().year
    scorer = FreshnessScorer()

    newest = scorer.score(f"https://example.com/blog/{this_year}/01/02/post")
    last_year = scorer.score(f"https://example.com/blog/{this_year - 1}/post")
    old = scorer.score(f"https://example.com/blog/{this_year - 6}/post")
    undated = scorer.score("https://example.com/about")

    assert newest == 1.0
    assert newest > last_year > old
    assert newest > undated


def test_explicit_current_year_is_still_honoured():
    scorer = FreshnessScorer(current_year=2024)
    assert scorer.score("https://example.com/2024/post") == 1.0
    # later years are treated as invalid relative to the given year
    assert scorer.score("https://example.com/2026/post") == 0.5
