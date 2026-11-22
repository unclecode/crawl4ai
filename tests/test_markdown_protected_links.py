"""Link protection is Markdown formatting, never part of the URL."""

import pytest

from crawl4ai.html2text import CustomHTML2Text
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

PAGE_URL = "https://example.com/docs/page.html"
LINKS = [
    ("https://other.example/path?item=2", "https://other.example/path?item=2"),
    ("guide.html", "https://example.com/docs/guide.html"),
    ("/help", "https://example.com/help"),
    ("//cdn.example/manual", "https://cdn.example/manual"),
    ("report 2026.html", "https://example.com/docs/report 2026.html"),
]


@pytest.mark.parametrize("href, resolved", LINKS)
@pytest.mark.parametrize("inline", [True, False])
def test_protection_wraps_the_resolved_destination(href, resolved, inline):
    converter = CustomHTML2Text(baseurl=PAGE_URL)
    converter.update_params(protect_links=True, inline_links=inline)

    markdown = converter.handle(f'<p>Read <a href="{href}">the guide</a>.</p>')

    if inline:
        assert f"[the guide](<{resolved}>)" in markdown
    else:
        assert "[the guide][1]" in markdown
        assert f"[1]: <{resolved}>" in markdown


@pytest.mark.parametrize("href, resolved", LINKS)
def test_citations_recover_the_destination_from_protected_markdown(href, resolved):
    generator = DefaultMarkdownGenerator(options={"protect_links": True})

    result = generator.generate_markdown(
        f'<p>Read <a href="{href}" title="More information">the guide</a>.</p>',
        base_url=PAGE_URL,
    )

    assert f'[the guide](<{resolved}> "More information")' in result.raw_markdown
    assert "Read the guide⟨1⟩." in result.markdown_with_citations
    expected_reference = f"⟨1⟩ {resolved}: More information - the guide\n"
    assert expected_reference in result.references_markdown


@pytest.mark.parametrize("inline", [True, False])
def test_unprotected_link_keeps_existing_format(inline):
    converter = CustomHTML2Text(baseurl=PAGE_URL)
    converter.update_params(inline_links=inline)

    markdown = converter.handle('<p>Read <a href="/help">the guide</a>.</p>')

    if inline:
        assert "[the guide](https://example.com/help)" in markdown
    else:
        assert "[1]: https://example.com/help" in markdown


def test_unprotected_markdown_still_has_a_reference():
    result = DefaultMarkdownGenerator().generate_markdown(
        '<p>Read <a href="guide.html">the guide</a>.</p>', base_url=PAGE_URL
    )

    assert "[the guide](https://example.com/docs/guide.html)" in result.raw_markdown
    assert "Read the guide⟨1⟩." in result.markdown_with_citations
    expected_reference = "⟨1⟩ https://example.com/docs/guide.html: the guide\n"
    assert expected_reference in result.references_markdown


def test_citations_strip_protected_destination_without_a_page_url():
    converted, references = DefaultMarkdownGenerator().convert_links_to_citations(
        "Read [the guide](<report 2026.html>)."
    )

    assert converted == "Read the guide⟨1⟩."
    assert "⟨1⟩ report 2026.html: the guide\n" in references


def test_protected_destination_preserves_url_punctuation():
    generator = DefaultMarkdownGenerator(options={"protect_links": True})
    result = generator.generate_markdown(
        '<p><a href="report(2026)[draft].html">the report</a></p>', base_url=PAGE_URL
    )

    expected = "https://example.com/docs/report(2026)[draft].html"
    assert f"[the report](<{expected}>)" in result.raw_markdown
    assert f"⟨1⟩ {expected}: the report\n" in result.references_markdown


@pytest.mark.parametrize(
    "literal",
    [
        "<p><code>[sample](&lt;path to a.md&gt;)</code></p>",
        "<pre><code>[sample](&lt;path to a.md&gt;)</code></pre>",
        "<blockquote><pre>[sample](&lt;path to a.md&gt;)</pre></blockquote>",
    ],
)
@pytest.mark.parametrize("protect_links", [False, True])
def test_protected_link_syntax_inside_code_remains_literal(literal, protect_links):
    generator = DefaultMarkdownGenerator(options={"protect_links": protect_links})
    result = generator.generate_markdown(
        '<p><a href="/one">first link</a></p>'
        + literal
        + '<p><a href="/two">second link</a></p>',
        base_url=PAGE_URL,
    )

    assert "[sample](<path to a.md>)" in result.markdown_with_citations
    assert "first link⟨1⟩" in result.markdown_with_citations
    assert "second link⟨2⟩" in result.markdown_with_citations
    assert "⟨1⟩ https://example.com/one:" in result.references_markdown
    assert "⟨2⟩ https://example.com/two:" in result.references_markdown
    assert "path to a.md" not in result.references_markdown
