"""Regression test: ``format_html`` must use a parser BeautifulSoup knows.

The function previously passed the feature string ``"lxml.parser"`` to
BeautifulSoup, which raises ``FeatureNotFound`` for every input (the only
valid feature names are ``"lxml"`` / ``"html.parser"``).
"""

import pytest

pytest.importorskip("bs4")
pytest.importorskip("lxml")

from crawl4ai.utils import format_html


def test_format_html_prettifies_instead_of_raising():
    formatted = format_html("<div><p>hello</p></div>")

    assert "<div>" in formatted
    assert "<p>" in formatted
    assert "hello" in formatted
    assert "\n" in formatted


def test_format_html_keeps_table_markup():
    formatted = format_html("<table><tr><td>1</td></tr></table>")

    assert "<table>" in formatted
    assert "<td>" in formatted
    assert "1" in formatted
