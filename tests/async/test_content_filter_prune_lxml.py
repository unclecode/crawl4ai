"""Tests for the lxml-native PruningContentFilterLXML.

Two concerns:
  1. The new filter satisfies the same behavioral contract as the original
     (ported from test_content_filter_prune.py).
  2. The new filter is output-equivalent to the original (bs4) implementation
     across a battery of HTML shapes and configs -- this is the fidelity guard
     for the lxml rewrite.
"""
import os
import sys
import time

import pytest
from bs4 import BeautifulSoup

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.content_filter_strategy_lxml import PruningContentFilterLXML


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def basic_html():
    return """
    <html><body><article>
        <h1>Main Article</h1>
        <p>This is a high-quality paragraph with substantial text content. It contains enough words to pass the threshold and has good text density without too many links. This kind of content should survive the pruning process.</p>
        <div class="sidebar">Low quality sidebar content</div>
        <div class="social-share">Share buttons</div>
    </article></body></html>
    """


@pytest.fixture
def link_heavy_html():
    return """
    <html><body><div class="content">
        <p>Good content paragraph that should remain.</p>
        <div class="links">
            <a href="#">Link 1</a><a href="#">Link 2</a><a href="#">Link 3</a><a href="#">Link 4</a>
        </div>
    </div></body></html>
    """


@pytest.fixture
def mixed_content_html():
    return """
    <html><body><article>
        <h1>Article Title</h1>
        <p class="summary">Short summary.</p>
        <div class="content">
            <p>Long high-quality paragraph with substantial content that should definitely survive the pruning process. This content has good text density and proper formatting which makes it valuable for retention.</p>
        </div>
        <div class="comments"><p>Short comment 1</p><p>Short comment 2</p></div>
    </article></body></html>
    """


# Battery of shapes that stress the metric reproduction (void elements,
# entities, nested/!direct anchors, text around removed tags, comments,
# unicode, tables, deep nesting, attributes).
EQUIVALENCE_CASES = {
    "void_img": '<body><div><p>text with <img src="a.png?x=1&y=2" alt="hi"> image content here now</p></div></body>',
    "void_mix": '<body><div>alpha<br>beta<hr><input name="q" value="z"> gamma content text</div></body>',
    "entities_text": '<body><div><p>Tom &amp; Jerry &lt;tag&gt; &copy; 2024 &nbsp; end of paragraph text</p></div></body>',
    "entities_attr": '<body><div><a href="/s?q=a&b=c&d=e">a very long anchor text node here</a> body text follows</div></body>',
    "nested_a_span": '<body><div class="x"><a href="#"><span>nested link text inside span</span></a> tail text after anchor</div></body>',
    "nested_a_multi": '<body><div><a href="#">part one <b>bold</b> part two</a> and more body text content</div></body>',
    "a_not_direct": '<body><div><p>wrapper text <a href="#">deep link</a> more wrapper text content here</p></div></body>',
    "tail_after_nav": '<body><div>before text content <nav>NAVIGATION MENU</nav> after text continues here now</div></body>',
    "tail_after_script": '<body><div>start text <script>var x=1;</script> middle part <style>.a{}</style> end content text</div></body>',
    "comment_interspersed": '<body><div>alpha text <!-- a comment --> beta text <!--another--> gamma delta content</div></body>',
    "pre_whitespace": '<body><pre>  line one\n      line two\n   line three with content  </pre></body>',
    "table": '<body><table><tr><td>cell one content</td><td>cell two content</td></tr><tr><td>three</td><td>four</td></tr></table></body>',
    "unicode_emoji": '<body><div><p>Héllo wörld 你好 مرحبا 🚀🔥 emoji test paragraph content</p></div></body>',
    "nbsp": '<body><div><p>&nbsp;&nbsp;&nbsp;</p><p>actual real content paragraph text goes here now today</p></div></body>',
    "many_attrs": '<body><div id="main" class="a b c" data-x="1" data-y="2&3" role="main"><p>paragraph text content here for the win today</p></div></body>',
    "header_footer_aside": '<body><header>HEAD</header><main><p>Main content paragraph that is substantial enough to keep around here.</p></main><aside>ASIDE JUNK</aside><footer>FOOT</footer></body>',
    "links_vs_content": '<body><div class="links">' + ''.join(f'<a href="#">L{i}</a>' for i in range(20)) + '</div><div class="content"><p>Good paragraph with real content that should clearly survive pruning here today.</p></div></body>',
    "deep_nested": '<body>' + '<div>' * 300 + 'deep content text that is long enough to matter here' + '</div>' * 300 + '</body>',
    "malformed": "<div>Unclosed div<p>Nested<span>content that keeps going on here</div>",
}

CONFIGS = [
    {},
    {"threshold_type": "dynamic"},
    {"threshold_type": "dynamic", "threshold": 0.45},
    {"threshold": 0.3},
    {"threshold": 0.7},
    {"min_word_threshold": 3},
    {"min_word_threshold": 10},
]


def _norm_block_texts(blocks):
    """Visible text of each block, whitespace-normalized (serialization-agnostic)."""
    return [" ".join(BeautifulSoup(b, "lxml").get_text(" ").split()) for b in blocks]


# --------------------------------------------------------------------------- #
# Behavioral contract (ported, run against the NEW class)
# --------------------------------------------------------------------------- #
class TestPruningContentFilterLXMLBehavior:
    def test_basic_pruning(self, basic_html):
        contents = PruningContentFilterLXML(min_word_threshold=5).filter_content(basic_html)
        combined = " ".join(contents).lower()
        assert "high-quality paragraph" in combined
        assert "sidebar content" not in combined
        assert "share buttons" not in combined

    def test_min_word_threshold(self, mixed_content_html):
        contents = PruningContentFilterLXML(min_word_threshold=10).filter_content(mixed_content_html)
        combined = " ".join(contents).lower()
        assert "short summary" not in combined
        assert "long high-quality paragraph" in combined
        assert "short comment" not in combined

    def test_link_density_impact(self, link_heavy_html):
        contents = PruningContentFilterLXML(threshold_type="dynamic").filter_content(link_heavy_html)
        combined = " ".join(contents).lower()
        assert "good content paragraph" in combined
        assert len([c for c in contents if "href" in c]) < 2

    def test_tag_importance(self, mixed_content_html):
        contents = PruningContentFilterLXML(threshold_type="dynamic").filter_content(mixed_content_html)
        assert any("article" in c.lower() for c in contents) or any("h1" in c.lower() for c in contents)

    def test_empty_input(self):
        f = PruningContentFilterLXML()
        assert f.filter_content("") == []
        assert f.filter_content(None) == []

    def test_malformed_html(self):
        contents = PruningContentFilterLXML().filter_content("<div>Unclosed div<p>Nested<span>content</div>")
        assert isinstance(contents, list)

    @pytest.mark.parametrize("threshold,expected_count", [(0.3, 4), (0.48, 2), (0.7, 1)])
    def test_threshold_levels(self, mixed_content_html, threshold, expected_count):
        contents = PruningContentFilterLXML(threshold_type="fixed", threshold=threshold).filter_content(mixed_content_html)
        assert len(contents) <= expected_count

    def test_consistent_output(self, basic_html):
        f = PruningContentFilterLXML()
        assert f.filter_content(basic_html) == f.filter_content(basic_html)


# --------------------------------------------------------------------------- #
# Fidelity: new output must match the original bs4 implementation
# --------------------------------------------------------------------------- #
class TestPruningEquivalence:
    @pytest.mark.parametrize("name", list(EQUIVALENCE_CASES.keys()))
    @pytest.mark.parametrize("config", CONFIGS)
    def test_blocks_match_original(self, name, config):
        html = EQUIVALENCE_CASES[name]
        old = PruningContentFilter(**config).filter_content(html)
        new = PruningContentFilterLXML(**config).filter_content(html)
        assert _norm_block_texts(old) == _norm_block_texts(new), (
            f"{name} {config}\n old={_norm_block_texts(old)}\n new={_norm_block_texts(new)}"
        )

    def test_fixture_files_match_original(self):
        """If saved server fixtures exist, diff old vs new on them too (large)."""
        fixtures = os.environ.get("PRUNE_FIXTURES_DIR")
        if not fixtures or not os.path.isdir(fixtures):
            pytest.skip("no PRUNE_FIXTURES_DIR set")
        for fn in sorted(os.listdir(fixtures)):
            if not fn.endswith(".html"):
                continue
            html = open(os.path.join(fixtures, fn)).read()
            for config in CONFIGS:
                old = PruningContentFilter(**config).filter_content(html)
                new = PruningContentFilterLXML(**config).filter_content(html)
                assert _norm_block_texts(old) == _norm_block_texts(new), f"{fn} {config}"


# --------------------------------------------------------------------------- #
# Performance: new must be substantially faster on a non-trivial page
# --------------------------------------------------------------------------- #
def test_performance_faster_than_original():
    # ~600 repeated cards -> a few hundred KB of HTML
    html = "<body>" + "".join(
        f'<div class="card"><h3>Card {i}</h3>'
        f'<p>Some descriptive paragraph text for card number {i} with enough words to score.</p>'
        f'<div class="meta"><a href="#">tag-a</a><a href="#">tag-b</a></div></div>'
        for i in range(600)
    ) + "</body>"

    def timed(cls):
        f = cls()
        t0 = time.perf_counter()
        out = f.filter_content(html)
        return time.perf_counter() - t0, out

    old_t, old_out = timed(PruningContentFilter)
    new_t, new_out = timed(PruningContentFilterLXML)

    assert _norm_block_texts(old_out) == _norm_block_texts(new_out)
    # Expect a large margin; assert a conservative 2x to avoid flakiness.
    assert new_t < old_t / 2, f"new={new_t*1000:.1f}ms not <2x faster than old={old_t*1000:.1f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
