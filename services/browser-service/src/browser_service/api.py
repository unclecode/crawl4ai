"""Browser service API endpoints."""

import time
from fastapi import APIRouter, HTTPException, Request
from crawl4ai_schemas import BrowserRequest, BrowserResponse

router = APIRouter(tags=["browser"])


@router.post("/navigate", response_model=BrowserResponse)
async def navigate(request: BrowserRequest, app_request: Request) -> BrowserResponse:
    """Navigate to a URL and perform actions.

    Args:
        request: Browser request with URL and actions
        app_request: FastAPI request object

    Returns:
        Browser response with HTML and metadata

    Raises:
        HTTPException: If navigation fails
    """
    start_time = time.time()
    browser_manager = app_request.app.state.browser_manager

    try:
        result = await browser_manager.navigate(
            url=str(request.url),
            action=request.action,
            headless=request.headless,
            timeout=request.timeout,
            wait_time=request.wait_time,
            user_agent=request.user_agent,
            viewport=request.viewport,
            javascript=request.javascript,
            cookies=request.cookies,
            headers=request.headers,
            proxy=request.proxy,
        )

        duration_ms = (time.time() - start_time) * 1000

        return BrowserResponse(
            success=True,
            url=result.get("url", str(request.url)),
            html=result.get("html"),
            screenshot=result.get("screenshot"),
            javascript_result=result.get("javascript_result"),
            cookies=result.get("cookies"),
            duration_ms=duration_ms,
            metadata=request.metadata,
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return BrowserResponse(
            success=False,
            url=str(request.url),
            error=str(e),
            duration_ms=duration_ms,
            metadata=request.metadata,
        )


@router.get("/status")
async def status(app_request: Request):
    """Get browser service status.

    Returns:
        Service status information
    """
    browser_manager = app_request.app.state.browser_manager
    return {
        "status": "running",
        "active_browsers": browser_manager.active_count(),
        "version": "0.1.0",
    }
