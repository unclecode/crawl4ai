from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field
from utils import FilterType


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)

class MarkdownRequest(BaseModel):
    """Request body for the /md endpoint."""
    urls: List[str]             = Field(...,min_length=1, max_length=100, description="Absolute http/https URLs to fetch")
    f:   FilterType             = Field(FilterType.FIT,
                                        description="Content‑filter strategy: FIT, RAW, BM25, or LLM")
    q:   Optional[str] = Field(None,  description="Query string used by BM25/LLM filters")
    c:   Optional[str] = Field("0",   description="Cache‑bust / revision counter")


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