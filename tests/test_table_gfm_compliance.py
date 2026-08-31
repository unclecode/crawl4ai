"""
Unit tests for GFM-compliant markdown table generation.

Tests that html2text generates tables with proper leading and trailing
pipe delimiters as per GitHub Flavored Markdown specification.

Fixes: https://github.com/unclecode/crawl4ai/issues/1731
"""

import pytest
import sys
import os

# Add parent directory to path to import html2text
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crawl4ai.html2text import HTML2Text


def _table_lines(result: str) -> list[str]:
    """Extract table lines (containing |) from html2text output, stripped."""
    return [line.strip() for line in result.split('\n') if '|' in line]


class TestTableGFMCompliance:
    """Test suite for GFM-compliant table generation (pad_tables=False)."""

    def test_table_has_leading_pipes(self):
        """All table rows start with |"""
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        lines = _table_lines(result)
        assert len(lines) > 0, "No table rows found in output"

        for i, line in enumerate(lines):
            assert line.startswith('|'), f"Line {i+1} missing leading pipe: {repr(line)}"

    def test_table_has_trailing_pipes(self):
        """All table rows end with |"""
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        lines = _table_lines(result)
        assert len(lines) > 0, "No table rows found in output"

        for i, line in enumerate(lines):
            assert line.endswith('|'), f"Line {i+1} missing trailing pipe: {repr(line)}"

    def test_cells_have_space_padding(self):
        """Cell content has spaces on both sides of pipe delimiters.

        Correct:   | A | B |
        Incorrect: | A| B |  (missing space after A)
        """
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        lines = _table_lines(result)
        # Check header and data rows (skip separator)
        for line in lines:
            if '---' in line:
                continue
            # Split by | and check that internal cells have spaces
            cells = line.split('|')
            # cells[0] is '' (before first |), cells[-1] is '' (after last |)
            for cell in cells[1:-1]:
                if cell.strip():  # Non-empty cell
                    assert cell.startswith(' '), f"Cell missing leading space: {repr(line)}"
                    assert cell.endswith(' '), f"Cell missing trailing space: {repr(line)}"

    def test_separator_row_format(self):
        """Separator row has format | --- | --- |"""
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        separators = [line.strip() for line in result.split('\n') if '---' in line]
        assert len(separators) > 0, "No separator row found"

        sep = separators[0]
        assert sep.startswith('|'), f"Separator missing leading pipe: {repr(sep)}"
        assert sep.endswith('|'), f"Separator missing trailing pipe: {repr(sep)}"
        assert sep == '| --- | --- |', f"Unexpected separator format: {repr(sep)}"

    def test_multirow_table(self):
        """Multi-row tables maintain GFM compliance throughout."""
        html = '''<table>
            <tr><th>Parameter</th><th>Guideline</th><th>Sources</th></tr>
            <tr><td>Arsenic</td><td>0.010</td><td>Naturally occurring</td></tr>
            <tr><td>Lead</td><td>0.005</td><td>Plumbing</td></tr>
            <tr><td>Mercury</td><td>0.001</td><td>Industrial</td></tr>
        </table>'''
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        lines = _table_lines(result)
        # 1 header + 1 separator + 3 data rows = 5 rows
        assert len(lines) >= 5, f"Expected at least 5 table rows, got {len(lines)}"

        for i, line in enumerate(lines):
            assert line.startswith('|'), f"Line {i+1} missing leading pipe"
            assert line.endswith('|'), f"Line {i+1} missing trailing pipe"

    def test_single_column_table(self):
        """Single-column tables are GFM compliant."""
        html = '<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        lines = _table_lines(result)
        assert len(lines) > 0, "No table rows found"
        for line in lines:
            assert line.startswith('|') and line.endswith('|'), \
                f"Single column row not GFM compliant: {repr(line)}"

    def test_empty_cells(self):
        """Tables with empty cells are GFM compliant."""
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td></td><td>Data</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        lines = _table_lines(result)
        assert len(lines) > 0, "No table rows found"
        for line in lines:
            assert line.startswith('|') and line.endswith('|'), \
                f"Row with empty cell not GFM compliant: {repr(line)}"

    def test_table_starts_on_own_line(self):
        """Table starts on its own line, not inline with preceding content."""
        html = '<p>Text before.</p><table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        # The first table line must start at the beginning of a line
        # (no leading whitespace before the pipe)
        for line in result.split('\n'):
            stripped = line.strip()
            if stripped.startswith('|'):
                # Check no leading whitespace (table row at column 0)
                assert line.startswith('|'), f"Table row not at line start: {repr(line)}"
                break
        else:
            pytest.fail("No table row starting with | found")

    def test_nested_table_starts_on_own_line(self):
        """Table nested in list item starts on its own line."""
        html = '<ul><li>Item<table><tr><th>X</th></tr><tr><td>1</td></tr></table></li></ul>'
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        # Find the first | line — it should not be on the same line as "Item"
        lines = result.split('\n')
        for line in lines:
            if 'Item' in line:
                assert '|' not in line, \
                    f"Table pipe on same line as 'Item': {repr(line)}"
                break

    def test_caption_does_not_merge_with_header(self):
        """Table with <caption> renders caption on its own line, not inline with header."""
        html = '''<table>
            <caption>Table 1. Parameters</caption>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>Lead</td><td>0.005</td></tr>
        </table>'''
        h = HTML2Text()
        h.body_width = 0
        result = h.handle(html)

        # Caption text should NOT be on the same line as the header pipe row
        for line in result.split('\n'):
            if 'Table 1' in line:
                assert '|' not in line, \
                    f"Caption on same line as table row: {repr(line)}"
                break

        # Header row should start with |
        table_lines = _table_lines(result)
        assert len(table_lines) >= 3, f"Expected at least 3 table rows, got {len(table_lines)}"
        assert table_lines[0].startswith('|'), f"Header not starting with pipe: {repr(table_lines[0])}"


class TestPadTablesUnchanged:
    """Verify pad_tables=True behavior is unchanged from upstream."""

    def test_pad_tables_produces_aligned_output(self):
        """pad_tables=True produces properly aligned GFM output."""
        html = '<table><tr><th>Parameter</th><th>Value</th></tr><tr><td>Lead</td><td>0.005 mg/L</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        h.pad_tables = True
        result = h.handle(html)

        lines = _table_lines(result)
        assert len(lines) >= 3, f"Expected at least 3 rows, got {len(lines)}"

        # All rows should have leading and trailing pipes
        for line in lines:
            assert line.startswith('|'), f"Padded row missing leading pipe: {repr(line)}"
            assert line.endswith('|'), f"Padded row missing trailing pipe: {repr(line)}"

        # All rows should have same width (padded alignment)
        widths = [len(line) for line in lines]
        assert len(set(widths)) == 1, f"Rows have uneven widths: {widths}"

    def test_pad_tables_no_double_pipes(self):
        """pad_tables=True does not produce double pipes |  | or | |."""
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        h.pad_tables = True
        result = h.handle(html)

        lines = _table_lines(result)
        for line in lines:
            # Should not have pipe-space-pipe (double boundary)
            assert '| |' not in line, f"Double pipes found: {repr(line)}"
            # Line should not start with |  | (extra pipe from both systems)
            assert not line.startswith('|  |'), f"Extra leading pipe: {repr(line)}"

    def test_pad_tables_separator_has_dashes(self):
        """pad_tables=True separator row uses dashes with proper alignment."""
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        h = HTML2Text()
        h.body_width = 0
        h.pad_tables = True
        result = h.handle(html)

        separators = [line.strip() for line in result.split('\n') if '---' in line]
        assert len(separators) >= 1, "No separator row found in padded table"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
