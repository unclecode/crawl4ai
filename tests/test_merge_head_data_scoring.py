"""
Unit tests for _merge_head_data() total_score calculation.

Verifies that total_score is computed for all links, including those
that fail head extraction and only have an intrinsic_score.

Regression tests for https://github.com/unclecode/crawl4ai/issues/1749
"""

import pytest
from unittest.mock import MagicMock

from crawl4ai.models import Link, Links
from crawl4ai.link_preview import LinkPreview
from crawl4ai.utils import calculate_total_score


class TestCalculateTotalScore:
    """Test the calculate_total_score utility function."""

    def test_intrinsic_only(self):
        """When only intrinsic_score is available, total_score should equal intrinsic_score."""
        score = calculate_total_score(
            intrinsic_score=5.0,
            contextual_score=None,
            score_links_enabled=True,
            query_provided=True,
        )
        assert score == 5.0

    def test_no_scoring_enabled(self):
        """When scoring is disabled, total_score should be neutral (5.0)."""
        score = calculate_total_score(
            intrinsic_score=8.0,
            contextual_score=0.5,
            score_links_enabled=False,
            query_provided=True,
        )
        assert score == 5.0

    def test_both_scores(self):
        """When both scores are available, total_score should be a weighted combination."""
        score = calculate_total_score(
            intrinsic_score=8.0,
            contextual_score=0.5,
            score_links_enabled=True,
            query_provided=True,
        )
        # 70% intrinsic + 30% contextual_scaled: (8.0 * 0.7) + (0.5 * 10.0 * 0.3) = 5.6 + 1.5 = 7.1
        assert score == pytest.approx(7.1, abs=0.01)

    def test_no_scores_at_all(self):
        """When no scores are available, total_score should be 0."""
        score = calculate_total_score(
            intrinsic_score=None,
            contextual_score=None,
            score_links_enabled=True,
            query_provided=False,
        )
        assert score == 0.0


class TestMergeHeadDataScoring:
    """Test _merge_head_data() calculates total_score for all links."""

    def _make_config(self, score_links=True, query="test query"):
        """Create a mock CrawlerRunConfig."""
        config = MagicMock()
        config.score_links = score_links
        config.link_preview_config.query = query
        return config

    def test_internal_link_with_head_data_gets_total_score(self):
        """Internal link with successful head extraction should have total_score."""
        link = Link(href="https://example.com/page1", text="Page 1", intrinsic_score=6.0)
        links = Links(internal=[link], external=[])

        head_results = [
            {
                "url": "https://example.com/page1",
                "head_data": {"title": "Page 1"},
                "status": "valid",
                "relevance_score": 0.8,
            }
        ]

        preview = LinkPreview()
        config = self._make_config()
        updated = preview._merge_head_data(links, head_results, config)

        assert updated.internal[0].total_score is not None
        assert updated.internal[0].total_score > 0

    def test_internal_link_without_head_data_gets_total_score(self):
        """Internal link that failed head extraction should still get total_score from intrinsic_score."""
        link = Link(href="https://example.com/doc.pdf", text="PDF Doc", intrinsic_score=5.0)
        links = Links(internal=[link], external=[])

        # No head results for this URL (simulates failed extraction)
        head_results = []

        preview = LinkPreview()
        config = self._make_config()
        updated = preview._merge_head_data(links, head_results, config)

        assert updated.internal[0].total_score is not None
        assert updated.internal[0].total_score == 5.0

    def test_external_link_without_head_data_gets_total_score(self):
        """External link that failed head extraction should still get total_score from intrinsic_score."""
        link = Link(href="https://external.com/page", text="External", intrinsic_score=4.0)
        links = Links(internal=[], external=[link])

        head_results = []

        preview = LinkPreview()
        config = self._make_config()
        updated = preview._merge_head_data(links, head_results, config)

        assert updated.external[0].total_score is not None
        assert updated.external[0].total_score == 4.0

    def test_mixed_links_all_get_total_score(self):
        """Mix of successful and failed head extractions should all have total_score."""
        internal_success = Link(href="https://example.com/page1", text="Page 1", intrinsic_score=7.0)
        internal_fail = Link(href="https://example.com/doc.pdf", text="PDF", intrinsic_score=5.0)
        external_success = Link(href="https://other.com/page", text="Other", intrinsic_score=6.0)
        external_fail = Link(href="https://other.com/timeout", text="Timeout", intrinsic_score=3.0)

        links = Links(
            internal=[internal_success, internal_fail],
            external=[external_success, external_fail],
        )

        head_results = [
            {
                "url": "https://example.com/page1",
                "head_data": {"title": "Page 1"},
                "status": "valid",
                "relevance_score": 0.9,
            },
            {
                "url": "https://other.com/page",
                "head_data": {"title": "Other Page"},
                "status": "valid",
                "relevance_score": 0.7,
            },
        ]

        preview = LinkPreview()
        config = self._make_config()
        updated = preview._merge_head_data(links, head_results, config)

        # All 4 links should have total_score set
        for link in updated.internal + updated.external:
            assert link.total_score is not None, f"total_score is None for {link.href}"
            assert link.total_score > 0, f"total_score is 0 for {link.href}"

    def test_link_without_intrinsic_score_and_no_head_data(self):
        """Link with no intrinsic_score and no head data should still get a total_score (0.0)."""
        link = Link(href="https://example.com/unknown", text="Unknown")
        links = Links(internal=[link], external=[])

        head_results = []

        preview = LinkPreview()
        config = self._make_config(query="test")
        updated = preview._merge_head_data(links, head_results, config)

        assert updated.internal[0].total_score is not None

    def test_scoring_disabled_returns_neutral_score(self):
        """When score_links is disabled, total_score should be neutral (5.0) for all links."""
        link = Link(href="https://example.com/page", text="Page", intrinsic_score=8.0)
        links = Links(internal=[link], external=[])

        head_results = []

        preview = LinkPreview()
        config = self._make_config(score_links=False)
        updated = preview._merge_head_data(links, head_results, config)

        assert updated.internal[0].total_score == 5.0
