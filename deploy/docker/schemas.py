from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from utils import FilterType


# =============================================================================
# Output Control Schemas - Pagination and field control for API responses
# =============================================================================


class OutputControl(BaseModel):
    """Controls pagination and field inclusion in responses.

    All parameters are optional. When not specified, full output is returned
    (backward compatible default behavior).
    """

    # Content pagination (applies to: markdown, html, cleaned_html, extracted_content)
    content_offset: Optional[int] = Field(
        None,
        ge=0,
        description="Character offset for text content fields (markdown, html, cleaned_html, extracted_content)",
    )
    content_limit: Optional[int] = Field(
        None, ge=1, description="Maximum characters to return for text content fields"
    )

    # Collection limiting (applies to: links, media, tables)
    max_links: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum number of links to include (applies to both internal and external)",
    )
    max_media: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum number of media items to include per category (images, videos, audios)",
    )
    max_tables: Optional[int] = Field(
        None, ge=0, description="Maximum number of tables to include"
    )

    # Field exclusion
    exclude_fields: Optional[List[str]] = Field(
        None,
        description=(
            "Fields to completely omit from response. Valid values: "
            "html, cleaned_html, fit_html, markdown, links, media, tables, metadata, "
            "response_headers, network_requests, console_messages, screenshot, pdf. "
            "Supports dot-notation for nested exclusion (e.g., 'markdown.references_markdown')"
        ),
    )


class ContentFieldStats(BaseModel):
    """Statistics for a paginated text field."""

    total_chars: int = Field(
        ..., description="Total character count of the original content"
    )
    returned_chars: int = Field(
        ..., description="Number of characters returned after pagination"
    )
    offset: int = Field(..., description="Character offset applied")
    has_more: bool = Field(
        ..., description="True if more content exists beyond the returned portion"
    )


class CollectionStats(BaseModel):
    """Statistics for a limited collection field."""

    total_count: int = Field(
        ..., description="Total item count in the original collection"
    )
    returned_count: int = Field(
        ..., description="Number of items returned after limiting"
    )


class OutputMeta(BaseModel):
    """Metadata about output pagination and truncation.

    Included in responses (as '_output_meta') when any pagination or limiting is applied.
    """

    truncated: bool = Field(
        ..., description="True if any content was truncated or limited"
    )

    # Per-field truncation info (only present for affected fields)
    content_stats: Optional[Dict[str, ContentFieldStats]] = Field(
        None,
        description="Statistics for text content fields that were paginated (e.g., 'markdown.raw_markdown')",
    )
    collection_stats: Optional[Dict[str, CollectionStats]] = Field(
        None,
        description="Statistics for collection fields that were limited (e.g., 'links.internal')",
    )
    excluded_fields: Optional[List[str]] = Field(
        None, description="List of fields that were excluded from response"
    )


# =============================================================================
# Request Schemas
# =============================================================================


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)
    output: Optional[OutputControl] = Field(
        None, description="Output control for pagination and field exclusion"
    )


class HookConfig(BaseModel):
    """Configuration for user-provided hooks"""

    code: Dict[str, str] = Field(
        default_factory=dict, description="Map of hook points to Python code strings"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Timeout in seconds for each hook execution",
    )

    class Config:
        schema_extra = {
            "example": {
                "code": {
                    "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Block images to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif}", lambda route: route.abort())
    return page
""",
                    "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # Scroll to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)
    return page
""",
                },
                "timeout": 30,
            }
        }


class CrawlRequestWithHooks(CrawlRequest):
    """Extended crawl request with hooks support"""

    hooks: Optional[HookConfig] = Field(
        default=None, description="Optional user-provided hook functions"
    )


class MarkdownRequest(BaseModel):
    """Request body for the /md endpoint."""

    url: str = Field(..., description="Absolute http/https URL to fetch")
    f: FilterType = Field(
        FilterType.FIT, description="Content‑filter strategy: fit, raw, bm25, or llm"
    )
    q: Optional[str] = Field(None, description="Query string used by BM25/LLM filters")
    c: Optional[str] = Field("0", description="Cache‑bust / revision counter")
    provider: Optional[str] = Field(
        None, description="LLM provider override (e.g., 'anthropic/claude-3-opus')"
    )
    temperature: Optional[float] = Field(
        None, description="LLM temperature override (0.0-2.0)"
    )
    base_url: Optional[str] = Field(None, description="LLM API base URL override")
    output: Optional[OutputControl] = Field(
        None, description="Output control for pagination and field exclusion"
    )


class RawCode(BaseModel):
    code: str


class HTMLRequest(BaseModel):
    url: str
    output: Optional[OutputControl] = Field(
        None, description="Output control for pagination and field exclusion"
    )


class ScreenshotRequest(BaseModel):
    url: str
    screenshot_wait_for: Optional[float] = 2
    output_path: Optional[str] = None
    output: Optional[OutputControl] = Field(
        None, description="Output control for pagination and field exclusion"
    )


class PDFRequest(BaseModel):
    url: str
    output_path: Optional[str] = None
    output: Optional[OutputControl] = Field(
        None, description="Output control for pagination and field exclusion"
    )


class JSEndpointRequest(BaseModel):
    url: str
    scripts: List[str] = Field(
        ..., description="List of separated JavaScript snippets to execute"
    )
    output: Optional[OutputControl] = Field(
        None, description="Output control for pagination and field exclusion"
    )


class WebhookConfig(BaseModel):
    """Configuration for webhook notifications."""

    webhook_url: HttpUrl
    webhook_data_in_payload: bool = False
    webhook_headers: Optional[Dict[str, str]] = None


class WebhookPayload(BaseModel):
    """Payload sent to webhook endpoints."""

    task_id: str
    task_type: str  # "crawl", "llm_extraction", etc.
    status: str  # "completed" or "failed"
    timestamp: str  # ISO 8601 format
    urls: List[str]
    error: Optional[str] = None
    data: Optional[Dict] = None  # Included only if webhook_data_in_payload=True
