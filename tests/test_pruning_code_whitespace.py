"""
PruningContentFilter must not prune inside <pre>/<code> blocks.

Syntax highlighters (pygments, prism, rouge) wrap every token in <span>,
including whitespace-only spans like <span class="w"> </span>. Those spans
score ~0.26-0.36 against the default 0.48 threshold and were decomposed,
collapsing `import torch` to `importtorch` — the fit_markdown counterpart of
the scraper-side bug fixed in #1181. Heavily-highlighted <pre> blocks (huge
tag_len, low text density) could also be dropped wholesale.
"""
import pytest
from crawl4ai.content_filter_strategy import PruningContentFilter


# Pygments-style highlighting: every token in a span, whitespace in class="w".
HIGHLIGHTED_CODE_HTML = """
<html><body>
<article>
    <h1>Using PyTorch</h1>
    <p>This paragraph carries enough real prose to pass the pruning threshold
    comfortably. It explains how to import the library and configure a device
    before running the model, so the surrounding article content is retained
    by the filter as fully relevant text.</p>
    <pre><code class="highlight"><span class="kn">import</span><span class="w"> </span><span class="nn">torch</span>
<span class="kn">import</span><span class="w"> </span><span class="nn">triton.language</span><span class="w"> </span><span class="k">as</span><span class="w"> </span><span class="nn">tl</span>
<span class="n">FROM</span><span class="w"> </span><span class="n">golang</span><span class="p">:</span><span class="mf">1.21</span><span class="w"> </span><span class="n">AS</span><span class="w"> </span><span class="n">builder</span></code></pre>
    <p>Another paragraph of real prose after the code block, long enough to be
    kept on its own merits, describing what the snippet above actually does in
    the larger training pipeline.</p>
</article>
<nav>
    <a href="/">Home</a>
    <a href="/docs">Docs</a>
</nav>
</body></html>
"""


def _filtered_html(html: str, **kwargs) -> str:
    chunks = PruningContentFilter(**kwargs).filter_content(html)
    return "\n".join(chunks)


def test_whitespace_spans_inside_code_survive():
    out = _filtered_html(HIGHLIGHTED_CODE_HTML)
    # The whitespace-only spans must still separate the tokens.
    assert '<span class="w"> </span>' in out
    assert "importtorch" not in out.replace("</span>", "").replace(
        '<span class="kn">', ""
    ).replace('<span class="nn">', "").replace('<span class="w">', "")


def test_highlighted_pre_block_not_dropped():
    out = _filtered_html(HIGHLIGHTED_CODE_HTML)
    # The heavily-tagged <pre> (low text density) must be kept wholesale.
    assert "<pre>" in out
    assert "triton.language" in out


def test_code_guard_does_not_disable_normal_pruning():
    out = _filtered_html(HIGHLIGHTED_CODE_HTML)
    # Boilerplate outside code blocks is still pruned.
    assert "/docs" not in out


def test_rendered_text_keeps_token_spacing():
    from bs4 import BeautifulSoup

    out = _filtered_html(HIGHLIGHTED_CODE_HTML)
    pre = BeautifulSoup(out, "html.parser").find("pre")
    assert pre is not None
    text = pre.get_text()
    assert "import torch" in text
    assert "FROM golang:1.21 AS builder" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
