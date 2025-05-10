from .__version__ import __version__ as crawl4ai_version
import os
import time
from colorama import Fore
from pathlib import Path
from typing import Optional, List, Self
import json
import asyncio

from contextlib import asynccontextmanager
from .models import CrawlResult, CrawlerTaskResult, MarkdownGenerationResult, DispatchResult, ScrapingResult, CrawlResultContainer
from .async_database import async_db_manager
from .chunking_strategy import IdentityChunking
from .async_crawler_strategy import (
    AsyncCrawlerStrategy,
    AsyncPlaywrightCrawlerStrategy,
    AsyncCrawlResponse,
)
from .cache_context import CacheMode, CacheContext
from .markdown_generation_strategy import (
    DefaultMarkdownGenerator,
    MarkdownGenerationStrategy,
)
from .deep_crawling import DeepCrawlDecorator
from .async_logger import AsyncLogger, AsyncLoggerBase
from .async_configs import BrowserConfig, CrawlerRunConfig
from .async_dispatcher import BaseDispatcher, MemoryAdaptiveDispatcher, RateLimiter

from .utils import (
    sanitize_input_encode,
    InvalidCSSSelectorError,
    fast_format_html,
    create_box_message,
    RobotsParser,
)

from typing import AsyncGenerator


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

    Attributes:
        browser_config (BrowserConfig): Configuration object for browser settings.
        crawler_strategy (AsyncCrawlerStrategy): Strategy for crawling web pages.
        logger (AsyncLogger): Logger instance for recording events and errors.
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
        base_directory: str = str(os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())),
        thread_safe: bool = False,
        logger: Optional[AsyncLoggerBase] = None,
        **kwargs,
    ):
        """
        Initialize the AsyncWebCrawler.

        Args:
            crawler_strategy: Strategy for crawling web pages. Default AsyncPlaywrightCrawlerStrategy
            config: Configuration object for browser settings. Default BrowserConfig()
            base_directory: Base directory for storing cache
            thread_safe: Whether to use thread-safe operations
            **kwargs: Additional arguments for backwards compatibility
        """
        # Handle browser configuration
        browser_config = config or BrowserConfig.from_kwargs(kwargs)

        self.browser_config = browser_config

        # Initialize logger first since other components may need it
        self.logger = logger or AsyncLogger(
            log_file=os.path.join(base_directory, ".crawl4ai", "crawler.log"),
            verbose=self.browser_config.verbose,
            tag_width=10,
        )

        # Initialize crawler strategy
        params = {k: v for k, v in kwargs.items() if k in ["browser_config", "logger"]}
        self.crawler_strategy = crawler_strategy or AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_config,
            logger=self.logger,
            **params,  # Pass remaining kwargs for backwards compatibility
        )

        # Thread safety setup
        self._lock = asyncio.Lock() if thread_safe else None

        # Initialize directories
        self.crawl4ai_folder = os.path.join(base_directory, ".crawl4ai")
        os.makedirs(self.crawl4ai_folder, exist_ok=True)
        os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)

        # Initialize robots parser
        self.robots_parser = RobotsParser()

        self.ready = False

        # Decorate arun method with deep crawling capabilities
        self._deep_handler = DeepCrawlDecorator(self)
        self.arun = self._deep_handler(self.arun)  

    async def start(self):
        """
        Start the crawler explicitly without using context manager.
        This is equivalent to using 'async with' but gives more control over the lifecycle.

        This method will:
        1. Check for builtin browser if browser_mode is 'builtin'
        2. Initialize the browser and context
        3. Perform warmup sequence
        4. Return the crawler instance for method chaining

        Returns:
            AsyncWebCrawler: The initialized crawler instance
        """
        # Check for builtin browser if requested
        if self.browser_config.browser_mode == "builtin" and not self.browser_config.cdp_url:
            # Import here to avoid circular imports
            from .browser_profiler import BrowserProfiler
            profiler = BrowserProfiler(logger=self.logger)
            
            # Get builtin browser info or launch if needed
            browser_info = profiler.get_builtin_browser_info()
            if not browser_info:
                self.logger.info("Builtin browser not found, launching new instance...", tag="BROWSER")
                cdp_url = await profiler.launch_builtin_browser()
                if not cdp_url:
                    self.logger.warning("Failed to launch builtin browser, falling back to dedicated browser", tag="BROWSER")
                else:
                    self.browser_config.cdp_url = cdp_url
                    self.browser_config.use_managed_browser = True
            else:
                self.logger.info(f"Using existing builtin browser at {browser_info.get('cdp_url')}", tag="BROWSER")
                self.browser_config.cdp_url = browser_info.get('cdp_url')
                self.browser_config.use_managed_browser = True
                
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

    async def __aenter__(self) -> Self:
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
        """Async void context manager."""
        yield

    async def arun(
        self,
        url: str,
        config: Optional[CrawlerRunConfig] = None,
        **kwargs,
    ) -> CrawlResultContainer:
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


        If `config.stream` is True it returns a `CrawlResultContainer` which wraps an async generator.

        Example:

            async for result in crawl_result:
                print(result.markdown)

        If `config.stream` is `False` and `config.deep_crawl_strategy` is `None` then the
        `CrawlResultContainer` will contain a single `CrawlResult` which can be accessed directly.

        Example:

            result = await crawler.arun(url="https://example.com", config=config)
            print(result.markdown)

        Otherwise it will contain a list of CrawlResult objects.

        Example:

            for result in crawl_result:
                print(result.markdown)

        If `config.deep_crawl_strategy` is not `None` it returns a `CrawlResultContainer` which can
        contain multiple `CrawlResult` objects.

        Args:
            url (str): The URL to crawl (http://, https://, file://, or raw:)
            crawler_config (Optional[CrawlerRunConfig]): Configuration object controlling crawl behavior
            [other parameters maintained for backwards compatibility]

        Returns:
            CrawlResultContainer: The result of crawling and processing
        """
        # Auto-start if not ready
        if not self.ready:
            await self.start()

        config = config or CrawlerRunConfig.from_kwargs(kwargs)
        if not isinstance(url, str) or not url:
            raise ValueError("Invalid URL, make sure the URL is a non-empty string")

        async with self._lock or self.nullcontext():
            try:
                self.logger.verbose = config.verbose

                # Default to ENABLED if no cache mode specified
                if config.cache_mode is None:
                    config.cache_mode = CacheMode.ENABLED

                # Create cache context
                cache_context = CacheContext(
                    url, config.cache_mode, False
                )

                # Initialize processing variables
                async_response: Optional[AsyncCrawlResponse] = None
                cached_result: Optional[CrawlResult] = None
                screenshot_data = None
                pdf_data = None
                extracted_content = None
                start_time = time.perf_counter()

                # Try to get cached result if appropriate
                if cache_context.should_read():
                    cached_result = await async_db_manager.aget_cached_url(url)

                html: str = ""
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
                    # if config.screenshot and not screenshot or config.pdf and not pdf:
                    if config.screenshot and not screenshot_data:
                        cached_result = None
                    
                    if config.pdf and not pdf_data:
                        cached_result = None

                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=bool(html),
                        timing=time.perf_counter() - start_time,
                        tag="FETCH",
                    )

                # Update proxy configuration from rotation strategy if available
                if config and config.proxy_rotation_strategy:
                    next_proxy = await config.proxy_rotation_strategy.get_next_proxy()
                    if next_proxy:
                        self.logger.info(
                            message="Switch proxy: {proxy}",
                            tag="PROXY",
                            params={"proxy": next_proxy.server},
                        )
                        config.proxy_config = next_proxy
                        # config = config.clone(proxy_config=next_proxy)

                # Fetch fresh content if needed
                if not cached_result or not html:
                    t1 = time.perf_counter()

                    if config.user_agent:
                        self.crawler_strategy.update_user_agent(config.user_agent)

                    # Check robots.txt if enabled
                    if config and config.check_robots_txt:
                        if not await self.robots_parser.can_fetch(url, self.browser_config.user_agent):
                            return CrawlResultContainer(CrawlResult(
                                url=url,
                                html="",
                                success=False,
                                status_code=403,
                                error_message="Access denied by robots.txt",
                                response_headers={"X-Robots-Status": "Blocked by robots.txt"}
                            ))

                    ##############################
                    # Call CrawlerStrategy.crawl #
                    ##############################
                    async_response = await self.crawler_strategy.crawl(
                        url,
                        config=config,  # Pass the entire config object
                        **kwargs,
                    )

                    html = sanitize_input_encode(async_response.html)
                    screenshot_data = async_response.screenshot
                    pdf_data = async_response.pdf_data
                    js_execution_result = async_response.js_execution_result

                    t2 = time.perf_counter()
                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=bool(html),
                        timing=t2 - t1,
                        tag="FETCH",
                    )

                    ###############################################################
                    # Process the HTML content, Call CrawlerStrategy.process_html #
                    ###############################################################
                    if "screenshot" in kwargs:
                        del kwargs["screenshot"]

                    crawl_result: CrawlResult = await self.aprocess_html(
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
                    crawl_result.js_execution_result = js_execution_result
                    crawl_result.ssl_certificate = (
                        async_response.ssl_certificate
                    )  # Add SSL certificate

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

                    return CrawlResultContainer(crawl_result)

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
                    return CrawlResultContainer(cached_result)

            except Exception:
                import traceback
                error_message = traceback.format_exc()

                self.logger.error_status(
                    url=url,
                    error=create_box_message(error_message, type="error"),
                    tag="ERROR",
                )

                return CrawlResultContainer(
                    CrawlResult(
                        url=url, html="", success=False, error_message=error_message
                    )
                )

    async def aprocess_html(
        self,
        url: str,
        html: str,
        extracted_content: Optional[str],
        config: CrawlerRunConfig,
        screenshot: Optional[str],
        pdf_data: Optional[bytes],
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

        Raises:
            ValueError: If processing fails
        """
        cleaned_html = ""
        try:
            _url = url if not kwargs.get("is_raw_html", False) else "Raw HTML"
            t1 = time.perf_counter()

            # Get scraping strategy and ensure it has a logger
            scraping_strategy = config.scraping_strategy
            if not scraping_strategy.logger:
                scraping_strategy.logger = self.logger

            # Process HTML content
            params = config.__dict__.copy()
            params.pop("url", None)            
            # add keys from kwargs to params that doesn't exist in params
            params.update({k: v for k, v in kwargs.items() if k not in params.keys()})

            
            ################################
            # Scraping Strategy Execution  #
            ################################
            result : ScrapingResult = scraping_strategy.scrap(url, html, **params)

            if result is None:
                raise ValueError(
                    f"Process HTML, Failed to extract content from the website: {url}"
                )

        except InvalidCSSSelectorError as e:
            raise ValueError from e
        except ValueError:
            raise
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

        ################################
        # Generate Markdown            #
        ################################
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

        # Log processing completion
        self.logger.info(
            message="{url:.50}... | Time: {timing}s",
            tag="SCRAPE",
            params={"url": _url, "timing": int((time.perf_counter() - t1) * 1000) / 1000},
        )

        #################################
        # Structured Content Extraction #
        #################################
        if not extracted_content and config.extraction_strategy:
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
                "markdown": markdown_result.raw_markdown,
                "html": html,
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
            extracted_content = json.dumps(
                config.extraction_strategy.run(url, sections),
                indent=4,
                default=str,
                ensure_ascii=False,
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
            markdown=markdown_result,
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
        # word_count_threshold=MIN_WORD_THRESHOLD,
        # extraction_strategy: ExtractionStrategy = None,
        # chunking_strategy: ChunkingStrategy = RegexChunking(),
        # content_filter: RelevantContentFilter = None,
        # cache_mode: Optional[CacheMode] = None,
        # bypass_cache: bool = False,
        # css_selector: str = None,
        # screenshot: bool = False,
        # pdf: bool = False,
        # user_agent: str = None,
        # verbose=True,
        **kwargs,
    ) -> CrawlResultContainer:
        """
        Runs the crawler for multiple URLs concurrently using a configurable dispatcher strategy.

        Args:
        urls: List of URLs to crawl
        config: Configuration object controlling crawl behavior for all URLs
        dispatcher: The dispatcher strategy instance to use. Defaults to MemoryAdaptiveDispatcher
        [other parameters maintained for backwards compatibility]

        Returns:
        CrawlResultContainer:
            A container which encapsulates a list of all results for none streaming requests or
            an async generator yielding results for streaming requests.

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
        config = config or CrawlerRunConfig.from_kwargs(kwargs)

        if dispatcher is None:
            dispatcher = MemoryAdaptiveDispatcher(
                rate_limiter=RateLimiter(
                    base_delay=1.0, max_delay=60.0, max_retries=3, max_burst=3
                ),
            )

        def transform_result(task_result: CrawlerTaskResult) -> CrawlResult:
            """Transform a CrawlerTaskResult into a CrawlResult.

            Attaches the dispatch result to the CrawlResult.

            Args:
                task_result (CrawlerTaskResult): The task result to transform.
            Returns:
                CrawlResult: The transformed crawl result.
            Raises:
                ValueError: If the task result does not contain exactly one result.
            """
            results: CrawlResultContainer = task_result.result
            if len(results) != 1:
                raise ValueError(
                    f"Expected a single result, but got {len(results)} results."
                )

            result: CrawlResult = results[0]
            result.dispatch_result = DispatchResult(
                task_id=task_result.task_id,
                memory_usage=task_result.memory_usage,
                peak_memory=task_result.peak_memory,
                start_time=task_result.start_time,
                end_time=task_result.end_time,
                error_message=task_result.error_message,
            )

            return result

        if config.stream:
            async def result_transformer() -> AsyncGenerator[CrawlResult, None]:
                async for task_result in dispatcher.run_urls_stream(
                    urls=urls, crawler=self, config=config
                ):
                    yield transform_result(task_result)

            return CrawlResultContainer(result_transformer())

        _results = await dispatcher.run_urls(urls=urls, crawler=self, config=config)
        return CrawlResultContainer([transform_result(res) for res in _results])

    async def aclear_cache(self):
        """Clear the cache database."""
        await async_db_manager.aclear_db()

    async def aflush_cache(self):
        """Flush the cache database."""
        await async_db_manager.aflush_db()

    async def aget_cache_size(self):
        """Get the total number of cached items."""
        return await async_db_manager.aget_total_count()
