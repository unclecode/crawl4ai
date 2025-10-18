"""Browser service client."""

from typing import Optional
from crawl4ai_schemas import BrowserRequest, BrowserResponse
from .base import BaseClient


class BrowserClient(BaseClient):
    """Client for Browser Management Service."""

    def __init__(self, base_url: Optional[str] = None, **kwargs):
        """Initialize browser client.

        Args:
            base_url: Browser service URL (optional, uses settings default)
            **kwargs: Additional client parameters
        """
        if base_url is None:
            from crawl4ai_core.config import get_settings

            base_url = get_settings().browser_service_url
        super().__init__(base_url, **kwargs)

    async def navigate(self, request: BrowserRequest) -> BrowserResponse:
        """Navigate to a URL and perform actions.

        Args:
            request: Browser request with URL and actions

        Returns:
            Browser response with HTML and metadata
        """
        response_data = await self.post(
            "/navigate",
            json=request.model_dump(mode="json"),
        )
        return BrowserResponse(**response_data)

    async def screenshot(self, url: str, **kwargs) -> BrowserResponse:
        """Capture a screenshot of a URL.

        Args:
            url: URL to screenshot
            **kwargs: Additional browser request parameters

        Returns:
            Browser response with screenshot data
        """
        request = BrowserRequest(url=url, action="screenshot", **kwargs)
        return await self.navigate(request)

    async def get_html(self, url: str, **kwargs) -> BrowserResponse:
        """Get HTML content of a URL.

        Args:
            url: URL to fetch
            **kwargs: Additional browser request parameters

        Returns:
            Browser response with HTML content
        """
        request = BrowserRequest(url=url, action="get_html", **kwargs)
        return await self.navigate(request)

    async def execute_js(self, url: str, javascript: str, **kwargs) -> BrowserResponse:
        """Execute JavaScript on a page.

        Args:
            url: URL to execute on
            javascript: JavaScript code to execute
            **kwargs: Additional browser request parameters

        Returns:
            Browser response with JavaScript result
        """
        request = BrowserRequest(
            url=url, action="execute_js", javascript=javascript, **kwargs
        )
        return await self.navigate(request)
