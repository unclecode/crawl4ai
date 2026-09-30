"""
convert_links_to_citations must not treat code as markdown links.

`handlers[0](event)` inside a fenced block or an inline code span has the
shape of a link, but it is code and has to survive citation conversion as is.
"""

from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def _cite(markdown, base_url="https://example.com/"):
    return DefaultMarkdownGenerator().convert_links_to_citations(markdown, base_url)


def test_fenced_code_block_is_left_alone():
    markdown = (
        "See [docs](https://example.com/docs).\n\n"
        "```python\nresult = handlers[0](event)\nx = matrix[i](y)\n```\n"
    )
    converted, references = _cite(markdown)
    assert "result = handlers[0](event)\nx = matrix[i](y)" in converted
    assert "See docs⟨1⟩." in converted
    assert "⟨1⟩ https://example.com/docs: docs" in references
    assert "⟨2⟩" not in references


def test_tilde_and_unclosed_fences_are_left_alone():
    markdown = "~~~\nf[a](b)\n~~~\n\n```\ng[c](d)\n"
    converted, references = _cite(markdown)
    assert converted == markdown
    assert "⟨1⟩" not in references


def test_inline_code_span_is_left_alone():
    markdown = "Call `callbacks[key](arg)` then read [the guide](/guide)."
    converted, references = _cite(markdown)
    assert converted == "Call `callbacks[key](arg)` then read the guide⟨1⟩."
    assert "⟨1⟩ https://example.com/guide: the guide" in references
    assert "⟨2⟩" not in references


def test_link_with_code_in_its_text_is_still_cited():
    converted, references = _cite("Use [`arun()`](/api#arun) here.")
    assert converted == "Use `arun()`⟨1⟩ here."
    assert "⟨1⟩ https://example.com/api#arun: `arun()`" in references


def test_generate_markdown_keeps_code_in_citations():
    html = (
        '<p>See <a href="/docs">docs</a>.</p>'
        "<pre><code>result = handlers[0](event)</code></pre>"
        "<p>Inline: <code>callbacks[key](arg)</code></p>"
    )
    result = DefaultMarkdownGenerator().generate_markdown(
        html, base_url="https://example.com/"
    )
    assert "handlers[0](event)" in result.markdown_with_citations
    assert "`callbacks[key](arg)`" in result.markdown_with_citations
    assert "https://example.com/event" not in result.references_markdown
    assert "https://example.com/arg" not in result.references_markdown
