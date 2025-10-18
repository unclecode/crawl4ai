"""Content scraping service client."""

from typing import Optional
from crawl4ai_schemas import ScrapingRequest, ScrapingResponse
from .base import BaseClient


class ScrapingClient(BaseClient):
    """Client for Content Scraping Service."""

    def __init__(self, base_url: Optional[str] = None, **kwargs):
        """Initialize scraping client.

        Args:
            base_url: Scraping service URL (optional, uses settings default)
            **kwargs: Additional client parameters
        """
        if base_url is None:
            from crawl4ai_core.config import get_settings

            base_url = get_settings().scraping_service_url
        super().__init__(base_url, **kwargs)

    async def scrape(self, request: ScrapingRequest) -> ScrapingResponse:
        """Scrape content from HTML.

        Args:
            request: Scraping request with HTML and options

        Returns:
            Scraping response with extracted content
        """
        response_data = await self.post(
            "/scrape",
            json=request.model_dump(mode="json"),
        )
        return ScrapingResponse(**response_data)

    async def extract_links(
        self, html: str, base_url: Optional[str] = None
    ) -> ScrapingResponse:
        """Extract all links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for relative links

        Returns:
            Scraping response with extracted links
        """
        request = ScrapingRequest(
            html=html,
            extract_links=True,
            base_url=base_url,
        )
        return await self.scrape(request)

    async def extract_images(
        self, html: str, base_url: Optional[str] = None
    ) -> ScrapingResponse:
        """Extract all images from HTML.

        Args:
            html: HTML content
            base_url: Base URL for relative URLs

        Returns:
            Scraping response with extracted images
        """
        request = ScrapingRequest(
            html=html,
            extract_images=True,
            base_url=base_url,
        )
        return await self.scrape(request)
