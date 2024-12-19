import os, sys
import time
import warnings
from enum import Enum
from colorama import init, Fore, Back, Style
from pathlib import Path
from typing import Optional, List, Union
import json
import asyncio
# from contextlib import nullcontext, asynccontextmanager
from contextlib import asynccontextmanager
from .models import CrawlResult, MarkdownGenerationResult
from .async_database import async_db_manager
from .chunking_strategy import *
from .content_filter_strategy import *
from .extraction_strategy import *
from .async_crawler_strategy import AsyncCrawlerStrategy, AsyncPlaywrightCrawlerStrategy, AsyncCrawlResponse
from .cache_context import CacheMode, CacheContext, _legacy_to_cache_mode
from .markdown_generation_strategy import DefaultMarkdownGenerator, MarkdownGenerationStrategy
from .content_scraping_strategy import WebScrapingStrategy
from .async_logger import AsyncLogger
from .async_configs import BrowserConfig, CrawlerRunConfig
from .config import (
    MIN_WORD_THRESHOLD, 
    IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
    URL_LOG_SHORTEN_LENGTH
)
from .utils import (
    sanitize_input_encode,
    InvalidCSSSelectorError,
    format_html,
    fast_format_html,
    create_box_message
)

from urllib.parse import urlparse
import random
from .__version__ import __version__ as crawl4ai_version


class AsyncWebCrawler:
    """
    Asynchronous web crawler with flexible caching capabilities.
    
    Migration Guide:
    Old way (deprecated):
        crawler = AsyncWebCrawler(always_by_pass_cache=True, browser_type="chromium", headless=True)
    
    New way (recommended):
        browser_config = BrowserConfig(browser_type="chromium", headless=True)
        crawler = AsyncWebCrawler(browser_config=browser_config)
    """
    _domain_last_hit = {}

    def __init__(
        self,
        crawler_strategy: Optional[AsyncCrawlerStrategy] = None,
        config: Optional[BrowserConfig] = None,
        always_bypass_cache: bool = False,
        always_by_pass_cache: Optional[bool] = None,  # Deprecated parameter
        base_directory: str = str(os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())),
        thread_safe: bool = False,
        **kwargs,
    ):
        """
        Initialize the AsyncWebCrawler.

        Args:
            crawler_strategy: Strategy for crawling web pages. If None, will create AsyncPlaywrightCrawlerStrategy
            config: Configuration object for browser settings. If None, will be created from kwargs
            always_bypass_cache: Whether to always bypass cache (new parameter)
            always_by_pass_cache: Deprecated, use always_bypass_cache instead
            base_directory: Base directory for storing cache
            thread_safe: Whether to use thread-safe operations
            **kwargs: Additional arguments for backwards compatibility
        """  
        # Handle browser configuration
        browser_config = config
        legacy_warning = False
        if browser_config is not None:
            legacy_warning = any(k in kwargs for k in ["browser_type", "headless", "viewport_width", "viewport_height"])
        else:
            # Create browser config from kwargs for backwards compatibility
            browser_config = BrowserConfig.from_kwargs(kwargs)

        self.browser_config = browser_config
        
        # Initialize logger first since other components may need it
        self.logger = AsyncLogger(
            log_file=os.path.join(base_directory, ".crawl4ai", "crawler.log"),
            verbose=self.browser_config.verbose,    
            tag_width=10
        )

        if legacy_warning:
            self.logger.warning(
                message="Both browser_config and legacy browser parameters provided. browser_config will take precedence.",
                tag="WARNING"
            )

        # Initialize crawler strategy
        self.crawler_strategy = crawler_strategy or AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_config,
            logger=self.logger,
            **kwargs  # Pass remaining kwargs for backwards compatibility
        )
        
        # Handle deprecated cache parameter
        if always_by_pass_cache is not None:
            if kwargs.get("warning", True):
                warnings.warn(
                    "'always_by_pass_cache' is deprecated and will be removed in version 0.5.0. "
                    "Use 'always_bypass_cache' instead. "
                    "Pass warning=False to suppress this warning.",
                    DeprecationWarning,
                    stacklevel=2
                )
            self.always_bypass_cache = always_by_pass_cache
        else:
            self.always_bypass_cache = always_bypass_cache

        # Thread safety setup
        self._lock = asyncio.Lock() if thread_safe else None
        
        # Initialize directories
        self.crawl4ai_folder = os.path.join(base_directory, ".crawl4ai")
        os.makedirs(self.crawl4ai_folder, exist_ok=True)
        os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)
        
        self.ready = False

    async def __aenter__(self):
        await self.crawler_strategy.__aenter__()
        await self.awarmup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.crawler_strategy.__aexit__(exc_type, exc_val, exc_tb)
    
    async def awarmup(self):
        """Initialize the crawler with warm-up sequence."""
        self.logger.info(f"Crawl4AI {crawl4ai_version}", tag="INIT")
        self.ready = True

    @asynccontextmanager
    async def nullcontext(self):
        """异步空上下文管理器"""
        yield
    
    async def arun(
            self,
            url: str,
            config: Optional[CrawlerRunConfig] = None,
            # Legacy parameters maintained for backwards compatibility
            word_count_threshold=MIN_WORD_THRESHOLD,
            extraction_strategy: ExtractionStrategy = None,
            chunking_strategy: ChunkingStrategy = RegexChunking(),
            content_filter: RelevantContentFilter = None,
            cache_mode: Optional[CacheMode] = None,
            # Deprecated cache parameters
            bypass_cache: bool = False,
            disable_cache: bool = False,
            no_cache_read: bool = False,
            no_cache_write: bool = False,
            # Other legacy parameters
            css_selector: str = None,
            screenshot: bool = False,
            pdf: bool = False,
            user_agent: str = None,
            verbose=True,
            **kwargs,
        ) -> CrawlResult:
            """
            Runs the crawler for a single source: URL (web, local file, or raw HTML).

            Migration Guide:
            Old way (deprecated):
                result = await crawler.arun(
                    url="https://example.com",
                    word_count_threshold=200,
                    screenshot=True,
                    ...
                )
            
            New way (recommended):
                config = CrawlerRunConfig(
                    word_count_threshold=200,
                    screenshot=True,
                    ...
                )
                result = await crawler.arun(url="https://example.com", crawler_config=config)

            Args:
                url: The URL to crawl (http://, https://, file://, or raw:)
                crawler_config: Configuration object controlling crawl behavior
                [other parameters maintained for backwards compatibility]
            
            Returns:
                CrawlResult: The result of crawling and processing
            """
            crawler_config = config
            if not isinstance(url, str) or not url:
                raise ValueError("Invalid URL, make sure the URL is a non-empty string")
            
            async with self._lock or self.nullcontext():
                try:
                    # Handle configuration
                    if crawler_config is not None:
                        if any(param is not None for param in [
                            word_count_threshold, extraction_strategy, chunking_strategy,
                            content_filter, cache_mode, css_selector, screenshot, pdf
                        ]):
                            self.logger.warning(
                                message="Both crawler_config and legacy parameters provided. crawler_config will take precedence.",
                                tag="WARNING"
                            )
                        config = crawler_config
                    else:
                        # Merge all parameters into a single kwargs dict for config creation
                        config_kwargs = {
                            "word_count_threshold": word_count_threshold,
                            "extraction_strategy": extraction_strategy,
                            "chunking_strategy": chunking_strategy,
                            "content_filter": content_filter,
                            "cache_mode": cache_mode,
                            "bypass_cache": bypass_cache,
                            "disable_cache": disable_cache,
                            "no_cache_read": no_cache_read,
                            "no_cache_write": no_cache_write,
                            "css_selector": css_selector,
                            "screenshot": screenshot,
                            "pdf": pdf,
                            "verbose": verbose,
                            **kwargs
                        }
                        config = CrawlerRunConfig.from_kwargs(config_kwargs)

                    # Handle deprecated cache parameters
                    if any([bypass_cache, disable_cache, no_cache_read, no_cache_write]):
                        if kwargs.get("warning", True):
                            warnings.warn(
                                "Cache control boolean flags are deprecated and will be removed in version 0.5.0. "
                                "Use 'cache_mode' parameter instead.",
                                DeprecationWarning,
                                stacklevel=2
                            )
                        
                        # Convert legacy parameters if cache_mode not provided
                        if config.cache_mode is None:
                            config.cache_mode = _legacy_to_cache_mode(
                                disable_cache=disable_cache,
                                bypass_cache=bypass_cache,
                                no_cache_read=no_cache_read,
                                no_cache_write=no_cache_write
                            )
                    
                    # Default to ENABLED if no cache mode specified
                    if config.cache_mode is None:
                        config.cache_mode = CacheMode.ENABLED

                    # Create cache context
                    cache_context = CacheContext(url, config.cache_mode, self.always_bypass_cache)

                    # Initialize processing variables
                    async_response: AsyncCrawlResponse = None
                    cached_result = None
                    screenshot_data = None
                    pdf_data = None
                    extracted_content = None
                    start_time = time.perf_counter()

                    # Try to get cached result if appropriate
                    if cache_context.should_read():
                        cached_result = await async_db_manager.aget_cached_url(url)

                    if cached_result:
                        html = sanitize_input_encode(cached_result.html)
                        extracted_content = sanitize_input_encode(cached_result.extracted_content or "")
                        # If screenshot is requested but its not in cache, then set cache_result to None
                        screenshot_data = cached_result.screenshot
                        pdf_data = cached_result.pdf
                        if config.screenshot and not screenshot or config.pdf and not pdf:
                            cached_result = None

                        self.logger.url_status(
                            url=cache_context.display_url,
                            success=bool(html),
                            timing=time.perf_counter() - start_time,
                            tag="FETCH"
                        )

                    # Fetch fresh content if needed
                    if not cached_result or not html:
                        t1 = time.perf_counter()
                        
                        if user_agent:
                            self.crawler_strategy.update_user_agent(user_agent)
                        
                        # Pass config to crawl method
                        async_response = await self.crawler_strategy.crawl(
                            url,
                            config=config  # Pass the entire config object
                        )
                        
                        html = sanitize_input_encode(async_response.html)
                        screenshot_data = async_response.screenshot
                        pdf_data = async_response.pdf_data
                        
                        t2 = time.perf_counter()
                        self.logger.url_status(
                            url=cache_context.display_url,
                            success=bool(html),
                            timing=t2 - t1,
                            tag="FETCH"
                        )

                    # Process the HTML content
                    crawl_result = await self.aprocess_html(
                        url=url,
                        html=html,
                        extracted_content=extracted_content,
                        config=config,  # Pass the config object instead of individual parameters
                        screenshot=screenshot_data,
                        pdf_data=pdf_data,
                        verbose=config.verbose,
                        **kwargs
                    )

                    # Set response data
                    if async_response:
                        crawl_result.status_code = async_response.status_code
                        crawl_result.response_headers = async_response.response_headers
                        crawl_result.downloaded_files = async_response.downloaded_files
                    else:
                        crawl_result.status_code = 200
                        crawl_result.response_headers = cached_result.response_headers if cached_result else {}

                    crawl_result.success = bool(html)
                    crawl_result.session_id = getattr(config, 'session_id', None)

                    self.logger.success(
                        message="{url:.50}... | Status: {status} | Total: {timing}",
                        tag="COMPLETE",
                        params={
                            "url": cache_context.display_url,
                            "status": crawl_result.success,
                            "timing": f"{time.perf_counter() - start_time:.2f}s"
                        },
                        colors={
                            "status": Fore.GREEN if crawl_result.success else Fore.RED,
                            "timing": Fore.YELLOW
                        }
                    )

                    # Update cache if appropriate
                    if cache_context.should_write() and not bool(cached_result):
                        await async_db_manager.acache_url(crawl_result)

                    return crawl_result

                except Exception as e:
                    error_context = get_error_context(sys.exc_info())
                
                    error_message = (
                        f"Unexpected error in _crawl_web at line {error_context['line_no']} "
                        f"in {error_context['function']} ({error_context['filename']}):\n"
                        f"Error: {str(e)}\n\n"
                        f"Code context:\n{error_context['code_context']}"
                    )
                    # if not hasattr(e, "msg"):
                    #     e.msg = str(e)
                    
                    self.logger.error_status(
                        url=url,
                        error=create_box_message(error_message, type="error"),
                        tag="ERROR"
                    )
                    
                    return CrawlResult(
                        url=url,
                        html="",
                        success=False,
                        error_message=error_message
                    )

    async def aprocess_html(
            self,
            url: str,
            html: str,
            extracted_content: str,
            config: CrawlerRunConfig,
            screenshot: str,
            pdf_data: str,
            verbose: bool,
            **kwargs,
        ) -> CrawlResult:
            """
            Process HTML content using the provided configuration.
            
            Args:
                url: The URL being processed
                html: Raw HTML content
                extracted_content: Previously extracted content (if any)
                config: Configuration object controlling processing behavior
                screenshot: Screenshot data (if any)
                verbose: Whether to enable verbose logging
                **kwargs: Additional parameters for backwards compatibility
            
            Returns:
                CrawlResult: Processed result containing extracted and formatted content
            """
            try:
                _url = url if not kwargs.get("is_raw_html", False) else "Raw HTML"
                t1 = time.perf_counter()

                # Initialize scraping strategy
                scrapping_strategy = WebScrapingStrategy(logger=self.logger)

                # Process HTML content
                result = scrapping_strategy.scrap(
                    url,
                    html,
                    word_count_threshold=config.word_count_threshold,
                    css_selector=config.css_selector,
                    only_text=config.only_text,
                    image_description_min_word_threshold=config.image_description_min_word_threshold,
                    content_filter=config.content_filter,
                    **kwargs
                )

                if result is None:
                    raise ValueError(f"Process HTML, Failed to extract content from the website: {url}")

            except InvalidCSSSelectorError as e:
                raise ValueError(str(e))
            except Exception as e:
                raise ValueError(f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}")

       

            # Extract results
            cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
            fit_markdown = sanitize_input_encode(result.get("fit_markdown", ""))
            fit_html = sanitize_input_encode(result.get("fit_html", ""))
            media = result.get("media", [])
            links = result.get("links", [])
            metadata = result.get("metadata", {})

            # Markdown Generation
            markdown_generator: Optional[MarkdownGenerationStrategy] = config.markdown_generator or DefaultMarkdownGenerator()
            if not config.content_filter and not markdown_generator.content_filter:
                markdown_generator.content_filter = PruningContentFilter()
            
            markdown_result: MarkdownGenerationResult = markdown_generator.generate_markdown(
                cleaned_html=cleaned_html,
                base_url=url,
                # html2text_options=kwargs.get('html2text', {})
            )
            markdown_v2 = markdown_result
            markdown = sanitize_input_encode(markdown_result.raw_markdown)

            # Log processing completion
            self.logger.info(
                message="Processed {url:.50}... | Time: {timing}ms",
                tag="SCRAPE",
                params={
                    "url": _url,
                    "timing": int((time.perf_counter() - t1) * 1000)
                }
            )

            # Handle content extraction if needed
            if (extracted_content is None and 
                config.extraction_strategy and 
                config.chunking_strategy and 
                not isinstance(config.extraction_strategy, NoExtractionStrategy)):
                
                t1 = time.perf_counter()
                
                # Handle different extraction strategy types
                if isinstance(config.extraction_strategy, (JsonCssExtractionStrategy, JsonCssExtractionStrategy)):
                    config.extraction_strategy.verbose = verbose
                    extracted_content = config.extraction_strategy.run(url, [html])
                    extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)
                else:
                    sections = config.chunking_strategy.chunk(markdown)
                    extracted_content = config.extraction_strategy.run(url, sections)
                    extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)

                # Log extraction completion
                self.logger.info(
                    message="Completed for {url:.50}... | Time: {timing}s",
                    tag="EXTRACT",
                    params={
                        "url": _url,
                        "timing": time.perf_counter() - t1
                    }
                )

            # Handle screenshot and PDF data
            screenshot_data = None if not screenshot else screenshot
            pdf_data = None if not pdf_data else pdf_data

            # Apply HTML formatting if requested
            if config.prettiify:
                cleaned_html = fast_format_html(cleaned_html)

            # Return complete crawl result
            return CrawlResult(
                url=url,
                html=html,
                cleaned_html=cleaned_html,
                markdown_v2=markdown_v2,
                markdown=markdown,
                fit_markdown=fit_markdown,
                fit_html=fit_html,
                media=media,
                links=links,
                metadata=metadata,
                screenshot=screenshot_data,
                pdf=pdf_data,
                extracted_content=extracted_content,
                success=True,
                error_message="",
            )    

    async def arun_many(
            self,
            urls: List[str],
            config: Optional[CrawlerRunConfig] = None,
            # Legacy parameters maintained for backwards compatibility
            word_count_threshold=MIN_WORD_THRESHOLD,
            extraction_strategy: ExtractionStrategy = None,
            chunking_strategy: ChunkingStrategy = RegexChunking(),
            content_filter: RelevantContentFilter = None,
            cache_mode: Optional[CacheMode] = None,
            bypass_cache: bool = False,
            css_selector: str = None,
            screenshot: bool = False,
            pdf: bool = False,
            user_agent: str = None,
            verbose=True,
            **kwargs,
        ) -> List[CrawlResult]:
            """
            Runs the crawler for multiple URLs concurrently.

            Migration Guide:
            Old way (deprecated):
                results = await crawler.arun_many(
                    urls,
                    word_count_threshold=200,
                    screenshot=True,
                    ...
                )
            
            New way (recommended):
                config = CrawlerRunConfig(
                    word_count_threshold=200,
                    screenshot=True,
                    ...
                )
                results = await crawler.arun_many(urls, crawler_config=config)

            Args:
                urls: List of URLs to crawl
                crawler_config: Configuration object controlling crawl behavior for all URLs
                [other parameters maintained for backwards compatibility]
            
            Returns:
                List[CrawlResult]: Results for each URL
            """
            crawler_config = config
            # Handle configuration
            if crawler_config is not None:
                if any(param is not None for param in [
                    word_count_threshold, extraction_strategy, chunking_strategy,
                    content_filter, cache_mode, css_selector, screenshot, pdf
                ]):
                    self.logger.warning(
                        message="Both crawler_config and legacy parameters provided. crawler_config will take precedence.",
                        tag="WARNING"
                    )
                config = crawler_config
            else:
                # Merge all parameters into a single kwargs dict for config creation
                config_kwargs = {
                    "word_count_threshold": word_count_threshold,
                    "extraction_strategy": extraction_strategy,
                    "chunking_strategy": chunking_strategy,
                    "content_filter": content_filter,
                    "cache_mode": cache_mode,
                    "bypass_cache": bypass_cache,
                    "css_selector": css_selector,
                    "screenshot": screenshot,
                    "pdf": pdf,
                    "verbose": verbose,
                    **kwargs
                }
                config = CrawlerRunConfig.from_kwargs(config_kwargs)

            if bypass_cache:
                if kwargs.get("warning", True):
                    warnings.warn(
                        "'bypass_cache' is deprecated and will be removed in version 0.5.0. "
                        "Use 'cache_mode=CacheMode.BYPASS' instead. "
                        "Pass warning=False to suppress this warning.",
                        DeprecationWarning,
                        stacklevel=2
                    )
                if config.cache_mode is None:
                    config.cache_mode = CacheMode.BYPASS

            semaphore_count = config.semaphore_count or 5
            semaphore = asyncio.Semaphore(semaphore_count)

            async def crawl_with_semaphore(url):
                # Handle rate limiting per domain
                domain = urlparse(url).netloc
                current_time = time.time()
                
                self.logger.debug(
                    message="Started task for {url:.50}...",
                    tag="PARALLEL",
                    params={"url": url}
                )

                # Get delay settings from config
                mean_delay = config.mean_delay
                max_range = config.max_range
                
                # Apply rate limiting
                if domain in self._domain_last_hit:
                    time_since_last = current_time - self._domain_last_hit[domain]
                    if time_since_last < mean_delay:
                        delay = mean_delay + random.uniform(0, max_range)
                        await asyncio.sleep(delay)
                
                self._domain_last_hit[domain] = current_time

                async with semaphore:
                    return await self.arun(
                        url,
                        crawler_config=config,  # Pass the entire config object
                        user_agent=user_agent  # Maintain user_agent override capability
                    )

            # Log start of concurrent crawling
            self.logger.info(
                message="Starting concurrent crawling for {count} URLs...",
                tag="INIT",
                params={"count": len(urls)}
            )

            # Execute concurrent crawls
            start_time = time.perf_counter()
            tasks = [crawl_with_semaphore(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.perf_counter()

            # Log completion
            self.logger.success(
                message="Concurrent crawling completed for {count} URLs | Total time: {timing}",
                tag="COMPLETE",
                params={
                    "count": len(urls),
                    "timing": f"{end_time - start_time:.2f}s"
                },
                colors={
                    "timing": Fore.YELLOW
                }
            )

            return [result if not isinstance(result, Exception) else str(result) for result in results]

    async def aclear_cache(self):
        """Clear the cache database."""
        await async_db_manager.cleanup()

    async def aflush_cache(self):
        """Flush the cache database."""
        await async_db_manager.aflush_db()

    async def aget_cache_size(self):
        """Get the total number of cached items."""
        return await async_db_manager.aget_total_count()


