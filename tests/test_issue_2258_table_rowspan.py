"""Tests for issue #2258: DefaultTableExtraction drops <th> row headers and
ignores rowspan, producing misaligned result.tables.

https://github.com/unclecode/crawl4ai/issues/2258

`extract_table_data` only iterated `.//td` for body rows, so a row-header
`<th>` inside `<tbody>` was dropped (shifting every following cell left and
padding the row with a phantom trailing ""), and `rowspan` was ignored
entirely, so a spanning cell's value was not repeated into the rows it
covers.
"""

from lxml import html as lhtml

from crawl4ai import DefaultTableExtraction


def _extract(html: str):
    # Wrap in a container so fromstring always returns a wrapper element,
    # even when the snippet is a single top-level <table>.
    root = lhtml.fromstring(f"<div>{html}</div>")
    return DefaultTableExtraction().extract_tables(root)


def test_th_row_header_in_tbody_is_kept():
    html = """
    <table>
    <tr><th></th><th>Feature A</th><th>Feature B</th></tr>
    <tr><th scope="row">Item 1</th><td>yes</td><td>yes</td></tr>
    <tr><th scope="row">Item 2</th><td>no</td><td>yes</td></tr>
    </table>
    """
    tables = _extract(html)
    assert len(tables) == 1
    assert tables[0]["headers"] == ["", "Feature A", "Feature B"]
    assert tables[0]["rows"] == [
        ["Item 1", "yes", "yes"],
        ["Item 2", "no", "yes"],
    ]


def test_rowspan_value_repeats_into_covered_rows():
    html = """
    <table>
    <thead><tr><th>Group</th><th>Option X</th><th>Option Y</th></tr></thead>
    <tbody>
    <tr><td rowspan="2">Group 1</td><td>value x</td><td>value y</td></tr>
    <tr><td colspan="2">note that applies to X and Y</td></tr>
    </tbody></table>
    """
    tables = _extract(html)
    assert len(tables) == 1
    assert tables[0]["headers"] == ["Group", "Option X", "Option Y"]
    assert tables[0]["rows"] == [
        ["Group 1", "value x", "value y"],
        ["Group 1", "note that applies to X and Y", "note that applies to X and Y"],
    ]


def test_rowspan_of_three_repeats_across_all_covered_rows():
    html = """
    <table>
    <thead><tr><th>Region</th><th>Quarter</th><th>Revenue</th></tr></thead>
    <tbody>
    <tr><td rowspan="3">EMEA</td><td>Q1</td><td>100</td></tr>
    <tr><td>Q2</td><td>110</td></tr>
    <tr><td>Q3</td><td>120</td></tr>
    </tbody></table>
    """
    tables = _extract(html)
    assert tables[0]["rows"] == [
        ["EMEA", "Q1", "100"],
        ["EMEA", "Q2", "110"],
        ["EMEA", "Q3", "120"],
    ]


def test_plain_table_without_spans_is_unaffected():
    html = """
    <table>
    <thead><tr><th>Name</th><th>Value</th></tr></thead>
    <tbody>
    <tr><td>a</td><td>1</td></tr>
    <tr><td>b</td><td>2</td></tr>
    </tbody></table>
    """
    tables = _extract(html)
    assert tables[0]["headers"] == ["Name", "Value"]
    assert tables[0]["rows"] == [["a", "1"], ["b", "2"]]
