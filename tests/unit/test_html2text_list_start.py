"""List numbering should tolerate a start attribute without a value."""

import pytest

from crawl4ai.html2text import HTML2Text
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.parametrize(
    ("tag", "attribute", "expected"),
    [
        ("ol", " start", ["1. Alpha", "2. Beta"]),
        ("ul", " start", ["* Alpha", "* Beta"]),
        ("ol", "", ["1. Alpha", "2. Beta"]),
        ("ol", " start=''", ["1. Alpha", "2. Beta"]),
        ("ol", " start='bad'", ["1. Alpha", "2. Beta"]),
        ("ol", " start='5'", ["5. Alpha", "6. Beta"]),
        ("ol", " start='0'", ["0. Alpha", "1. Beta"]),
        ("ol", " start='-2'", ["-2. Alpha", "-1. Beta"]),
    ],
)
def test_list_start_attribute(tag, attribute, expected):
    html = f"<{tag}{attribute}><li>Alpha</li><li>Beta</li></{tag}>"

    markdown = HTML2Text(bodywidth=0).handle(html)

    assert [line.strip() for line in markdown.splitlines() if line.strip()] == expected


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("ol", ["1. Alpha", "2. Beta"]), ("ul", ["* Alpha", "* Beta"])],
)
def test_markdown_generator_with_unvalued_list_start(tag, expected):
    html = f"<{tag} start><li>Alpha</li><li>Beta</li></{tag}>"

    markdown = DefaultMarkdownGenerator().generate_markdown(html).raw_markdown

    assert [line.strip() for line in markdown.splitlines() if line.strip()] == expected
