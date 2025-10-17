# c4ai_tools.py
"""Crawl4AI tools for Claude Code SDK agent."""

import json
import asyncio
from typing import Any, Dict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from claude_agent_sdk import tool

from .browser_manager import BrowserManager

# Global session storage (for named sessions only)
CRAWLER_SESSIONS: Dict[str, AsyncWebCrawler] = {}
CRAWLER_SESSION_URLS: Dict[str, str] = {}  # Track current URL per session

@tool("quick_crawl", "One-shot crawl for simple extraction. Returns markdown, HTML, or structured data.", {
    "url": str,
    "output_format": str,  # "markdown" | "html" | "structured" | "screenshot"
    "extraction_schema": str,  # Optional: JSON schema for structured extraction
    "js_code": str,  # Optional: JavaScript to execute before extraction
    "wait_for": str,  # Optional: CSS selector to wait for
})
async def quick_crawl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Fast single-page crawl using persistent browser."""

    # Use singleton browser manager
    crawler_config = BrowserConfig(headless=True, verbose=False)
    crawler = await BrowserManager.get_browser(crawler_config)

    run_config = CrawlerRunConfig(verbose=False, 
        cache_mode=CacheMode.BYPASS,
        js_code=args.get("js_code"),
        wait_for=args.get("wait_for"),
    )

    # Add extraction strategy if structured data requested
    if args.get("extraction_schema"):
        run_config.extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            schema=json.loads(args["extraction_schema"]),
            instruction="Extract data according to the provided schema."
        )

    result = await crawler.arun(url=args["url"], config=run_config)

    if not result.success:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({"error": result.error_message, "success": False})
            }]
        }

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
        "data": output_map.get(args["output_format"], markdown_content)
    }

    return {"content": [{"type": "text", "text": json.dumps(response, indent=2)}]}


@tool("start_session", "Start a named browser session for multi-step crawling and automation.", {
    "session_id": str,
    "headless": bool,  # Default True
})
async def start_session(args: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize a named crawler session using the singleton browser."""

    session_id = args["session_id"]
    if session_id in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} already exists",
            "success": False
        })}]}

    # Use the singleton browser
    crawler_config = BrowserConfig(
        headless=args.get("headless", True),
        verbose=False
    )
    crawler = await BrowserManager.get_browser(crawler_config)

    # Store reference for named session
    CRAWLER_SESSIONS[session_id] = crawler

    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "session_id": session_id,
        "message": f"Browser session {session_id} started"
    })}]}


@tool("navigate", "Navigate to a URL in an active session.", {
    "session_id": str,
    "url": str,
    "wait_for": str,  # Optional: CSS selector to wait for
    "js_code": str,  # Optional: JavaScript to execute after load
})
async def navigate(args: Dict[str, Any]) -> Dict[str, Any]:
    """Navigate to URL in session."""

    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}

    crawler = CRAWLER_SESSIONS[session_id]
    run_config = CrawlerRunConfig(verbose=False, 
        cache_mode=CacheMode.BYPASS,
        wait_for=args.get("wait_for"),
        js_code=args.get("js_code"),
    )

    result = await crawler.arun(url=args["url"], config=run_config)

    # Store current URL for this session
    if result.success:
        CRAWLER_SESSION_URLS[session_id] = result.url

    return {"content": [{"type": "text", "text": json.dumps({
        "success": result.success,
        "url": result.url,
        "message": f"Navigated to {args['url']}"
    })}]}


@tool("extract_data", "Extract data from current page in session using schema or return markdown.", {
    "session_id": str,
    "output_format": str,  # "markdown" | "structured"
    "extraction_schema": str,  # Required for structured, JSON schema
    "wait_for": str,  # Optional: Wait for element before extraction
    "js_code": str,  # Optional: Execute JS before extraction
})
async def extract_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """Extract data from current page."""

    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}

    # Check if we have a current URL for this session
    if session_id not in CRAWLER_SESSION_URLS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": "No page loaded in session. Use 'navigate' first.",
            "success": False
        })}]}

    crawler = CRAWLER_SESSIONS[session_id]
    current_url = CRAWLER_SESSION_URLS[session_id]

    run_config = CrawlerRunConfig(verbose=False, 
        cache_mode=CacheMode.BYPASS,
        wait_for=args.get("wait_for"),
        js_code=args.get("js_code"),
    )

    if args["output_format"] == "structured" and args.get("extraction_schema"):
        run_config.extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            schema=json.loads(args["extraction_schema"]),
            instruction="Extract data according to schema."
        )

    result = await crawler.arun(url=current_url, config=run_config)

    if not result.success:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": result.error_message,
            "success": False
        })}]}

    # Handle markdown - can be string or MarkdownGenerationResult object
    markdown_content = ""
    if isinstance(result.markdown, str):
        markdown_content = result.markdown
    elif hasattr(result.markdown, 'raw_markdown'):
        markdown_content = result.markdown.raw_markdown

    data = (result.extracted_content if args["output_format"] == "structured"
            else markdown_content)

    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "data": data
    }, indent=2)}]}


@tool("execute_js", "Execute JavaScript in the current page context.", {
    "session_id": str,
    "js_code": str,
    "wait_for": str,  # Optional: Wait for element after execution
})
async def execute_js(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute JavaScript in session."""

    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}

    # Check if we have a current URL for this session
    if session_id not in CRAWLER_SESSION_URLS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": "No page loaded in session. Use 'navigate' first.",
            "success": False
        })}]}

    crawler = CRAWLER_SESSIONS[session_id]
    current_url = CRAWLER_SESSION_URLS[session_id]

    run_config = CrawlerRunConfig(verbose=False, 
        cache_mode=CacheMode.BYPASS,
        js_code=args["js_code"],
        wait_for=args.get("wait_for"),
    )

    result = await crawler.arun(url=current_url, config=run_config)

    return {"content": [{"type": "text", "text": json.dumps({
        "success": result.success,
        "message": "JavaScript executed"
    })}]}


@tool("screenshot", "Take a screenshot of the current page.", {
    "session_id": str,
})
async def screenshot(args: Dict[str, Any]) -> Dict[str, Any]:
    """Capture screenshot."""

    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}

    # Check if we have a current URL for this session
    if session_id not in CRAWLER_SESSION_URLS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": "No page loaded in session. Use 'navigate' first.",
            "success": False
        })}]}

    crawler = CRAWLER_SESSIONS[session_id]
    current_url = CRAWLER_SESSION_URLS[session_id]

    result = await crawler.arun(
        url=current_url,
        config=CrawlerRunConfig(verbose=False, cache_mode=CacheMode.BYPASS, screenshot=True)
    )

    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "screenshot": result.screenshot if result.success else None
    })}]}


@tool("close_session", "Close and cleanup a named browser session.", {
    "session_id": str,
})
async def close_session(args: Dict[str, Any]) -> Dict[str, Any]:
    """Close named crawler session (browser stays alive for other operations)."""

    session_id = args["session_id"]
    if session_id not in CRAWLER_SESSIONS:
        return {"content": [{"type": "text", "text": json.dumps({
            "error": f"Session {session_id} not found",
            "success": False
        })}]}

    # Remove from named sessions, but don't close the singleton browser
    CRAWLER_SESSIONS.pop(session_id)
    CRAWLER_SESSION_URLS.pop(session_id, None)  # Remove URL tracking

    return {"content": [{"type": "text", "text": json.dumps({
        "success": True,
        "message": f"Session {session_id} closed"
    })}]}


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
