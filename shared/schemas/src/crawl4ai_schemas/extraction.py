"""Extraction service API schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractionSchema(BaseModel):
    """Schema for structured data extraction."""

    name: str = Field(description="Schema name")
    fields: List[Dict[str, Any]] = Field(description="Field definitions")
    base_selector: Optional[str] = Field(default=None, description="Base CSS selector")


class ExtractionRequest(BaseModel):
    """Request to extraction service."""

    content: str = Field(description="Content to extract from (HTML or text)")
    extraction_type: str = Field(
        default="css", description="Extraction type: css, xpath, regex, llm"
    )
    schema: Optional[ExtractionSchema] = Field(
        default=None, description="Extraction schema"
    )
    css_selector: Optional[str] = Field(default=None, description="CSS selector")
    xpath: Optional[str] = Field(default=None, description="XPath expression")
    regex_pattern: Optional[str] = Field(default=None, description="Regex pattern")
    llm_prompt: Optional[str] = Field(default=None, description="LLM extraction prompt")
    llm_model: Optional[str] = Field(default=None, description="LLM model name")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ExtractionResponse(BaseModel):
    """Response from extraction service."""

    success: bool = Field(description="Whether extraction was successful")
    data: Optional[Any] = Field(default=None, description="Extracted data")
    count: int = Field(default=0, description="Number of extracted items")
    extraction_type: str = Field(description="Extraction type used")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration_ms: float = Field(description="Processing duration in milliseconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
