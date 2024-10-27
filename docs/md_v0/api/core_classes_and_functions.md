# Core Classes and Functions

## Overview

In this section, we will delve into the core classes and functions that make up the Crawl4AI library. This includes the `WebCrawler` class, various `CrawlerStrategy` classes, `ChunkingStrategy` classes, and `ExtractionStrategy` classes. Understanding these core components will help you leverage the full power of Crawl4AI for your web crawling and data extraction needs.

## WebCrawler Class

The `WebCrawler` class is the main class you'll interact with. It provides the interface for crawling web pages and extracting data.

### Initialization

```python
from crawl4ai import WebCrawler

# Create an instance of WebCrawler
crawler = WebCrawler()
```

### Methods

- **`warmup()`**: Prepares the crawler for use, such as loading necessary models.
- **`run(url: str, **kwargs)`**: Runs the crawler on the specified URL with optional parameters for customization.

```python
crawler.warmup()
result = crawler.run(url="https://www.nbcnews.com/business")
print(result)
```

## CrawlerStrategy Classes

The `CrawlerStrategy` classes define how the web crawling is executed. The base class is `CrawlerStrategy`, which is extended by specific implementations like `LocalSeleniumCrawlerStrategy`.

### CrawlerStrategy Base Class

An abstract base class that defines the interface for different crawler strategies.

```python
from abc import ABC, abstractmethod

class CrawlerStrategy(ABC):
    @abstractmethod
    def crawl(self, url: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def take_screenshot(self, save_path: str):
        pass
    
    @abstractmethod
    def update_user_agent(self, user_agent: str):
        pass
    
    @abstractmethod
    def set_hook(self, hook_type: str, hook: Callable):
        pass
```

### LocalSeleniumCrawlerStrategy Class

A concrete implementation of `CrawlerStrategy` that uses Selenium to crawl web pages.

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

```python
result = strategy.crawl("https://www.example.com")
strategy.take_screenshot("screenshot.png")
strategy.update_user_agent("Mozilla/5.0")
strategy.set_hook("before_get_url", lambda: print("About to get URL"))
```

## ChunkingStrategy Classes

The `ChunkingStrategy` classes define how the text from a web page is divided into chunks. Here are a few examples:

### RegexChunking Class

Splits text using regular expressions.

```python
from crawl4ai.chunking_strategy import RegexChunking

chunker = RegexChunking(patterns=[r'\n\n'])
chunks = chunker.chunk("This is a sample text. It will be split into chunks.")
```

### NlpSentenceChunking Class

Uses NLP to split text into sentences.

```python
from crawl4ai.chunking_strategy import NlpSentenceChunking

chunker = NlpSentenceChunking()
chunks = chunker.chunk("This is a sample text. It will be split into sentences.")
```

## ExtractionStrategy Classes

The `ExtractionStrategy` classes define how meaningful content is extracted from the chunks. Here are a few examples:

### CosineStrategy Class

Clusters text chunks based on cosine similarity.

```python
from crawl4ai.extraction_strategy import CosineStrategy

extractor = CosineStrategy(semantic_filter="finance", word_count_threshold=10)
extracted_content = extractor.extract(url="https://www.example.com", html="<html>...</html>")
```

### LLMExtractionStrategy Class

Uses a Language Model to extract meaningful blocks from HTML.

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy

extractor = LLMExtractionStrategy(provider='openai', api_token='your_api_token', instruction='Extract only news about AI.')
extracted_content = extractor.extract(url="https://www.example.com", html="<html>...</html>")
```

## Conclusion

By understanding these core classes and functions, you can customize and extend Crawl4AI to suit your specific web crawling and data extraction needs. Happy crawling! 🕷️🤖

