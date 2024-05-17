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


class WebCrawler:
    def __init__(
        self,
        # db_path: str = None,
        crawler_strategy: CrawlerStrategy = None,
        always_by_pass_cache: bool = False,
        verbose: bool = False,
    ):
        # self.db_path = db_path
        self.crawler_strategy = crawler_strategy or LocalSeleniumCrawlerStrategy(verbose=verbose)
        self.always_by_pass_cache = always_by_pass_cache

        # Create the .crawl4ai folder in the user's home directory if it doesn't exist
        self.crawl4ai_folder = os.path.join(Path.home(), ".crawl4ai")
        os.makedirs(self.crawl4ai_folder, exist_ok=True)
        os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)

        # If db_path is not provided, use the default path
        # if not db_path:
            # self.db_path = f"{self.crawl4ai_folder}/crawl4ai.db"
        
        # flush_db()
        init_db()
        
        self.ready = False
        
    def warmup(self):
        print("[LOG] 🌤️  Warming up the WebCrawler")
        result = self.run(
            url='https://crawl4ai.uccode.io/',
            word_count_threshold=5,
            extraction_strategy= NoExtractionStrategy(),
            bypass_cache=False,
            verbose = False
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
            **kwargs,
        )
        pass


    def run(
        self,
        url: str,
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        bypass_cache: bool = False,
        css_selector: str = None,
        verbose=True,
        **kwargs,
    ) -> CrawlResult:
        extraction_strategy = extraction_strategy or NoExtractionStrategy()
        extraction_strategy.verbose = verbose
        # Check if extraction strategy is an instance of ExtractionStrategy if not raise an error
        if not isinstance(extraction_strategy, ExtractionStrategy):
            raise ValueError("Unsupported extraction strategy")
        if not isinstance(chunking_strategy, ChunkingStrategy):
            raise ValueError("Unsupported chunking strategy")
        
        # make sure word_count_threshold is not lesser than MIN_WORD_THRESHOLD
        if word_count_threshold < MIN_WORD_THRESHOLD:
            word_count_threshold = MIN_WORD_THRESHOLD

        # Check cache first
        if not bypass_cache and not self.always_by_pass_cache:
            cached = get_cached_url(url)
            if cached:
                return CrawlResult(
                    **{
                        "url": cached[0],
                        "html": cached[1],
                        "cleaned_html": cached[2],
                        "markdown": cached[3],
                        "extracted_content": cached[4],
                        "success": cached[5],
                        "error_message": "",
                    }
                )

        # Initialize WebDriver for crawling
        t = time.time()
        html = self.crawler_strategy.crawl(url)
        success = True
        error_message = ""
        # Extract content from HTML
        try:
            result = get_content_of_website(html, word_count_threshold, css_selector=css_selector)
            if result is None:
                raise ValueError(f"Failed to extract content from the website: {url}")
        except InvalidCSSSelectorError as e:
            raise ValueError(str(e))
        
        cleaned_html = result.get("cleaned_html", html)
        markdown = result.get("markdown", "")

        # Print a profession LOG style message, show time taken and say crawling is done
        if verbose:
            print(
                f"[LOG] 🚀 Crawling done for {url}, success: {success}, time taken: {time.time() - t} seconds"
            )

        extracted_content = []
        if verbose:
            print(f"[LOG] 🔥 Extracting semantic blocks for {url}, Strategy: {extraction_strategy.name}")
        t = time.time()
        # Split markdown into sections
        sections = chunking_strategy.chunk(markdown)
        # sections = merge_chunks_based_on_token_threshold(sections, CHUNK_TOKEN_THRESHOLD)

        extracted_content = extraction_strategy.run(
            url, sections,
        )
        extracted_content = json.dumps(extracted_content)

        if verbose:
            print(
                f"[LOG] 🚀 Extraction done for {url}, time taken: {time.time() - t} seconds."
            )

        # Cache the result
        cleaned_html = beautify_html(cleaned_html)
        cache_url(
            url,
            html,
            cleaned_html,
            markdown,
            extracted_content,
            success,
        )

        return CrawlResult(
            url=url,
            html=html,
            cleaned_html=cleaned_html,
            markdown=markdown,
            extracted_content=extracted_content,
            success=success,
            error_message=error_message,
        )

    def fetch_pages(
        self,
        url_models: List[UrlModel],
        provider: str = DEFAULT_PROVIDER,
        api_token: str = None,
        extract_blocks_flag: bool = True,
        word_count_threshold=MIN_WORD_THRESHOLD,
        use_cached_html: bool = False,
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
                    [use_cached_html] * len(url_models),
                    [extraction_strategy] * len(url_models),
                    [chunking_strategy] * len(url_models),
                    *[kwargs] * len(url_models),
                )
            )

        return results
