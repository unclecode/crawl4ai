from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from utils import FilterType


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)


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


class RawCode(BaseModel):
    code: str


class HTMLRequest(BaseModel):
    url: str


class ScreenshotRequest(BaseModel):
    url: str
    screenshot_wait_for: Optional[float] = 2
    output_path: Optional[str] = None


class PDFRequest(BaseModel):
    url: str
    output_path: Optional[str] = None


class JSEndpointRequest(BaseModel):
    url: str
    scripts: List[str] = Field(
        ..., description="List of separated JavaScript snippets to execute"
    )


class SeedRequest(BaseModel):
    """Request model for URL seeding endpoint."""

    url: str = Field(..., example="https://docs.crawl4ai.com")
    config: Dict[str, Any] = Field(default_factory=dict)


# --- C4A Script Schemas ---


class C4AScriptPayload(BaseModel):
    """Input model for receiving a C4A-Script."""

    script: str = Field(..., description="The C4A-Script content to process.")


# --- Adaptive Crawling Schemas ---


class AdaptiveConfigPayload(BaseModel):
    """Pydantic model for receiving AdaptiveConfig parameters."""

    confidence_threshold: float = 0.7
    max_pages: int = 20
    top_k_links: int = 3
    strategy: str = "statistical"  # "statistical" or "embedding"
    embedding_model: Optional[str] = "sentence-transformers/all-MiniLM-L6-v2"
    # Add any other AdaptiveConfig fields you want to expose


class AdaptiveCrawlRequest(BaseModel):
    """Input model for the adaptive digest job."""

    start_url: str = Field(..., description="The starting URL for the adaptive crawl.")
    query: str = Field(..., description="The user query to guide the crawl.")
    config: Optional[AdaptiveConfigPayload] = Field(
        None, description="Optional adaptive crawler configuration."
    )


class AdaptiveJobStatus(BaseModel):
    """Output model for the job status."""

    task_id: str
    status: str
    metrics: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
