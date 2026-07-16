"""
Tests for issue #1043: Missing Mermaid Flowcharts

Verifies that mermaid SVG diagrams are preserved as text content
during HTML scraping, rather than being stripped entirely.
"""

import pytest
from lxml import html as lhtml
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


@pytest.fixture
def strategy():
    return LXMLWebScrapingStrategy()


def _make_html(body_content: str) -> str:
    return f"<html><body>{body_content}</body></html>"


# -- Mermaid SVG detection and replacement --

FLOWCHART_SVG = """
<div>
    <p>Before diagram</p>
    <svg id="mermaid-abc123" aria-roledescription="flowchart-v2" xmlns="http://www.w3.org/2000/svg">
        <g class="node"><foreignObject><div><span class="nodeLabel">Start</span></div></foreignObject></g>
        <g class="node"><foreignObject><div><span class="nodeLabel">Process Data</span></div></foreignObject></g>
        <g class="node"><foreignObject><div><span class="nodeLabel">End</span></div></foreignObject></g>
        <g class="edgeLabel"><foreignObject><div><span>yes</span></div></foreignObject></g>
    </svg>
    <p>After diagram</p>
</div>
"""

CLASS_DIAGRAM_SVG = """
<div>
    <svg id="mermaid-def456" aria-roledescription="class" xmlns="http://www.w3.org/2000/svg">
        <g class="node"><foreignObject><div><span class="nodeLabel">MyClass</span></div></foreignObject></g>
        <g class="node"><foreignObject><div><span class="nodeLabel">+method() : void</span></div></foreignObject></g>
        <g class="node"><foreignObject><div><span class="nodeLabel">-field : int</span></div></foreignObject></g>
    </svg>
</div>
"""

SEQUENCE_SVG = """
<div>
    <svg id="mermaid-seq789" aria-roledescription="sequence" xmlns="http://www.w3.org/2000/svg">
        <g class="label"><foreignObject><div><span>Alice</span></div></foreignObject></g>
        <g class="label"><foreignObject><div><span>Bob</span></div></foreignObject></g>
        <g class="edgeLabel"><foreignObject><div><span>Hello</span></div></foreignObject></g>
    </svg>
</div>
"""


class TestMermaidSVGDetection:
    """Test that mermaid SVGs are detected by their id prefix."""

    def test_flowchart_svg_detected(self, strategy):
        html = _make_html(FLOWCHART_SVG)
        result = strategy._scrap("http://test.com", html)
        assert result is not None
        cleaned = result.get("cleaned_html", "")
        assert "Start" in cleaned
        assert "Process Data" in cleaned

    def test_non_mermaid_svg_not_affected(self, strategy):
        """Regular SVGs without mermaid id should be unaffected."""
        html = _make_html("""
            <div>
                <svg id="logo" xmlns="http://www.w3.org/2000/svg">
                    <text>Logo Text</text>
                </svg>
                <p>Content here</p>
            </div>
        """)
        result = strategy._scrap("http://test.com", html)
        assert result is not None

    def test_mermaid_svg_replaced_with_pre_code(self, strategy):
        """Mermaid SVG should be replaced with pre/code block."""
        html = _make_html(FLOWCHART_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "language-mermaid" in cleaned or "mermaid" in cleaned.lower()


class TestMermaidTextExtraction:
    """Test that text content is correctly extracted from mermaid SVGs."""

    def test_node_labels_extracted(self, strategy):
        html = _make_html(FLOWCHART_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "Start" in cleaned
        assert "Process Data" in cleaned
        assert "End" in cleaned

    def test_edge_labels_extracted(self, strategy):
        html = _make_html(FLOWCHART_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "yes" in cleaned

    def test_class_diagram_labels_extracted(self, strategy):
        html = _make_html(CLASS_DIAGRAM_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "MyClass" in cleaned
        assert "+method() : void" in cleaned

    def test_sequence_diagram_labels_extracted(self, strategy):
        html = _make_html(SEQUENCE_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "Alice" in cleaned
        assert "Bob" in cleaned

    def test_duplicate_labels_deduplicated(self, strategy):
        """Same label appearing multiple times should only appear once."""
        html = _make_html("""
            <div>
                <svg id="mermaid-dup" aria-roledescription="flowchart-v2" xmlns="http://www.w3.org/2000/svg">
                    <g class="node"><foreignObject><div><span class="nodeLabel">Repeated</span></div></foreignObject></g>
                    <g class="node"><foreignObject><div><span class="nodeLabel">Repeated</span></div></foreignObject></g>
                    <g class="node"><foreignObject><div><span class="nodeLabel">Unique</span></div></foreignObject></g>
                </svg>
            </div>
        """)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        # Should have Repeated once, not twice
        assert cleaned.count("Repeated") == 1
        assert "Unique" in cleaned


class TestMermaidDiagramType:
    """Test that diagram type is preserved."""

    def test_flowchart_type_preserved(self, strategy):
        html = _make_html(FLOWCHART_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "flowchart" in cleaned.lower()

    def test_class_type_preserved(self, strategy):
        html = _make_html(CLASS_DIAGRAM_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "class" in cleaned.lower()

    def test_sequence_type_preserved(self, strategy):
        html = _make_html(SEQUENCE_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "sequence" in cleaned.lower()


class TestMermaidSurroundingContent:
    """Test that surrounding content is preserved."""

    def test_text_before_diagram_preserved(self, strategy):
        html = _make_html(FLOWCHART_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "Before diagram" in cleaned

    def test_text_after_diagram_preserved(self, strategy):
        html = _make_html(FLOWCHART_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "After diagram" in cleaned


class TestMermaidEdgeCases:
    """Test edge cases for mermaid SVG handling."""

    def test_empty_mermaid_svg(self, strategy):
        """SVG with no text content should be handled gracefully."""
        html = _make_html("""
            <div>
                <svg id="mermaid-empty" aria-roledescription="flowchart-v2" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100" height="100"/>
                </svg>
                <p>Content</p>
            </div>
        """)
        result = strategy._scrap("http://test.com", html)
        assert result is not None
        cleaned = result.get("cleaned_html", "")
        assert "Content" in cleaned

    def test_multiple_mermaid_svgs(self, strategy):
        """Multiple mermaid diagrams on one page."""
        html = _make_html(FLOWCHART_SVG + CLASS_DIAGRAM_SVG)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "Start" in cleaned
        assert "MyClass" in cleaned

    def test_mermaid_svg_no_aria(self, strategy):
        """Mermaid SVG without aria-roledescription should use 'diagram' fallback."""
        html = _make_html("""
            <div>
                <svg id="mermaid-noaria" xmlns="http://www.w3.org/2000/svg">
                    <g class="node"><foreignObject><div><span class="nodeLabel">Node A</span></div></foreignObject></g>
                </svg>
            </div>
        """)
        result = strategy._scrap("http://test.com", html)
        cleaned = result.get("cleaned_html", "")
        assert "Node A" in cleaned
        assert "diagram" in cleaned.lower()

    def test_mermaid_svg_malformed_no_crash(self, strategy):
        """Malformed SVG should not crash the scraper."""
        html = _make_html("""
            <div>
                <svg id="mermaid-bad" xmlns="http://www.w3.org/2000/svg">
                </svg>
                <p>Still works</p>
            </div>
        """)
        result = strategy._scrap("http://test.com", html)
        assert result is not None
        cleaned = result.get("cleaned_html", "")
        assert "Still works" in cleaned
