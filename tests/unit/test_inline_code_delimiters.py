"""Inline code must retain its text after Markdown is parsed again."""

from html import escape

import pytest
from markdown_it import MarkdownIt

from crawl4ai.html2text import CustomHTML2Text
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def code_spans(markdown):
    return [
        child.content
        for token in MarkdownIt("commonmark").parse(markdown)
        for child in token.children or []
        if child.type == "code_inline"
    ]


@pytest.mark.parametrize(
    "content",
    [
        "a`b",
        "`name`",
        "x``y`z",
        "```",
        "`prefix",
        "suffix`",
        " a ",
        "  a  ",
        "plain",
        " ",
        "  ",
        " a",
        "a ",
        r"a\`b",
    ],
)
@pytest.mark.parametrize("in_link", [False, True])
def test_inline_code_round_trips_through_commonmark(content, in_link):
    source = f"<code>{escape(content)}</code>"
    if in_link:
        source = f'<a href="https://example.com/docs">{source}</a>'

    markdown = CustomHTML2Text().handle(f"<p>Use {source} here.</p>")

    assert code_spans(markdown) == [content]
    if in_link:
        assert "](https://example.com/docs)" in markdown


def test_entity_and_comment_chunks_share_one_delimiter():
    markdown = CustomHTML2Text().handle("<code>a&#96;<!-- split -->&#96;b</code>")

    assert code_spans(markdown) == ["a``b"]


def test_multiple_spans_do_not_share_buffered_content():
    markdown = CustomHTML2Text().handle("<code>a`b</code> then <code>c``d</code>")

    assert code_spans(markdown) == ["a`b", "c``d"]


def test_unclosed_code_is_flushed_at_end_of_input():
    converter = CustomHTML2Text()

    assert code_spans(converter.handle("<code>a`b")) == ["a`b"]
    assert converter.handle("<p>next page</p>").strip() == "next page"


def test_streamed_input_and_custom_output_callback():
    output = []
    converter = CustomHTML2Text(out=output.append)
    converter.feed("<code>a`")
    converter.feed("`b</code>")
    converter.finish()

    assert code_spans("".join(output)) == ["a``b"]


def test_pre_blocks_keep_their_existing_output():
    source = '<pre data-language="python"><code>print(`x`)\nnext()</code></pre>'

    markdown = CustomHTML2Text().handle(source)

    assert markdown == "\n```python\nprint(`x`)\nnext()\n```\n\n"


def test_preserved_code_tags_keep_their_html():
    converter = CustomHTML2Text()
    converter.update_params(preserve_tags=["code"])

    assert converter.handle("<code>a`b</code>").strip() == "<code>a`b</code>"


def test_hidden_content_is_not_added_to_the_code_buffer():
    markdown = CustomHTML2Text().handle(
        "<code>a<script>hidden</script><style>also hidden</style>b</code>"
    )

    assert code_spans(markdown) == ["ab"]


def test_empty_code_does_not_emit_literal_delimiters():
    assert CustomHTML2Text().handle("before<code></code>after").strip() == "beforeafter"


def test_pre_code_option_keeps_its_existing_output():
    markdown = CustomHTML2Text(handle_code_in_pre=True).handle(
        "<pre><code>print(1)</code></pre>"
    )

    assert markdown == "\n```\n`print(1)`\n```\n\n"


def test_default_markdown_generator_uses_safe_delimiters():
    result = DefaultMarkdownGenerator().generate_markdown(
        "<p>Use <code>`name`</code> here.</p>", citations=False
    )

    assert code_spans(result.raw_markdown) == ["`name`"]
