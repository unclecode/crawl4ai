"""Browser service API schemas."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl


class PageAction(str, Enum):
    """Browser page actions."""

    NAVIGATE = "navigate"
    CLICK = "click"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    GET_HTML = "get_html"
    EXECUTE_JS = "execute_js"


class BrowserRequest(BaseModel):
    """Request to browser service."""

    url: HttpUrl = Field(description="URL to navigate to")
    action: PageAction = Field(
        default=PageAction.NAVIGATE, description="Action to perform"
    )
    headless: bool = Field(default=True, description="Run in headless mode")
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
    wait_time: float = Field(
        default=0, ge=0, le=30, description="Wait time after action"
    )
    user_agent: Optional[str] = Field(default=None, description="Custom user agent")
    viewport: Optional[Dict[str, int]] = Field(
        default=None, description="Viewport size {width, height}"
    )
    javascript: Optional[str] = Field(default=None, description="JavaScript to execute")
    cookies: Optional[Dict[str, str]] = Field(
        default=None, description="Cookies to set"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None, description="Custom headers"
    )
    proxy: Optional[str] = Field(default=None, description="Proxy URL")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BrowserResponse(BaseModel):
    """Response from browser service."""

    success: bool = Field(description="Whether the action was successful")
    url: str = Field(description="Final URL after navigation")
    html: Optional[str] = Field(default=None, description="Page HTML content")
    screenshot: Optional[str] = Field(
        default=None, description="Base64 encoded screenshot"
    )
    javascript_result: Optional[Any] = Field(
        default=None, description="Result of JavaScript execution"
    )
    cookies: Optional[Dict[str, str]] = Field(
        default=None, description="Current cookies"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration_ms: float = Field(description="Action duration in milliseconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
