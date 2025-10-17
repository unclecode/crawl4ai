from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from utils import FilterType


# ============================================================================
# Dispatcher Schemas
# ============================================================================

class DispatcherType(str, Enum):
    """Available dispatcher types for crawling."""
    MEMORY_ADAPTIVE = "memory_adaptive"
    SEMAPHORE = "semaphore"


class DispatcherInfo(BaseModel):
    """Information about a dispatcher type."""
    type: DispatcherType
    name: str
    description: str
    config: Dict[str, Any]
    features: List[str]


class DispatcherStatsResponse(BaseModel):
    """Response model for dispatcher statistics."""
    type: DispatcherType
    active_sessions: int
    config: Dict[str, Any]
    stats: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional dispatcher-specific statistics"
    )


class DispatcherSelection(BaseModel):
    """Model for selecting a dispatcher in crawl requests."""
    dispatcher: Optional[DispatcherType] = Field(
        None, 
        description="Dispatcher type to use. Defaults to memory_adaptive if not specified."
    )


# ============================================================================
# End Dispatcher Schemas
# ============================================================================


# ============================================================================
# Table Extraction Schemas
# ============================================================================

class TableExtractionStrategy(str, Enum):
    """Available table extraction strategies."""
    NONE = "none"
    DEFAULT = "default"
    LLM = "llm"
    FINANCIAL = "financial"


class TableExtractionConfig(BaseModel):
    """Configuration for table extraction."""
    
    strategy: TableExtractionStrategy = Field(
        default=TableExtractionStrategy.DEFAULT,
        description="Table extraction strategy to use"
    )
    
    # Common configuration for all strategies
    table_score_threshold: int = Field(
        default=7,
        ge=0,
        le=100,
        description="Minimum score for a table to be considered a data table (default strategy)"
    )
    min_rows: int = Field(
        default=0,
        ge=0,
        description="Minimum number of rows for a valid table"
    )
    min_cols: int = Field(
        default=0,
        ge=0,
        description="Minimum number of columns for a valid table"
    )
    
    # LLM-specific configuration
    llm_provider: Optional[str] = Field(
        None,
        description="LLM provider for LLM strategy (e.g., 'openai/gpt-4')"
    )
    llm_model: Optional[str] = Field(
        None,
        description="Specific LLM model to use"
    )
    llm_api_key: Optional[str] = Field(
        None,
        description="API key for LLM provider (if not in environment)"
    )
    llm_base_url: Optional[str] = Field(
        None,
        description="Custom base URL for LLM API"
    )
    extraction_prompt: Optional[str] = Field(
        None,
        description="Custom prompt for LLM table extraction"
    )
    
    # Financial-specific configuration
    decimal_separator: str = Field(
        default=".",
        description="Decimal separator for financial tables (e.g., '.' or ',')"
    )
    thousand_separator: str = Field(
        default=",",
        description="Thousand separator for financial tables (e.g., ',' or '.')"
    )
    
    # General options
    verbose: bool = Field(
        default=False,
        description="Enable verbose logging for table extraction"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "strategy": "default",
                "table_score_threshold": 7,
                "min_rows": 2,
                "min_cols": 2
            }
        }


class TableExtractionRequest(BaseModel):
    """Request for dedicated table extraction endpoint."""
    
    url: Optional[str] = Field(
        None,
        description="URL to crawl and extract tables from"
    )
    html: Optional[str] = Field(
        None,
        description="Raw HTML content to extract tables from"
    )
    config: TableExtractionConfig = Field(
        default_factory=lambda: TableExtractionConfig(),
        description="Table extraction configuration"
    )
    
    # Browser config (only used if URL is provided)
    browser_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Browser configuration for URL crawling"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/data-table",
                "config": {
                    "strategy": "default",
                    "min_rows": 2
                }
            }
        }


class TableExtractionBatchRequest(BaseModel):
    """Request for batch table extraction."""
    
    html_list: Optional[List[str]] = Field(
        None,
        description="List of HTML contents to extract tables from"
    )
    url_list: Optional[List[str]] = Field(
        None,
        description="List of URLs to extract tables from"
    )
    config: TableExtractionConfig = Field(
        default_factory=lambda: TableExtractionConfig(),
        description="Table extraction configuration"
    )
    browser_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Browser configuration"
    )


# ============================================================================
# End Table Extraction Schemas
# ============================================================================


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)

    anti_bot_strategy: Literal["default", "stealth", "undetected", "max_evasion"] = (
        Field("default", description="The anti-bot strategy to use for the crawl.")
    )
    headless: bool = Field(True, description="Run the browser in headless mode.")
    
    # Dispatcher selection
    dispatcher: Optional[DispatcherType] = Field(
        None, 
        description="Dispatcher type to use for crawling. Defaults to memory_adaptive if not specified."
    )
    
    # Proxy rotation configuration
    proxy_rotation_strategy: Optional[Literal["round_robin", "random", "least_used", "failure_aware"]] = Field(
        None, description="Proxy rotation strategy to use for the crawl."
    )
    proxies: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of proxy configurations (dicts with server, username, password, etc.)"
    )
    proxy_failure_threshold: Optional[int] = Field(
        3, ge=1, le=10, description="Failure threshold for failure_aware strategy"
    )
    proxy_recovery_time: Optional[int] = Field(
        300, ge=60, le=3600, description="Recovery time in seconds for failure_aware strategy"
    )
    
    # Table extraction configuration
    table_extraction: Optional[TableExtractionConfig] = Field(
        None, description="Optional table extraction configuration to extract tables during crawl"
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


class HTTPCrawlRequest(BaseModel):
    """Request model for HTTP-only crawling endpoints."""
    
    urls: List[str] = Field(min_length=1, max_length=100, description="List of URLs to crawl")
    http_config: Optional[Dict] = Field(
        default_factory=dict, 
        description="HTTP crawler configuration (method, headers, timeout, etc.)"
    )
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        description="Crawler run configuration (extraction, filtering, etc.)"
    )
    
    # Dispatcher selection (same as browser crawling)
    dispatcher: Optional[DispatcherType] = Field(
        None, 
        description="Dispatcher type to use. Defaults to memory_adaptive if not specified."
    )


class HTTPCrawlRequestWithHooks(HTTPCrawlRequest):
    """Extended HTTP crawl request with hooks support"""

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


class URLDiscoveryRequest(BaseModel):
    """Request model for URL discovery endpoint."""

    domain: str = Field(..., example="docs.crawl4ai.com", description="Domain to discover URLs from")
    seeding_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration for URL discovery using AsyncUrlSeeder",
        example={
            "source": "sitemap+cc",
            "pattern": "*",
            "live_check": False,
            "extract_head": False,
            "max_urls": -1,
            "concurrency": 1000,
            "hits_per_sec": 5,
            "force": False,
            "verbose": False,
            "query": None,
            "score_threshold": None,
            "scoring_method": "bm25",
            "filter_nonsense_urls": True
        }
    )


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


class LinkAnalysisRequest(BaseModel):
    """Request body for the /links/analyze endpoint."""
    url: str = Field(..., description="URL to analyze for links")
    config: Optional[Dict] = Field(
        default_factory=dict,
        description="Optional LinkPreviewConfig dictionary"
    )
