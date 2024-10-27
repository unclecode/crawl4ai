import os, time
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from pathlib import Path

from .models import UrlModel, CrawlResult
from .database import init_db, get_cached_url, cache_url, DB_PATH, flush_db
from .utils import *
from .chunking_strategy import *
from .extraction_strategy import *
from .crawler_strategy import *
from typing import List
from concurrent.futures import ThreadPoolExecutor
from .config import *
import warnings
import json
warnings.filterwarnings("ignore", message='Field "model_name" has conflict with protected namespace "model_".')


class WebCrawler:
    def __init__(self, crawler_strategy: CrawlerStrategy = None, always_by_pass_cache: bool = False, verbose: bool = False):
        self.crawler_strategy = crawler_strategy or LocalSeleniumCrawlerStrategy(verbose=verbose)
        self.always_by_pass_cache = always_by_pass_cache
        self.crawl4ai_folder = os.path.join(Path.home(), ".crawl4ai")
        os.makedirs(self.crawl4ai_folder, exist_ok=True)
        os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)
        init_db()
        self.ready = False
        
    def warmup(self):
        print("[LOG] 🌤️  Warming up the WebCrawler")
        self.run(
            url='https://google.com/',
            word_count_threshold=5,
            extraction_strategy=NoExtractionStrategy(),
            bypass_cache=False,
            verbose=False
        )
        self.ready = True
        print("[LOG] 🌞 WebCrawler is ready to crawl")
        
    def fetch_page(
        self,
        url_model: UrlModel,
        provider: str = DEFAULT_PROVIDER,
        api_token: str = None,
        extract_blocks_flag: bool = True,
        word_count_threshold=MIN_WORD_THRESHOLD,
        css_selector: str = None,
        screenshot: bool = False,
        use_cached_html: bool = False,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        **kwargs,
    ) -> CrawlResult:
        return self.run(
            url_model.url,
            word_count_threshold,
            extraction_strategy or NoExtractionStrategy(),
            chunking_strategy,
            bypass_cache=url_model.forced,
            css_selector=css_selector,
            screenshot=screenshot,
            **kwargs,
        )
        pass

    def fetch_pages(
        self,
        url_models: List[UrlModel],
        provider: str = DEFAULT_PROVIDER,
        api_token: str = None,
        extract_blocks_flag: bool = True,
        word_count_threshold=MIN_WORD_THRESHOLD,
        use_cached_html: bool = False,
        css_selector: str = None,
        screenshot: bool = False,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        **kwargs,
    ) -> List[CrawlResult]:
        extraction_strategy = extraction_strategy or NoExtractionStrategy()
        def fetch_page_wrapper(url_model, *args, **kwargs):
            return self.fetch_page(url_model, *args, **kwargs)

        with ThreadPoolExecutor() as executor:
            results = list(
                executor.map(
                    fetch_page_wrapper,
                    url_models,
                    [provider] * len(url_models),
                    [api_token] * len(url_models),
                    [extract_blocks_flag] * len(url_models),
                    [word_count_threshold] * len(url_models),
                    [css_selector] * len(url_models),
                    [screenshot] * len(url_models),
                    [use_cached_html] * len(url_models),
                    [extraction_strategy] * len(url_models),
                    [chunking_strategy] * len(url_models),
                    *[kwargs] * len(url_models),
                )
            )

        return results

    def run(
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

                cached = None
                screenshot_data = None
                extracted_content = None
                if not bypass_cache and not self.always_by_pass_cache:
                    cached = get_cached_url(url)
                
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
                    if user_agent:
                        self.crawler_strategy.update_user_agent(user_agent)
                    t1 = time.time()
                    html = sanitize_input_encode(self.crawler_strategy.crawl(url, **kwargs))
                    t2 = time.time()
                    if verbose:
                        print(f"[LOG] 🚀 Crawling done for {url}, success: {bool(html)}, time taken: {t2 - t1:.2f} seconds")
                    if screenshot:
                        screenshot_data = self.crawler_strategy.take_screenshot()

                
                crawl_result = self.process_html(url, html, extracted_content, word_count_threshold, extraction_strategy, chunking_strategy, css_selector, screenshot_data, verbose, bool(cached), **kwargs)
                crawl_result.success = bool(html)
                return crawl_result
            except Exception as e:
                if not hasattr(e, "msg"):
                    e.msg = str(e)
                print(f"[ERROR] 🚫 Failed to crawl {url}, error: {e.msg}")    
                return CrawlResult(url=url, html="", success=False, error_message=e.msg)

    def process_html(
            self,
            url: str,
            html: str,
            extracted_content: str,
            word_count_threshold: int,
            extraction_strategy: ExtractionStrategy,
            chunking_strategy: ChunkingStrategy,
            css_selector: str,
            screenshot: bool,
            verbose: bool,
            is_cached: bool,
            **kwargs,
        ) -> CrawlResult:
            t = time.time()
            # Extract content from HTML
            try:
                t1 = time.time()
                result = get_content_of_website_optimized(url, html, word_count_threshold, css_selector=css_selector, only_text=kwargs.get("only_text", False))
                if verbose:
                    print(f"[LOG] 🚀 Content extracted for {url}, success: True, time taken: {time.time() - t1:.2f} seconds")
                
                if result is None:
                    raise ValueError(f"Failed to extract content from the website: {url}")
            except InvalidCSSSelectorError as e:
                raise ValueError(str(e))
            
            cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
            markdown = sanitize_input_encode(result.get("markdown", ""))
            media = result.get("media", [])
            links = result.get("links", [])
            metadata = result.get("metadata", {})
                        
            if extracted_content is None:
                if verbose:
                    print(f"[LOG] 🔥 Extracting semantic blocks for {url}, Strategy: {extraction_strategy.name}")

                sections = chunking_strategy.chunk(markdown)
                extracted_content = extraction_strategy.run(url, sections)
                extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)

                if verbose:
                    print(f"[LOG] 🚀 Extraction done for {url}, time taken: {time.time() - t:.2f} seconds.")
                
            screenshot = None if not screenshot else screenshot
            
            if not is_cached:
                cache_url(
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
                media=media,
                links=links,
                metadata=metadata,
                screenshot=screenshot,
                extracted_content=extracted_content,
                success=True,
                error_message="",
            )