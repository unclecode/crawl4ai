"""A pipe inside a table cell must not add a column.

A GFM row is split on every unescaped pipe, so a cell holding one pushes the
rest of the row into columns the header does not have, and every row after it
reads one column out of step. The cell text reached the output unescaped, so a
regex alternation, a shell command or a part number broke the table it sat in.
"""

import re

import pytest

from crawl4ai.html2text import CustomHTML2Text, HTML2Text

_UNESCAPED_PIPE = re.compile(r"(?<!\\)((?:\\\\)*)\|")
# CommonMark: a backslash escapes ASCII punctuation, and nothing else.
_ESCAPE = re.compile(r"\\([!-/:-@\[-`{-~])")

CONVERTERS = [HTML2Text, CustomHTML2Text]


def _rows(markdown: str) -> list:
    """Read the markdown table back the way a reader does."""
    rows = []
    for line in markdown.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = _UNESCAPED_PIPE.split(line.strip("|"))[::2]
        rows.append([_ESCAPE.sub(r"\1", cell).strip() for cell in cells])
    return rows


def _convert(converter, html: str) -> str:
    return converter(bodywidth=0).handle(html)


@pytest.mark.parametrize("converter", CONVERTERS)
@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("a|b|c", "a|b|c"),
        ("USB-A|USB-C", "USB-A|USB-C"),
        # A backslash already in the cell must not consume the escape.
        (r"a\|b", r"a\|b"),
        # The controls: neither needs escaping.
        (r"C:\path", r"C:\path"),
        ("plain", "plain"),
    ],
)
def test_a_pipe_in_a_cell_stays_inside_the_cell(converter, cell, expected):
    html = f"<table><tr><th>Name</th><th>Value</th></tr><tr><td>codec</td><td>{cell}</td></tr></table>"

    rows = _rows(_convert(converter, html))

    assert rows[0] == ["Name", "Value"]
    assert rows[-1] == ["codec", expected]


@pytest.mark.parametrize("converter", CONVERTERS)
def test_a_pipe_in_a_header_cell_stays_inside_the_cell(converter):
    html = "<table><tr><th>a|b</th><th>Value</th></tr><tr><td>1</td><td>2</td></tr></table>"

    rows = _rows(_convert(converter, html))

    assert rows[0] == ["a|b", "Value"]
    assert rows[-1] == ["1", "2"]


@pytest.mark.parametrize("converter", CONVERTERS)
def test_a_pipe_inside_inline_code_in_a_cell_is_escaped(converter):
    """A code span does not protect a pipe: GFM splits the row first."""
    html = "<table><tr><th>Cmd</th></tr><tr><td><code>grep -E 'a|b'</code></td></tr></table>"

    rows = _rows(_convert(converter, html))

    assert rows[-1] == ["`grep -E 'a|b'`"]


@pytest.mark.parametrize("converter", CONVERTERS)
def test_a_pipe_outside_a_table_is_left_alone(converter):
    assert _convert(converter, "<p>stdin | stdout</p>").strip() == "stdin | stdout"


@pytest.mark.parametrize("converter", CONVERTERS)
def test_bypass_tables_is_left_alone(converter):
    """`bypass_tables` emits the table as HTML, where a pipe is just a pipe."""
    html = "<table><tr><th>A</th></tr><tr><td>a|b</td></tr></table>"
    instance = converter(bodywidth=0)
    instance.bypass_tables = True

    assert "a|b" in instance.handle(html)


@pytest.mark.parametrize("converter", CONVERTERS)
def test_the_table_padder_splits_on_unescaped_pipes_only(converter):
    """`pad_tables` reformats the finished table, so it has to agree.

    Splitting the row on every pipe turned an escaped one back into a column
    boundary and the padded table came out wider than its header.
    """
    html = "<table><tr><th>Name</th><th>Modes</th></tr><tr><td>codec</td><td>a|b|c</td></tr></table>"
    instance = converter(bodywidth=0)
    instance.pad_tables = True

    rows = _rows(instance.handle(html))

    assert [len(row) for row in rows] == [2, 2, 2]
    assert rows[-1] == ["codec", "a|b|c"]


@pytest.mark.parametrize("converter", CONVERTERS)
def test_the_table_padder_leaves_a_plain_table_alone(converter):
    html = "<table><tr><th>Name</th><th>Value</th></tr><tr><td>codec</td><td>x</td></tr></table>"
    instance = converter(bodywidth=0)
    instance.pad_tables = True

    rows = _rows(instance.handle(html))

    assert rows[0] == ["Name", "Value"]
    assert rows[-1] == ["codec", "x"]

