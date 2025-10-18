"""Filtering service API schemas."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FilterType(str, Enum):
    """Content filter types."""

    BM25 = "bm25"
    PRUNING = "pruning"
    LLM = "llm"
    RELEVANCE = "relevance"


class FilteringRequest(BaseModel):
    """Request to filtering service."""

    content: str = Field(description="Content to filter")
    filter_type: FilterType = Field(description="Type of filter to apply")
    query: Optional[str] = Field(
        default=None, description="Query for relevance filtering"
    )
    threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Filter threshold"
    )
    llm_model: Optional[str] = Field(
        default=None, description="LLM model for LLM filtering"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class FilteringResponse(BaseModel):
    """Response from filtering service."""

    success: bool = Field(description="Whether filtering was successful")
    filtered_content: Optional[str] = Field(
        default=None, description="Filtered content"
    )
    relevance_score: Optional[float] = Field(
        default=None, description="Relevance score (0-1)"
    )
    filter_type: FilterType = Field(description="Filter type applied")
    original_length: int = Field(description="Original content length")
    filtered_length: int = Field(description="Filtered content length")
    reduction_percent: float = Field(description="Content reduction percentage")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration_ms: float = Field(description="Processing duration in milliseconds")
