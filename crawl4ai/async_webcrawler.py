import os
import time
from pathlib import Path
from typing import Optional
import json
import asyncio
from .models import CrawlResult
from .async_database import async_db_manager
from .chunking_strategy import *
from .extraction_strategy import *
from .async_crawler_strategy import AsyncCrawlerStrategy, AsyncPlaywrightCrawlerStrategy, AsyncCrawlResponse
from .content_scrapping_strategy import WebScrapingStrategy
from .config import MIN_WORD_THRESHOLD, IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
from .utils import (
    sanitize_input_encode,
    InvalidCSSSelectorError,
    format_html
)
from ._version import __version__ as crawl4ai_version

class AsyncWebCrawler:
    def __init__(
        self,
        crawler_strategy: Optional[AsyncCrawlerStrategy] = None,
        always_by_pass_cache: bool = False,
        base_directory: str = str(Path.home()),
        **kwargs,
    ):
        self.crawler_strategy = crawler_strategy or AsyncPlaywrightCrawlerStrategy(
            **kwargs
        )
        self.always_by_pass_cache = always_by_pass_cache
        # self.crawl4ai_folder = os.path.join(Path.home(), ".crawl4ai")
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
        # Print a message for crawl4ai and its version
        if self.verbose:
            print(f"[LOG] 🚀 Crawl4AI {crawl4ai_version}")
            print("[LOG] 🌤️  Warming up the AsyncWebCrawler")
        # await async_db_manager.ainit_db()
        # # await async_db_manager.initialize()
        # await self.arun(
        #     url="https://google.com/",
        #     word_count_threshold=5,
        #     bypass_cache=False,
        #     verbose=False,
        # )
        self.ready = True
        if self.verbose:
            print("[LOG] 🌞 AsyncWebCrawler is ready to crawl")

    async def arun(
        self,
        url: str,
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        bypass_cache: bool = False,
        css_selector: str = None,
        screenshot: bool = False,
        user_agent: str = None,
        verbose=True,
        disable_cache: bool = False,
        no_cache_read: bool = False,
        no_cache_write: bool = False,
        **kwargs,
    ) -> CrawlResult:
        """
        Runs the crawler for a single source: URL (web, local file, or raw HTML).

        Args:
            url (str): The URL to crawl. Supported prefixes:
                - 'http://' or 'https://': Web URL to crawl.
                - 'file://': Local file path to process.
                - 'raw:': Raw HTML content to process.
            ... [other existing parameters]

        Returns:
            CrawlResult: The result of the crawling and processing.
        """
        try:
            if disable_cache:
                bypass_cache = True
                no_cache_read = True
                no_cache_write = True
            
            extraction_strategy = extraction_strategy or NoExtractionStrategy()
            extraction_strategy.verbose = verbose
            if not isinstance(extraction_strategy, ExtractionStrategy):
                raise ValueError("Unsupported extraction strategy")
            if not isinstance(chunking_strategy, ChunkingStrategy):
                raise ValueError("Unsupported chunking strategy")
            
            word_count_threshold = max(word_count_threshold, MIN_WORD_THRESHOLD)

            async_response: AsyncCrawlResponse = None
            cached = None
            screenshot_data = None
            extracted_content = None
            
            is_web_url = url.startswith(('http://', 'https://'))
            is_local_file = url.startswith("file://")
            is_raw_html = url.startswith("raw:")
            _url = url if not is_raw_html else "Raw HTML"
            
            start_time = time.perf_counter()
            cached_result = None
            if is_web_url and (not bypass_cache or not no_cache_read) and not self.always_by_pass_cache:
                cached_result = await async_db_manager.aget_cached_url(url)
                        
            if cached_result:
                html = sanitize_input_encode(cached_result.html)
                extracted_content = sanitize_input_encode(cached_result.extracted_content or "")
                if screenshot:
                    screenshot_data = cached_result.screenshot
                    if not screenshot_data:
                        cached_result = None
                if verbose:
                    print(
                        f"[LOG] 1️⃣  ✅ Page fetched (cache) for {_url}, success: {bool(html)}, time taken: {time.perf_counter() - start_time:.2f} seconds"
                    )


            if not cached or not html:
                t1 = time.perf_counter()
                
                if user_agent:
                    self.crawler_strategy.update_user_agent(user_agent)
                async_response: AsyncCrawlResponse = await self.crawler_strategy.crawl(url, screenshot=screenshot, **kwargs)
                html = sanitize_input_encode(async_response.html)
                screenshot_data = async_response.screenshot
                t2 = time.perf_counter()
                if verbose:
                    print(
                        f"[LOG] 1️⃣  ✅ Page fetched (no-cache) for {_url}, success: {bool(html)}, time taken: {t2 - t1:.2f} seconds"
                    )

            t1 = time.perf_counter()
            crawl_result = await self.aprocess_html(
                url=url,
                html=html,
                extracted_content=extracted_content,
                word_count_threshold=word_count_threshold,
                extraction_strategy=extraction_strategy,
                chunking_strategy=chunking_strategy,
                css_selector=css_selector,
                screenshot=screenshot_data,
                verbose=verbose,
                is_cached=bool(cached),
                async_response=async_response,
                bypass_cache=bypass_cache,
                is_web_url = is_web_url,
                is_local_file = is_local_file,
                is_raw_html = is_raw_html,
                **kwargs,
            )
            
            if async_response:
                crawl_result.status_code = async_response.status_code
                crawl_result.response_headers = async_response.response_headers
                crawl_result.downloaded_files = async_response.downloaded_files
            else:
                crawl_result.status_code = 200
                crawl_result.response_headers = cached_result.response_headers if cached_result else {}

            crawl_result.success = bool(html)
            crawl_result.session_id = kwargs.get("session_id", None)

            if verbose:
                print(
                    f"[LOG] 🔥 🚀 Crawling done for {_url}, success: {crawl_result.success}, time taken: {time.perf_counter() - start_time:.2f} seconds"
                )

            if not is_raw_html and not no_cache_write:
                if not bool(cached_result) or kwargs.get("bypass_cache", False) or self.always_by_pass_cache:
                    await async_db_manager.acache_url(crawl_result)


            return crawl_result
        
        except Exception as e:
            if not hasattr(e, "msg"):
                e.msg = str(e)
            print(f"[ERROR] 🚫 arun(): Failed to crawl {_url}, error: {e.msg}")
            return CrawlResult(url=url, html="", markdown = f"[ERROR] 🚫 arun(): Failed to crawl {_url}, error: {e.msg}", success=False, error_message=e.msg)

    async def arun_many(
        self,
        urls: List[str],
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        bypass_cache: bool = False,
        css_selector: str = None,
        screenshot: bool = False,
        user_agent: str = None,
        verbose=True,
        **kwargs,
    ) -> List[CrawlResult]:
        """
        Runs the crawler for multiple sources: URLs (web, local files, or raw HTML).

        Args:
            urls (List[str]): A list of URLs with supported prefixes:
                - 'http://' or 'https://': Web URL to crawl.
                - 'file://': Local file path to process.
                - 'raw:': Raw HTML content to process.
            ... [other existing parameters]

        Returns:
            List[CrawlResult]: The results of the crawling and processing.
        """
        semaphore_count = kwargs.get('semaphore_count', 5)  # Adjust as needed
        semaphore = asyncio.Semaphore(semaphore_count)

        async def crawl_with_semaphore(url):
            async with semaphore:
                return await self.arun(
                    url,
                    word_count_threshold=word_count_threshold,
                    extraction_strategy=extraction_strategy,
                    chunking_strategy=chunking_strategy,
                    bypass_cache=bypass_cache,
                    css_selector=css_selector,
                    screenshot=screenshot,
                    user_agent=user_agent,
                    verbose=verbose,
                    **kwargs,
                )

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [result if not isinstance(result, Exception) else str(result) for result in results]

    async def aprocess_html(
        self,
        url: str,
        html: str,
        extracted_content: str,
        word_count_threshold: int,
        extraction_strategy: ExtractionStrategy,
        chunking_strategy: ChunkingStrategy,
        css_selector: str,
        screenshot: str,
        verbose: bool,
        **kwargs,
    ) -> CrawlResult:
        t = time.perf_counter()
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
                only_text=kwargs.get("only_text", False),
                image_description_min_word_threshold=kwargs.get(
                    "image_description_min_word_threshold", IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
                ),
                **kwargs,
            )

            if result is None:
                raise ValueError(f"Process HTML, Failed to extract content from the website: {url}")
        except InvalidCSSSelectorError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}")

        cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
        markdown = sanitize_input_encode(result.get("markdown", ""))
        fit_markdown = sanitize_input_encode(result.get("fit_markdown", ""))
        fit_html = sanitize_input_encode(result.get("fit_html", ""))
        media = result.get("media", [])
        links = result.get("links", [])
        metadata = result.get("metadata", {})
        
        if verbose:
            print(
                f"[LOG] 2️⃣  ✅ Scraping done for {_url}, success: True, time taken: {time.perf_counter() - t1:.2f} seconds"
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
            if verbose:
                print(
                    f"[LOG] 3️⃣  ✅ Extraction done for {_url}, time taken: {time.perf_counter() - t1:.2f} seconds"
                )

        screenshot = None if not screenshot else screenshot
        
        return CrawlResult(
            url=url,
            html=html,
            cleaned_html=format_html(cleaned_html),
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
        # await async_db_manager.aclear_db()
        await async_db_manager.cleanup()

    async def aflush_cache(self):
        await async_db_manager.aflush_db()

    async def aget_cache_size(self):
        return await async_db_manager.aget_total_count()


