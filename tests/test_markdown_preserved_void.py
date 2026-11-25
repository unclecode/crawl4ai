import pytest

from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.parametrize(
    "element",
    [
        '<img src="cover.png" alt="Cover">',
        '<img src="cover.png"/>',
        "<br>",
        "<input checked>",
    ],
)
def test_preserved_void_tag_keeps_following_paragraph(element):
    generator = DefaultMarkdownGenerator(options={"preserve_tags": ["img", "br", "input"]})
    html = f"<p>Cover</p>{element}<p>Chapter one.</p>"
    result = generator.generate_markdown(html)
    assert result.raw_markdown.strip().splitlines() == [
        "Cover", "", element, "", "Chapter one."
    ]


def test_preserved_void_tag_inside_preserved_block():
    figure = '<figure><img src="cover.png"><figcaption>Cover</figcaption></figure>'
    generator = DefaultMarkdownGenerator(options={"preserve_tags": ["figure", "img"]})
    result = generator.generate_markdown(f"{figure}<p>Next</p>")
    assert figure in result.raw_markdown
    assert result.raw_markdown.strip().endswith("Next")


def test_unselected_image_keeps_markdown_image_syntax():
    generator = DefaultMarkdownGenerator(options={"preserve_tags": ["br"]})
    result = generator.generate_markdown('<p><img alt="Cover" src="cover.png"></p><p>Next</p>')
    assert "![Cover](cover.png)" in result.raw_markdown
    assert result.raw_markdown.strip().endswith("Next")
