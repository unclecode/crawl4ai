import os
import time
import warnings
from enum import Enum
from colorama import init, Fore, Back, Style
from pathlib import Path
from typing import Optional, List, Union
import json
import asyncio
from .models import CrawlResult, MarkdownGenerationResult
from .async_database import async_db_manager
from .chunking_strategy import *
from .content_filter_strategy import *
from .extraction_strategy import *
from .async_crawler_strategy import AsyncCrawlerStrategy, AsyncPlaywrightCrawlerStrategy, AsyncCrawlResponse
from .cache_context import CacheMode, CacheContext, _legacy_to_cache_mode
from .content_scraping_strategy import WebScrapingStrategy
from .async_logger import AsyncLogger

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
    
    Migration Guide (from version X.X.X):
    Old way (deprecated):
        crawler = AsyncWebCrawler(always_by_pass_cache=True)
        result = await crawler.arun(
            url="https://example.com",
            bypass_cache=True,
            no_cache_read=True,
            no_cache_write=False
        )
    
    New way (recommended):
        crawler = AsyncWebCrawler(always_bypass_cache=True)
        result = await crawler.arun(
            url="https://example.com",
            cache_mode=CacheMode.WRITE_ONLY
        )
    
    To disable deprecation warnings:
        Pass warning=False to suppress the warning.
    """
    _domain_last_hit = {}

    def __init__(
        self,
        crawler_strategy: Optional[AsyncCrawlerStrategy] = None,
        always_bypass_cache: bool = False,
        always_by_pass_cache: Optional[bool] = None,  # Deprecated parameter
        base_directory: str = str(os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())),
        **kwargs,
    ):
        """
        Initialize the AsyncWebCrawler.

        Args:
            crawler_strategy: Strategy for crawling web pages
            always_bypass_cache: Whether to always bypass cache (new parameter)
            always_by_pass_cache: Deprecated, use always_bypass_cache instead
            base_directory: Base directory for storing cache
        """  
        self.verbose = kwargs.get("verbose", False)
        self.logger = AsyncLogger(
            log_file=os.path.join(base_directory, ".crawl4ai", "crawler.log"),
            verbose=self.verbose,
            tag_width=10
        )
        
        self.crawler_strategy = crawler_strategy or AsyncPlaywrightCrawlerStrategy(
            logger = self.logger,
            **kwargs
        )
        
        # Handle deprecated parameter
        if always_by_pass_cache is not None:
            if kwargs.get("warning", True):
                warnings.warn(
                    "'always_by_pass_cache' is deprecated and will be removed in version X.X.X. "
                    "Use 'always_bypass_cache' instead. "
                    "Pass warning=False to suppress this warning.",
                    DeprecationWarning,
                    stacklevel=2
                )
            self.always_bypass_cache = always_by_pass_cache
        else:
            self.always_bypass_cache = always_bypass_cache

        self.crawl4ai_folder = os.path.join(base_directory, ".crawl4ai")
        os.makedirs(self.crawl4ai_folder, exist_ok=True)
        os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)
        self.ready = False
        self.verbose = kwargs.get("verbose", False)

    async def __aenter__(self):
        await self.crawler_strategy.__aenter__()
        await self.awarmup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.crawler_strategy.__aexit__(exc_type, exc_val, exc_tb)

    async def awarmup(self):
        """Initialize the crawler with warm-up sequence."""
        self.logger.info(f"Crawl4AI {crawl4ai_version}", tag="INIT")
        # if self.verbose:
        #     print(f"{Fore.CYAN}{self.tag_format('INIT')} {self.log_icons['INIT']} Crawl4AI {crawl4ai_version}{Style.RESET_ALL}")
        #     print(f"{Fore.CYAN}{self.tag_format('INIT')} {self.log_icons['INIT']} Warming up AsyncWebCrawler{Style.RESET_ALL}")
        self.ready = True
        # if self.verbose:
        #     print(f"{Fore.GREEN}{self.tag_format('READY')} {self.log_icons['READY']} AsyncWebCrawler initialized{Style.RESET_ALL}")

    async def arun(
        self,
        url: str,
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        content_filter: RelevantContentFilter = None,
        cache_mode: Optional[CacheMode] = None,
        # Deprecated parameters
        bypass_cache: bool = False,
        disable_cache: bool = False,
        no_cache_read: bool = False,
        no_cache_write: bool = False,
        # Other parameters
        css_selector: str = None,
        screenshot: bool = False,
        user_agent: str = None,
        verbose=True,
        **kwargs,
    ) -> CrawlResult:
        """
        Runs the crawler for a single source: URL (web, local file, or raw HTML).

        Migration from legacy cache parameters:
            Old way (deprecated):
                await crawler.arun(url, bypass_cache=True, no_cache_read=True)
            
            New way:
                await crawler.arun(url, cache_mode=CacheMode.BYPASS)

        Args:
            url: The URL to crawl (http://, https://, file://, or raw:)
            cache_mode: Cache behavior control (recommended)
            word_count_threshold: Minimum word count threshold
            extraction_strategy: Strategy for content extraction
            chunking_strategy: Strategy for content chunking
            css_selector: CSS selector for content extraction
            screenshot: Whether to capture screenshot
            user_agent: Custom user agent
            verbose: Enable verbose logging
            
            Deprecated Args:
                bypass_cache: Use cache_mode=CacheMode.BYPASS instead
                disable_cache: Use cache_mode=CacheMode.DISABLED instead
                no_cache_read: Use cache_mode=CacheMode.WRITE_ONLY instead
                no_cache_write: Use cache_mode=CacheMode.READ_ONLY instead

        Returns:
            CrawlResult: The result of crawling and processing
        """
        try:
            # Handle deprecated parameters
            if any([bypass_cache, disable_cache, no_cache_read, no_cache_write]):
                if kwargs.get("warning", True):
                    warnings.warn(
                        "Cache control boolean flags are deprecated and will be removed in version X.X.X. "
                        "Use 'cache_mode' parameter instead. Examples:\n"
                        "- For bypass_cache=True, use cache_mode=CacheMode.BYPASS\n"
                        "- For disable_cache=True, use cache_mode=CacheMode.DISABLED\n"
                        "- For no_cache_read=True, use cache_mode=CacheMode.WRITE_ONLY\n"
                        "- For no_cache_write=True, use cache_mode=CacheMode.READ_ONLY\n"
                        "Pass warning=False to suppress this warning.",
                        DeprecationWarning,
                        stacklevel=2
                    )
                
                # Convert legacy parameters if cache_mode not provided
                if cache_mode is None:
                    cache_mode = _legacy_to_cache_mode(
                        disable_cache=disable_cache,
                        bypass_cache=bypass_cache,
                        no_cache_read=no_cache_read,
                        no_cache_write=no_cache_write
                    )
            
            # Default to ENABLED if no cache mode specified
            if cache_mode is None:
                cache_mode = CacheMode.ENABLED

            # Create cache context
            cache_context = CacheContext(url, cache_mode, self.always_bypass_cache)

            extraction_strategy = extraction_strategy or NoExtractionStrategy()
            extraction_strategy.verbose = verbose
            if not isinstance(extraction_strategy, ExtractionStrategy):
                raise ValueError("Unsupported extraction strategy")
            if not isinstance(chunking_strategy, ChunkingStrategy):
                raise ValueError("Unsupported chunking strategy")
            
            word_count_threshold = max(word_count_threshold, MIN_WORD_THRESHOLD)

            async_response: AsyncCrawlResponse = None
            cached_result = None
            screenshot_data = None
            extracted_content = None
            
            start_time = time.perf_counter()
            
            # Try to get cached result if appropriate
            if cache_context.should_read():
                cached_result = await async_db_manager.aget_cached_url(url)
                        
            if cached_result:
                html = sanitize_input_encode(cached_result.html)
                extracted_content = sanitize_input_encode(cached_result.extracted_content or "")
                if screenshot:
                    screenshot_data = cached_result.screenshot
                    if not screenshot_data:
                        cached_result = None
                # if verbose:
                #     print(f"{Fore.BLUE}{self.tag_format('FETCH')} {self.log_icons['FETCH']} Cache hit for {cache_context.display_url} | Status: {Fore.GREEN if bool(html) else Fore.RED}{bool(html)}{Style.RESET_ALL} | Time: {time.perf_counter() - start_time:.2f}s")
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
                async_response: AsyncCrawlResponse = await self.crawler_strategy.crawl(
                    url, 
                    screenshot=screenshot, 
                    **kwargs
                )
                html = sanitize_input_encode(async_response.html)
                screenshot_data = async_response.screenshot
                t2 = time.perf_counter()
                self.logger.url_status(
                    url=cache_context.display_url,
                    success=bool(html),
                    timing=t2 - t1,
                    tag="FETCH"
                )
                # if verbose:
                #     print(f"{Fore.BLUE}{self.tag_format('FETCH')} {self.log_icons['FETCH']} Live fetch for {cache_context.display_url}... | Status: {Fore.GREEN if bool(html) else Fore.RED}{bool(html)}{Style.RESET_ALL} | Time: {t2 - t1:.2f}s")

            # Process the HTML content
            crawl_result = await self.aprocess_html(
                url=url,
                html=html,
                extracted_content=extracted_content,
                word_count_threshold=word_count_threshold,
                extraction_strategy=extraction_strategy,
                chunking_strategy=chunking_strategy,
                content_filter=content_filter,
                css_selector=css_selector,
                screenshot=screenshot_data,
                verbose=verbose,
                is_cached=bool(cached_result),
                async_response=async_response,
                is_web_url=cache_context.is_web_url,
                is_local_file=cache_context.is_local_file,
                is_raw_html=cache_context.is_raw_html,
                **kwargs,
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
            crawl_result.session_id = kwargs.get("session_id", None)

            # if verbose:
            #     print(f"{Fore.GREEN}{self.tag_format('COMPLETE')} {self.log_icons['COMPLETE']} {cache_context.display_url[:URL_LOG_SHORTEN_LENGTH]}... | Status: {Fore.GREEN if crawl_result.success else Fore.RED}{crawl_result.success} | {Fore.YELLOW}Total: {time.perf_counter() - start_time:.2f}s{Style.RESET_ALL}")
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
            if not hasattr(e, "msg"):
                e.msg = str(e)
            # print(f"{Fore.RED}{self.tag_format('ERROR')} {self.log_icons['ERROR']} Failed to crawl {cache_context.display_url[:URL_LOG_SHORTEN_LENGTH]}... | {e.msg}{Style.RESET_ALL}")
            
            self.logger.error_status(
                url=cache_context.display_url,
                error=create_box_message(e.msg, type = "error"),
                tag="ERROR"
            )            
            return CrawlResult(
                url=url, 
                html="", 
                success=False, 
                error_message=e.msg
            )

    async def arun_many(
        self,
        urls: List[str],
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        content_filter: RelevantContentFilter = None,
        cache_mode: Optional[CacheMode] = None,
        # Deprecated parameters
        bypass_cache: bool = False,
        css_selector: str = None,
        screenshot: bool = False,
        user_agent: str = None,
        verbose=True,
        **kwargs,
    ) -> List[CrawlResult]:
        """
        Runs the crawler for multiple URLs concurrently.

        Migration from legacy parameters:
            Old way (deprecated):
                results = await crawler.arun_many(urls, bypass_cache=True)
            
            New way:
                results = await crawler.arun_many(urls, cache_mode=CacheMode.BYPASS)

        Args:
            urls: List of URLs to crawl
            cache_mode: Cache behavior control (recommended)
            [other parameters same as arun()]

        Returns:
            List[CrawlResult]: Results for each URL
        """
        if bypass_cache:
            if kwargs.get("warning", True):
                warnings.warn(
                    "'bypass_cache' is deprecated and will be removed in version X.X.X. "
                    "Use 'cache_mode=CacheMode.BYPASS' instead. "
                    "Pass warning=False to suppress this warning.",
                    DeprecationWarning,
                    stacklevel=2
                )
            if cache_mode is None:
                cache_mode = CacheMode.BYPASS

        semaphore_count = kwargs.get('semaphore_count', 10)
        semaphore = asyncio.Semaphore(semaphore_count)

        async def crawl_with_semaphore(url):
            domain = urlparse(url).netloc
            current_time = time.time()
            
            # print(f"{Fore.LIGHTBLACK_EX}{self.tag_format('PARALLEL')} Started task for {url[:50]}...{Style.RESET_ALL}")
            self.logger.debug(
                message="Started task for {url:.50}...",
                tag="PARALLEL",
                params={"url": url}
            )            
            
            # Get delay settings from kwargs or use defaults
            mean_delay = kwargs.get('mean_delay', 0.1)  # 0.5 seconds default mean delay
            max_range = kwargs.get('max_range', 0.3)    # 1 seconds default max additional delay
            
            # Check if we need to wait
            if domain in self._domain_last_hit:
                time_since_last = current_time - self._domain_last_hit[domain]
                if time_since_last < mean_delay:
                    delay = mean_delay + random.uniform(0, max_range)
                    await asyncio.sleep(delay)
            
            # Update last hit time
            self._domain_last_hit[domain] = current_time    
                    
            async with semaphore:
                return await self.arun(
                    url,
                    word_count_threshold=word_count_threshold,
                    extraction_strategy=extraction_strategy,
                    chunking_strategy=chunking_strategy,
                    content_filter=content_filter,
                    cache_mode=cache_mode,
                    css_selector=css_selector,
                    screenshot=screenshot,
                    user_agent=user_agent,
                    verbose=verbose,
                    **kwargs,
                )

        # Print start message
        # print(f"{Fore.CYAN}{self.tag_format('INIT')} {self.log_icons['INIT']} Starting concurrent crawling for {len(urls)} URLs...{Style.RESET_ALL}")
        self.logger.info(
            message="Starting concurrent crawling for {count} URLs...",
            tag="INIT",
            params={"count": len(urls)}
        )        
        start_time = time.perf_counter()
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        # print(f"{Fore.YELLOW}{self.tag_format('COMPLETE')} {self.log_icons['COMPLETE']} Concurrent crawling completed for {len(urls)} URLs | Total time: {end_time - start_time:.2f}s{Style.RESET_ALL}")
        self.logger.success(
            message="Concurrent crawling completed for {count} URLs | " + Fore.YELLOW + " Total time: {timing}" + Style.RESET_ALL,
            tag="COMPLETE",
            params={
                "count": len(urls),
                "timing": f"{end_time - start_time:.2f}s"
            },
            colors={"timing": Fore.YELLOW}
        )        
        return [result if not isinstance(result, Exception) else str(result) for result in results]


    async def aprocess_html(
        self,
        url: str,
        html: str,
        extracted_content: str,
        word_count_threshold: int,
        extraction_strategy: ExtractionStrategy,
        chunking_strategy: ChunkingStrategy,
        content_filter: RelevantContentFilter,
        css_selector: str,
        screenshot: str,
        verbose: bool,
        **kwargs,
    ) -> CrawlResult:
        # Extract content from HTML
        try:
            _url = url if not kwargs.get("is_raw_html", False) else "Raw HTML"
            t1 = time.perf_counter()
            scrapping_strategy = WebScrapingStrategy()
            # result = await scrapping_strategy.ascrap(
            result = scrapping_strategy.scrap(
                url,
                html,
                word_count_threshold=word_count_threshold,
                css_selector=css_selector,
                only_text=kwargs.pop("only_text", False),
                image_description_min_word_threshold=kwargs.pop(
                    "image_description_min_word_threshold", IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
                ),
                content_filter = content_filter,
                **kwargs,
            )

            if result is None:
                raise ValueError(f"Process HTML, Failed to extract content from the website: {url}")
        except InvalidCSSSelectorError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}")

        markdown_v2: MarkdownGenerationResult = result.get("markdown_v2", None)
        
        cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
        markdown = sanitize_input_encode(result.get("markdown", ""))
        fit_markdown = sanitize_input_encode(result.get("fit_markdown", ""))
        fit_html = sanitize_input_encode(result.get("fit_html", ""))
        media = result.get("media", [])
        links = result.get("links", [])
        metadata = result.get("metadata", {})
        
        # if verbose:
        #     print(f"{Fore.MAGENTA}{self.tag_format('SCRAPE')} {self.log_icons['SCRAPE']} Processed {_url[:URL_LOG_SHORTEN_LENGTH]}...{Style.RESET_ALL} | Time: {int((time.perf_counter() - t1) * 1000)}ms")
        self.logger.info(
            message="Processed {url:.50}... | Time: {timing}ms",
            tag="SCRAPE",
            params={
                "url": _url,
                "timing": int((time.perf_counter() - t1) * 1000)
            }
        )


        if extracted_content is None and extraction_strategy and chunking_strategy and not isinstance(extraction_strategy, NoExtractionStrategy):
            t1 = time.perf_counter()
            # Check if extraction strategy is type of JsonCssExtractionStrategy
            if isinstance(extraction_strategy, JsonCssExtractionStrategy) or isinstance(extraction_strategy, JsonCssExtractionStrategy):
                extraction_strategy.verbose = verbose
                extracted_content = extraction_strategy.run(url, [html])
                extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)
            else:
                sections = chunking_strategy.chunk(markdown)
                extracted_content = extraction_strategy.run(url, sections)
                extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)
            # if verbose:
                # print(f"{Fore.YELLOW}{self.tag_format('EXTRACT')} {self.log_icons['EXTRACT']} Completed for {_url[:URL_LOG_SHORTEN_LENGTH]}...{Style.RESET_ALL} | Time: {time.perf_counter() - t1:.2f}s{Style.RESET_ALL}")
            self.logger.info(
                message="Completed for {url:.50}... | Time: {timing}s",
                tag="EXTRACT",
                params={
                    "url": _url,
                    "timing": time.perf_counter() - t1
                }
            )

        screenshot = None if not screenshot else screenshot
        
        
        if kwargs.get("prettiify", False):
            cleaned_html = fast_format_html(cleaned_html)
        
        return CrawlResult(
            url=url,
            html=html,
            cleaned_html=cleaned_html,
            markdown_v2=markdown_v2,
            markdown=markdown,
            fit_markdown=fit_markdown,
            fit_html= fit_html,
            media=media,
            links=links,
            metadata=metadata,
            screenshot=screenshot,
            extracted_content=extracted_content,
            success=True,
            error_message="",
        )

    async def aclear_cache(self):
        """Clear the cache database."""
        await async_db_manager.cleanup()

    async def aflush_cache(self):
        """Flush the cache database."""
        await async_db_manager.aflush_db()

    async def aget_cache_size(self):
        """Get the total number of cached items."""
        return await async_db_manager.aget_total_count()


