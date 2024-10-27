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
from .content_scrapping_strategy import WebScrappingStrategy
from .config import MIN_WORD_THRESHOLD, IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
from .utils import (
    sanitize_input_encode,
    InvalidCSSSelectorError,
    format_html
)


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
        if self.verbose:
            print("[LOG] 🌤️  Warming up the AsyncWebCrawler")
        await async_db_manager.ainit_db()
        await self.arun(
            url="https://google.com/",
            word_count_threshold=5,
            bypass_cache=False,
            verbose=False,
        )
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
        **kwargs,
    ) -> CrawlResult:
        try:
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
            if not bypass_cache and not self.always_by_pass_cache:
                cached = await async_db_manager.aget_cached_url(url)

            if kwargs.get("warmup", True) and not self.ready:
                return None

            if cached:
                html = sanitize_input_encode(cached[1])
                extracted_content = sanitize_input_encode(cached[4])
                if screenshot:
                    screenshot_data = cached[9]
                    if not screenshot_data:
                        cached = None

            if not cached or not html:
                t1 = time.time()
                if user_agent:
                    self.crawler_strategy.update_user_agent(user_agent)
                async_response: AsyncCrawlResponse = await self.crawler_strategy.crawl(url, screenshot=screenshot, **kwargs)
                html = sanitize_input_encode(async_response.html)
                screenshot_data = async_response.screenshot
                t2 = time.time()
                if verbose:
                    print(
                        f"[LOG] 🚀 Crawling done for {url}, success: {bool(html)}, time taken: {t2 - t1:.2f} seconds"
                    )

            crawl_result = await self.aprocess_html(
                url,
                html,
                extracted_content,
                word_count_threshold,
                extraction_strategy,
                chunking_strategy,
                css_selector,
                screenshot_data,
                verbose,
                bool(cached),
                async_response=async_response,
                **kwargs,
            )
            crawl_result.status_code = async_response.status_code if async_response else 200
            crawl_result.response_headers = async_response.response_headers if async_response else {}
            crawl_result.success = bool(html)
            crawl_result.session_id = kwargs.get("session_id", None)
            return crawl_result
        except Exception as e:
            if not hasattr(e, "msg"):
                e.msg = str(e)
            print(f"[ERROR] 🚫 arun(): Failed to crawl {url}, error: {e.msg}")
            return CrawlResult(url=url, html="", markdown = f"[ERROR] 🚫 arun(): Failed to crawl {url}, error: {e.msg}", success=False, error_message=e.msg)

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
        tasks = [
            self.arun(
                url,
                word_count_threshold,
                extraction_strategy,
                chunking_strategy,
                bypass_cache,
                css_selector,
                screenshot,
                user_agent,
                verbose,
                **kwargs
            )
            for url in urls
        ]
        return await asyncio.gather(*tasks)


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
        is_cached: bool,
        **kwargs,
    ) -> CrawlResult:
        t = time.time()
        # Extract content from HTML
        try:
            t1 = time.time()
            scrapping_strategy = WebScrappingStrategy()
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
            if verbose:
                print(
                    f"[LOG] 🚀 Content extracted for {url}, success: True, time taken: {time.time() - t1:.2f} seconds"
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

        if extracted_content is None and extraction_strategy and chunking_strategy:
            if verbose:
                print(
                    f"[LOG] 🔥 Extracting semantic blocks for {url}, Strategy: {self.__class__.__name__}"
                )

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
                f"[LOG] 🚀 Extraction done for {url}, time taken: {time.time() - t:.2f} seconds."
            )

        screenshot = None if not screenshot else screenshot

        if not is_cached:
            await async_db_manager.acache_url(
                url,
                html,
                cleaned_html,
                markdown,
                extracted_content,
                True,
                json.dumps(media),
                json.dumps(links),
                json.dumps(metadata),
                screenshot=screenshot,
            )

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
        await async_db_manager.aclear_db()

    async def aflush_cache(self):
        await async_db_manager.aflush_db()

    async def aget_cache_size(self):
        return await async_db_manager.aget_total_count()
