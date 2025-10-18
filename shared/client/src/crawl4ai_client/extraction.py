"""Extraction service client."""

from typing import Optional
from crawl4ai_schemas import ExtractionRequest, ExtractionResponse, ExtractionSchema
from .base import BaseClient


class ExtractionClient(BaseClient):
    """Client for Extraction Service."""

    def __init__(self, base_url: Optional[str] = None, **kwargs):
        """Initialize extraction client.

        Args:
            base_url: Extraction service URL (optional, uses settings default)
            **kwargs: Additional client parameters
        """
        if base_url is None:
            from crawl4ai_core.config import get_settings

            base_url = get_settings().extraction_service_url
        super().__init__(base_url, **kwargs)

    async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        """Extract structured data from content.

        Args:
            request: Extraction request with content and schema

        Returns:
            Extraction response with extracted data
        """
        response_data = await self.post(
            "/extract",
            json=request.model_dump(mode="json"),
        )
        return ExtractionResponse(**response_data)

    async def extract_css(self, content: str, css_selector: str) -> ExtractionResponse:
        """Extract data using CSS selector.

        Args:
            content: HTML content
            css_selector: CSS selector

        Returns:
            Extraction response with extracted data
        """
        request = ExtractionRequest(
            content=content,
            extraction_type="css",
            css_selector=css_selector,
        )
        return await self.extract(request)

    async def extract_xpath(self, content: str, xpath: str) -> ExtractionResponse:
        """Extract data using XPath.

        Args:
            content: HTML content
            xpath: XPath expression

        Returns:
            Extraction response with extracted data
        """
        request = ExtractionRequest(
            content=content,
            extraction_type="xpath",
            xpath=xpath,
        )
        return await self.extract(request)

    async def extract_with_schema(
        self, content: str, schema: ExtractionSchema
    ) -> ExtractionResponse:
        """Extract data using a schema.

        Args:
            content: HTML content
            schema: Extraction schema

        Returns:
            Extraction response with extracted data
        """
        request = ExtractionRequest(
            content=content,
            extraction_type="css",
            schema=schema,
        )
        return await self.extract(request)
