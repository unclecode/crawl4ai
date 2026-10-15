"""
CrewAI integration for Crawl4AI - provides web scraping tools for CrewAI agents.

Usage:
    from crawl4ai.crewai_tool import create_crawl4ai_tools
    
    tools = create_crawl4ai_tools()
    # Use with CrewAI agents
"""

import asyncio
import json
from typing import Optional
from functools import wraps

try:
    from crewai.tools import tool
except ImportError:
    raise ImportError(
        "CrewAI is required to use crawl4ai_tool. "
        "Install it with: pip install crewai"
    )

from .async_webcrawler import AsyncWebCrawler, CacheMode
from .async_configs import BrowserConfig, CrawlerRunConfig


# Global crawler instance for efficiency
_crawler_instance: Optional[AsyncWebCrawler] = None


async def _get_crawler() -> AsyncWebCrawler:
    """Get or create a global crawler instance."""
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = AsyncWebCrawler()
        await _crawler_instance.start()
    return _crawler_instance


def _sync_wrapper(async_func):
    """Wrapper to convert async functions to sync for CrewAI compatibility."""
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(async_func(*args, **kwargs))
    
    return wrapper


@tool
@_sync_wrapper
async def crawl_website(
    url: str,
    cache_mode: str = "BYPASS",
    include_links: bool = False,
    include_images: bool = False,
    js_enabled: bool = False,
    timeout: int = 30,
    extraction_strategy: Optional[str] = None,
) -> dict:
    """
    Crawl a website and extract its content.
    
    Args:
        url: The URL to crawl
        cache_mode: Cache mode - BYPASS, CACHED, or CACHE_FIRST (default: BYPASS)
        include_links: Include all links found on the page (default: False)
        include_images: Include image metadata (default: False)
        js_enabled: Enable JavaScript rendering (default: False)
        timeout: Request timeout in seconds (default: 30)
        extraction_strategy: Extraction strategy - "cosine", "llm", or None for default (default: None)
    
    Returns:
        Dictionary containing:
            - success: bool - Whether the crawl was successful
            - url: str - The crawled URL
            - status_code: int - HTTP status code
            - markdown: str - Page content in Markdown format
            - html: str - Original HTML (if available)
            - links: list - List of links (if include_links=True)
            - media: list - Media elements (if include_images=True)
            - error: str - Error message (if failed)
    """
    try:
        crawler = await _get_crawler()
        
        browser_config = BrowserConfig(
            headless=True,
            use_managed_browser=False,
        )
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode[cache_mode],
            js_enabled=js_enabled,
            timeout=timeout,
            include_links=include_links,
            include_images=include_images,
        )
        
        result = await crawler.arun(
            url=url,
            config=crawler_config,
        )
        
        response = {
            "success": result.success,
            "url": result.url,
            "status_code": result.status_code,
            "markdown": result.markdown,
        }
        
        if include_links and result.links:
            response["links"] = result.links
        
        if include_images and result.media:
            response["media"] = result.media
        
        if result.html and extraction_strategy:
            response["html"] = result.html
        
        if not result.success:
            response["error"] = result.error_message
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
        }


@tool
@_sync_wrapper
async def extract_data_from_url(
    url: str,
    extraction_schema: dict,
    js_enabled: bool = False,
    timeout: int = 30,
) -> dict:
    """
    Extract structured data from a website using a defined schema.
    
    Args:
        url: The URL to crawl and extract from
        extraction_schema: Dictionary defining the data extraction pattern
        js_enabled: Enable JavaScript rendering (default: False)
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Dictionary containing:
            - success: bool - Whether extraction was successful
            - url: str - The crawled URL
            - extracted_data: dict - Extracted structured data
            - raw_markdown: str - Raw page content
            - error: str - Error message (if failed)
    """
    try:
        crawler = await _get_crawler()
        
        crawler_config = CrawlerRunConfig(
            js_enabled=js_enabled,
            timeout=timeout,
        )
        
        result = await crawler.arun(
            url=url,
            config=crawler_config,
        )
        
        if not result.success:
            return {
                "success": False,
                "url": url,
                "error": result.error_message,
            }
        
        # Parse extraction schema and apply to markdown content
        extracted_data = _parse_content_by_schema(result.markdown, extraction_schema)
        
        return {
            "success": True,
            "url": url,
            "extracted_data": extracted_data,
            "raw_markdown": result.markdown,
        }
        
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
        }


@tool
@_sync_wrapper
async def crawl_multiple_urls(
    urls: list,
    cache_mode: str = "BYPASS",
    js_enabled: bool = False,
    timeout: int = 30,
) -> dict:
    """
    Crawl multiple websites in parallel.
    
    Args:
        urls: List of URLs to crawl
        cache_mode: Cache mode - BYPASS, CACHED, or CACHE_FIRST (default: BYPASS)
        js_enabled: Enable JavaScript rendering (default: False)
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Dictionary containing:
            - results: list - List of crawl results for each URL
            - success_count: int - Number of successful crawls
            - failed_count: int - Number of failed crawls
    """
    try:
        crawler = await _get_crawler()
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode[cache_mode],
            js_enabled=js_enabled,
            timeout=timeout,
        )
        
        results = await crawler.arun_many(
            [{"url": url} for url in urls],
            config=crawler_config,
        )
        
        parsed_results = []
        success_count = 0
        failed_count = 0
        
        for result in results:
            parsed_result = {
                "url": result.url,
                "success": result.success,
                "status_code": result.status_code,
                "markdown": result.markdown[:500] if result.markdown else None,
            }
            if not result.success:
                parsed_result["error"] = result.error_message
                failed_count += 1
            else:
                success_count += 1
            
            parsed_results.append(parsed_result)
        
        return {
            "results": parsed_results,
            "success_count": success_count,
            "failed_count": failed_count,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@tool
def search_and_crawl(
    query: str,
    num_results: int = 5,
    include_links: bool = True,
) -> dict:
    """
    Search for a query and crawl the top results.
    
    Args:
        query: Search query
        num_results: Number of results to return (default: 5)
        include_links: Include links from each page (default: True)
    
    Returns:
        Dictionary containing search results and crawled content
    """
    # Note: This is a placeholder - actual implementation would use a search API
    return {
        "success": False,
        "error": "Search functionality requires additional configuration. "
                 "Use crawl_website() with specific URLs instead.",
    }


def _parse_content_by_schema(content: str, schema: dict) -> dict:
    """
    Parse markdown content according to a schema.
    
    This is a simple implementation that looks for schema keys in the content.
    For more advanced extraction, consider using extraction strategies.
    """
    extracted = {}
    
    for key, pattern in schema.items():
        if isinstance(pattern, str):
            # Simple substring search
            if pattern.lower() in content.lower():
                extracted[key] = pattern
        elif isinstance(pattern, dict):
            # Pattern-based extraction
            extracted[key] = pattern.get("default", None)
    
    return extracted


def create_crawl4ai_tools(custom_config: Optional[dict] = None) -> list:
    """
    Create CrewAI tools for web crawling with Crawl4AI.
    
    Args:
        custom_config: Optional custom configuration for the crawler
    
    Returns:
        List of CrewAI tool functions
    
    Example:
        from crawl4ai.crewai_tool import create_crawl4ai_tools
        from crewai import Agent, Task, Crew
        
        tools = create_crawl4ai_tools()
        
        agent = Agent(
            role="Research Assistant",
            goal="Find and summarize information from websites",
            tools=tools,
            llm="gpt-4"
        )
    """
    return [
        crawl_website,
        extract_data_from_url,
        crawl_multiple_urls,
        search_and_crawl,
    ]


async def cleanup_crawler():
    """Clean up the global crawler instance."""
    global _crawler_instance
    if _crawler_instance is not None:
        await _crawler_instance.close()
        _crawler_instance = None
