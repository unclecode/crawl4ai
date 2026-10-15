"""Row spans cover cells within their own table row group."""

import pytest
from lxml import html as lhtml

from crawl4ai import DefaultTableExtraction


def _extract(markup):
    tables = DefaultTableExtraction().extract_tables(
        lhtml.fromstring(f"<div><table>{markup}</table></div>")
    )
    assert len(tables) == 1
    return tables[0]


@pytest.mark.parametrize("group", ["tbody", "tfoot", None])
def test_zero_rowspan_covers_remaining_rows(group):
    rows = """
    <tr><td rowspan="0">A</td><td>a1</td></tr>
    <tr><td>a2</td></tr>
    <tr><td>a3</td></tr>
    """
    if group:
        rows = f"<{group}>{rows}</{group}>"
    table = _extract("<thead><tr><th>Group</th><th>Value</th></tr></thead>" + rows)

    assert table["rows"] == [["A", "a1"], ["A", "a2"], ["A", "a3"]]
    assert table["metadata"]["row_count"] == 3
    assert table["metadata"]["column_count"] == 2


@pytest.mark.parametrize("rowspan", ["0", "2", "99"])
@pytest.mark.parametrize("next_group", ["tbody", "tfoot"])
def test_rowspan_stops_at_row_group_boundary(rowspan, next_group):
    table = _extract(f"""
        <thead><tr><th>Group</th><th>Value</th></tr></thead>
        <tbody>
        <tr><td rowspan="{rowspan}">A</td><td>a1</td></tr>
        <tr><td>a2</td></tr>
        </tbody>
        <{next_group}>
        <tr><td>B</td><td>b1</td></tr>
        <tr><td>B</td><td>b2</td></tr>
        </{next_group}>
    """)

    assert table["rows"] == [
        ["A", "a1"],
        ["A", "a2"],
        ["B", "b1"],
        ["B", "b2"],
    ]


@pytest.mark.parametrize("rowspan", ["0", "00", " 0 ", "+0", "-0"])
def test_zero_rowspan_from_middle_of_group_combines_with_colspan(rowspan):
    table = _extract(f"""
        <thead><tr><th>Left</th><th>Middle</th><th>Right</th></tr></thead>
        <tbody>
        <tr><td>l1</td><td>m1</td><td>r1</td></tr>
        <tr><td colspan="2" rowspan="{rowspan}">Shared</td><td>r2</td></tr>
        <tr><td>r3</td></tr>
        </tbody>
    """)

    assert table["rows"] == [
        ["l1", "m1", "r1"],
        ["Shared", "Shared", "r2"],
        ["Shared", "Shared", "r3"],
    ]


@pytest.mark.parametrize("rowspan", ["-2", "invalid"])
def test_invalid_rowspan_does_not_expand_to_end_of_group(rowspan):
    table = _extract(f"""
        <thead><tr><th>Group</th><th>Value</th></tr></thead>
        <tbody>
        <tr><td rowspan="{rowspan}">A</td><td>a1</td></tr>
        <tr><td>B</td><td>b1</td></tr>
        </tbody>
    """)

    assert table["rows"] == [["A", "a1"], ["B", "b1"]]
