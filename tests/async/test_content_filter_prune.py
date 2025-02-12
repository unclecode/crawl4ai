import os, sys
import pytest

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.content_filter_strategy import PruningContentFilter


@pytest.fixture
def basic_html():
    return """
    <html>
        <body>
            <article>
                <h1>Main Article</h1>
                <p>This is a high-quality paragraph with substantial text content. It contains enough words to pass the threshold and has good text density without too many links. This kind of content should survive the pruning process.</p>
                <div class="sidebar">Low quality sidebar content</div>
                <div class="social-share">Share buttons</div>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def link_heavy_html():
    return """
    <html>
        <body>
            <div class="content">
                <p>Good content paragraph that should remain.</p>
                <div class="links">
                    <a href="#">Link 1</a>
                    <a href="#">Link 2</a>
                    <a href="#">Link 3</a>
                    <a href="#">Link 4</a>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mixed_content_html():
    return """
    <html>
        <body>
            <article>
                <h1>Article Title</h1>
                <p class="summary">Short summary.</p>
                <div class="content">
                    <p>Long high-quality paragraph with substantial content that should definitely survive the pruning process. This content has good text density and proper formatting which makes it valuable for retention.</p>
                </div>
                <div class="comments">
                    <p>Short comment 1</p>
                    <p>Short comment 2</p>
                </div>
            </article>
        </body>
    </html>
    """


class TestPruningContentFilter:
    def test_basic_pruning(self, basic_html):
        """Test basic content pruning functionality"""
        filter = PruningContentFilter(min_word_threshold=5)
        contents = filter.filter_content(basic_html)

        combined_content = " ".join(contents).lower()
        assert "high-quality paragraph" in combined_content
        assert "sidebar content" not in combined_content
        assert "share buttons" not in combined_content

    def test_min_word_threshold(self, mixed_content_html):
        """Test minimum word threshold filtering"""
        filter = PruningContentFilter(min_word_threshold=10)
        contents = filter.filter_content(mixed_content_html)

        combined_content = " ".join(contents).lower()
        assert "short summary" not in combined_content
        assert "long high-quality paragraph" in combined_content
        assert "short comment" not in combined_content

    def test_threshold_types(self, basic_html):
        """Test fixed vs dynamic thresholds"""
        fixed_filter = PruningContentFilter(threshold_type="fixed", threshold=0.48)
        dynamic_filter = PruningContentFilter(threshold_type="dynamic", threshold=0.45)

        fixed_contents = fixed_filter.filter_content(basic_html)
        dynamic_contents = dynamic_filter.filter_content(basic_html)

        assert len(fixed_contents) != len(
            dynamic_contents
        ), "Fixed and dynamic thresholds should yield different results"

    def test_link_density_impact(self, link_heavy_html):
        """Test handling of link-heavy content"""
        filter = PruningContentFilter(threshold_type="dynamic")
        contents = filter.filter_content(link_heavy_html)

        combined_content = " ".join(contents).lower()
        assert "good content paragraph" in combined_content
        assert (
            len([c for c in contents if "href" in c]) < 2
        ), "Should prune link-heavy sections"

    def test_tag_importance(self, mixed_content_html):
        """Test tag importance in scoring"""
        filter = PruningContentFilter(threshold_type="dynamic")
        contents = filter.filter_content(mixed_content_html)

        has_article = any("article" in c.lower() for c in contents)
        has_h1 = any("h1" in c.lower() for c in contents)
        assert has_article or has_h1, "Should retain important tags"

    def test_empty_input(self):
        """Test handling of empty input"""
        filter = PruningContentFilter()
        assert filter.filter_content("") == []
        assert filter.filter_content(None) == []

    def test_malformed_html(self):
        """Test handling of malformed HTML"""
        malformed_html = "<div>Unclosed div<p>Nested<span>content</div>"
        filter = PruningContentFilter()
        contents = filter.filter_content(malformed_html)
        assert isinstance(contents, list)

    def test_performance(self, basic_html):
        """Test performance with timer"""
        filter = PruningContentFilter()

        import time

        start = time.perf_counter()
        filter.filter_content(basic_html)
        duration = time.perf_counter() - start

        # Extra strict on performance since you mentioned milliseconds matter
        assert duration < 0.1, f"Processing took too long: {duration:.3f} seconds"

    @pytest.mark.parametrize(
        "threshold,expected_count",
        [
            (0.3, 4),  # Very lenient
            (0.48, 2),  # Default
            (0.7, 1),  # Very strict
        ],
    )
    def test_threshold_levels(self, mixed_content_html, threshold, expected_count):
        """Test different threshold levels"""
        filter = PruningContentFilter(threshold_type="fixed", threshold=threshold)
        contents = filter.filter_content(mixed_content_html)
        assert (
            len(contents) <= expected_count
        ), f"Expected {expected_count} or fewer elements with threshold {threshold}"

    def test_consistent_output(self, basic_html):
        """Test output consistency across multiple runs"""
        filter = PruningContentFilter()
        first_run = filter.filter_content(basic_html)
        second_run = filter.filter_content(basic_html)
        assert first_run == second_run, "Output should be consistent"


if __name__ == "__main__":
    pytest.main([__file__])
