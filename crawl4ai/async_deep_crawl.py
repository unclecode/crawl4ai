# crawl4ai/async_deep_crawl.py

"""Remember:
# Update CrawlerRunConfig in async_configs.py (additional field)
class CrawlerRunConfig(BaseModel):
    deep_crawl_strategy: Optional[DeepCrawlStrategy] = Field(
        default=None,
        description="Strategy for deep crawling websites"
    )
    # ... other existing fields remain unchanged

# In AsyncWebCrawler class (partial implementation)
class AsyncWebCrawler:
    def __init__(self, *args, **kwargs):
        # Existing initialization
        self._deep_handler = DeepCrawlHandler(self)
        self.arun = self._deep_handler(self.arun)  # Decorate original method

    async def arun(self, url: str, config: Optional[CrawlerRunConfig] = None, **kwargs):
        # ... existing implementation
"""

import asyncio
from collections import deque
from functools import wraps
from typing import AsyncGenerator, List, Optional, Set, Union, TypeVar
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .async_webcrawler import AsyncWebCrawler, CrawlResult
    from .async_configs import CrawlerRunConfig
    from .async_dispatcher import  MemoryAdaptiveDispatcher

    CrawlResultT = TypeVar('CrawlResultT', bound=CrawlResult)
    RunManyReturn = Union[CrawlResultT, List[CrawlResultT], AsyncGenerator[CrawlResultT, None]]


class DeepCrawlStrategy(BaseModel):
    """Base class for deep crawling strategies."""
    max_depth: int = Field(default=3, description="Maximum crawl depth from initial URL")
    include_external: bool = Field(default=False, description="Follow links to external domains")
    
    class Config:
        arbitrary_types_allowed = True

    async def run(
        self,
        crawler: "AsyncWebCrawler",
        start_url: str,
        config: "CrawlerRunConfig"
    ) -> "RunManyReturn":
        """Execute the crawling strategy."""
        raise NotImplementedError

class BreadthFirstSearchStrategy(DeepCrawlStrategy):
    """Breadth-first search implementation for deep crawling."""
    
    async def run(
        self, 
        crawler: "AsyncWebCrawler", 
        start_url: str, 
        config: "CrawlerRunConfig"
    ) -> "RunManyReturn":
        """BFS implementation using arun_many for batch processing."""
        async def stream_results():
            """Inner async generator for streaming results."""
            nonlocal crawler, start_url, config
            base_domain = urlparse(start_url).netloc
            queue = deque([(start_url, 0)])
            visited: Set[str] = set()
            
            # Create config copy without deep strategy for child requests
            child_config = config.copy(update={
                'deep_crawl_strategy': None,
                'stream': False  # Process levels sequentially
            })

            while queue:
                current_url, depth = queue.popleft()
                
                if depth > self.max_depth or current_url in visited:
                    continue
                    
                visited.add(current_url)

                # Process current level using arun_many
                batch_results = await crawler.arun_many(
                    urls=[current_url],
                    config=child_config,
                    dispatcher=MemoryAdaptiveDispatcher()
                )

                for result in batch_results:
                    yield result

                    # Queue next level if within depth limit
                    if depth < self.max_depth:
                        new_urls = self._extract_links(result, base_domain)
                        for url in new_urls:
                            if url not in visited:
                                queue.append((url, depth + 1))

        # Handle streaming vs non-streaming
        if config.stream:
            return stream_results()
        else:
            results: List[CrawlResultT] = []
            async for result in stream_results():
                results.append(result)
            return results

    def _extract_links(self, result: "CrawlResult", base_domain: str) -> List[str]:
        """Extract links from crawl result with domain filtering."""
        internal = result.links.get('internal', [])
        external = result.links.get('external', []) if self.include_external else []
        
        return [
            url for url in internal + external
            if self._same_domain(url, base_domain) or self.include_external
        ]

    def _same_domain(self, url: str, base_domain: str) -> bool:
        """Check if URL belongs to the base domain."""
        return urlparse(url).netloc == base_domain

class DeepCrawlHandler:
    """Decorator that adds deep crawling capabilities to arun."""
    
    def __init__(self, crawler: "AsyncWebCrawler"):
        self.crawler = crawler

    def __call__(self, original_arun):
        @wraps(original_arun)
        async def wrapped_arun(url: str, config: Optional["CrawlerRunConfig"] = None, **kwargs):
            # First run the original arun
            initial_result = await original_arun(url, config=config, **kwargs)
            
            if config and config.deep_crawl_strategy:
                # Execute deep crawl strategy if configured
                return await config.deep_crawl_strategy.run(
                    crawler=self.crawler,
                    start_url=url,
                    config=config
                )
            
            return initial_result

        return wrapped_arun

async def main():
    """Example deep crawl of documentation site."""
    config = CrawlerRunConfig(
        deep_crawl_strategy=BreadthFirstSearchStrategy(
            max_depth=2,
            include_external=False
        ),
        stream=True,
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        print("Starting deep crawl in streaming mode:")
        async for result in await crawler.arun(
            url="https://docs.crawl4ai.com",
            config=config
        ):
            print(f"→ {result.url} (Depth: {result.metadata.get('depth', 0)})")

        print("\nStarting deep crawl in batch mode:")
        config.stream = False
        results = await crawler.arun(
            url="https://docs.crawl4ai.com",
            config=config
        )
        print(f"Crawled {len(results)} pages")
        print(f"Example page: {results[0].url}")

if __name__ == "__main__":
    asyncio.run(main())