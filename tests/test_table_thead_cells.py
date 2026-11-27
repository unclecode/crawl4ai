"""Explicit header rows must keep td cells and their column positions."""

import pytest
from lxml import html as lhtml

from crawl4ai import DefaultTableExtraction
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


@pytest.fixture(params=["extract_tables", "scrap"])
def extract_table(request):
    def extract(fragment):
        strategy = DefaultTableExtraction()
        if request.param == "extract_tables":
            tables = strategy.extract_tables(lhtml.fromstring(f"<div>{fragment}</div>"))
        else:
            result = LXMLWebScrapingStrategy().scrap(
                "https://example.com/products",
                f"<html><body>{fragment}</body></html>",
                table_extraction=strategy,
                word_count_threshold=0,
            )
            assert result.success
            tables = result.media.tables
        assert len(tables) == 1
        return tables[0]

    return extract


@pytest.mark.parametrize(
    "header_cells,expected_headers",
    [
        pytest.param(
            "<td>Product</td><td>Price</td>",
            ["Product", "Price"],
            id="td-only",
        ),
        pytest.param(
            "<td>Product</td><th>Price</th>",
            ["Product", "Price"],
            id="td-before-th",
        ),
        pytest.param(
            "<th>Product</th><td>Price</td>",
            ["Product", "Price"],
            id="td-after-th",
        ),
        pytest.param(
            "<td></td><th>Price</th>",
            ["", "Price"],
            id="empty-corner",
        ),
        pytest.param(
            "<th>Product</th><th>Price</th>",
            ["Product", "Price"],
            id="th-only-control",
        ),
    ],
)
def test_thead_cells_preserve_columns(extract_table, header_cells, expected_headers):
    table = extract_table(f"""
        <table>
        <thead><tr>{header_cells}</tr></thead>
        <tbody>
        <tr><th scope="row">Widget</th><td>19.99</td></tr>
        <tr><th scope="row">Gadget</th><td>39.99</td></tr>
        </tbody>
        </table>
        """)
    assert table["rows"] == [["Widget", "19.99"], ["Gadget", "39.99"]]
    assert table["headers"] == expected_headers
    assert table["metadata"]["column_count"] == 2
    assert table["metadata"]["row_count"] == 2
    assert table["metadata"]["has_headers"] is True


@pytest.mark.parametrize("cell_tag", ["td", "th"])
def test_thead_colspan_keeps_existing_expansion(extract_table, cell_tag):
    table = extract_table(f"""
        <table>
        <thead><tr><{cell_tag} colspan="2">Item</{cell_tag}><th>Price</th></tr></thead>
        <tbody>
        <tr><td>Widget</td><td>Blue</td><td>19.99</td></tr>
        <tr><td>Gadget</td><td>Red</td><td>39.99</td></tr>
        </tbody>
        </table>
        """)
    assert table["rows"] == [
        ["Widget", "Blue", "19.99"],
        ["Gadget", "Red", "39.99"],
    ]
    assert table["headers"] == ["Item", "Item", "Price"]
    assert table["metadata"]["column_count"] == 3


def test_multiple_thead_rows_still_use_first_row(extract_table):
    table = extract_table("""
        <table>
        <thead>
        <tr><th>Product</th><th colspan="2">Prices</th></tr>
        <tr><th>Name</th><th>Retail</th><th>Wholesale</th></tr>
        </thead>
        <tbody>
        <tr><td>Widget</td><td>19.99</td><td>17.99</td></tr>
        <tr><td>Gadget</td><td>39.99</td><td>35.99</td></tr>
        </tbody>
        </table>
        """)
    assert table["headers"] == ["Product", "Prices", "Prices"]
    assert table["rows"] == [
        ["Widget", "19.99", "17.99"],
        ["Gadget", "39.99", "35.99"],
    ]
    assert table["metadata"]["row_count"] == 2
