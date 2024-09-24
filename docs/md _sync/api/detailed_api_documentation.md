# Detailed API Documentation

## Overview

This section provides comprehensive documentation for the Crawl4AI API, covering all classes, methods, and their parameters. This guide will help you understand how to utilize the API to its full potential, enabling efficient web crawling and data extraction.

## WebCrawler Class

The `WebCrawler` class is the primary interface for crawling web pages and extracting data.

### Initialization

```python
from crawl4ai import WebCrawler

crawler = WebCrawler()
```

### Methods

#### `warmup()`

Prepares the crawler for use, such as loading necessary models.

```python
crawler.warmup()
```

#### `run(url: str, **kwargs) -> CrawlResult`

Crawls the specified URL and returns the result.

- **Parameters:**
  - `url` (str): The URL to crawl.
  - `**kwargs`: Additional parameters for customization.

- **Returns:**
  - `CrawlResult`: An object containing the crawl result.

- **Example:**

```python
result = crawler.run(url="https://www.nbcnews.com/business")
print(result)
```

### CrawlResult Class

Represents the result of a crawl operation.

- **Attributes:**
  - `url` (str): The URL of the crawled page.
  - `html` (str): The raw HTML of the page.
  - `success` (bool): Whether the crawl was successful.
  - `cleaned_html` (Optional[str]): The cleaned HTML.
  - `media` (Dict[str, List[Dict]]): Media tags in the page (images, audio, video).
  - `links` (Dict[str, List[Dict]]): Links in the page (external, internal).
  - `screenshot` (Optional[str]): Base64 encoded screenshot.
  - `markdown` (Optional[str]): Extracted content in Markdown format.
  - `extracted_content` (Optional[str]): Extracted meaningful content.
  - `metadata` (Optional[dict]): Metadata from the page.
  - `error_message` (Optional[str]): Error message if any.

## CrawlerStrategy Classes

The `CrawlerStrategy` classes define how the web crawling is executed.

### CrawlerStrategy Base Class

An abstract base class for different crawler strategies.

#### Methods

- **`crawl(url: str, **kwargs) -> str`**: Crawls the specified URL.
- **`take_screenshot(save_path: str)`**: Takes a screenshot of the current page.
- **`update_user_agent(user_agent: str)`**: Updates the user agent for the browser.
- **`set_hook(hook_type: str, hook: Callable)`**: Sets a hook for various events.

### LocalSeleniumCrawlerStrategy Class

Uses Selenium to crawl web pages.

#### Initialization

```python
from crawl4ai.crawler_strategy import LocalSeleniumCrawlerStrategy

strategy = LocalSeleniumCrawlerStrategy(js_code=["console.log('Hello, world!');"])
```

#### Methods

- **`crawl(url: str, **kwargs)`**: Crawls the specified URL.
- **`take_screenshot(save_path: str)`**: Takes a screenshot of the current page.
- **`update_user_agent(user_agent: str)`**: Updates the user agent for the browser.
- **`set_hook(hook_type: str, hook: Callable)`**: Sets a hook for various events.

#### Example

```python
result = strategy.crawl("https://www.example.com")
strategy.take_screenshot("screenshot.png")
strategy.update_user_agent("Mozilla/5.0")
strategy.set_hook("before_get_url", lambda: print("About to get URL"))
```

## ChunkingStrategy Classes

The `ChunkingStrategy` classes define how the text from a web page is divided into chunks.

### RegexChunking Class

Splits text using regular expressions.

#### Initialization

```python
from crawl4ai.chunking_strategy import RegexChunking

chunker = RegexChunking(patterns=[r'\n\n'])
```

#### Methods

- **`chunk(text: str) -> List[str]`**: Splits the text into chunks.

#### Example

```python
chunks = chunker.chunk("This is a sample text. It will be split into chunks.")
```

### NlpSentenceChunking Class

Uses NLP to split text into sentences.

#### Initialization

```python
from crawl4ai.chunking_strategy import NlpSentenceChunking

chunker = NlpSentenceChunking()
```

#### Methods

- **`chunk(text: str) -> List[str]`**: Splits the text into sentences.

#### Example

```python
chunks = chunker.chunk("This is a sample text. It will be split into sentences.")
```

### TopicSegmentationChunking Class

Uses the TextTiling algorithm to segment text into topics.

#### Initialization

```python
from crawl4ai.chunking_strategy import TopicSegmentationChunking

chunker = TopicSegmentationChunking(num_keywords=3)
```

#### Methods

- **`chunk(text: str) -> List[str]`**: Splits the text into topic-based segments.

#### Example

```python
chunks = chunker.chunk("This is a sample text. It will be split into topic-based segments.")
```

### FixedLengthWordChunking Class

Splits text into chunks of fixed length based on the number of words.

#### Initialization

```python
from crawl4ai.chunking_strategy import FixedLengthWordChunking

chunker = FixedLengthWordChunking(chunk_size=100)
```

#### Methods

- **`chunk(text: str) -> List[str]`**: Splits the text into fixed-length word chunks.

#### Example

```python
chunks = chunker.chunk("This is a sample text. It will be split into fixed-length word chunks.")
```

### SlidingWindowChunking Class

Uses a sliding window approach to chunk text.

#### Initialization

```python
from crawl4ai.chunking_strategy import SlidingWindowChunking

chunker = SlidingWindowChunking(window_size=100, step=50)
```

#### Methods

- **`chunk(text: str) -> List[str]`**: Splits the text using a sliding window approach.

#### Example

```python
chunks = chunker.chunk("This is a sample text. It will be split using a sliding window approach.")
```

## ExtractionStrategy Classes

The `ExtractionStrategy` classes define how meaningful content is extracted from the chunks.

### NoExtractionStrategy Class

Returns the entire HTML content without any modification.

#### Initialization

```python
from crawl4ai.extraction_strategy import NoExtractionStrategy

extractor = NoExtractionStrategy()
```

#### Methods

- **`extract(url: str, html: str) -> str`**: Returns the HTML content.

#### Example

```python
extracted_content = extractor.extract(url="https://www.example.com", html="<html>...</html>")
```

### LLMExtractionStrategy Class

Uses a Language Model to extract meaningful blocks from HTML.

#### Initialization

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy

extractor = LLMExtractionStrategy(provider='openai', api_token='your_api_token', instruction='Extract only news about AI.')
```

#### Methods

- **`extract(url: str, html: str) -> str`**: Extracts meaningful content using the LLM.

#### Example

```python
extracted_content = extractor.extract(url="https://www.example.com", html="<html>...</html>")
```

### CosineStrategy Class

Clusters text chunks based on cosine similarity.

#### Initialization

```python
from crawl4ai.extraction_strategy import CosineStrategy

extractor = CosineStrategy(semantic_filter="finance", word_count_threshold=10)
```

#### Methods

- **`extract(url: str, html: str) -> str`**: Extracts clusters of text based on cosine similarity.

#### Example

```python
extracted_content = extractor.extract(url="https://www.example.com", html="<html>...</html>")
```

### TopicExtractionStrategy Class

Uses the TextTiling algorithm to segment HTML content into topics and extract keywords.

#### Initialization

```python
from crawl4ai.extraction_strategy import TopicExtractionStrategy

extractor = TopicExtractionStrategy(num_keywords=3)
```

#### Methods

- **`extract(url: str, html: str) -> str`**: Extracts topic-based segments and keywords.

#### Example

```python
extracted_content = extractor.extract(url="https://www.example.com", html="<html>...</html>")
```

## Parameters

Here are the common parameters used across various classes and methods:

- **`url`** (str): The URL to crawl.
- **`html`** (str): The HTML content of the page.
- **`user_agent`** (str): The user agent for the HTTP requests.
- **`patterns`** (list): A list of regular expression patterns for chunking.
- **`num_keywords`** (int): Number of keywords for topic extraction.
- **`chunk_size`** (int): Number of words in each chunk.
- **`window_size`** (int): Number of words in the sliding window.
- **`step`** (int): Step size for the sliding window.
- **`semantic_filter`** (str): Keywords for filtering relevant documents.
- **`word_count_threshold`** (int): Minimum number of words per cluster.
- **`max_dist`** (float): Maximum cophenetic distance for clustering.
- **`linkage_method`** (str): Linkage method for hierarchical clustering.
- **`top_k`** (int): Number of top categories to extract.
- **`provider`** (

str): Provider for language model completions.
- **`api_token`** (str): API token for the provider.
- **`instruction`** (str): Instruction to guide the LLM extraction.

## Conclusion

This detailed API documentation provides a thorough understanding of the classes, methods, and parameters in the Crawl4AI library. With this knowledge, you can effectively use the API to perform advanced web crawling and data extraction tasks.