"""Base HTTP client for Crawl4AI services."""

import httpx
from typing import Any, Dict, Optional
from crawl4ai_core.config import Settings, get_settings


class BaseClient:
    """Base HTTP client with common functionality."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        settings: Optional[Settings] = None,
    ):
        """Initialize the base client.

        Args:
            base_url: Base URL of the service
            timeout: Request timeout in seconds
            settings: Application settings (optional)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.settings = settings or get_settings()
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request.

        Args:
            path: API path (relative to base_url)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        response = await self.client.get(path, **kwargs)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a POST request.

        Args:
            path: API path (relative to base_url)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        response = await self.client.post(path, **kwargs)
        response.raise_for_status()
        return response.json()

    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a PUT request.

        Args:
            path: API path (relative to base_url)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        response = await self.client.put(path, **kwargs)
        response.raise_for_status()
        return response.json()

    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request.

        Args:
            path: API path (relative to base_url)
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        response = await self.client.delete(path, **kwargs)
        response.raise_for_status()
        return response.json()
