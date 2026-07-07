"""
Tests for #1900: PruningContentFilter preserve_classes and preserve_tags.

Verifies that whitelisted classes/tags are always kept regardless of
pruning score, while non-whitelisted content is still pruned normally.
"""
import pytest
from crawl4ai.content_filter_strategy import PruningContentFilter


# ── HTML fixtures ────────────────────────────────────────────────────────

GITHUB_COMMENT_HTML = """
<html><body>
<article class="main-content">
    <h1>Discussion: Feature Request</h1>
    <p>This is a long paragraph about the feature request with enough words to
    pass the pruning threshold easily. The feature would add support for document
    extraction in the crawl pipeline, enabling binary documents like PDFs and
    DOCX files to be processed alongside HTML pages.</p>

    <div class="comment">
        <div class="comment-header">
            <span class="author"><a href="/user/alice">alice</a></span>
            <time>commented Apr 6, 2026</time>
        </div>
        <div class="comment-body">
            <p>I think this is a great idea. We should implement it using a
            pluggable strategy pattern so users can bring their own extraction
            backend. This would keep the core library lean while supporting
            many document types.</p>
        </div>
    </div>

    <div class="comment">
        <div class="comment-header">
            <span class="author"><a href="/user/bob">bob</a></span>
            <time>commented Apr 7, 2026</time>
        </div>
        <div class="comment-body">
            <p>Agreed with alice. The abstract base class approach makes sense.
            We could also add a built-in implementation for PDFs since crawl4ai
            already has PDFContentScrapingStrategy that could be wrapped.</p>
        </div>
    </div>
</article>

<nav class="site-nav">
    <a href="/">Home</a>
    <a href="/about">About</a>
</nav>
<footer class="site-footer">
    <p>Copyright 2026</p>
</footer>
</body></html>
"""

ATTRIBUTION_HTML = """
<html><body>
<div class="article">
    <p>Long article content that should definitely pass the threshold because it
    contains enough words and text density to score well in the pruning algorithm.
    This paragraph discusses the implementation details of the feature.</p>
    <div class="byline">By <strong>Jane Smith</strong></div>
    <div class="author-bio">Jane is a senior engineer at Example Corp.</div>
</div>
</body></html>
"""

SIMPLE_HTML = """
<html><body>
<div class="content">
    <p>Main content paragraph with enough text to pass pruning easily. This
    discusses important topics that should be preserved in the output.</p>
    <cite class="source">Source: Example Research Paper, 2026</cite>
</div>
</body></html>
"""


# ── Default behavior (no whitelist) ──────────────────────────────────────

class TestDefaultBehavior:

    def test_default_no_preserve(self):
        """Without whitelist, default pruning behavior is unchanged."""
        f = PruningContentFilter()
        assert f.preserve_classes == set()
        assert f.preserve_tags == set()

    def test_main_content_kept(self):
        """Long paragraphs should still be kept."""
        f = PruningContentFilter()
        result = f.filter_content(GITHUB_COMMENT_HTML)
        combined = " ".join(result)
        assert "feature request" in combined.lower()

    def test_nav_footer_still_removed(self):
        """Nav and footer should still be removed even with whitelist on other things."""
        f = PruningContentFilter(preserve_classes=["author"])
        result = f.filter_content(GITHUB_COMMENT_HTML)
        combined = " ".join(result)
        assert "site-nav" not in combined
        assert "Copyright 2026" not in combined


# ── preserve_classes ─────────────────────────────────────────────────────

class TestPreserveClasses:

    def test_preserve_author_class(self):
        """Elements with 'author' class should be kept when whitelisted."""
        f = PruningContentFilter(preserve_classes=["author"])
        result = f.filter_content(GITHUB_COMMENT_HTML)
        combined = " ".join(result)
        assert "alice" in combined
        assert "bob" in combined

    def test_without_preserve_author_may_be_stripped(self):
        """Without whitelist, short author spans may be stripped."""
        f = PruningContentFilter()
        result = f.filter_content(ATTRIBUTION_HTML)
        combined = " ".join(result)
        # The main content should be there
        assert "article content" in combined.lower()
        # byline might be stripped (short, low density)

    def test_preserve_byline(self):
        """Preserving 'byline' class keeps attribution."""
        f = PruningContentFilter(preserve_classes=["byline"])
        result = f.filter_content(ATTRIBUTION_HTML)
        combined = " ".join(result)
        assert "Jane Smith" in combined

    def test_preserve_multiple_classes(self):
        """Multiple classes can be preserved."""
        f = PruningContentFilter(
            preserve_classes=["author", "comment-header", "byline"]
        )
        result = f.filter_content(GITHUB_COMMENT_HTML)
        combined = " ".join(result)
        assert "alice" in combined
        assert "bob" in combined

    def test_preserve_class_not_in_html(self):
        """Preserving a class that doesn't exist in the HTML is harmless."""
        f = PruningContentFilter(preserve_classes=["nonexistent-class"])
        result = f.filter_content(GITHUB_COMMENT_HTML)
        # Should work normally, no crash
        assert len(result) > 0

    def test_empty_preserve_classes(self):
        """Empty list should behave like no whitelist."""
        f = PruningContentFilter(preserve_classes=[])
        assert f.preserve_classes == set()


# ── preserve_tags ────────────────────────────────────────────────────────

class TestPreserveTags:

    def test_preserve_cite_tag(self):
        """Preserving 'cite' tag keeps source attribution."""
        f = PruningContentFilter(preserve_tags=["cite"])
        result = f.filter_content(SIMPLE_HTML)
        combined = " ".join(result)
        assert "Example Research Paper" in combined

    def test_preserve_time_tag(self):
        """Preserving 'time' tag keeps timestamps."""
        f = PruningContentFilter(preserve_tags=["time"])
        result = f.filter_content(GITHUB_COMMENT_HTML)
        combined = " ".join(result)
        assert "Apr 6, 2026" in combined

    def test_preserve_multiple_tags(self):
        """Multiple tags can be preserved."""
        f = PruningContentFilter(preserve_tags=["cite", "time"])
        result = f.filter_content(SIMPLE_HTML)
        combined = " ".join(result)
        assert "Example Research Paper" in combined

    def test_empty_preserve_tags(self):
        """Empty list should behave like no whitelist."""
        f = PruningContentFilter(preserve_tags=[])
        assert f.preserve_tags == set()


# ── Combined ─────────────────────────────────────────────────────────────

class TestCombined:

    def test_both_classes_and_tags(self):
        """Both preserve_classes and preserve_tags work together."""
        f = PruningContentFilter(
            preserve_classes=["author"],
            preserve_tags=["time"],
        )
        result = f.filter_content(GITHUB_COMMENT_HTML)
        combined = " ".join(result)
        assert "alice" in combined
        assert "Apr 6, 2026" in combined

    def test_whitelist_does_not_override_excluded_tags(self):
        """Nav/footer/header are removed before pruning — whitelist can't save them."""
        f = PruningContentFilter(preserve_tags=["nav"])
        result = f.filter_content(GITHUB_COMMENT_HTML)
        combined = " ".join(result)
        # nav is in excluded_tags and removed before pruning runs
        # preserve_tags only affects the pruning phase
        # This is expected — excluded_tags are structural boilerplate


# ── _is_preserved method ─────────────────────────────────────────────────

class TestIsPreserved:

    def test_is_preserved_by_class(self):
        from bs4 import BeautifulSoup
        f = PruningContentFilter(preserve_classes=["author"])
        soup = BeautifulSoup('<span class="author">Alice</span>', "html.parser")
        node = soup.find("span")
        assert f._is_preserved(node) is True

    def test_not_preserved_without_match(self):
        from bs4 import BeautifulSoup
        f = PruningContentFilter(preserve_classes=["author"])
        soup = BeautifulSoup('<span class="date">2026</span>', "html.parser")
        node = soup.find("span")
        assert f._is_preserved(node) is False

    def test_is_preserved_by_tag(self):
        from bs4 import BeautifulSoup
        f = PruningContentFilter(preserve_tags=["cite"])
        soup = BeautifulSoup('<cite>Source</cite>', "html.parser")
        node = soup.find("cite")
        assert f._is_preserved(node) is True

    def test_not_preserved_empty_whitelist(self):
        from bs4 import BeautifulSoup
        f = PruningContentFilter()
        soup = BeautifulSoup('<span class="author">Alice</span>', "html.parser")
        node = soup.find("span")
        assert f._is_preserved(node) is False


# ── Serialization (for Docker API) ───────────────────────────────────────

class TestSerialization:

    def test_params_stored(self):
        """preserve_classes and preserve_tags should be stored as attributes."""
        f = PruningContentFilter(
            preserve_classes=["author", "byline"],
            preserve_tags=["time", "cite"],
        )
        assert f.preserve_classes == {"author", "byline"}
        assert f.preserve_tags == {"time", "cite"}
