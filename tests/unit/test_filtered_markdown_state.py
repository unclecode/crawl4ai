"""Filtered Markdown must only contain state from the filtered HTML."""

import pytest

from crawl4ai.content_filter_strategy_lxml import PruningContentFilterLXML
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

REMOVED_HTML = '<aside><abbr title="Removed advertisement">AD</abbr></aside>'
KEPT_HTML = "<p>Kept article prose.</p>"


def filtered_generator(**kwargs):
    return DefaultMarkdownGenerator(
        content_filter=PruningContentFilterLXML(threshold=0), **kwargs
    )


def test_removed_abbreviation_does_not_leak_into_fit_markdown():
    html = REMOVED_HTML + KEPT_HTML
    result = filtered_generator().generate_markdown(html)
    unfiltered = DefaultMarkdownGenerator().generate_markdown(html)

    assert result.raw_markdown == unfiltered.raw_markdown
    assert result.markdown_with_citations == unfiltered.markdown_with_citations
    assert result.references_markdown == unfiltered.references_markdown
    assert "*[AD]: Removed advertisement" in result.raw_markdown
    assert "AD" not in result.fit_html
    assert "Kept article prose." in result.fit_html
    assert result.fit_markdown.strip() == "Kept article prose."


def test_fully_removed_content_has_empty_fit_markdown():
    result = filtered_generator().generate_markdown(REMOVED_HTML)

    assert "*[AD]: Removed advertisement" in result.raw_markdown
    assert result.fit_html == ""
    assert result.fit_markdown.strip() == ""


def test_kept_abbreviation_survives_without_removed_definition():
    html = REMOVED_HTML + '<p>Kept <abbr title="World Wide Web">WWW</abbr>.</p>'
    result = filtered_generator().generate_markdown(html)

    assert "AD" not in result.fit_html
    assert "WWW" in result.fit_html
    assert result.fit_markdown.count("*[WWW]: World Wide Web") == 1
    assert "Removed advertisement" not in result.fit_markdown


def test_noop_filter_keeps_abbreviation_definition_once():
    html = '<p>Kept <abbr title="World Wide Web">WWW</abbr>.</p>'
    result = filtered_generator().generate_markdown(html)

    assert result.fit_markdown.strip() == result.raw_markdown.strip()
    assert result.fit_markdown.count("*[WWW]: World Wide Web") == 1


@pytest.mark.parametrize(
    "option_source", ["constructor", "options", "html2text_options"]
)
def test_filtered_conversion_preserves_options_and_base_url(option_source):
    options = {
        "ignore_emphasis": True,
        "body_width": 40,
        "escape_snob": True,
        "ignore_links": option_source == "options",
    }
    generator_options = {"options": options} if option_source == "constructor" else {}
    call_options = {} if option_source == "constructor" else {option_source: options}
    html = (
        '<p><strong>Kept prose</strong> with <a href="article">a link</a>'
        " and _literal_ text that is long enough to wrap onto multiple lines.</p>"
    )
    base_url = "https://example.com/docs/"
    result = filtered_generator(**generator_options).generate_markdown(
        html, base_url=base_url, **call_options
    )
    expected = DefaultMarkdownGenerator(options=options).generate_markdown(
        result.fit_html, base_url=base_url
    )

    assert result.fit_markdown == expected.raw_markdown
    assert "**" not in result.fit_markdown
    assert r"\_literal\_" in result.fit_markdown
    assert all(
        len(line) <= options["body_width"] for line in result.fit_markdown.splitlines()
    )
    if options["ignore_links"]:
        assert "https://example.com/docs/article" not in result.fit_markdown
    else:
        assert "[a link](https://example.com/docs/article)" in " ".join(
            result.fit_markdown.split()
        )


def test_no_filter_does_not_generate_fit_output():
    result = DefaultMarkdownGenerator().generate_markdown(REMOVED_HTML + KEPT_HTML)

    assert "*[AD]: Removed advertisement" in result.raw_markdown
    assert result.fit_html == ""
    assert result.fit_markdown == ""


def test_repeated_generator_calls_do_not_share_abbreviations():
    generator = filtered_generator()
    first = generator.generate_markdown(
        '<p>Kept <abbr title="World Wide Web">WWW</abbr>.</p>'
    )
    second = generator.generate_markdown(KEPT_HTML)

    assert "*[WWW]: World Wide Web" in first.fit_markdown
    assert second.fit_markdown.strip() == "Kept article prose."
    assert "WWW" not in second.raw_markdown


def test_filtered_links_keep_effective_html_base_url():
    html = (
        '<html><head><base href="https://cdn.example.com/articles/"></head>'
        '<body><p>Kept article with <a href="next">a link</a>.</p></body></html>'
    )
    result = filtered_generator(
        options={"baseurl": "https://option.example.com/"}
    ).generate_markdown(html, base_url="https://example.com/docs/")

    assert "<base" not in result.fit_html
    assert "[a link](https://cdn.example.com/articles/next)" in result.raw_markdown
    assert "[a link](https://cdn.example.com/articles/next)" in result.fit_markdown
