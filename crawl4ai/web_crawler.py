import os, time
from pathlib import Path

from .models import UrlModel, CrawlResult
from .database import init_db, get_cached_url, cache_url
from .utils import *
from .chunking_strategy import *
from .extraction_strategy import *
from .crawler_strategy import *
from typing import List
from concurrent.futures import ThreadPoolExecutor
from .config import * 

class WebCrawler:
    def __init__(self, db_path: str, crawler_strategy: CrawlerStrategy = LocalSeleniumCrawlerStrategy()):
        self.db_path = db_path
        init_db(self.db_path)
        self.crawler_strategy = crawler_strategy
        
        # Create the .crawl4ai folder in the user's home directory if it doesn't exist
        self.crawl4ai_folder = os.path.join(Path.home(), ".crawl4ai")
        os.makedirs(self.crawl4ai_folder, exist_ok=True)        
        os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)
       

    def fetch_page(self, 
                   url_model: UrlModel, 
                   provider: str = DEFAULT_PROVIDER, 
                   api_token: str = None, 
                   extract_blocks_flag: bool = True, 
                   word_count_threshold = MIN_WORD_THRESHOLD,
                   use_cached_html: bool = False,
                   extraction_strategy: ExtractionStrategy = LLMExtractionStrategy(),
                   chunking_strategy: ChunkingStrategy = RegexChunking(),
                   **kwargs                   
                   ) -> CrawlResult:

        # make sure word_count_threshold is not lesser than MIN_WORD_THRESHOLD
        if word_count_threshold < MIN_WORD_THRESHOLD:
            word_count_threshold = MIN_WORD_THRESHOLD
            
        # Check cache first
        cached = get_cached_url(self.db_path, str(url_model.url))
        if cached and not url_model.forced:
            return CrawlResult(**{
                "url": cached[0],
                "html": cached[1],
                "cleaned_html": cached[2],
                "markdown": cached[3],
                "parsed_json": cached[4],
                "success": cached[5],
                "error_message": ""
            })
            

        # Initialize WebDriver for crawling
        t = time.time()
        try:
            html = self.crawler_strategy.crawl(str(url_model.url))
            success = True
            error_message = ""
        except Exception as e:
            html = ""
            success = False
            error_message = str(e)        
        
        # Extract content from HTML
        result = get_content_of_website(html, word_count_threshold)
        cleaned_html = result.get('cleaned_html', html)
        markdown = result.get('markdown', "")
        
        # Print a profession LOG style message, show time taken and say crawling is done
        print(f"[LOG] 🚀 Crawling done for {url_model.url}, success: {success}, time taken: {time.time() - t} seconds")
        

        parsed_json = []
        if extract_blocks_flag:
            print(f"[LOG] 🚀 Extracting semantic blocks for {url_model.url}")
            t = time.time()
            # Split markdown into sections
            sections = chunking_strategy.chunk(markdown)                          
            # sections = merge_chunks_based_on_token_threshold(sections, CHUNK_TOKEN_THRESHOLD)

            parsed_json = extraction_strategy.run(str(url_model.url), sections, provider, api_token)
            parsed_json = json.dumps(parsed_json)
            
            
            print(f"[LOG] 🚀 Extraction done for {url_model.url}, time taken: {time.time() - t} seconds.")
        else:
            parsed_json = "{}"
            print(f"[LOG] 🚀 Skipping extraction for {url_model.url}")

        # Cache the result
        cleaned_html = beautify_html(cleaned_html)
        cache_url(self.db_path, str(url_model.url), html, cleaned_html, markdown, parsed_json, success)

        return CrawlResult(
            url=str(url_model.url), 
            html=html, 
            cleaned_html=cleaned_html, 
            markdown=markdown, 
            parsed_json=parsed_json, 
            success=success, 
            error_message=error_message
        )

    def fetch_pages(self, url_models: List[UrlModel], provider: str = DEFAULT_PROVIDER, api_token: str = None, 
                    extract_blocks_flag: bool = True, word_count_threshold=MIN_WORD_THRESHOLD,
                    use_cached_html: bool = False, extraction_strategy: ExtractionStrategy = LLMExtractionStrategy(),
                    chunking_strategy: ChunkingStrategy = RegexChunking(), **kwargs) -> List[CrawlResult]:
        
        def fetch_page_wrapper(url_model, *args, **kwargs):
            return self.fetch_page(url_model, *args, **kwargs)

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(fetch_page_wrapper, url_models, 
                                        [provider] * len(url_models), 
                                        [api_token] * len(url_models),
                                        [extract_blocks_flag] * len(url_models),
                                        [word_count_threshold] * len(url_models),
                                        [use_cached_html] * len(url_models),
                                        [extraction_strategy] * len(url_models),
                                        [chunking_strategy] * len(url_models),
                                        *[kwargs] * len(url_models)))

        return results