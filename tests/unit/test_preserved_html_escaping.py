import pytest
from bs4 import BeautifulSoup

from crawl4ai.html2text import CustomHTML2Text
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.parametrize(
    "source",
    [
        '<div title="a &quot;quote&quot; &amp; b">text</div>',
        '<div><span title="a &quot;quote&quot; &amp; b">text</span></div>',
        "<div>&lt;name&gt; &amp; &#60;value&#62;</div>",
        "<div>plain text &amp;lt;literal&amp;gt;</div>",
        "<div>&nbsp;&#160;&#xA0;</div>",
        "<div>&mdash; &copy; &eacute;</div>",
        "<div><script>const x = a < b && c > d;</script></div>",
        "<div><style>p::before { content: '&amp;'; }</style></div>",
    ],
)
def test_preserved_html_round_trips_text_and_attributes(source):
    converter = CustomHTML2Text()
    converter.update_params(preserve_tags=["div"])
    expected = BeautifulSoup(source, "html.parser")
    actual = BeautifulSoup(converter.handle(source), "html.parser")

    assert actual.div.get_text() == expected.div.get_text()
    assert [tag.attrs for tag in actual.div.find_all(True)] == [
        tag.attrs for tag in expected.div.find_all(True)
    ]
    assert actual.div.attrs == expected.div.attrs
    assert [tag.string for tag in actual.div.find_all(["script", "style"])] == [
        tag.string for tag in expected.div.find_all(["script", "style"])
    ]


def test_markdown_generator_keeps_literal_angle_brackets_in_preserved_html():
    result = DefaultMarkdownGenerator(
        options={"preserve_tags": ["div"]}
    ).generate_markdown(
        "<div>Use &lt;model&gt; &amp; &lt;query&gt;.</div>", citations=False
    )
    assert BeautifulSoup(result.raw_markdown, "html.parser").div.get_text() == (
        "Use <model> & <query>."
    )


@pytest.mark.parametrize(
    "unicode_snob, expected",
    [(False, "-- (C) e 🙂"), (True, "— © é 🙂")],
)
def test_unpreserved_entities_keep_configured_normalization(unicode_snob, expected):
    converter = CustomHTML2Text()
    converter.update_params(unicode_snob=unicode_snob)
    assert (
        converter.handle("<p>&mdash; &copy; &eacute; &#x1F642;</p>").strip() == expected
    )
