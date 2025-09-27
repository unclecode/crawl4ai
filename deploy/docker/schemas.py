from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from utils import FilterType


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)
    output_path: Optional[str] = Field(None, description="Path to save crawl results as JSON (recommended for large multi-URL crawls to avoid MCP token limits)")

class MarkdownRequest(BaseModel):
    """Request body for the /md endpoint."""
    url: str = Field(..., description="Absolute URL to fetch (http/https) or raw HTML via raw: scheme")
    filter: FilterType = Field(
        FilterType.FIT,
        description="Filter type. Allowed values: 'raw', 'fit', 'bm25', 'llm'"
    )
    query: Optional[str] = Field(
        None,
        description="Query used when filter is 'bm25' or 'llm' (recommended/required for meaningful results)"
    )
    cache: Optional[str] = Field("0", description="Cache-bust / revision counter")
    provider: Optional[str] = Field(
        None,
        description="LLM provider override for filter='llm' (e.g., 'openai/gpt-4o-mini'). API key must be configured",
    )


class RawCode(BaseModel):
    code: str

class HTMLRequest(BaseModel):
    url: str
    
class ScreenshotRequest(BaseModel):
    url: str
    screenshot_wait_for: Optional[float] = Field(2, description="Delay before capture in seconds. Zero/negative values accepted (treated as immediate capture). Default: 2 seconds")
    output_path: Optional[str] = Field(None, description="Path to save PNG to disk (recommended to avoid large base64 responses)")

class PDFRequest(BaseModel):
    url: str
    output_path: Optional[str] = Field(None, description="Path to save PDF to disk (recommended to avoid large base64 responses)")


class JSEndpointRequest(BaseModel):
    url: str
    scripts: List[str] = Field(
        ...,
        description="List of separated JavaScript snippets to execute"
    )


class StandardizedResponse(BaseModel):
    """Standardized response format for all crawl operations."""
    success: bool = Field(..., description="Whether the operation succeeded")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="List of crawl results")
    server_processing_time_s: Optional[float] = Field(None, description="Server processing time in seconds")
    server_memory_delta_mb: Optional[float] = Field(None, description="Memory usage delta in MB")
    server_peak_memory_mb: Optional[float] = Field(None, description="Peak memory usage in MB")
    error_message: Optional[str] = Field(None, description="Error message if operation failed")

    @classmethod
    def success_response(
        cls,
        results: List[Dict[str, Any]],
        processing_time: Optional[float] = None,
        memory_delta: Optional[float] = None,
        memory_peak: Optional[float] = None
    ) -> "StandardizedResponse":
        """Create a successful response."""
        return cls(
            success=True,
            results=results,
            server_processing_time_s=processing_time,
            server_memory_delta_mb=memory_delta,
            server_peak_memory_mb=memory_peak
        )

    @classmethod
    def error_response(
        cls,
        error_message: str,
        processing_time: Optional[float] = None
    ) -> "StandardizedResponse":
        """Create an error response."""
        return cls(
            success=False,
            results=[],
            error_message=error_message,
            server_processing_time_s=processing_time
        )


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    success: bool = Field(False, description="Always false for error responses")
    error_type: str = Field(..., description="Type of error (network, validation, security, etc.)")
    error_message: str = Field(..., description="User-friendly error message")
    error_code: Optional[str] = Field(None, description="Specific error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    suggestions: Optional[List[str]] = Field(None, description="Suggested actions to resolve the error")
    operation: Optional[str] = Field(None, description="Operation that failed")

    @classmethod
    def network_error(
        cls,
        error_code: str,
        message: str,
        operation: str = "operation",
        suggestions: Optional[List[str]] = None
    ) -> "ErrorResponse":
        """Create a network error response."""
        return cls(
            error_type="network",
            error_message=message,
            error_code=error_code,
            operation=operation,
            suggestions=suggestions or []
        )

    @classmethod
    def validation_error(
        cls,
        field_name: str,
        invalid_value: Any,
        expected_format: str,
        suggestions: Optional[List[str]] = None
    ) -> "ErrorResponse":
        """Create a validation error response."""
        return cls(
            error_type="validation",
            error_message=f"Invalid value for {field_name}: {invalid_value}",
            details={
                "field_name": field_name,
                "invalid_value": str(invalid_value),
                "expected_format": expected_format
            },
            suggestions=suggestions or [f"Provide a valid {expected_format} for {field_name}"]
        )

    @classmethod
    def security_error(
        cls,
        violation_type: str,
        attempted_action: str,
        allowed_scope: str,
        suggestions: Optional[List[str]] = None
    ) -> "ErrorResponse":
        """Create a security error response."""
        return cls(
            error_type="security",
            error_message=f"Security violation: {violation_type}",
            details={
                "violation_type": violation_type,
                "attempted_action": attempted_action,
                "allowed_scope": allowed_scope
            },
            suggestions=suggestions or [f"Ensure your action is within the allowed scope: {allowed_scope}"]
        )

    @classmethod
    def configuration_error(
        cls,
        config_key: str,
        config_value: Any,
        suggestion: str
    ) -> "ErrorResponse":
        """Create a configuration error response."""
        return cls(
            error_type="configuration",
            error_message=f"Invalid configuration for {config_key}",
            details={
                "config_key": config_key,
                "config_value": str(config_value)
            },
            suggestions=[suggestion]
        )

    @classmethod
    def processing_error(
        cls,
        processing_stage: str,
        data_type: str,
        recovery_suggestion: str,
        operation: str = "processing"
    ) -> "ErrorResponse":
        """Create a processing error response."""
        return cls(
            error_type="processing",
            error_message=f"Processing failed at {processing_stage} for {data_type}",
            operation=operation,
            details={
                "processing_stage": processing_stage,
                "data_type": data_type
            },
            suggestions=[recovery_suggestion]
        )
