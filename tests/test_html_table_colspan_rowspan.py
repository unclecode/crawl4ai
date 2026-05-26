import pytest
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

@pytest.mark.asyncio
async def test_colspan_rowspan_preserved():
    """
    Test that colspan and rowspan attributes are preserved during HTML cleaning/sanitization.
    This ensures table structures don't break when crawling.
    """
    html = """
    <html>
    <body>
        <table>
            <tr>
                <td colspan="2" id="cell1">Header 1</td>
                <td rowspan="2" id="cell2">Header 2</td>
            </tr>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig()
        result = await crawler.arun(f"raw:{html}", config=config)
        
    assert result.success, "Crawl should succeed"
    
    # Check that colspan and rowspan attributes are preserved in the sanitized HTML
    assert 'colspan="2"' in result.html, "colspan attribute was removed during sanitization"
    assert 'rowspan="2"' in result.html, "rowspan attribute was removed during sanitization"
