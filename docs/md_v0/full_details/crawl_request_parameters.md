# Crawl Request Parameters

The `run` function in Crawl4AI is designed to be highly configurable, allowing you to customize the crawling and extraction process to suit your needs. Below are the parameters you can use with the `run` function, along with their descriptions, possible values, and examples.

## Parameters

### url (str)
**Description:** The URL of the webpage to crawl.
**Required:** Yes
**Example:**
```python
url = "https://www.nbcnews.com/business"
```

### word_count_threshold (int)
**Description:** The minimum number of words a block must contain to be considered meaningful. The default value is `5`.
**Required:** No
**Default Value:** `5`
**Example:**
```python
word_count_threshold = 10
```

### extraction_strategy (ExtractionStrategy)
**Description:** The strategy to use for extracting content from the HTML. It must be an instance of `ExtractionStrategy`. If not provided, the default is `NoExtractionStrategy`.
**Required:** No
**Default Value:** `NoExtractionStrategy()`
**Example:**
```python
extraction_strategy = CosineStrategy(semantic_filter="finance")
```

### chunking_strategy (ChunkingStrategy)
**Description:** The strategy to use for chunking the text before processing. It must be an instance of `ChunkingStrategy`. The default value is `RegexChunking()`.
**Required:** No
**Default Value:** `RegexChunking()`
**Example:**
```python
chunking_strategy = NlpSentenceChunking()
```

### bypass_cache (bool)
**Description:** Whether to force a fresh crawl even if the URL has been previously crawled. The default value is `False`.
**Required:** No
**Default Value:** `False`
**Example:**
```python
bypass_cache = True
```

### css_selector (str)
**Description:** The CSS selector to target specific parts of the HTML for extraction. If not provided, the entire HTML will be processed.
**Required:** No
**Default Value:** `None`
**Example:**
```python
css_selector = "div.article-content"
```

### screenshot (bool)
**Description:** Whether to take screenshots of the page. The default value is `False`.
**Required:** No
**Default Value:** `False`
**Example:**
```python
screenshot = True
```

### user_agent (str)
**Description:** The user agent to use for the HTTP requests. If not provided, a default user agent will be used.
**Required:** No
**Default Value:** `None`
**Example:**
```python
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
```

### verbose (bool)
**Description:** Whether to enable verbose logging. The default value is `True`.
**Required:** No
**Default Value:** `True`
**Example:**
```python
verbose = True
```

### **kwargs
Additional keyword arguments that can be passed to customize the crawling process further. Some notable options include:

- **only_text (bool):** Whether to extract only text content, excluding HTML tags. Default is `False`.

**Example:**
```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    css_selector="p",
    only_text=True
)
```

## Example Usage

Here's an example of how to use the `run` function with various parameters:

```python
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import CosineStrategy
from crawl4ai.chunking_strategy import NlpSentenceChunking

# Create the WebCrawler instance 
crawler = WebCrawler() 

# Run the crawler with custom parameters
result = crawler.run(
    url="https://www.nbcnews.com/business",
    word_count_threshold=10,
    extraction_strategy=CosineStrategy(semantic_filter="finance"),
    chunking_strategy=NlpSentenceChunking(),
    bypass_cache=True,
    css_selector="div.article-content",
    screenshot=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    verbose=True,
    only_text=True
)

print(result)
```

This example demonstrates how to configure various parameters to customize the crawling and extraction process using Crawl4AI.
