"""Header colspans must be validated before expanding the header list."""

import pytest
from lxml import html as lhtml

from crawl4ai import DefaultTableExtraction


@pytest.fixture(params=["thead", "implicit_th", "implicit_td"])
def extract_header(request):
    def extract(span):
        attribute = "" if span is None else f' colspan="{span}"'
        tag = "td" if request.param == "implicit_td" else "th"
        header = f"<tr><{tag}{attribute}>Product</{tag}><{tag}>Price</{tag}></tr>"
        if request.param == "thead":
            header = f"<thead>{header}</thead>"
        root = lhtml.fromstring(
            f"<div><table>{header}<tbody>"
            "<tr><td>Notebook</td><td>12</td></tr>"
            "<tr><td>Pencil</td><td>2</td></tr>"
            "</tbody></table></div>"
        )
        # Exercise the public extraction path independently of table scoring.
        tables = DefaultTableExtraction(table_score_threshold=0).extract_tables(root)
        assert len(tables) == 1, "An invalid header span must not discard the table"
        return tables[0]

    return extract


@pytest.mark.parametrize("span", [None, "", "lots", "100%", "0", "-3"])
def test_invalid_or_missing_header_span_defaults_to_one(extract_header, span):
    table = extract_header(span)
    assert table["headers"] == ["Product", "Price"]
    assert table["rows"][-2:] == [["Notebook", "12"], ["Pencil", "2"]]
    assert table["metadata"]["column_count"] == 2


@pytest.mark.parametrize(
    "span, expected",
    [("1", 1), ("2", 2), ("1000", 1000), ("1001", 1000), ("10000", 1000)],
)
def test_header_span_is_bounded_without_changing_valid_spans(
    extract_header, span, expected
):
    table = extract_header(span)
    assert table["headers"] == ["Product"] * expected + ["Price"]
    assert table["metadata"]["column_count"] == expected + 1
    assert all(len(row) == expected + 1 for row in table["rows"])
    assert table["rows"][-2][:2] == ["Notebook", "12"]


def test_invalid_header_does_not_drop_its_table_or_other_tables():
    root = lhtml.fromstring("""
    <div>
      <table><thead><tr><th colspan="">First</th></tr></thead>
        <tbody><tr><td>kept</td></tr></tbody></table>
      <table><thead><tr><th>Second</th></tr></thead>
        <tbody><tr><td>also kept</td></tr></tbody></table>
    </div>
    """)
    tables = DefaultTableExtraction(table_score_threshold=0).extract_tables(root)
    assert [table["headers"] for table in tables] == [["First"], ["Second"]]
    assert [table["rows"] for table in tables] == [[["kept"]], [["also kept"]]]
