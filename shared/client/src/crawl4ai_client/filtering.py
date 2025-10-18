"""Filtering service client."""

from typing import Optional
from crawl4ai_schemas import FilteringRequest, FilteringResponse, FilterType
from .base import BaseClient


class FilteringClient(BaseClient):
    """Client for Filtering Service."""

    def __init__(self, base_url: Optional[str] = None, **kwargs):
        """Initialize filtering client.

        Args:
            base_url: Filtering service URL (optional, uses settings default)
            **kwargs: Additional client parameters
        """
        if base_url is None:
            from crawl4ai_core.config import get_settings

            base_url = get_settings().filtering_service_url
        super().__init__(base_url, **kwargs)

    async def filter_content(self, request: FilteringRequest) -> FilteringResponse:
        """Filter content based on relevance.

        Args:
            request: Filtering request with content and filter type

        Returns:
            Filtering response with filtered content
        """
        response_data = await self.post(
            "/filter",
            json=request.model_dump(mode="json"),
        )
        return FilteringResponse(**response_data)

    async def filter_bm25(
        self, content: str, query: str, threshold: float = 0.5
    ) -> FilteringResponse:
        """Filter content using BM25 algorithm.

        Args:
            content: Content to filter
            query: Search query
            threshold: Filter threshold (0-1)

        Returns:
            Filtering response with filtered content
        """
        request = FilteringRequest(
            content=content,
            filter_type=FilterType.BM25,
            query=query,
            threshold=threshold,
        )
        return await self.filter_content(request)

    async def filter_pruning(
        self, content: str, threshold: float = 0.5
    ) -> FilteringResponse:
        """Filter content using pruning algorithm.

        Args:
            content: Content to filter
            threshold: Filter threshold (0-1)

        Returns:
            Filtering response with filtered content
        """
        request = FilteringRequest(
            content=content,
            filter_type=FilterType.PRUNING,
            threshold=threshold,
        )
        return await self.filter_content(request)
