"""Default table extraction preserves each table's complete caption text."""

import pytest
from lxml import html as lhtml

from crawl4ai import DefaultTableExtraction

ROWS = "<tr><th>Item</th><th>Total</th></tr>" "<tr><td>A</td><td>10</td></tr>"


@pytest.mark.parametrize(
    ("caption_html", "expected"),
    [
        pytest.param("", "", id="missing"),
        pytest.param("<caption></caption>", "", id="empty"),
        pytest.param("<caption> \n\t </caption>", "", id="whitespace"),
        pytest.param("<caption> Annual sales </caption>", "Annual sales", id="plain"),
        pytest.param(
            "<caption><span>Annual sales</span></caption>",
            "Annual sales",
            id="span-only",
        ),
        pytest.param(
            "<caption> Sales <em>2025</em> by region </caption>",
            "Sales 2025 by region",
            id="mixed-text-and-tail",
        ),
        pytest.param(
            "<caption><span>Annual</span> sales</caption>",
            "Annual sales",
            id="leading-inline-with-tail",
        ),
        pytest.param(
            "<caption><span>Sales <strong>2025</strong></span></caption>",
            "Sales 2025",
            id="nested-inline",
        ),
        pytest.param(
            "<caption><span>Sales &amp; returns</span> &lt; 100</caption>",
            "Sales & returns < 100",
            id="entities",
        ),
        pytest.param(
            "<caption> First </caption><caption>Second</caption>",
            "First",
            id="first-caption-only",
        ),
        pytest.param(
            "<caption><span>Annual sales</span></caption>Outside caption",
            "Annual sales",
            id="exclude-caption-tail",
        ),
    ],
)
def test_extract_table_data_caption(caption_html, expected):
    """Caption text includes descendants and tails, with only outer whitespace stripped."""
    table = lhtml.fromstring(f"<table>{caption_html}{ROWS}</table>")

    result = DefaultTableExtraction().extract_table_data(table)

    assert result["caption"] == expected
    assert result["metadata"]["has_caption"] is bool(expected)
    assert result["headers"] == ["Item", "Total"]
    assert result["rows"] == [["A", "10"]]


@pytest.mark.parametrize("outer_caption", ["", "<caption>Outer table</caption>"])
def test_nested_table_caption_belongs_only_to_nested_table(outer_caption):
    """An inner table's caption must never supply the outer table's caption."""
    outer = lhtml.fromstring(
        f"<table>{outer_caption}<tr><td>"
        f"<table><caption>Inner table</caption>{ROWS}</table>"
        "</td></tr></table>"
    )
    inner = outer.xpath(".//table")[0]
    strategy = DefaultTableExtraction()

    outer_result = strategy.extract_table_data(outer)
    inner_result = strategy.extract_table_data(inner)

    assert outer_result["caption"] == ("Outer table" if outer_caption else "")
    assert outer_result["metadata"]["has_caption"] is bool(outer_caption)
    assert inner_result["caption"] == "Inner table"
    assert inner_result["metadata"]["has_caption"] is True


def test_extract_tables_preserves_inline_caption():
    """The public table-discovery path returns the same complete caption."""
    element = lhtml.fromstring(
        "<div><table><caption>Sales <em>2025</em> by region</caption>"
        f"{ROWS}</table></div>"
    )

    results = DefaultTableExtraction().extract_tables(element)

    assert len(results) == 1
    assert results[0]["caption"] == "Sales 2025 by region"
    assert results[0]["metadata"]["has_caption"] is True
    assert results[0]["headers"] == ["Item", "Total"]
    assert results[0]["rows"] == [["A", "10"]]
