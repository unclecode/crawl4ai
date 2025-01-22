import os
import sys
import time
import warnings
from colorama import Fore
from pathlib import Path
from typing import Optional, List
import json
import asyncio

# from contextlib import nullcontext, asynccontextmanager
from contextlib import asynccontextmanager
from .models import CrawlResult, MarkdownGenerationResult, CrawlerTaskResult, DispatchResult
from .async_database import async_db_manager
from .chunking_strategy import *  # noqa: F403
from .chunking_strategy import RegexChunking, ChunkingStrategy, IdentityChunking
from .content_filter_strategy import *  # noqa: F403
from .content_filter_strategy import RelevantContentFilter
from .extraction_strategy import * # noqa: F403
from .extraction_strategy import NoExtractionStrategy, ExtractionStrategy
from .async_crawler_strategy import (
    AsyncCrawlerStrategy,
    AsyncPlaywrightCrawlerStrategy,
    AsyncCrawlResponse,
)
from .cache_context import CacheMode, CacheContext, _legacy_to_cache_mode
from .markdown_generation_strategy import (
    DefaultMarkdownGenerator,
    MarkdownGenerationStrategy,
)
from .async_logger import AsyncLogger
from .async_configs import BrowserConfig, CrawlerRunConfig
from .async_dispatcher import * # noqa: F403
from .async_dispatcher import BaseDispatcher, MemoryAdaptiveDispatcher, RateLimiter

from .config import MIN_WORD_THRESHOLD
from .utils import (
    sanitize_input_encode,
    InvalidCSSSelectorError,
    fast_format_html,
    create_box_message,
    get_error_context,
    RobotsParser,
)

from typing import Union, AsyncGenerator, List, TypeVar
from collections.abc import AsyncGenerator

CrawlResultT = TypeVar('CrawlResultT', bound=CrawlResult)
RunManyReturn = Union[List[CrawlResultT], AsyncGenerator[CrawlResultT, None]]

from .__version__ import __version__ as crawl4ai_version


class AsyncWebCrawler:
    """
    Asynchronous web crawler with flexible caching capabilities.

    There are two ways to use the crawler:

    1. Using context manager (recommended for simple cases):
        ```python
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url="https://example.com")
        ```

    2. Using explicit lifecycle management (recommended for long-running applications):
        ```python
        crawler = AsyncWebCrawler()
        await crawler.start()

        # Use the crawler multiple times
        result1 = await crawler.arun(url="https://example.com")
        result2 = await crawler.arun(url="https://another.com")

        await crawler.close()
        ```

    Migration Guide:
    Old way (deprecated):
        crawler = AsyncWebCrawler(always_by_pass_cache=True, browser_type="chromium", headless=True)

    New way (recommended):
        browser_config = BrowserConfig(browser_type="chromium", headless=True)
        crawler = AsyncWebCrawler(config=browser_config)


    Attributes:
        browser_config (BrowserConfig): Configuration object for browser settings.
        crawler_strategy (AsyncCrawlerStrategy): Strategy for crawling web pages.
        logger (AsyncLogger): Logger instance for recording events and errors.
        always_bypass_cache (bool): Whether to always bypass cache.
        crawl4ai_folder (str): Directory for storing cache.
        base_directory (str): Base directory for storing cache.
        ready (bool): Whether the crawler is ready for use.

        Methods:
            start(): Start the crawler explicitly without using context manager.
            close(): Close the crawler explicitly without using context manager.
            arun(): Run the crawler for a single source: URL (web, local file, or raw HTML).
            awarmup(): Perform warmup sequence.
            arun_many(): Run the crawler for multiple sources.
            aprocess_html(): Process HTML content.

    Typical Usage:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url="https://example.com")
            print(result.markdown)

        Using configuration:
        browser_config = BrowserConfig(browser_type="chromium", headless=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS
            )
            result = await crawler.arun(url="https://example.com", config=crawler_config)
            print(result.markdown)
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
        if browser_config is not None:
            if any(
                k in kwargs
                for k in [
                    "browser_type",
                    "headless",
                    "viewport_width",
                    "viewport_height",
                ]
            ):
                self.logger.warning(
                    message="Both browser_config and legacy browser parameters provided. browser_config will take precedence.",
                    tag="WARNING",
                )
        else:
            # Create browser config from kwargs for backwards compatibility
            browser_config = BrowserConfig.from_kwargs(kwargs)

        self.browser_config = browser_config

        # Initialize logger first since other components may need it
        self.logger = AsyncLogger(
            log_file=os.path.join(base_directory, ".crawl4ai", "crawler.log"),
            verbose=self.browser_config.verbose,
            tag_width=10,
        )

        # Initialize crawler strategy
        params = {k: v for k, v in kwargs.items() if k in ["browser_congig", "logger"]}
        self.crawler_strategy = crawler_strategy or AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_config,
            logger=self.logger,
            **params,  # Pass remaining kwargs for backwards compatibility
        )

        # If craweler strategy doesnt have logger, use crawler logger
        if not self.crawler_strategy.logger:
            self.crawler_strategy.logger = self.logger

        # Handle deprecated cache parameter
        if always_by_pass_cache is not None:
            if kwargs.get("warning", True):
                warnings.warn(
                    "'always_by_pass_cache' is deprecated and will be removed in version 0.5.0. "
                    "Use 'always_bypass_cache' instead. "
                    "Pass warning=False to suppress this warning.",
                    DeprecationWarning,
                    stacklevel=2,
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

        # Initialize robots parser
        self.robots_parser = RobotsParser()

        self.ready = False

    async def start(self):
        """
        Start the crawler explicitly without using context manager.
        This is equivalent to using 'async with' but gives more control over the lifecycle.

        This method will:
        1. Initialize the browser and context
        2. Perform warmup sequence
        3. Return the crawler instance for method chaining

        Returns:
            AsyncWebCrawler: The initialized crawler instance
        """
        await self.crawler_strategy.__aenter__()
        await self.awarmup()
        return self

    async def close(self):
        """
        Close the crawler explicitly without using context manager.
        This should be called when you're done with the crawler if you used start().

        This method will:
        1. Clean up browser resources
        2. Close any open pages and contexts
        """
        await self.crawler_strategy.__aexit__(None, None, None)

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def awarmup(self):
        """
        Initialize the crawler with warm-up sequence.

        This method:
        1. Logs initialization info
        2. Sets up browser configuration
        3. Marks the crawler as ready
        """
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
                    # if any(param is not None for param in [
                    #     word_count_threshold, extraction_strategy, chunking_strategy,
                    #     content_filter, cache_mode, css_selector, screenshot, pdf
                    # ]):
                    #     self.logger.warning(
                    #         message="Both crawler_config and legacy parameters provided. crawler_config will take precedence.",
                    #         tag="WARNING"
                    #     )
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
                        **kwargs,
                    }
                    config = CrawlerRunConfig.from_kwargs(config_kwargs)

                # Handle deprecated cache parameters
                if any([bypass_cache, disable_cache, no_cache_read, no_cache_write]):
                    if kwargs.get("warning", True):
                        warnings.warn(
                            "Cache control boolean flags are deprecated and will be removed in version 0.5.0. "
                            "Use 'cache_mode' parameter instead.",
                            DeprecationWarning,
                            stacklevel=2,
                        )

                    # Convert legacy parameters if cache_mode not provided
                    if config.cache_mode is None:
                        config.cache_mode = _legacy_to_cache_mode(
                            disable_cache=disable_cache,
                            bypass_cache=bypass_cache,
                            no_cache_read=no_cache_read,
                            no_cache_write=no_cache_write,
                        )

                # Default to ENABLED if no cache mode specified
                if config.cache_mode is None:
                    config.cache_mode = CacheMode.ENABLED

                # Create cache context
                cache_context = CacheContext(
                    url, config.cache_mode, self.always_bypass_cache
                )

                # Initialize processing variables
                async_response: AsyncCrawlResponse = None
                cached_result: CrawlResult = None
                screenshot_data = None
                pdf_data = None
                extracted_content = None
                start_time = time.perf_counter()

                # Try to get cached result if appropriate
                if cache_context.should_read():
                    cached_result = await async_db_manager.aget_cached_url(url)

                if cached_result:
                    html = sanitize_input_encode(cached_result.html)
                    extracted_content = sanitize_input_encode(
                        cached_result.extracted_content or ""
                    )
                    extracted_content = (
                        None
                        if not extracted_content or extracted_content == "[]"
                        else extracted_content
                    )
                    # If screenshot is requested but its not in cache, then set cache_result to None
                    screenshot_data = cached_result.screenshot
                    pdf_data = cached_result.pdf
                    if config.screenshot and not screenshot or config.pdf and not pdf:
                        cached_result = None

                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=bool(html),
                        timing=time.perf_counter() - start_time,
                        tag="FETCH",
                    )

                # Fetch fresh content if needed
                if not cached_result or not html:
                    t1 = time.perf_counter()

                    if user_agent:
                        self.crawler_strategy.update_user_agent(user_agent)

                    # Check robots.txt if enabled
                    if config and config.check_robots_txt:
                        if not await self.robots_parser.can_fetch(url, self.browser_config.user_agent):
                            return CrawlResult(
                                url=url,
                                html="",
                                success=False,
                                status_code=403,
                                error_message="Access denied by robots.txt",
                                response_headers={"X-Robots-Status": "Blocked by robots.txt"}
                            )

                    # Pass config to crawl method
                    async_response = await self.crawler_strategy.crawl(
                        url,
                        config=config,  # Pass the entire config object
                    )

                    html = sanitize_input_encode(async_response.html)
                    screenshot_data = async_response.screenshot
                    pdf_data = async_response.pdf_data

                    t2 = time.perf_counter()
                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=bool(html),
                        timing=t2 - t1,
                        tag="FETCH",
                    )

                    # Process the HTML content
                    crawl_result : CrawlResult = await self.aprocess_html(
                        url=url,
                        html=html,
                        extracted_content=extracted_content,
                        config=config,  # Pass the config object instead of individual parameters
                        screenshot=screenshot_data,
                        pdf_data=pdf_data,
                        verbose=config.verbose,
                        is_raw_html=True if url.startswith("raw:") else False,
                        **kwargs,
                    )

                    crawl_result.status_code = async_response.status_code
                    crawl_result.redirected_url = async_response.redirected_url or url
                    crawl_result.response_headers = async_response.response_headers
                    crawl_result.downloaded_files = async_response.downloaded_files
                    crawl_result.ssl_certificate = (
                        async_response.ssl_certificate
                    )  # Add SSL certificate

                    # # Check and set values from async_response to crawl_result
                    # try:
                    #     for key in vars(async_response):
                    #         if hasattr(crawl_result, key):
                    #             value = getattr(async_response, key, None)
                    #             current_value = getattr(crawl_result, key, None)
                    #             if value is not None and not current_value:
                    #                 try:
                    #                     setattr(crawl_result, key, value)
                    #                 except Exception as e:
                    #                     self.logger.warning(
                    #                         message=f"Failed to set attribute {key}: {str(e)}",
                    #                         tag="WARNING"
                    #                     )
                    # except Exception as e:
                    #     self.logger.warning(
                    #         message=f"Error copying response attributes: {str(e)}",
                    #         tag="WARNING"
                    #     )

                    crawl_result.success = bool(html)
                    crawl_result.session_id = getattr(config, "session_id", None)

                    self.logger.success(
                        message="{url:.50}... | Status: {status} | Total: {timing}",
                        tag="COMPLETE",
                        params={
                            "url": cache_context.display_url,
                            "status": crawl_result.success,
                            "timing": f"{time.perf_counter() - start_time:.2f}s",
                        },
                        colors={
                            "status": Fore.GREEN if crawl_result.success else Fore.RED,
                            "timing": Fore.YELLOW,
                        },
                    )

                    # Update cache if appropriate
                    if cache_context.should_write() and not bool(cached_result):
                        await async_db_manager.acache_url(crawl_result)

                    return crawl_result

                else:
                    self.logger.success(
                        message="{url:.50}... | Status: {status} | Total: {timing}",
                        tag="COMPLETE",
                        params={
                            "url": cache_context.display_url,
                            "status": True,
                            "timing": f"{time.perf_counter() - start_time:.2f}s",
                        },
                        colors={"status": Fore.GREEN, "timing": Fore.YELLOW},
                    )

                    cached_result.success = bool(html)
                    cached_result.session_id = getattr(config, "session_id", None)
                    cached_result.redirected_url = cached_result.redirected_url or url
                    return cached_result

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
                    tag="ERROR",
                )

                return CrawlResult(
                    url=url, html="", success=False, error_message=error_message
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
            pdf_data: PDF data (if any)
            verbose: Whether to enable verbose logging
            **kwargs: Additional parameters for backwards compatibility

        Returns:
            CrawlResult: Processed result containing extracted and formatted content
        """
        try:
            _url = url if not kwargs.get("is_raw_html", False) else "Raw HTML"
            t1 = time.perf_counter()

            # Get scraping strategy and ensure it has a logger
            scraping_strategy = config.scraping_strategy
            if not scraping_strategy.logger:
                scraping_strategy.logger = self.logger

            # Process HTML content
            params = {k: v for k, v in config.to_dict().items() if k not in ["url"]}
            # add keys from kwargs to params that doesn't exist in params
            params.update({k: v for k, v in kwargs.items() if k not in params.keys()})

            result = scraping_strategy.scrap(url, html, **params)

            if result is None:
                raise ValueError(
                    f"Process HTML, Failed to extract content from the website: {url}"
                )

        except InvalidCSSSelectorError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(
                f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}"
            )

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

        # Markdown Generation
        markdown_generator: Optional[MarkdownGenerationStrategy] = (
            config.markdown_generator or DefaultMarkdownGenerator()
        )

        # Uncomment if by default we want to use PruningContentFilter
        # if not config.content_filter and not markdown_generator.content_filter:
        #     markdown_generator.content_filter = PruningContentFilter()

        markdown_result: MarkdownGenerationResult = (
            markdown_generator.generate_markdown(
                cleaned_html=cleaned_html,
                base_url=url,
                # html2text_options=kwargs.get('html2text', {})
            )
        )
        markdown_v2 = markdown_result
        markdown = sanitize_input_encode(markdown_result.raw_markdown)

        # Log processing completion
        self.logger.info(
            message="Processed {url:.50}... | Time: {timing}ms",
            tag="SCRAPE",
            params={"url": _url, "timing": int((time.perf_counter() - t1) * 1000)},
        )

        # Handle content extraction if needed
        if (
            not bool(extracted_content)
            and config.extraction_strategy
            and not isinstance(config.extraction_strategy, NoExtractionStrategy)
        ):
            t1 = time.perf_counter()

            # Choose content based on input_format
            content_format = config.extraction_strategy.input_format
            if content_format == "fit_markdown" and not markdown_result.fit_markdown:
                self.logger.warning(
                    message="Fit markdown requested but not available. Falling back to raw markdown.",
                    tag="EXTRACT",
                    params={"url": _url},
                )
                content_format = "markdown"

            content = {
                "markdown": markdown,
                "html": html,
                "fit_markdown": markdown_result.raw_markdown,
            }.get(content_format, markdown)

            # Use IdentityChunking for HTML input, otherwise use provided chunking strategy
            chunking = (
                IdentityChunking()
                if content_format == "html"
                else config.chunking_strategy
            )
            sections = chunking.chunk(content)
            extracted_content = config.extraction_strategy.run(url, sections)
            extracted_content = json.dumps(
                extracted_content, indent=4, default=str, ensure_ascii=False
            )

            # Log extraction completion
            self.logger.info(
                message="Completed for {url:.50}... | Time: {timing}s",
                tag="EXTRACT",
                params={"url": _url, "timing": time.perf_counter() - t1},
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
            fit_markdown=markdown_result.fit_markdown,
            fit_html=markdown_result.fit_html,
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
        dispatcher: Optional[BaseDispatcher] = None,
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
        **kwargs
        ) -> RunManyReturn:
        """
        Runs the crawler for multiple URLs concurrently using a configurable dispatcher strategy.

        Args:
        urls: List of URLs to crawl
        config: Configuration object controlling crawl behavior for all URLs
        dispatcher: The dispatcher strategy instance to use. Defaults to MemoryAdaptiveDispatcher
        [other parameters maintained for backwards compatibility]

        Returns:
        Union[List[CrawlResult], AsyncGenerator[CrawlResult, None]]:
            Either a list of all results or an async generator yielding results

        Examples:

        # Batch processing (default)
        results = await crawler.arun_many(
            urls=["https://example1.com", "https://example2.com"],
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        for result in results:
            print(f"Processed {result.url}: {len(result.markdown)} chars")

        # Streaming results
        async for result in await crawler.arun_many(
            urls=["https://example1.com", "https://example2.com"],
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=True),
        ):
            print(f"Processed {result.url}: {len(result.markdown)} chars")
        """
        if config is None:
            config = CrawlerRunConfig(
                word_count_threshold=word_count_threshold,
                extraction_strategy=extraction_strategy,
                chunking_strategy=chunking_strategy,
                content_filter=content_filter,
                cache_mode=cache_mode,
                bypass_cache=bypass_cache,
                css_selector=css_selector,
                screenshot=screenshot,
                pdf=pdf,
                verbose=verbose,
                **kwargs,
            )

        if dispatcher is None:
            dispatcher = MemoryAdaptiveDispatcher(
                rate_limiter=RateLimiter(
                    base_delay=(1.0, 3.0), max_delay=60.0, max_retries=3
                ),
            )

        transform_result = lambda task_result: (
            setattr(task_result.result, 'dispatch_result', 
                DispatchResult(
                    task_id=task_result.task_id,
                    memory_usage=task_result.memory_usage,
                    peak_memory=task_result.peak_memory,
                    start_time=task_result.start_time,
                    end_time=task_result.end_time,
                    error_message=task_result.error_message,
                )
            ) or task_result.result
        )

        stream = config.stream
        
        if stream:
            async def result_transformer():
                async for task_result in dispatcher.run_urls_stream(crawler=self, urls=urls, config=config):
                    yield transform_result(task_result)
            return result_transformer()
        else:
            _results = await dispatcher.run_urls(crawler=self, urls=urls, config=config)
            return [transform_result(res) for res in _results]    

    async def aclear_cache(self):
        """Clear the cache database."""
        await async_db_manager.cleanup()

    async def aflush_cache(self):
        """Flush the cache database."""
        await async_db_manager.aflush_db()

    async def aget_cache_size(self):
        """Get the total number of cached items."""
        return await async_db_manager.aget_total_count()
