from .__version__ import __version__ as crawl4ai_version
import os
import sys
import time
from pathlib import Path
from typing import Optional, List
import json
import asyncio

# from contextlib import nullcontext, asynccontextmanager
from contextlib import asynccontextmanager
from .models import (
    CrawlResult,
    MarkdownGenerationResult,
    DispatchResult,
    ScrapingResult,
    CrawlResultContainer,
    RunManyReturn
)
from .async_database import async_db_manager
from .chunking_strategy import *  # noqa: F403
from .chunking_strategy import IdentityChunking
from .content_filter_strategy import *  # noqa: F403
from .extraction_strategy import *  # noqa: F403
from .extraction_strategy import NoExtractionStrategy
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
from .async_configs import BrowserConfig, CrawlerRunConfig, ProxyConfig, SeedingConfig
from .async_dispatcher import *  # noqa: F403
from .async_dispatcher import BaseDispatcher, MemoryAdaptiveDispatcher, RateLimiter
from .async_url_seeder import AsyncUrlSeeder

from .utils import (
    sanitize_input_encode,
    InvalidCSSSelectorError,
    fast_format_html,
    get_error_context,
    RobotsParser,
    preprocess_html_for_schema,
)


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
        crawler_strategy: AsyncCrawlerStrategy = None,
        config: BrowserConfig = None,
        base_directory: str = str(
            os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())),
        thread_safe: bool = False,
        logger: AsyncLoggerBase = None,
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
        browser_config = config or BrowserConfig()

        self.browser_config = browser_config

        # Initialize logger first since other components may need it
        self.logger = logger or AsyncLogger(
            log_file=os.path.join(base_directory, ".crawl4ai", "crawler.log"),
            verbose=self.browser_config.verbose,
            tag_width=10,
        )

        # Initialize crawler strategy
        params = {k: v for k, v in kwargs.items() if k in [
            "browser_config", "logger"]}
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
        
        self.url_seeder: Optional[AsyncUrlSeeder] = None

    async def start(self):
        """
        Start the crawler explicitly without using context manager.
        This is equivalent to using 'async with' but gives more control over the lifecycle.
        Returns:
            AsyncWebCrawler: The initialized crawler instance
        """
        await self.crawler_strategy.__aenter__()
        self.logger.info(f"Crawl4AI {crawl4ai_version}", tag="INIT")
        self.ready = True
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

    @asynccontextmanager
    async def nullcontext(self):
        """异步空上下文管理器"""
        yield

    async def arun(
        self,
        url: str,
        config: CrawlerRunConfig = None,
        **kwargs,
    ) -> RunManyReturn:
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
        # Auto-start if not ready
        if not self.ready:
            await self.start()

        config = config or CrawlerRunConfig()
        if not isinstance(url, str) or not url:
            raise ValueError(
                "Invalid URL, make sure the URL is a non-empty string")

        async with self._lock or self.nullcontext():
            try:
                self.logger.verbose = config.verbose

                # Default to ENABLED if no cache mode specified
                if config.cache_mode is None:
                    config.cache_mode = CacheMode.ENABLED

                # Create cache context
                cache_context = CacheContext(url, config.cache_mode, False)

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
                    next_proxy: ProxyConfig = await config.proxy_rotation_strategy.get_next_proxy()
                    if next_proxy:
                        self.logger.info(
                            message="Switch proxy: {proxy}",
                            tag="PROXY",
                            params={"proxy": next_proxy.server}
                        )
                        config.proxy_config = next_proxy
                        # config = config.clone(proxy_config=next_proxy)

                # Fetch fresh content if needed
                if not cached_result or not html:
                    t1 = time.perf_counter()

                    if config.user_agent:
                        self.crawler_strategy.update_user_agent(
                            config.user_agent)

                    # Check robots.txt if enabled
                    if config and config.check_robots_txt:
                        if not await self.robots_parser.can_fetch(
                            url, self.browser_config.user_agent
                        ):
                            return CrawlResult(
                                url=url,
                                html="",
                                success=False,
                                status_code=403,
                                error_message="Access denied by robots.txt",
                                response_headers={
                                    "X-Robots-Status": "Blocked by robots.txt"
                                },
                            )

                    ##############################
                    # Call CrawlerStrategy.crawl #
                    ##############################
                    async_response = await self.crawler_strategy.crawl(
                        url,
                        config=config,  # Pass the entire config object
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
                    crawl_result: CrawlResult = await self.aprocess_html(
                        url=url,
                        html=html,
                        extracted_content=extracted_content,
                        config=config,  # Pass the config object instead of individual parameters
                        screenshot_data=screenshot_data,
                        pdf_data=pdf_data,
                        verbose=config.verbose,
                        is_raw_html=True if url.startswith("raw:") else False,
                        redirected_url=async_response.redirected_url,
                        **kwargs,
                    )

                    crawl_result.status_code = async_response.status_code
                    crawl_result.redirected_url = async_response.redirected_url or url
                    crawl_result.response_headers = async_response.response_headers
                    crawl_result.downloaded_files = async_response.downloaded_files
                    crawl_result.js_execution_result = js_execution_result
                    crawl_result.mhtml = async_response.mhtml_data
                    crawl_result.ssl_certificate = async_response.ssl_certificate
                    # Add captured network and console data if available
                    crawl_result.network_requests = async_response.network_requests
                    crawl_result.console_messages = async_response.console_messages

                    crawl_result.success = bool(html)
                    crawl_result.session_id = getattr(
                        config, "session_id", None)

                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=crawl_result.success,
                        timing=time.perf_counter() - start_time,
                        tag="COMPLETE",
                    )

                    # Update cache if appropriate
                    if cache_context.should_write() and not bool(cached_result):
                        await async_db_manager.acache_url(crawl_result)

                    return CrawlResultContainer(crawl_result)

                else:
                    self.logger.url_status(
                        url=cache_context.display_url,
                        success=True,
                        timing=time.perf_counter() - start_time,
                        tag="COMPLETE"
                    )
                    cached_result.success = bool(html)
                    cached_result.session_id = getattr(
                        config, "session_id", None)
                    cached_result.redirected_url = cached_result.redirected_url or url
                    return CrawlResultContainer(cached_result)

            except Exception as e:
                error_context = get_error_context(sys.exc_info())

                error_message = (
                    f"Unexpected error in _crawl_web at line {error_context['line_no']} "
                    f"in {error_context['function']} ({error_context['filename']}):\n"
                    f"Error: {str(e)}\n\n"
                    f"Code context:\n{error_context['code_context']}"
                )

                self.logger.error_status(
                    url=url,
                    error=error_message,
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
        extracted_content: str,
        config: CrawlerRunConfig,
        screenshot_data: str,
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
            screenshot_data: Screenshot data (if any)
            pdf_data: PDF data (if any)
            verbose: Whether to enable verbose logging
            **kwargs: Additional parameters for backwards compatibility

        Returns:
            CrawlResult: Processed result containing extracted and formatted content
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
            params.update({k: v for k, v in kwargs.items()
                          if k not in params.keys()})

            ################################
            # Scraping Strategy Execution  #
            ################################
            result: ScrapingResult = scraping_strategy.scrap(
                url, html, **params)

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
            cleaned_html = sanitize_input_encode(
                result.get("cleaned_html", ""))
            media = result.get("media", {})
            tables = media.pop("tables", []) if isinstance(media, dict) else []
            links = result.get("links", {})
            metadata = result.get("metadata", {})
        else:
            cleaned_html = sanitize_input_encode(result.cleaned_html)
            # media = result.media.model_dump()
            # tables = media.pop("tables", [])
            # links = result.links.model_dump()
            media = result.media.model_dump() if hasattr(result.media, 'model_dump') else result.media
            tables = media.pop("tables", []) if isinstance(media, dict) else []
            links = result.links.model_dump() if hasattr(result.links, 'model_dump') else result.links
            metadata = result.metadata

        fit_html = preprocess_html_for_schema(html_content=html, text_threshold= 500, max_size= 300_000)

        ################################
        # Generate Markdown            #
        ################################
        markdown_generator: Optional[MarkdownGenerationStrategy] = (
            config.markdown_generator or DefaultMarkdownGenerator()
        )

        # --- SELECT HTML SOURCE BASED ON CONTENT_SOURCE ---
        # Get the desired source from the generator config, default to 'cleaned_html'
        selected_html_source = getattr(markdown_generator, 'content_source', 'cleaned_html')

        # Define the source selection logic using dict dispatch
        html_source_selector = {
            "raw_html": lambda: html,  # The original raw HTML
            "cleaned_html": lambda: cleaned_html,  # The HTML after scraping strategy
            "fit_html": lambda: fit_html,  # The HTML after preprocessing for schema
        }

        markdown_input_html = cleaned_html  # Default to cleaned_html

        try:
            # Get the appropriate lambda function, default to returning cleaned_html if key not found
            source_lambda = html_source_selector.get(selected_html_source, lambda: cleaned_html)
            # Execute the lambda to get the selected HTML
            markdown_input_html = source_lambda()

            # Log which source is being used (optional, but helpful for debugging)
            # if self.logger and verbose:
            #     actual_source_used = selected_html_source if selected_html_source in html_source_selector else 'cleaned_html (default)'
            #     self.logger.debug(f"Using '{actual_source_used}' as source for Markdown generation for {url}", tag="MARKDOWN_SRC")

        except Exception as e:
            # Handle potential errors, especially from preprocess_html_for_schema
            if self.logger:
                self.logger.warning(
                    f"Error getting/processing '{selected_html_source}' for markdown source: {e}. Falling back to cleaned_html.",
                    tag="MARKDOWN_SRC"
                )
            # Ensure markdown_input_html is still the default cleaned_html in case of error
            markdown_input_html = cleaned_html
        # --- END: HTML SOURCE SELECTION ---

        # Uncomment if by default we want to use PruningContentFilter
        # if not config.content_filter and not markdown_generator.content_filter:
        #     markdown_generator.content_filter = PruningContentFilter()

        markdown_result: MarkdownGenerationResult = (
            markdown_generator.generate_markdown(
                input_html=markdown_input_html,
                base_url=params.get("redirected_url", url)
                # html2text_options=kwargs.get('html2text', {})
            )
        )

        # Log processing completion
        self.logger.url_status(
            url=_url,
            success=True,
            timing=int((time.perf_counter() - t1) * 1000) / 1000,
            tag="SCRAPE"
        )
        # self.logger.info(
        #     message="{url:.50}... | Time: {timing}s",
        #     tag="SCRAPE",
        #     params={"url": _url, "timing": int((time.perf_counter() - t1) * 1000) / 1000},
        # )

        ################################
        # Structured Content Extraction           #
        ################################
        if (
            not bool(extracted_content)
            and config.extraction_strategy
            and not isinstance(config.extraction_strategy, NoExtractionStrategy)
        ):
            t1 = time.perf_counter()
            # Choose content based on input_format
            content_format = config.extraction_strategy.input_format
            if content_format == "fit_markdown" and not markdown_result.fit_markdown:

                self.logger.url_status(
                        url=_url,
                        success=bool(html),
                        timing=time.perf_counter() - t1,
                        tag="EXTRACT",
                    )
                content_format = "markdown"

            content = {
                "markdown": markdown_result.raw_markdown,
                "html": html,
                "fit_html": fit_html,
                "cleaned_html": cleaned_html,
                "fit_markdown": markdown_result.fit_markdown,
            }.get(content_format, markdown_result.raw_markdown)

            # Use IdentityChunking for HTML input, otherwise use provided chunking strategy
            chunking = (
                IdentityChunking()
                if content_format in ["html", "cleaned_html", "fit_html"]
                else config.chunking_strategy
            )
            sections = chunking.chunk(content)
            extracted_content = config.extraction_strategy.run(url, sections)
            extracted_content = json.dumps(
                extracted_content, indent=4, default=str, ensure_ascii=False
            )

            # Log extraction completion
            self.logger.url_status(
                        url=_url,
                        success=bool(html),
                        timing=time.perf_counter() - t1,
                        tag="EXTRACT",
                    )

        # Apply HTML formatting if requested
        if config.prettiify:
            cleaned_html = fast_format_html(cleaned_html)

        # Return complete crawl result
        return CrawlResult(
            url=url,
            html=html,
            fit_html=fit_html,
            cleaned_html=cleaned_html,
            markdown=markdown_result,
            media=media,
            tables=tables,                       # NEW
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
        config: Optional[Union[CrawlerRunConfig, List[CrawlerRunConfig]]] = None,
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
    ) -> RunManyReturn:
        """
        Runs the crawler for multiple URLs concurrently using a configurable dispatcher strategy.

        Args:
        urls: List of URLs to crawl
        config: Configuration object(s) controlling crawl behavior. Can be:
            - Single CrawlerRunConfig: Used for all URLs
            - List[CrawlerRunConfig]: Configs with url_matcher for URL-specific settings
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
        config = config or CrawlerRunConfig()
        # if config is None:
        #     config = CrawlerRunConfig(
        #         word_count_threshold=word_count_threshold,
        #         extraction_strategy=extraction_strategy,
        #         chunking_strategy=chunking_strategy,
        #         content_filter=content_filter,
        #         cache_mode=cache_mode,
        #         bypass_cache=bypass_cache,
        #         css_selector=css_selector,
        #         screenshot=screenshot,
        #         pdf=pdf,
        #         verbose=verbose,
        #         **kwargs,
        #     )

        if dispatcher is None:
            dispatcher = MemoryAdaptiveDispatcher(
                rate_limiter=RateLimiter(
                    base_delay=(1.0, 3.0), max_delay=60.0, max_retries=3
                ),
            )

        def transform_result(task_result):
            return (
                setattr(
                    task_result.result,
                    "dispatch_result",
                    DispatchResult(
                        task_id=task_result.task_id,
                        memory_usage=task_result.memory_usage,
                        peak_memory=task_result.peak_memory,
                        start_time=task_result.start_time,
                        end_time=task_result.end_time,
                        error_message=task_result.error_message,
                    ),
                )
                or task_result.result
            )

        # Handle stream setting - use first config's stream setting if config is a list
        if isinstance(config, list):
            stream = config[0].stream if config else False
        else:
            stream = config.stream

        if stream:

            async def result_transformer():
                async for task_result in dispatcher.run_urls_stream(
                    crawler=self, urls=urls, config=config
                ):
                    yield transform_result(task_result)

            return result_transformer()
        else:
            _results = await dispatcher.run_urls(crawler=self, urls=urls, config=config)
            return [transform_result(res) for res in _results]

    async def aseed_urls(
        self,
        domain_or_domains: Union[str, List[str]],
        config: Optional[SeedingConfig] = None,
        **kwargs
    ) -> Union[List[str], Dict[str, List[Union[str, Dict[str, Any]]]]]:
        """
        Discovers, filters, and optionally validates URLs for a given domain(s)
        using sitemaps and Common Crawl archives.

        Args:
            domain_or_domains: A single domain string (e.g., "iana.org") or a list of domains.
            config: A SeedingConfig object to control the seeding process.
                    Parameters passed directly via kwargs will override those in 'config'.
            **kwargs: Additional parameters (e.g., `source`, `live_check`, `extract_head`,
                      `pattern`, `concurrency`, `hits_per_sec`, `force_refresh`, `verbose`)
                      that will be used to construct or update the SeedingConfig.

        Returns:
            If `extract_head` is False:
                - For a single domain: `List[str]` of discovered URLs.
                - For multiple domains: `Dict[str, List[str]]` mapping each domain to its URLs.
            If `extract_head` is True:
                - For a single domain: `List[Dict[str, Any]]` where each dict contains 'url'
                  and 'head_data' (parsed <head> metadata).
                - For multiple domains: `Dict[str, List[Dict[str, Any]]]` mapping each domain
                  to a list of URL data dictionaries.

        Raises:
            ValueError: If `domain_or_domains` is not a string or a list of strings.
            Exception: Any underlying exceptions from AsyncUrlSeeder or network operations.

        Example:
            >>> # Discover URLs from sitemap with live check for 'example.com'
            >>> result = await crawler.aseed_urls("example.com", source="sitemap", live_check=True, hits_per_sec=10)

            >>> # Discover URLs from Common Crawl, extract head data for 'example.com' and 'python.org'
            >>> multi_domain_result = await crawler.aseed_urls(
            >>>     ["example.com", "python.org"],
            >>>     source="cc", extract_head=True, concurrency=200, hits_per_sec=50
            >>> )
        """
        # Initialize AsyncUrlSeeder here if it hasn't been already
        if not self.url_seeder:
            # Pass the crawler's base_directory for seeder's cache management
            # Pass the crawler's logger for consistent logging
            self.url_seeder = AsyncUrlSeeder(
                base_directory=self.crawl4ai_folder,
                logger=self.logger
            )                    

        # Merge config object with direct kwargs, giving kwargs precedence
        seeding_config = config.clone(**kwargs) if config else SeedingConfig.from_kwargs(kwargs)
        
        # Ensure base_directory is set for the seeder's cache
        seeding_config.base_directory = seeding_config.base_directory or self.crawl4ai_folder        
        # Ensure the seeder uses the crawler's logger (if not already set)
        if not self.url_seeder.logger:
            self.url_seeder.logger = self.logger

        # Pass verbose setting if explicitly provided in SeedingConfig or kwargs
        if seeding_config.verbose is not None:
            self.url_seeder.logger.verbose = seeding_config.verbose
        else: # Default to crawler's verbose setting
            self.url_seeder.logger.verbose = self.logger.verbose


        if isinstance(domain_or_domains, str):
            self.logger.info(
                message="Starting URL seeding for domain: {domain}",
                tag="SEED",
                params={"domain": domain_or_domains}
            )
            return await self.url_seeder.urls(
                domain_or_domains,
                seeding_config
            )
        elif isinstance(domain_or_domains, (list, tuple)):
            self.logger.info(
                message="Starting URL seeding for {count} domains",
                tag="SEED",
                params={"count": len(domain_or_domains)}
            )
            # AsyncUrlSeeder.many_urls directly accepts a list of domains and individual params.
            return await self.url_seeder.many_urls(
                domain_or_domains,
                seeding_config
            )
        else:
            raise ValueError("`domain_or_domains` must be a string or a list of strings.")