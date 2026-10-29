"""Regression tests for nested tags preserved during Markdown generation."""

import pytest

from crawl4ai import DefaultMarkdownGenerator


@pytest.mark.parametrize(
    ("html", "preserve_tags"),
    [
        (
            '<div class="outer">outer<div class="inner">inner</div>end</div>',
            ["div"],
        ),
        (
            '<section id="outer">outer<div id="inner">inner</div>end</section>',
            ["section", "div"],
        ),
        (
            "<table><tr><td>outer<table><tr><td>inner</td></tr></table>"
            "end</td></tr></table>",
            ["table"],
        ),
        (
            '<div id="outer"><div id="middle"><div id="inner">'
            "content</div></div></div>",
            ["div"],
        ),
        (
            '<div class="outer">outer<span class="inner">inner</span>end</div>',
            ["div"],
        ),
        (
            '<div id="first">one</div><div id="second">two</div>',
            ["div"],
        ),
    ],
    ids=["same-tag", "mixed-tags", "nested-table", "three-levels", "child", "siblings"],
)
def test_markdown_preserves_nested_html_tags(html, preserve_tags):
    generator = DefaultMarkdownGenerator(options={"preserve_tags": preserve_tags})

    result = generator.generate_markdown(html, citations=False)

    # Preserved blocks gain separating newlines, but retain their HTML structure.
    assert result.raw_markdown.strip().replace("\n", "") == html
