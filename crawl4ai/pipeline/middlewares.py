import time
import sys
from typing import Dict, Any, List
import json

from crawl4ai.models import (
    CrawlResult,
    MarkdownGenerationResult,
    ScrapingResult,
    CrawlResultContainer,
)
from crawl4ai.async_database import async_db_manager
from crawl4ai.cache_context import CacheMode, CacheContext
from crawl4ai.utils import (
    sanitize_input_encode,
    InvalidCSSSelectorError,
    fast_format_html,
    create_box_message,
    get_error_context,
)


async def initialize_context_middleware(context: Dict[str, Any]) -> int:
    """Initialize the context with basic configuration and validation"""
    url = context.get("url")
    config = context.get("config")
    
    if not isinstance(url, str) or not url:
        context["error_message"] = "Invalid URL, make sure the URL is a non-empty string"
        return 0
    
    # Default to ENABLED if no cache mode specified
    if config.cache_mode is None:
        config.cache_mode = CacheMode.ENABLED
    
    # Create cache context
    context["cache_context"] = CacheContext(url, config.cache_mode, False)
    context["start_time"] = time.perf_counter()
    
    return 1

# middlewares.py additions

async def browser_hub_middleware(context: Dict[str, Any]) -> int:
    """
    Initialize or connect to a Browser-Hub and add it to the pipeline context.
    
    This middleware handles browser hub initialization for all three scenarios:
    1. Default configuration when nothing is specified
    2. Custom configuration when browser_config is provided
    3. Connection to existing hub when browser_hub_connection is provided
    
    Args:
        context: The pipeline context dictionary
        
    Returns:
        int: 1 for success, 0 for failure
    """
    from crawl4ai.browser.browser_hub import BrowserHub
    
    try:
        # Get configuration from context
        browser_config = context.get("browser_config")
        browser_hub_id = context.get("browser_hub_id")
        browser_hub_connection = context.get("browser_hub_connection")
        logger = context.get("logger")
        
        # If we already have a browser hub in context, use it
        if context.get("browser_hub"):
            return 1
        
        # Get or create Browser-Hub
        browser_hub = await BrowserHub.get_browser_manager(
            config=browser_config,
            hub_id=browser_hub_id,
            connection_info=browser_hub_connection,
            logger=logger
        )
        
        # Add to context
        context["browser_hub"] = browser_hub
        return 1
    except Exception as e:
        context["error_message"] = f"Failed to initialize browser hub: {str(e)}"
        return 0


async def fetch_content_middleware(context: Dict[str, Any]) -> int:
    """
    Fetch content from the web using the browser hub.
    
    This middleware uses the browser hub to get pages for crawling,
    and properly releases them back to the pool when done.
    
    Args:
        context: The pipeline context dictionary
        
    Returns:
        int: 1 for success, 0 for failure
    """
    url = context.get("url")
    config = context.get("config")
    browser_hub = context.get("browser_hub")
    logger = context.get("logger")
    
    # Skip if using cached result
    if context.get("cached_result") and context.get("html"):
        return 1
    
    try:
        # Create crawler strategy without initializing its browser manager
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        
        crawler_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_hub.config if browser_hub else None,
            logger=logger
        )
        
        # Replace the browser manager with our shared instance
        crawler_strategy.browser_manager = browser_hub
        
        # Perform crawl without trying to initialize the browser
        # The crawler will use the provided browser_manager to get pages
        async_response = await crawler_strategy.crawl(url, config=config)
        
        # Store results in context
        context["html"] = async_response.html
        context["screenshot_data"] = async_response.screenshot
        context["pdf_data"] = async_response.pdf_data
        context["js_execution_result"] = async_response.js_execution_result
        context["async_response"] = async_response
        
        return 1
    except Exception as e:
        context["error_message"] = f"Error fetching content: {str(e)}"
        return 0


async def check_cache_middleware(context: Dict[str, Any]) -> int:
    """Check if there's a cached result and load it if available"""
    url = context.get("url")
    config = context.get("config")
    cache_context = context.get("cache_context")
    logger = context.get("logger")
    
    # Initialize variables
    context["cached_result"] = None
    context["html"] = None
    context["extracted_content"] = None
    context["screenshot_data"] = None
    context["pdf_data"] = None
    
    # Try to get cached result if appropriate
    if cache_context.should_read():
        cached_result = await async_db_manager.aget_cached_url(url)
        context["cached_result"] = cached_result
        
        if cached_result:
            html = sanitize_input_encode(cached_result.html)
            extracted_content = sanitize_input_encode(cached_result.extracted_content or "")
            extracted_content = None if not extracted_content or extracted_content == "[]" else extracted_content
            
            # If screenshot is requested but its not in cache, then set cache_result to None
            screenshot_data = cached_result.screenshot
            pdf_data = cached_result.pdf
            
            if config.screenshot and not screenshot_data:
                context["cached_result"] = None
            
            if config.pdf and not pdf_data:
                context["cached_result"] = None
            
            context["html"] = html
            context["extracted_content"] = extracted_content
            context["screenshot_data"] = screenshot_data
            context["pdf_data"] = pdf_data
            
            logger.url_status(
                url=cache_context.display_url,
                success=bool(html),
                timing=time.perf_counter() - context["start_time"],
                tag="FETCH",
            )
    
    return 1


async def configure_proxy_middleware(context: Dict[str, Any]) -> int:
    """Configure proxy if a proxy rotation strategy is available"""
    config = context.get("config")
    logger = context.get("logger")
    
    # Skip if using cached result
    if context.get("cached_result") and context.get("html"):
        return 1
    
    # Update proxy configuration from rotation strategy if available
    if config and config.proxy_rotation_strategy:
        next_proxy = await config.proxy_rotation_strategy.get_next_proxy()
        if next_proxy:
            logger.info(
                message="Switch proxy: {proxy}",
                tag="PROXY",
                params={"proxy": next_proxy.server},
            )
            config.proxy_config = next_proxy
    
    return 1


async def check_robots_txt_middleware(context: Dict[str, Any]) -> int:
    """Check if the URL is allowed by robots.txt if enabled"""
    url = context.get("url")
    config = context.get("config")
    browser_config = context.get("browser_config")
    robots_parser = context.get("robots_parser")
    
    # Skip if using cached result
    if context.get("cached_result") and context.get("html"):
        return 1
    
    # Check robots.txt if enabled
    if config and config.check_robots_txt:
        if not await robots_parser.can_fetch(url, browser_config.user_agent):
            context["crawl_result"] = CrawlResult(
                url=url,
                html="",
                success=False,
                status_code=403,
                error_message="Access denied by robots.txt",
                response_headers={"X-Robots-Status": "Blocked by robots.txt"}
            )
            return 0
    
    return 1


async def fetch_content_middleware_(context: Dict[str, Any]) -> int:
    """Fetch content from the web using the crawler strategy"""
    url = context.get("url")
    config = context.get("config")
    crawler_strategy = context.get("crawler_strategy")
    logger = context.get("logger")
    
    # Skip if using cached result
    if context.get("cached_result") and context.get("html"):
        return 1
    
    try:
        t1 = time.perf_counter()
        
        if config.user_agent:
            crawler_strategy.update_user_agent(config.user_agent)
        
        # Call CrawlerStrategy.crawl
        async_response = await crawler_strategy.crawl(url, config=config)
        
        html = sanitize_input_encode(async_response.html)
        screenshot_data = async_response.screenshot
        pdf_data = async_response.pdf_data
        js_execution_result = async_response.js_execution_result
        
        t2 = time.perf_counter()
        logger.url_status(
            url=context["cache_context"].display_url,
            success=bool(html),
            timing=t2 - t1,
            tag="FETCH",
        )
        
        context["html"] = html
        context["screenshot_data"] = screenshot_data
        context["pdf_data"] = pdf_data
        context["js_execution_result"] = js_execution_result
        context["async_response"] = async_response
        
        return 1
    except Exception as e:
        context["error_message"] = f"Error fetching content: {str(e)}"
        return 0


async def scrape_content_middleware(context: Dict[str, Any]) -> int:
    """Apply scraping strategy to extract content"""
    url = context.get("url")
    html = context.get("html")
    config = context.get("config")
    extracted_content = context.get("extracted_content")
    logger = context.get("logger")
    
    # Skip if already have a crawl result
    if context.get("crawl_result"):
        return 1
    
    try:
        _url = url if not context.get("is_raw_html", False) else "Raw HTML"
        t1 = time.perf_counter()
        
        # Get scraping strategy and ensure it has a logger
        scraping_strategy = config.scraping_strategy
        if not scraping_strategy.logger:
            scraping_strategy.logger = logger
        
        # Process HTML content
        params = config.__dict__.copy()
        params.pop("url", None)
        # Add keys from kwargs to params that don't exist in params
        kwargs = context.get("kwargs", {})
        params.update({k: v for k, v in kwargs.items() if k not in params.keys()})
        
        # Scraping Strategy Execution
        result: ScrapingResult = scraping_strategy.scrap(url, html, **params)
        
        if result is None:
            raise ValueError(f"Process HTML, Failed to extract content from the website: {url}")
        
        # Extract results - handle both dict and ScrapingResult
        if isinstance(result, dict):
            cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
            media = result.get("media", {})
            links = result.get("links", {})
            metadata = result.get("metadata", {})
        else:
            cleaned_html = sanitize_input_encode(result.cleaned_html)
            media = result.media.model_dump()
            links = result.links.model_dump()
            metadata = result.metadata
        
        context["cleaned_html"] = cleaned_html
        context["media"] = media
        context["links"] = links
        context["metadata"] = metadata
        
        # Log processing completion
        logger.info(
            message="{url:.50}... | Time: {timing}s",
            tag="SCRAPE",
            params={
                "url": _url,
                "timing": int((time.perf_counter() - t1) * 1000) / 1000,
            },
        )
        
        return 1
    except InvalidCSSSelectorError as e:
        context["error_message"] = str(e)
        return 0
    except Exception as e:
        context["error_message"] = f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}"
        return 0


async def generate_markdown_middleware(context: Dict[str, Any]) -> int:
    """Generate markdown from cleaned HTML"""
    url = context.get("url")
    cleaned_html = context.get("cleaned_html")
    config = context.get("config")
    
    # Skip if already have a crawl result
    if context.get("crawl_result"):
        return 1
    
    # Generate Markdown
    markdown_generator = config.markdown_generator
    
    markdown_result: MarkdownGenerationResult = markdown_generator.generate_markdown(
        cleaned_html=cleaned_html,
        base_url=url,
    )
    
    context["markdown_result"] = markdown_result
    
    return 1


async def extract_structured_content_middleware(context: Dict[str, Any]) -> int:
    """Extract structured content using extraction strategy"""
    url = context.get("url")
    extracted_content = context.get("extracted_content")
    config = context.get("config")
    markdown_result = context.get("markdown_result")
    cleaned_html = context.get("cleaned_html")
    logger = context.get("logger")
    
    # Skip if already have a crawl result or extracted content
    if context.get("crawl_result") or bool(extracted_content):
        return 1
    
    from crawl4ai.chunking_strategy import IdentityChunking
    from crawl4ai.extraction_strategy import NoExtractionStrategy
    
    if config.extraction_strategy and not isinstance(config.extraction_strategy, NoExtractionStrategy):
        t1 = time.perf_counter()
        _url = url if not context.get("is_raw_html", False) else "Raw HTML"
        
        # Choose content based on input_format
        content_format = config.extraction_strategy.input_format
        if content_format == "fit_markdown" and not markdown_result.fit_markdown:
            logger.warning(
                message="Fit markdown requested but not available. Falling back to raw markdown.",
                tag="EXTRACT",
                params={"url": _url},
            )
            content_format = "markdown"
        
        content = {
            "markdown": markdown_result.raw_markdown,
            "html": context.get("html"),
            "cleaned_html": cleaned_html,
            "fit_markdown": markdown_result.fit_markdown,
        }.get(content_format, markdown_result.raw_markdown)
        
        # Use IdentityChunking for HTML input, otherwise use provided chunking strategy
        chunking = (
            IdentityChunking()
            if content_format in ["html", "cleaned_html"]
            else config.chunking_strategy
        )
        sections = chunking.chunk(content)
        extracted_content = config.extraction_strategy.run(url, sections)
        extracted_content = json.dumps(
            extracted_content, indent=4, default=str, ensure_ascii=False
        )
        
        context["extracted_content"] = extracted_content
        
        # Log extraction completion
        logger.info(
            message="Completed for {url:.50}... | Time: {timing}s",
            tag="EXTRACT",
            params={"url": _url, "timing": time.perf_counter() - t1},
        )
    
    return 1


async def format_html_middleware(context: Dict[str, Any]) -> int:
    """Format HTML if prettify is enabled"""
    config = context.get("config")
    cleaned_html = context.get("cleaned_html")
    
    # Skip if already have a crawl result
    if context.get("crawl_result"):
        return 1
    
    # Apply HTML formatting if requested
    if config.prettiify and cleaned_html:
        context["cleaned_html"] = fast_format_html(cleaned_html)
    
    return 1


async def write_cache_middleware(context: Dict[str, Any]) -> int:
    """Write result to cache if appropriate"""
    cache_context = context.get("cache_context")
    cached_result = context.get("cached_result")
    
    # Skip if already have a crawl result or not using cache
    if context.get("crawl_result") or not cache_context.should_write() or bool(cached_result):
        return 1
    
    # We'll create the CrawlResult in build_result_middleware and cache it there
    # to avoid creating it twice
    
    return 1


async def build_result_middleware(context: Dict[str, Any]) -> int:
    """Build the final CrawlResult object"""
    url = context.get("url")
    html = context.get("html", "")
    cache_context = context.get("cache_context")
    cached_result = context.get("cached_result")
    config = context.get("config")
    logger = context.get("logger")
    
    # If we already have a crawl result (from an earlier middleware like robots.txt check)
    if context.get("crawl_result"):
        result = context["crawl_result"]
        context["final_result"] = CrawlResultContainer(result)
        return 1
    
    # If we have a cached result
    if cached_result and html:
        logger.success(
            message="{url:.50}... | Status: {status} | Total: {timing}",
            tag="COMPLETE",
            params={
                "url": cache_context.display_url,
                "status": True,
                "timing": f"{time.perf_counter() - context['start_time']:.2f}s",
            },
            colors={"status": "green", "timing": "yellow"},
        )
        
        cached_result.success = bool(html)
        cached_result.session_id = getattr(config, "session_id", None)
        cached_result.redirected_url = cached_result.redirected_url or url
        context["final_result"] = CrawlResultContainer(cached_result)
        return 1
    
    # Build a new result
    try:
        # Get all necessary components from context
        cleaned_html = context.get("cleaned_html", "")
        markdown_result = context.get("markdown_result")
        media = context.get("media", {})
        links = context.get("links", {})
        metadata = context.get("metadata", {})
        screenshot_data = context.get("screenshot_data")
        pdf_data = context.get("pdf_data")
        extracted_content = context.get("extracted_content")
        async_response = context.get("async_response")
        
        # Create the CrawlResult
        crawl_result = CrawlResult(
            url=url,
            html=html,
            cleaned_html=cleaned_html,
            markdown=markdown_result,
            media=media,
            links=links,
            metadata=metadata,
            screenshot=screenshot_data,
            pdf=pdf_data,
            extracted_content=extracted_content,
            success=bool(html),
            error_message="",
        )
        
        # Add response details if available
        if async_response:
            crawl_result.status_code = async_response.status_code
            crawl_result.redirected_url = async_response.redirected_url or url
            crawl_result.response_headers = async_response.response_headers
            crawl_result.downloaded_files = async_response.downloaded_files
            crawl_result.js_execution_result = context.get("js_execution_result")
            crawl_result.ssl_certificate = async_response.ssl_certificate
        
        crawl_result.session_id = getattr(config, "session_id", None)
        
        # Log completion
        logger.success(
            message="{url:.50}... | Status: {status} | Total: {timing}",
            tag="COMPLETE",
            params={
                "url": cache_context.display_url,
                "status": crawl_result.success,
                "timing": f"{time.perf_counter() - context['start_time']:.2f}s",
            },
            colors={
                "status": "green" if crawl_result.success else "red",
                "timing": "yellow",
            },
        )
        
        # Update cache if appropriate
        if cache_context.should_write() and not bool(cached_result):
            await async_db_manager.acache_url(crawl_result)
        
        context["final_result"] = CrawlResultContainer(crawl_result)
        return 1
    except Exception as e:
        error_context = get_error_context(sys.exc_info())
        
        error_message = (
            f"Unexpected error in build_result at line {error_context['line_no']} "
            f"in {error_context['function']} ({error_context['filename']}):\n"
            f"Error: {str(e)}\n\n"
            f"Code context:\n{error_context['code_context']}"
        )
        
        logger.error_status(
            url=url,
            error=create_box_message(error_message, type="error"),
            tag="ERROR",
        )
        
        context["final_result"] = CrawlResultContainer(
            CrawlResult(
                url=url, html="", success=False, error_message=error_message
            )
        )
        return 1


async def handle_error_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
    """Error handler middleware"""
    url = context.get("url", "")
    error_message = context.get("error_message", "Unknown error")
    logger = context.get("logger")
    
    # Log the error
    if logger:
        logger.error_status(
            url=url,
            error=create_box_message(error_message, type="error"),
            tag="ERROR",
        )
    
    # Create a failure result
    context["final_result"] = CrawlResultContainer(
        CrawlResult(
            url=url, html="", success=False, error_message=error_message
        )
    )
    
    return context


# Custom middlewares as requested

async def sentiment_analysis_middleware(context: Dict[str, Any]) -> int:
    """Analyze sentiment of generated markdown using TextBlob"""
    from textblob import TextBlob
    
    markdown_result = context.get("markdown_result")
    
    # Skip if no markdown or already failed
    if not markdown_result or not context.get("success", True):
        return 1
    
    try:
        # Get raw markdown text
        raw_markdown = markdown_result.raw_markdown
        
        # Analyze sentiment
        blob = TextBlob(raw_markdown)
        sentiment = blob.sentiment
        
        # Add sentiment to context
        context["sentiment_analysis"] = {
            "polarity": sentiment.polarity,  # -1.0 to 1.0 (negative to positive)
            "subjectivity": sentiment.subjectivity,  # 0.0 to 1.0 (objective to subjective)
            "classification": "positive" if sentiment.polarity > 0.1 else 
                             "negative" if sentiment.polarity < -0.1 else "neutral"
        }
        
        return 1
    except Exception as e:
        # Don't fail the pipeline on sentiment analysis failure
        context["sentiment_analysis_error"] = str(e)
        return 1


async def log_timing_middleware(context: Dict[str, Any], name: str) -> int:
    """Log timing information for a specific point in the pipeline"""
    context[f"_timing_mark_{name}"] = time.perf_counter()
    
    # Calculate duration if we have a start time
    start_key = f"_timing_start_{name}"
    if start_key in context:
        duration = context[f"_timing_mark_{name}"] - context[start_key]
        context[f"_timing_duration_{name}"] = duration
        
        # Log the timing if we have a logger
        logger = context.get("logger")
        if logger:
            logger.info(
                message="{name} completed in {duration:.2f}s",
                tag="TIMING",
                params={"name": name, "duration": duration},
            )
    
    return 1


async def validate_url_middleware(context: Dict[str, Any], patterns: List[str]) -> int:
    """Validate URL against glob patterns"""
    import fnmatch
    url = context.get("url", "")
    
    # If no patterns provided, allow all
    if not patterns:
        return 1
    
    # Check if URL matches any of the allowed patterns
    for pattern in patterns:
        if fnmatch.fnmatch(url, pattern):
            return 1
    
    # If we get here, URL didn't match any patterns
    context["error_message"] = f"URL '{url}' does not match any allowed patterns"
    return 0


# Update the default middleware list function
def create_default_middleware_list():
    """Return the default list of middleware functions for the pipeline."""
    return [
        initialize_context_middleware,
        check_cache_middleware,
        browser_hub_middleware,  # Add browser hub middleware before fetch_content
        configure_proxy_middleware,
        check_robots_txt_middleware,
        fetch_content_middleware,
        scrape_content_middleware,
        generate_markdown_middleware,
        extract_structured_content_middleware,
        format_html_middleware,
        build_result_middleware
    ]
