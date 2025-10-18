"""Content scraping service API endpoints."""

import time
from fastapi import APIRouter, HTTPException
from crawl4ai_schemas import ScrapingRequest, ScrapingResponse

from .scraper import ContentScraper

router = APIRouter(tags=["scraping"])
scraper = ContentScraper()


@router.post("/scrape", response_model=ScrapingResponse)
async def scrape(request: ScrapingRequest) -> ScrapingResponse:
    """Scrape content from HTML.

    Args:
        request: Scraping request with HTML and options

    Returns:
        Scraping response with extracted content

    Raises:
        HTTPException: If scraping fails
    """
    start_time = time.time()

    try:
        result = scraper.scrape(
            html=request.html,
            extract_links=request.extract_links,
            extract_images=request.extract_images,
            extract_media=request.extract_media,
            extract_metadata=request.extract_metadata,
            base_url=request.base_url,
        )

        duration_ms = (time.time() - start_time) * 1000

        return ScrapingResponse(
            success=True,
            text=result.get("text"),
            links=result.get("links", []),
            images=result.get("images", []),
            media=result.get("media", []),
            metadata=result.get("metadata", {}),
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return ScrapingResponse(
            success=False,
            error=str(e),
            duration_ms=duration_ms,
        )


@router.get("/status")
async def status():
    """Get scraping service status.

    Returns:
        Service status information
    """
    return {
        "status": "running",
        "version": "0.1.0",
    }
