# Crawl4AI

Welcome to the official documentation for Crawl4AI! 🕷️🤖 Crawl4AI is an open-source Python library designed to simplify web crawling and extract useful information from web pages. This documentation will guide you through the features, usage, and customization of Crawl4AI.

## Introduction

Crawl4AI has one clear task: to make crawling and data extraction from web pages easy and efficient, especially for large language models (LLMs) and AI applications. Whether you are using it as a REST API or a Python library, Crawl4AI offers a robust and flexible solution with full asynchronous support.

## Quick Start

Here's a quick example to show you how easy it is to use Crawl4AI with its new asynchronous capabilities:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://www.nbcnews.com/business")

        # Print the extracted content
        print(result.markdown)

# Run the async main function
asyncio.run(main())
```

### Explanation

1. **Importing the Library**: We start by importing the `AsyncWebCrawler` class from the `crawl4ai` library and the `asyncio` module.
2. **Creating an Async Context**: We use an async context manager to create an instance of `AsyncWebCrawler`.
3. **Running the Crawler**: The `arun()` method is used to asynchronously crawl the specified URL and extract meaningful content.
4. **Printing the Result**: The extracted content is printed, showcasing the data extracted from the web page.
5. **Running the Async Function**: We use `asyncio.run()` to execute our async main function.

## Documentation Structure

This documentation is organized into several sections to help you navigate and find the information you need quickly:

### [Home](index.md)

An introduction to Crawl4AI, including a quick start guide and an overview of the documentation structure.

### [Installation](installation.md)

Instructions on how to install Crawl4AI and its dependencies.

### [Introduction](introduction.md)

A detailed introduction to Crawl4AI, its features, and how it can be used for various web crawling and data extraction tasks.

### [Quick Start](quickstart.md)

A step-by-step guide to get you up and running with Crawl4AI, including installation instructions and basic usage examples.

### [Examples](examples/index.md)

This section contains practical examples demonstrating different use cases of Crawl4AI:

- [Structured Data Extraction](examples/json_css_extraction.md)
- [LLM Extraction](examples/llm_extraction.md)
- [JS Execution & CSS Filtering](examples/js_execution_css_filtering.md)
- [Hooks & Auth](examples/hooks_auth.md)
- [Summarization](examples/summarization.md)
- [Research Assistant](examples/research_assistant.md)

### [Full Details of Using Crawler](full_details/crawl_request_parameters.md)

Comprehensive details on using the crawler, including:

- [Crawl Request Parameters](full_details/crawl_request_parameters.md)
- [Crawl Result Class](full_details/crawl_result_class.md)
- [Session Based Crawling](full_details/session_based_crawling.md)
- [Advanced Structured Data Extraction JsonCssExtraction](full_details/advanced_jsoncss_extraction.md)
- [Advanced Features](full_details/advanced_features.md)
- [Chunking Strategies](full_details/chunking_strategies.md)
- [Extraction Strategies](full_details/extraction_strategies.md)

### [Change Log](changelog.md)

A log of all changes, updates, and improvements made to Crawl4AI.

### [Contact](contact.md)

Information on how to get in touch with the developers, report issues, and contribute to the project.

## Get Started

To get started with Crawl4AI, follow the quick start guide above or explore the detailed sections of this documentation. Whether you are a beginner or an advanced user, Crawl4AI has something to offer to make your web crawling and data extraction tasks easier, more efficient, and now fully asynchronous.

Happy Crawling! 🕸️🚀