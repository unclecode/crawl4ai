# Crawl4AI v0.2.77

Welcome to the official documentation for Crawl4AI! 🕷️🤖 Crawl4AI is an open-source Python library designed to simplify web crawling and extract useful information from web pages. This documentation will guide you through the features, usage, and customization of Crawl4AI.


## Try the [Demo](demo.md)

Just try it now and crawl different pages to see how it works. You can set the links, see the structures of the output, and also view the Python sample code on how to run it. The old demo is available at [/old_demo](/old) where you can see more details.

## Introduction

Crawl4AI has one clear task: to make crawling and data extraction from web pages easy and efficient, especially for large language models (LLMs) and AI applications. Whether you are using it as a REST API or a Python library, Crawl4AI offers a robust and flexible solution.

## Quick Start

Here's a quick example to show you how easy it is to use Crawl4AI:

```python
from crawl4ai import WebCrawler

# Create an instance of WebCrawler
crawler = WebCrawler()

# Warm up the crawler (load necessary models)
crawler.warmup()

# Run the crawler on a URL
result = crawler.run(url="https://www.nbcnews.com/business")

# Print the extracted content
print(result.extracted_content)
```

### Explanation

1. **Importing the Library**: We start by importing the `WebCrawler` class from the `crawl4ai` library.
2. **Creating an Instance**: An instance of `WebCrawler` is created.
3. **Warming Up**: The `warmup()` method prepares the crawler by loading necessary models and settings.
4. **Running the Crawler**: The `run()` method is used to crawl the specified URL and extract meaningful content.
5. **Printing the Result**: The extracted content is printed, showcasing the data extracted from the web page.

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

- [LLM Extraction](examples/llm_extraction.md)
- [JS Execution & CSS Filtering](examples/js_execution_css_filtering.md)
- [Hooks & Auth](examples/hooks_auth.md)
- [Summarization](examples/summarization.md)
- [Research Assistant](examples/research_assistant.md)

### [Full Details of Using Crawler](full_details/crawl_request_parameters.md)

Comprehensive details on using the crawler, including:

- [Crawl Request Parameters](full_details/crawl_request_parameters.md)
- [Crawl Result Class](full_details/crawl_result_class.md)
- [Advanced Features](full_details/advanced_features.md)
- [Chunking Strategies](full_details/chunking_strategies.md)
- [Extraction Strategies](full_details/extraction_strategies.md)

### [API Reference](api/core_classes_and_functions.md)

Detailed documentation of the API, covering:

- [Core Classes and Functions](api/core_classes_and_functions.md)
- [Detailed API Documentation](api/detailed_api_documentation.md)

### [Change Log](changelog.md)

A log of all changes, updates, and improvements made to Crawl4AI.

### [Contact](contact.md)

Information on how to get in touch with the developers, report issues, and contribute to the project.

## Get Started

To get started with Crawl4AI, follow the quick start guide above or explore the detailed sections of this documentation. Whether you are a beginner or an advanced user, Crawl4AI has something to offer to make your web crawling and data extraction tasks easier and more efficient.

Happy Crawling! 🕸️🚀
