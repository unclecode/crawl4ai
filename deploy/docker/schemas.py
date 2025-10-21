from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from utils import FilterType


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)

class MarkdownRequest(BaseModel):
    """Request body for the /md endpoint."""
    url: str                    = Field(...,  description="Absolute http/https URL to fetch")
    f:   FilterType             = Field(FilterType.FIT, description="Content‑filter strategy: fit, raw, bm25, or llm")
    q:   Optional[str] = Field(None,  description="Query string used by BM25/LLM filters")
    c:   Optional[str] = Field("0",   description="Cache‑bust / revision counter")
    provider: Optional[str] = Field(None, description="LLM provider override (e.g., 'anthropic/claude-3-opus')")


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
        ...,
        description="List of separated JavaScript snippets to execute"
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