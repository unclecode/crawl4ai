# crawl_tools.py
"""Crawl4AI tools for OpenAI Agents SDK."""

import json
from typing import Any, Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from agents import function_tool

from .browser_manager import BrowserManager

# Global session storage (for named sessions only)
CRAWLER_SESSIONS: Dict[str, AsyncWebCrawler] = {}
CRAWLER_SESSION_URLS: Dict[str, str] = {}  # Track current URL per session


@function_tool
async def quick_crawl(
    url: str,
    output_format: str = "markdown",
    extraction_schema: Optional[str] = None,
    js_code: Optional[str] = None,
    wait_for: Optional[str] = None
) -> str:
    """One-shot crawl for simple extraction. Returns markdown, HTML, or structured data.

    Args:
        url: The URL to crawl
        output_format: Output format - "markdown", "html", "structured", or "screenshot"
        extraction_schema: Optional JSON schema for structured extraction
        js_code: Optional JavaScript to execute before extraction
        wait_for: Optional CSS selector to wait for

    Returns:
        JSON string with success status, url, and extracted data
    """
    # Use singleton browser manager
    crawler_config = BrowserConfig(headless=True, verbose=False)
    crawler = await BrowserManager.get_browser(crawler_config)

    run_config = CrawlerRunConfig(
        verbose=False,
        cache_mode=CacheMode.BYPASS,
        js_code=js_code,
        wait_for=wait_for,
    )

    # Add extraction strategy if structured data requested
    if extraction_schema:
        run_config.extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            schema=json.loads(extraction_schema),
            instruction="Extract data according to the provided schema."
        )

    result = await crawler.arun(url=url, config=run_config)

    if not result.success:
        return json.dumps({
            "error": result.error_message,
            "success": False
        }, indent=2)

    # Handle markdown - can be string or MarkdownGenerationResult object
    markdown_content = ""
    if isinstance(result.markdown, str):
        markdown_content = result.markdown
    elif hasattr(result.markdown, 'raw_markdown'):
        markdown_content = result.markdown.raw_markdown

    output_map = {
        "markdown": markdown_content,
        "html": result.html,
        "structured": result.extracted_content,
        "screenshot": result.screenshot,
    }

    response = {
        "success": True,
        "url": result.url,
        "data": output_map.get(output_format, markdown_content)
    }

    return json.dumps(response, indent=2)


@function_tool
async def start_session(
    session_id: str,
    headless: bool = True
) -> str:
    """Start a named browser session for multi-step crawling and automation.

    Args:
        session_id: Unique identifier for the session
        headless: Whether to run browser in headless mode (default True)

    Returns:
        JSON string with success status and session info
    """
    if session_id in CRAWLER_SESSIONS:
        return json.dumps({
            "error": f"Session {session_id} already exists",
            "success": False
        }, indent=2)

    # Use the singleton browser
    crawler_config = BrowserConfig(
        headless=headless,
        verbose=False
    )
    crawler = await BrowserManager.get_browser(crawler_config)

    # Store reference for named session
    CRAWLER_SESSIONS[session_id] = crawler

    return json.dumps({
        "success": True,
        "session_id": session_id,
        "message": f"Browser session {session_id} started"
    }, indent=2)


@function_tool
async def navigate(
    session_id: str,
    url: str,
    wait_for: Optional[str] = None,
    js_code: Optional[str] = None
) -> str:
    """Navigate to a URL in an active session.

    Args:
        session_id: The session identifier
        url: The URL to navigate to
        wait_for: Optional CSS selector to wait for
        js_code: Optional JavaScript to execute after load

    Returns:
        JSON string with navigation result
    """
    if session_id not in CRAWLER_SESSIONS:
        return json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        }, indent=2)

    crawler = CRAWLER_SESSIONS[session_id]
    run_config = CrawlerRunConfig(
        verbose=False,
        cache_mode=CacheMode.BYPASS,
        wait_for=wait_for,
        js_code=js_code,
    )

    result = await crawler.arun(url=url, config=run_config)

    # Store current URL for this session
    if result.success:
        CRAWLER_SESSION_URLS[session_id] = result.url

    return json.dumps({
        "success": result.success,
        "url": result.url,
        "message": f"Navigated to {url}"
    }, indent=2)


@function_tool
async def extract_data(
    session_id: str,
    output_format: str = "markdown",
    extraction_schema: Optional[str] = None,
    wait_for: Optional[str] = None,
    js_code: Optional[str] = None
) -> str:
    """Extract data from current page in session using schema or return markdown.

    Args:
        session_id: The session identifier
        output_format: "markdown" or "structured"
        extraction_schema: Required for structured - JSON schema
        wait_for: Optional - Wait for element before extraction
        js_code: Optional - Execute JS before extraction

    Returns:
        JSON string with extracted data
    """
    if session_id not in CRAWLER_SESSIONS:
        return json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        }, indent=2)

    # Check if we have a current URL for this session
    if session_id not in CRAWLER_SESSION_URLS:
        return json.dumps({
            "error": "No page loaded in session. Use 'navigate' first.",
            "success": False
        }, indent=2)

    crawler = CRAWLER_SESSIONS[session_id]
    current_url = CRAWLER_SESSION_URLS[session_id]

    run_config = CrawlerRunConfig(
        verbose=False,
        cache_mode=CacheMode.BYPASS,
        wait_for=wait_for,
        js_code=js_code,
    )

    if output_format == "structured" and extraction_schema:
        run_config.extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            schema=json.loads(extraction_schema),
            instruction="Extract data according to schema."
        )

    result = await crawler.arun(url=current_url, config=run_config)

    if not result.success:
        return json.dumps({
            "error": result.error_message,
            "success": False
        }, indent=2)

    # Handle markdown - can be string or MarkdownGenerationResult object
    markdown_content = ""
    if isinstance(result.markdown, str):
        markdown_content = result.markdown
    elif hasattr(result.markdown, 'raw_markdown'):
        markdown_content = result.markdown.raw_markdown

    data = (result.extracted_content if output_format == "structured"
            else markdown_content)

    return json.dumps({
        "success": True,
        "data": data
    }, indent=2)


@function_tool
async def execute_js(
    session_id: str,
    js_code: str,
    wait_for: Optional[str] = None
) -> str:
    """Execute JavaScript in the current page context.

    Args:
        session_id: The session identifier
        js_code: JavaScript code to execute
        wait_for: Optional - Wait for element after execution

    Returns:
        JSON string with execution result
    """
    if session_id not in CRAWLER_SESSIONS:
        return json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        }, indent=2)

    # Check if we have a current URL for this session
    if session_id not in CRAWLER_SESSION_URLS:
        return json.dumps({
            "error": "No page loaded in session. Use 'navigate' first.",
            "success": False
        }, indent=2)

    crawler = CRAWLER_SESSIONS[session_id]
    current_url = CRAWLER_SESSION_URLS[session_id]

    run_config = CrawlerRunConfig(
        verbose=False,
        cache_mode=CacheMode.BYPASS,
        js_code=js_code,
        wait_for=wait_for,
    )

    result = await crawler.arun(url=current_url, config=run_config)

    return json.dumps({
        "success": result.success,
        "message": "JavaScript executed"
    }, indent=2)


@function_tool
async def screenshot(session_id: str) -> str:
    """Take a screenshot of the current page.

    Args:
        session_id: The session identifier

    Returns:
        JSON string with screenshot data
    """
    if session_id not in CRAWLER_SESSIONS:
        return json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        }, indent=2)

    # Check if we have a current URL for this session
    if session_id not in CRAWLER_SESSION_URLS:
        return json.dumps({
            "error": "No page loaded in session. Use 'navigate' first.",
            "success": False
        }, indent=2)

    crawler = CRAWLER_SESSIONS[session_id]
    current_url = CRAWLER_SESSION_URLS[session_id]

    result = await crawler.arun(
        url=current_url,
        config=CrawlerRunConfig(verbose=False, cache_mode=CacheMode.BYPASS, screenshot=True)
    )

    return json.dumps({
        "success": True,
        "screenshot": result.screenshot if result.success else None
    }, indent=2)


@function_tool
async def close_session(session_id: str) -> str:
    """Close and cleanup a named browser session.

    Args:
        session_id: The session identifier

    Returns:
        JSON string with closure confirmation
    """
    if session_id not in CRAWLER_SESSIONS:
        return json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        }, indent=2)

    # Remove from named sessions, but don't close the singleton browser
    CRAWLER_SESSIONS.pop(session_id)
    CRAWLER_SESSION_URLS.pop(session_id, None)  # Remove URL tracking

    return json.dumps({
        "success": True,
        "message": f"Session {session_id} closed"
    }, indent=2)


# Export all tools
CRAWL_TOOLS = [
    quick_crawl,
    start_session,
    navigate,
    extract_data,
    execute_js,
    screenshot,
    close_session,
]
