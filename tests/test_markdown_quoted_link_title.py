import pytest

from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.parametrize(
    ("html_title", "markdown_title"),
    [
        ("The &quot;Blue&quot; Guide", "The &quot;Blue&quot; Guide"),
        ("Write &quot;&amp;quot;&quot;", "Write &quot;&amp;quot;&quot;"),
        ("Research &amp; Development", "Research & Development"),
        ("Simple title", "Simple title"),
    ],
)
def test_inline_link_title_survives_citation_conversion(html_title, markdown_title):
    html = f'<a href="https://example.org/guide" title="{html_title}">Guide</a>'
    result = DefaultMarkdownGenerator().generate_markdown(html)

    assert result.raw_markdown.strip() == f'[Guide](https://example.org/guide "{markdown_title}")'
    assert result.markdown_with_citations.strip() == "Guide⟨1⟩"
    assert f"⟨1⟩ https://example.org/guide: {markdown_title} - Guide" in result.references_markdown
