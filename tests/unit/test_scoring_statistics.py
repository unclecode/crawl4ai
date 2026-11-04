import pytest

from crawl4ai.deep_crawling.scorers import (
    CompositeScorer,
    KeywordRelevanceScorer,
    ScoringStats,
)


@pytest.mark.parametrize(
    "scores", [[0.2, 0.8, 0.4], [-0.2, -0.8, -0.4], [-1.0, 0.0, 2.0]]
)
@pytest.mark.parametrize("read_mode", ["after", "before", "each"])
def test_extrema_do_not_depend_on_when_statistics_are_read(scores, read_mode):
    stats = ScoringStats()
    if read_mode == "before":
        assert stats.get_min() == stats.get_max() == stats.get_average() == 0.0

    for index, score in enumerate(scores):
        stats.update(score)
        if read_mode == "each":
            assert stats.get_min() == min(scores[: index + 1])
            assert stats.get_max() == max(scores[: index + 1])

    assert stats.get_min() == min(scores)
    assert stats.get_max() == max(scores)
    assert stats.get_average() == pytest.approx(sum(scores) / len(scores))


@pytest.mark.parametrize("composite", [False, True])
def test_scorer_statistics_track_observed_weighted_scores(composite):
    scorer = KeywordRelevanceScorer(["python", "blog"], weight=2.0)
    if composite:
        scorer = CompositeScorer([scorer])
    scores = [
        scorer.score(url)
        for url in [
            "https://example.com/python-blog",
            "https://example.com/python",
            "https://example.com/other",
        ]
    ]

    assert scores == [2.0, 1.0, 0.0]
    assert scorer.stats.get_min() == 0.0
    assert scorer.stats.get_max() == 2.0
    assert scorer.stats.get_average() == 1.0
