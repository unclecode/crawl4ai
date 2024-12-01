# Content Filtering in Crawl4AI

This guide explains how to use content filtering strategies in Crawl4AI to extract the most relevant information from crawled web pages.  You'll learn how to use the built-in `BM25ContentFilter` and how to create your own custom content filtering strategies.

## Relevance Content Filter

The `RelevanceContentFilter` is an abstract class that provides a common interface for content filtering strategies. Specific filtering algorithms, like `PruningContentFilter` or `BM25ContentFilter`, inherit from this class and implement the `filter_content` method. This method takes the HTML content as input and returns a list of filtered text blocks.


## Pruning Content Filter

The `PruningContentFilter` is a tree-shaking algorithm that analyzes the HTML DOM structure and removes less relevant nodes based on various metrics like text density, link density, and tag importance. It evaluates each node using a composite scoring system and "prunes" nodes that fall below a certain threshold.

### Usage

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.content_filter_strategy import PruningContentFilter

async def filter_content(url):
    async with AsyncWebCrawler() as crawler:
        content_filter = PruningContentFilter(
            min_word_threshold=5,
            threshold_type='dynamic',
            threshold=0.45
        )
        result = await crawler.arun(url=url, extraction_strategy=content_filter, fit_markdown=True)
        if result.success:
            print(f"Cleaned Markdown:\n{result.fit_markdown}")
```

### Parameters

- **`min_word_threshold`**: (Optional) Minimum number of words a node must contain to be considered relevant. Nodes with fewer words are automatically pruned.

- **`threshold_type`**: (Optional, default 'fixed') Controls how pruning thresholds are calculated:
  - `'fixed'`: Uses a constant threshold value for all nodes
  - `'dynamic'`: Adjusts threshold based on node characteristics like tag importance and text/link ratios

- **`threshold`**: (Optional, default 0.48) Base threshold value for node pruning:
  - For fixed threshold: Nodes scoring below this value are removed
  - For dynamic threshold: This value is adjusted based on node properties

### How It Works

The pruning algorithm evaluates each node using multiple metrics:
- Text density: Ratio of actual text to overall node content
- Link density: Proportion of text within links
- Tag importance: Weight based on HTML tag type (e.g., article, p, div)
- Content quality: Metrics like text length and structural importance

Nodes scoring below the threshold are removed, effectively "shaking" less relevant content from the DOM tree. This results in a cleaner document containing only the most relevant content blocks.

The algorithm is particularly effective for:
- Removing boilerplate content
- Eliminating navigation menus and sidebars
- Preserving main article content
- Maintaining document structure while removing noise


## BM25 Algorithm

The `BM25ContentFilter` uses the BM25 algorithm, a ranking function used in information retrieval to estimate the relevance of documents to a given search query. In Crawl4AI, this algorithm helps to identify and extract text chunks that are most relevant to the page's metadata or a user-specified query.

### Usage

To use the `BM25ContentFilter`, initialize it and then pass it as the `extraction_strategy` parameter to the `arun` method of the crawler.

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.content_filter_strategy import BM25ContentFilter

async def filter_content(url, query=None):
    async with AsyncWebCrawler() as crawler:
        content_filter = BM25ContentFilter(user_query=query)
        result = await crawler.arun(url=url, extraction_strategy=content_filter, fit_markdown=True) # Set fit_markdown flag to True to trigger BM25 filtering
        if result.success:
            print(f"Filtered Content (JSON):\n{result.extracted_content}")
            print(f"\nFiltered Markdown:\n{result.fit_markdown}") # New field in CrawlResult object
            print(f"\nFiltered HTML:\n{result.fit_html}") # New field in CrawlResult object. Note that raw HTML may have tags re-organized due to internal parsing.
        else:
            print("Error:", result.error_message)

# Example usage:
asyncio.run(filter_content("https://en.wikipedia.org/wiki/Apple", "fruit nutrition health")) # with query
asyncio.run(filter_content("https://en.wikipedia.org/wiki/Apple")) # without query, metadata will be used as the query.

```

### Parameters

- **`user_query`**:  (Optional) A string representing the search query. If not provided, the filter extracts relevant metadata (title, description, keywords) from the page and uses that as the query.
- **`bm25_threshold`**: (Optional, default 1.0)  A float value that controls the threshold for relevance.  Higher values result in stricter filtering, returning only the most relevant text chunks. Lower values result in more lenient filtering.


## Fit Markdown Flag

Setting the `fit_markdown` flag to `True` in the `arun` method activates the BM25 content filtering during the crawl. The `fit_markdown` parameter instructs the scraper to extract and clean the HTML, primarily to prepare for a Large Language Model that cannot process large amounts of data. Setting this flag not only improves the quality of the extracted content but also adds the filtered content to two new attributes in the returned  `CrawlResult` object: `fit_markdown` and `fit_html`.


## Custom Content Filtering Strategies

You can create your own custom filtering strategies by inheriting from the `RelevantContentFilter` class and implementing the `filter_content` method.  This allows you to tailor the filtering logic to your specific needs.

```python
from crawl4ai.content_filter_strategy import RelevantContentFilter
from bs4 import BeautifulSoup, Tag
from typing import List

class MyCustomFilter(RelevantContentFilter):
    def filter_content(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        # Implement custom filtering logic here
        # Example: extract all paragraphs within divs with class "article-body"
        filtered_paragraphs = []
        for tag in soup.select("div.article-body p"):
            if isinstance(tag, Tag):
                filtered_paragraphs.append(str(tag)) # Add the cleaned HTML element.  
        return filtered_paragraphs



async def custom_filter_demo(url: str):
    async with AsyncWebCrawler() as crawler:
        custom_filter = MyCustomFilter()
        result = await crawler.arun(url, extraction_strategy=custom_filter)
        if result.success:
            print(result.extracted_content)

```

This example demonstrates extracting paragraphs from a specific div class.  You can customize this logic to implement different filtering strategies, use regular expressions, analyze text density, or apply other relevant techniques.

## Conclusion

Content filtering strategies provide a powerful way to refine the output of your crawls. By using `BM25ContentFilter` or creating custom strategies, you can focus on the most pertinent information and improve the efficiency of your data processing pipeline.
