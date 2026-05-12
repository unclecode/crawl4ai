from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from utils import FilterType


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Optional BrowserConfig overrides (e.g. headless, user_agent, proxy, viewport)"
    )
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        description=(
            "Optional CrawlerRunConfig overrides. Key parameters: "
            "wait_until ('load', 'domcontentloaded', 'networkidle', 'commit') — when to consider navigation done; "
            "delay_before_return_html (float, seconds) — extra wait before capturing HTML, useful for SPAs; "
            "cache_mode ('enabled', 'disabled', 'read_only', 'write_only', 'bypass') — cache behaviour; "
            "js_code (str | list) — JavaScript to execute after page load; "
            "wait_for (str) — CSS selector or JS expression to wait for before returning; "
            "screenshot (bool) — capture a screenshot; pdf (bool) — generate a PDF; "
            "extraction_strategy (dict) — structured extraction config; "
            "markdown_generator (dict) — markdown generation config. "
            "All CrawlerRunConfig fields are accepted; unknown keys are silently ignored."
        )
    )
    crawler_configs: Optional[List[Dict]] = Field(
        default=None,
        description=(
            "List of per-URL CrawlerRunConfig dicts for arun_many(). "
            "When provided, each config can include a 'url_matcher' pattern "
            "to match against specific URLs. Takes precedence over crawler_config."
        ),
    )


class HookConfig(BaseModel):
    """Configuration for user-provided hooks"""
    code: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of hook points to Python code strings"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Timeout in seconds for each hook execution"
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
"""
                },
                "timeout": 30
            }
        }


class CrawlRequestWithHooks(CrawlRequest):
    """Extended crawl request with hooks support"""
    hooks: Optional[HookConfig] = Field(
        default=None,
        description="Optional user-provided hook functions"
    )

class MarkdownRequest(BaseModel):
    """Request body for the /md endpoint."""
    url: str                    = Field(...,  description="Absolute http/https URL to fetch")
    f:   FilterType             = Field(FilterType.FIT, description="Content‑filter strategy: fit, raw, bm25, or llm")
    q:   Optional[str] = Field(None,  description="Query string used by BM25/LLM filters")
    c:   Optional[str] = Field("0",   description="Cache‑bust / revision counter")
    provider: Optional[str] = Field(None, description="LLM provider override (e.g., 'anthropic/claude-3-opus')")
    temperature: Optional[float] = Field(None, description="LLM temperature override (0.0-2.0)")
    base_url: Optional[str] = Field(None, description="LLM API base URL override")
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Optional CrawlerRunConfig overrides (e.g. wait_until, delay_before_return_html, cache_mode). "
                    "Takes precedence over the 'c' cache parameter when cache_mode is specified here. "
                    "scraping_strategy is always set to LXMLWebScrapingStrategy by this endpoint and cannot be overridden."
    )


class RawCode(BaseModel):
    code: str

class HTMLRequest(BaseModel):
    url: str
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Optional CrawlerRunConfig overrides (e.g. wait_until, delay_before_return_html, cache_mode)"
    )

class ScreenshotRequest(BaseModel):
    url: str
    screenshot_wait_for: Optional[float] = None
    wait_for_images: Optional[bool] = None
    output_path: Optional[str] = None
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Optional CrawlerRunConfig overrides (e.g. wait_until, delay_before_return_html, cache_mode). "
                    "screenshot=True is always enforced."
    )

class PDFRequest(BaseModel):
    url: str
    output_path: Optional[str] = None
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Optional CrawlerRunConfig overrides (e.g. wait_until, delay_before_return_html, cache_mode). "
                    "pdf=True is always enforced."
    )


class JSEndpointRequest(BaseModel):
    url: str
    scripts: List[str] = Field(
        ...,
        description="List of separated JavaScript snippets to execute"
    )
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Optional CrawlerRunConfig overrides (e.g. wait_until, delay_before_return_html, cache_mode). "
                    "js_code is always set from the scripts parameter and cannot be overridden via crawler_config."
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