from typing import List, Optional, Dict
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
