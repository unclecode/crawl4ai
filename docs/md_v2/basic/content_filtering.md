# Content Filtering in Crawl4AI

This guide explains how to use content filtering strategies in Crawl4AI to extract the most relevant information from crawled web pages. You'll learn how to use the built-in `BM25ContentFilter` and how to create your own custom content filtering strategies.

## Relevance Content Filter

The `RelevanceContentFilter` is an abstract class providing a common interface for content filtering strategies. Specific algorithms, like `PruningContentFilter` or `BM25ContentFilter`, inherit from this class and implement the `filter_content` method. This method takes the HTML content as input and returns a list of filtered text blocks.

## Pruning Content Filter

The `PruningContentFilter` removes less relevant nodes based on metrics like text density, link density, and tag importance. Nodes that fall below a defined threshold are pruned, leaving only high-value content.

### Usage

```python
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter

config = CrawlerRunConfig(
    content_filter=PruningContentFilter(
        min_word_threshold=5,
        threshold_type='dynamic',
        threshold=0.45
    ),
    fit_markdown=True  # Activates markdown fitting
)

result = await crawler.arun(url="https://example.com", config=config)

if result.success:
    print(f"Cleaned Markdown:\n{result.fit_markdown}")
```

### Parameters

- **`min_word_threshold`**: (Optional) Minimum number of words a node must contain to be considered relevant. Nodes with fewer words are automatically pruned.
- **`threshold_type`**: (Optional, default 'fixed') Controls how pruning thresholds are calculated:
  - `'fixed'`: Uses a constant threshold value for all nodes.
  - `'dynamic'`: Adjusts thresholds based on node properties (e.g., tag importance, text/link ratios).
- **`threshold`**: (Optional, default 0.48) Base threshold for pruning:
  - Fixed: Nodes scoring below this value are removed.
  - Dynamic: This value adjusts based on node characteristics.

### How It Works

The algorithm evaluates each node using:
- **Text density**: Ratio of text to overall content.
- **Link density**: Proportion of text within links.
- **Tag importance**: Weights based on HTML tag type (e.g., `<article>`, `<p>`, `<div>`).
- **Content quality**: Metrics like text length and structural importance.

## BM25 Algorithm

The `BM25ContentFilter` uses the BM25 algorithm to rank and extract text chunks based on relevance to a search query or page metadata.

### Usage

```python
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter

config = CrawlerRunConfig(
    content_filter=BM25ContentFilter(user_query="fruit nutrition health"),
    fit_markdown=True  # Activates markdown fitting
)

result = await crawler.arun(url="https://example.com", config=config)

if result.success:
    print(f"Filtered Content:\n{result.extracted_content}")
    print(f"\nFiltered Markdown:\n{result.fit_markdown}")
    print(f"\nFiltered HTML:\n{result.fit_html}")
else:
    print("Error:", result.error_message)
```

### Parameters

- **`user_query`**: (Optional) A string representing the search query. If not provided, the filter extracts metadata (title, description, keywords) and uses it as the query.
- **`bm25_threshold`**: (Optional, default 1.0) Threshold controlling relevance:
  - Higher values return stricter, more relevant results.
  - Lower values include more lenient filtering.

