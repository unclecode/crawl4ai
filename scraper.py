import os
import asyncio
from urllib.parse import urlparse

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
)
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    URLPatternFilter,
    DomainFilter,
)

async def scrape_with_crawl4ai(base_url, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Set up filters to control the crawl
    filter_chain = FilterChain(
        [
            # Only stay on the docs.crawl4ai.com domain
            DomainFilter(allowed_domains=["docs.crawl4ai.com"]),
            # Only scrape pages that look like documentation
            URLPatternFilter(
                patterns=[
                    "*/core/*",
                    "*/advanced/*",
                    "*/extraction/*",
                    "*/api/*",
                    # Include the root page as well
                    "https://docs.crawl4ai.com/",
                ]
            ),
        ]
    )

    # 2. Configure the deep crawl strategy
    # We use BFS (Breadth-First Search) to explore the site level by level.
    # A depth of 5 is likely sufficient to cover the whole doc site.
    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=5,
        filter_chain=filter_chain,
    )

    # 3. Configure the crawler run
    # We use the deep crawl strategy and a markdown generator.
    config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_strategy,
        markdown_generator=DefaultMarkdownGenerator(),
        verbose=True,  # To see the progress
    )

    # 4. Run the crawler
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=base_url, config=config)

    # 5. Process and save the results
    for result in results:
        if result.success and result.markdown:
            # Create a filename from the URL
            path = urlparse(result.url).path
            if path == '/' or path == '':
                filename = 'index.md'
            else:
                # Sanitize the path to create a valid filename
                # e.g., /core/quickstart/ -> quickstart.md
                filename = os.path.basename(path.strip('/'))
                if not filename.endswith('.md'):
                    filename += '.md'

            if filename == '.md' or not filename:
                filename = 'index.md'

            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result.markdown.raw_markdown)
            print(f"Saved {result.url} to {filepath}")
        elif not result.success:
            print(f"Failed to crawl {result.url}: {result.error_message}")

if __name__ == '__main__':
    BASE_URL = 'https://docs.crawl4ai.com/'
    # I'll use a new directory to compare with the old results
    OUTPUT_DIR = 'documentation_crawl4ai'
    asyncio.run(scrape_with_crawl4ai(BASE_URL, OUTPUT_DIR))
