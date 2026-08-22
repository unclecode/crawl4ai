import pytest

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig


@pytest.mark.asyncio
async def test_overlay_removal_preserves_document_structure_and_removes_dialog():
    html = """
    <html class="popup-shell">
      <head class="modal-metadata"><title>Keep the document</title></head>
      <body class="popup-menu-open" style="position: fixed">
        <main><h1>Content survives</h1></main>
        <div id="newsletter-modal" class="modal overlay"
             style="position: fixed; z-index: 9999; width: 90vw; height: 90vh">
          Subscribe now
        </div>
      </body>
    </html>
    """

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            f"raw:{html}",
            config=CrawlerRunConfig(remove_overlay_elements=True, verbose=False),
        )

    assert result.success, result.error_message
    cleaned = result.html.lower()
    assert "<html" in cleaned
    assert "<head" in cleaned
    assert "<body" in cleaned
    assert "content survives" in cleaned
    assert "newsletter-modal" not in cleaned
    assert "subscribe now" not in cleaned
