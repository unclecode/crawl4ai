import pytest

from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.parametrize("html", ["", "<p>A paragraph with no links.</p>"])
def test_markdown_without_links_has_no_reference_section(html):
    result = DefaultMarkdownGenerator().generate_markdown(html)

    assert result.markdown_with_citations == result.raw_markdown
    assert result.references_markdown == ""


@pytest.mark.parametrize("citations", [True, False])
def test_markdown_with_links_respects_citations_option(citations):
    url = "https://example.org/reference"
    result = DefaultMarkdownGenerator().generate_markdown(
        f'<p>Read <a href="{url}">the reference</a>.</p>', citations=citations
    )

    if citations:
        assert "the reference⟨1⟩" in result.markdown_with_citations
        assert f"⟨1⟩ {url}" in result.references_markdown
    else:
        assert result.markdown_with_citations == result.raw_markdown
        assert result.references_markdown == ""
