
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from ..crawl4ai import WebCrawler
from ..crawl4ai.crawler_strategy import CrawlerStrategy
from ..crawl4ai.extraction_strategy import ExtractionStrategy
from ..crawl4ai.chunking_strategy import ChunkingStrategy, RegexChunking
from ..crawl4ai.config import MIN_WORD_THRESHOLD
from typing import List, Optional, Iterator

class Crawl4aiLoader(BaseLoader):
    """Crawl4ai loader for web crawling and extract useful information from web pages"""
    def __init__(self,
                 url: str, 
                 word_count_threshold: Optional[int]=MIN_WORD_THRESHOLD,
                 extraction_strategy: Optional[ExtractionStrategy]=None,
                 chunking_strategy: Optional[ChunkingStrategy]= RegexChunking(),
                 bypass_cache: Optional[bool]=False,
                 css_selector: Optional[str]=None,
                 screenshot: Optional[bool]=False,
                 user_agent: Optional[str]=None,
                 crawler_strategy: Optional[CrawlerStrategy]=None,
                 always_by_pass_cache: Optional[bool]=False,
                 verbose: Optional[bool]=False) -> None:
        crawler = WebCrawler(crawler_strategy, always_by_pass_cache, verbose)
        crawler.warmup()
        self.crawler = crawler
        self.url = url
        self.word_count_threshold=word_count_threshold
        self.extraction_strategy=extraction_strategy
        self.chunking_strategy=chunking_strategy
        self.bypass_cache=bypass_cache
        self.css_selector=css_selector
        self.screenshot=screenshot
        self.user_agent = user_agent
        self.verbose=verbose
    def lazy_load(self) -> Iterator[Document]:
        crawlResult = self.crawler.run(
            url=self.url,
            word_count_threshold=self.word_count_threshold,
            extraction_strategy=self.extraction_strategy,
            chunking_strategy=self.chunking_strategy,
            bypass_cache=self.bypass_cache,
            css_selector=self.css_selector,
            screenshot=self.screenshot,
            user_agent=self.user_agent,
            verbose=self.verbose
        )
        if(self.extraction_strategy==None):
            yield Document(page_content=crawlResult.markdown, metadata=crawlResult)
        else:
            yield Document(page_content=crawlResult.extracted_content, metadata=crawlResult)