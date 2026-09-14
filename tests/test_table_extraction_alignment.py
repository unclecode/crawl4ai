"""Row alignment in DefaultTableExtraction.

`result.tables[i]["rows"]` has to match the grid a browser renders. Two shapes
used to come out misaligned: a `<th scope="row">` in the body was dropped, and
a `rowspan` cell did not occupy the rows below it.

Fixes: https://github.com/unclecode/crawl4ai/issues/2258
"""

import os
import sys

import pytest
from lxml import html as lhtml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crawl4ai.table_extraction import DefaultTableExtraction


def _extract(markup: str) -> dict:
    tree = lhtml.fromstring(markup)
    table = tree if tree.tag == "table" else tree.xpath("//table")[0]
    return DefaultTableExtraction().extract_table_data(table)


class TestRowAlignment:
    def test_a_th_row_header_stays_in_the_first_column(self):
        result = _extract(
            """<table>
            <tr><th></th><th>Feature A</th><th>Feature B</th></tr>
            <tr><th scope="row">Item 1</th><td>yes</td><td>yes</td></tr>
            <tr><th scope="row">Item 2</th><td>no</td><td>yes</td></tr>
            </table>"""
        )

        assert result["headers"] == ["", "Feature A", "Feature B"]
        assert result["rows"] == [
            ["Item 1", "yes", "yes"],
            ["Item 2", "no", "yes"],
        ]

    def test_the_header_row_is_not_repeated_as_data(self):
        # Without a thead the first row is the header, and it is also in the
        # set of body rows. Now that `th` counts as a body cell, it has to be
        # skipped explicitly rather than by having no `td` in it.
        result = _extract(
            """<table>
            <tr><th>A</th><th>B</th></tr>
            <tr><td>1</td><td>2</td></tr>
            </table>"""
        )

        assert result["headers"] == ["A", "B"]
        assert result["rows"] == [["1", "2"]]

    def test_a_rowspan_cell_fills_the_rows_it_covers(self):
        result = _extract(
            """<table>
            <thead><tr><th>Group</th><th>Option X</th><th>Option Y</th></tr></thead>
            <tbody>
            <tr><td rowspan="2">G1</td><td>x1</td><td>y1</td></tr>
            <tr><td>x2</td><td>y2</td></tr>
            </tbody></table>"""
        )

        assert result["rows"] == [
            ["G1", "x1", "y1"],
            ["G1", "x2", "y2"],
        ]

    def test_a_rowspan_runs_out_after_the_rows_it_declared(self):
        result = _extract(
            """<table>
            <thead><tr><th>Group</th><th>Value</th></tr></thead>
            <tbody>
            <tr><td rowspan="2">G1</td><td>a</td></tr>
            <tr><td>b</td></tr>
            <tr><td>G2</td><td>c</td></tr>
            </tbody></table>"""
        )

        assert result["rows"] == [["G1", "a"], ["G1", "b"], ["G2", "c"]]

    def test_a_rowspan_in_a_later_column_lands_in_that_column(self):
        result = _extract(
            """<table>
            <thead><tr><th>A</th><th>B</th><th>C</th></tr></thead>
            <tbody>
            <tr><td>a1</td><td rowspan="2">shared</td><td>c1</td></tr>
            <tr><td>a2</td><td>c2</td></tr>
            </tbody></table>"""
        )

        assert result["rows"] == [
            ["a1", "shared", "c1"],
            ["a2", "shared", "c2"],
        ]

    def test_colspan_still_repeats_across_the_columns_it_covers(self):
        result = _extract(
            """<table>
            <thead><tr><th>A</th><th>B</th><th>C</th></tr></thead>
            <tbody><tr><td colspan="2">wide</td><td>c</td></tr></tbody></table>"""
        )

        assert result["rows"] == [["wide", "wide", "c"]]

    def test_a_cell_with_both_spans_covers_the_whole_block(self):
        result = _extract(
            """<table>
            <thead><tr><th>A</th><th>B</th><th>C</th></tr></thead>
            <tbody>
            <tr><td rowspan="2" colspan="2">block</td><td>c1</td></tr>
            <tr><td>c2</td></tr>
            </tbody></table>"""
        )

        assert result["rows"] == [
            ["block", "block", "c1"],
            ["block", "block", "c2"],
        ]

    @pytest.mark.parametrize("rowspan", ["0", "-1", "", "nonsense"])
    def test_a_rowspan_that_is_not_a_positive_number_is_ignored(self, rowspan):
        # lxml hands back whatever the document said. A table must not be
        # turned into an error, and no row may be carried into.
        markup = f"""<table>
        <thead><tr><th>A</th><th>B</th></tr></thead>
        <tbody>
        <tr><td rowspan="{rowspan}">x</td><td>a</td></tr>
        <tr><td>y</td><td>b</td></tr>
        </tbody></table>"""

        assert _extract(markup)["rows"] == [["x", "a"], ["y", "b"]]

    @pytest.mark.parametrize("colspan", ["0", "-1", "", "nonsense"])
    def test_a_colspan_that_is_not_a_positive_number_still_yields_one_cell(
        self, colspan
    ):
        # Zero columns would drop the cell entirely and shift the rest left,
        # which is the same misalignment this change exists to fix.
        markup = f"""<table>
        <thead><tr><th>A</th><th>B</th></tr></thead>
        <tbody><tr><td colspan="{colspan}">x</td><td>a</td></tr></tbody></table>"""

        assert _extract(markup)["rows"] == [["x", "a"]]

    def test_a_plain_table_is_unchanged(self):
        result = _extract(
            """<table>
            <thead><tr><th>A</th><th>B</th></tr></thead>
            <tbody><tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></tbody></table>"""
        )

        assert result["headers"] == ["A", "B"]
        assert result["rows"] == [["1", "2"], ["3", "4"]]
        assert result["metadata"]["column_count"] == 2
        assert result["metadata"]["row_count"] == 2
