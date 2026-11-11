"""Rows of a table nested in a cell must not show up as rows of the outer table.

`extract_table_data` collected body rows with ``.//tr`` and header rows with
``.//thead/tr``, both of which also match the rows of every table nested inside
a cell: the inner rows were emitted as extra outer rows (their text was already
part of the outer cell, so it was duplicated) and an inner ``<thead>`` was used
as the outer table's header.
"""

from lxml import html as lhtml

from crawl4ai import DefaultTableExtraction


def _extract(html: str):
    table = lhtml.fromstring(f"<div>{html}</div>").xpath("//table")[0]
    return DefaultTableExtraction().extract_table_data(table)


def test_nested_table_rows_are_not_outer_rows():
    data = _extract("""
    <table>
    <tr><th>A</th><th>B</th></tr>
    <tr><td>1</td><td>2</td></tr>
    <tr><td colspan="2"><table><tr><td>x</td><td>y</td></tr><tr><td>z</td><td>w</td></tr></table></td></tr>
    </table>""")

    assert data["headers"] == ["A", "B"]
    assert data["rows"] == [["1", "2"], ["xyzw", "xyzw"]]
    assert data["metadata"]["row_count"] == 2


def test_nested_thead_does_not_become_the_outer_header():
    data = _extract("""
    <table>
    <tr><td>A</td><td>B</td></tr>
    <tr><td><table><thead><tr><th>inner</th><th>inner2</th></tr></thead>
    <tr><td>x</td><td>y</td></tr></table></td><td>right</td></tr>
    </table>""")

    assert data["headers"] == ["A", "B"]
    # Cell text keeps the inner table's whitespace, so compare with it collapsed.
    assert [[" ".join(c.split()) for c in row] for row in data["rows"]] == [
        ["A", "B"],
        ["innerinner2 xy", "right"],
    ]


def test_thead_cells_that_are_td_still_become_the_header():
    """Only direct children are read, but those may be <td> as well as <th>."""
    data = _extract("""
    <table>
    <thead><tr><td>A</td><td colspan="2">B</td></tr></thead>
    <tr><td>1</td><td>2</td><td>3</td></tr>
    </table>""")

    assert data["headers"] == ["A", "B", "B"]
    assert data["rows"] == [["1", "2", "3"]]
