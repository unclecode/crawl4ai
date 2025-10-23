# tests/async/test_extraction_strategy.py
import pytest
from bs4 import BeautifulSoup
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Sample HTML inspired by Hacker News or similar structures
SAMPLE_HTML = """
<table>
    <tbody>
        <tr class='athing' id='1'>
            <td class="title">
                <span class="titleline">
                    <a href="https://example.com">My Awesome Project</a>
                </span>
            </td>
        </tr>
        <tr>
            <td class="subtext">
                <span class="score" id="score_1">100 points</span>
                by <a href="user?id=testuser" class="hnuser">testuser</a>
                <span class="age" title="2023-11-10T12:00:00">
                    <a href="item?id=1">2 hours ago</a>
                </span>
            </td>
        </tr>
        <tr class='athing' id='2'>
            <td class="title">
                <span class="titleline">
                    <a href="https://another.com">Another Cool Thing</a>
                </span>
            </td>
        </tr>
        <tr>
            <td class="subtext">
                <span class="score" id="score_2">50 points</span>
                by <a href="user?id=anotheruser" class="hnuser">anotheruser</a>
                <span class="age" title="2023-11-10T14:00:00">
                    <a href="item?id=2">30 minutes ago</a>
                </span>
            </td>
        </tr>
    </tbody>
</table>
"""

class TestJsonCssExtractorStrategy:

    def test_sibling_selector_with_descendant(self):
        """Tests extracting a descendant from a next sibling."""
        schema = {
            "name": "HackerNewsItems",
            "baseSelector": "tr.athing",
            "fields": [
                {
                    "name": "title",
                    "selector": ".titleline a",
                    "type": "text"
                },
                {
                    "name": "points",
                    "selector": "+ tr .score",
                    "type": "text"
                }
            ]
        }
        strategy = JsonCssExtractionStrategy(schema=schema)
        results = strategy.run(url="http://test.com", sections=[SAMPLE_HTML])
        
        assert len(results) == 2
        assert results[0]['title'] == "My Awesome Project"
        assert results[0]['points'] == "100 points"
        assert results[1]['title'] == "Another Cool Thing"
        assert results[1]['points'] == "50 points"

    def test_sibling_selector_without_descendant(self):
        """Tests extracting the entire next sibling element."""
        schema = {
            "name": "HackerNewsItems",
            "baseSelector": "tr.athing",
            "fields": [
                {
                    "name": "title",
                    "selector": ".titleline a",
                    "type": "text"
                },
                {
                    "name": "metadata_row",
                    "selector": "+ tr", # Select the whole next sibling <tr>
                    "type": "html"
                }
            ]
        }
        strategy = JsonCssExtractionStrategy(schema=schema)
        results = strategy.run(url="http://test.com", sections=[SAMPLE_HTML])
        
        assert len(results) == 2
        assert results[0]['title'] == "My Awesome Project"
        assert '<td class="subtext">' in results[0]['metadata_row']
        assert 'id="score_1"' in results[0]['metadata_row']
        
        # Test the second item
        assert results[1]['title'] == "Another Cool Thing"
        assert '<td class="subtext">' in results[1]['metadata_row']
        assert 'id="score_2"' in results[1]['metadata_row']
        

    def test_sibling_selector_no_match(self):
        """Tests behavior when no matching sibling is found."""
        html_with_missing_sibling = """
        <table>
            <tbody>
                <tr class='athing' id='1'>
                    <td class="title">
                        <a href="https://example.com">Item with no subtext</a>
                    </td>
                </tr>
                <!-- The sibling tr is missing here -->
                 <tr class='athing' id='2'>
                    <td class="title">
                       <a href="https://another.com">Another item</a>
                    </td>
                </tr>
            </tbody>
        </table>
        """
        schema = {
            "name": "Items",
            "baseSelector": "tr.athing",
            "fields": [
                {"name": "title", "selector": ".title a", "type": "text"},
                {"name": "points", "selector": "+ tr .score", "type": "text", "default": "N/A"}
            ]
        }
        strategy = JsonCssExtractionStrategy(schema=schema)
        results = strategy.run(url="http://test.com", sections=[html_with_missing_sibling])
        
        assert len(results) == 2
        assert results[0]['title'] == "Item with no subtext"
        assert results[0]['points'] == "N/A" # Should use default value
        assert 'points' not in results[1] or results[1]['points'] == "N/A" # Second one also has no sibling


    def test_standard_descendant_selector_regression(self):
        """Ensures that standard selectors still work correctly."""
        schema = {
            "name": "HackerNewsItems",
            "baseSelector": "tr.athing",
            "fields": [
                {
                    "name": "title",
                    "selector": ".titleline a", # Standard descendant selector
                    "type": "text"
                },
                {
                    "name": "link",
                    "selector": ".titleline a", # Standard descendant selector
                    "type": "attribute",
                    "attribute": "href"
                }
            ]
        }
        strategy = JsonCssExtractionStrategy(schema=schema)
        results = strategy.run(url="http://test.com", sections=[SAMPLE_HTML])
        
        assert len(results) == 2
        assert results[0]['title'] == "My Awesome Project"
        assert results[0]['link'] == "https://example.com"
        assert results[1]['title'] == "Another Cool Thing"
        assert results[1]['link'] == "https://another.com"