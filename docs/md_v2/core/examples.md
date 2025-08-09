# Code Examples

This page provides a comprehensive list of example scripts that demonstrate various features and capabilities of Crawl4AI. Each example is designed to showcase specific functionality, making it easier for you to understand how to implement these features in your own projects.

## Getting Started Examples

| Example | Description | Link |
|---------|-------------|------|
| Hello World | A simple introductory example demonstrating basic usage of AsyncWebCrawler with JavaScript execution and content filtering. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/hello_world.py) |
| Quickstart | A comprehensive collection of examples showcasing various features including basic crawling, content cleaning, link analysis, JavaScript execution, CSS selectors, media handling, custom hooks, proxy configuration, screenshots, and multiple extraction strategies. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/quickstart.py) |
| Quickstart Set 1 | Basic examples for getting started with Crawl4AI. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/quickstart_examples_set_1.py) |
| Quickstart Set 2 | More advanced examples for working with Crawl4AI. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/quickstart_examples_set_2.py) |

## Browser & Crawling Features

| Example | Description | Link |
|---------|-------------|------|
| Built-in Browser | Demonstrates how to use the built-in browser capabilities. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/builtin_browser_example.py) |
| Browser Optimization | Focuses on browser performance optimization techniques. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/browser_optimization_example.py) |
| arun vs arun_many | Compares the `arun` and `arun_many` methods for single vs. multiple URL crawling. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/arun_vs_arun_many.py) |
| Multiple URLs | Shows how to crawl multiple URLs asynchronously. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/async_webcrawler_multiple_urls_example.py) |
| Page Interaction | Guide on interacting with dynamic elements through clicks. | [View Guide](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/tutorial_dynamic_clicks.md) |
| Crawler Monitor | Shows how to monitor the crawler's activities and status. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/crawler_monitor_example.py) |
| Full Page Screenshot & PDF | Guide on capturing full-page screenshots and PDFs from massive webpages. | [View Guide](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/full_page_screenshot_and_pdf_export.md) |

## Advanced Crawling & Deep Crawling

| Example | Description | Link |
|---------|-------------|------|
| Deep Crawling | An extensive tutorial on deep crawling capabilities, demonstrating BFS and BestFirst strategies, stream vs. non-stream execution, filters, scorers, and advanced configurations. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/deepcrawl_example.py) |
| Virtual Scroll | Comprehensive examples for handling virtualized scrolling on sites like Twitter, Instagram. Demonstrates different scrolling scenarios with local test server. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/virtual_scroll_example.py) |
| Adaptive Crawling | Demonstrates intelligent crawling that automatically determines when sufficient information has been gathered. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/adaptive_crawling/) |
| Dispatcher | Shows how to use the crawl dispatcher for advanced workload management. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/dispatcher_example.py) |
| Storage State | Tutorial on managing browser storage state for persistence. | [View Guide](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/storage_state_tutorial.md) |
| Network Console Capture | Demonstrates how to capture and analyze network requests and console logs. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/network_console_capture_example.py) |

## Extraction Strategies

| Example | Description | Link |
|---------|-------------|------|
| Extraction Strategies | Demonstrates different extraction strategies with various input formats (markdown, HTML, fit_markdown) and JSON-based extractors (CSS and XPath). | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/extraction_strategies_examples.py) |
| Scraping Strategies | Compares the performance of different scraping strategies. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/scraping_strategies_performance.py) |
| LLM Extraction | Demonstrates LLM-based extraction specifically for OpenAI pricing data. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/llm_extraction_openai_pricing.py) |
| LLM Markdown | Shows how to use LLMs to generate markdown from crawled content. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/llm_markdown_generator.py) |
| Summarize Page | Shows how to summarize web page content. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/summarize_page.py) |

## E-commerce & Specialized Crawling

| Example | Description | Link |
|---------|-------------|------|
| Amazon Product Extraction | Demonstrates how to extract structured product data from Amazon search results using CSS selectors. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/amazon_product_extraction_direct_url.py) |
| Amazon with Hooks | Shows how to use hooks with Amazon product extraction. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/amazon_product_extraction_using_hooks.py) |
| Amazon with JavaScript | Demonstrates using custom JavaScript for Amazon product extraction. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/amazon_product_extraction_using_use_javascript.py) |
| Crypto Analysis | Demonstrates how to crawl and analyze cryptocurrency data. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/crypto_analysis_example.py) |
| SERP API | Demonstrates using Crawl4AI with search engine result pages. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/serp_api_project_11_feb.py) |

## Anti-Bot & Stealth Features

| Example | Description | Link |
|---------|-------------|------|
| Stealth Mode Quick Start | Five practical examples showing how to use stealth mode for bypassing basic bot detection. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/stealth_mode_quick_start.py) |
| Stealth Mode Comprehensive | Comprehensive demonstration of stealth mode features with bot detection testing and comparisons. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/stealth_mode_example.py) |
| Undetected Browser | Simple example showing how to use the undetected browser adapter. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/hello_world_undetected.py) |
| Undetected Browser Demo | Basic demo comparing regular and undetected browser modes. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/undetected_simple_demo.py) |
| Undetected Tests | Advanced tests comparing regular vs undetected browsers on various bot detection services. | [View Folder](https://github.com/unclecode/crawl4ai/tree/main/docs/examples/undetectability/) |

## Customization & Security

| Example | Description | Link |
|---------|-------------|------|
| Hooks | Illustrates how to use hooks at different stages of the crawling process for advanced customization. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/hooks_example.py) |
| Identity-Based Browsing | Illustrates identity-based browsing configurations for authentic browsing experiences. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/identity_based_browsing.py) |
| Proxy Rotation | Shows how to use proxy rotation for web scraping and avoiding IP blocks. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/proxy_rotation_demo.py) |
| SSL Certificate | Illustrates SSL certificate handling and verification. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/ssl_example.py) |
| Language Support | Shows how to handle different languages during crawling. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/language_support_example.py) |
| Geolocation | Demonstrates how to use geolocation features. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/use_geo_location.py) |

## Docker & Deployment

| Example | Description | Link |
|---------|-------------|------|
| Docker Config | Demonstrates how to create and use Docker configuration objects. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_config_obj.py) |
| Docker Basic | A test suite for Docker deployment, showcasing various functionalities through the Docker API. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_example.py) |
| Docker REST API | Shows how to interact with Crawl4AI Docker using REST API calls. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_python_rest_api.py) |
| Docker SDK | Demonstrates using the Python SDK for Crawl4AI Docker. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_python_sdk.py) |

## Application Examples

| Example | Description | Link |
|---------|-------------|------|
| Research Assistant | Demonstrates how to build a research assistant using Crawl4AI. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/research_assistant.py) |
| REST Call | Shows how to make REST API calls with Crawl4AI. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/rest_call.py) |
| Chainlit Integration | Shows how to integrate Crawl4AI with Chainlit. | [View Guide](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/chainlit.md) |
| Crawl4AI vs FireCrawl | Compares Crawl4AI with the FireCrawl library. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/crawlai_vs_firecrawl.py) |

## Content Generation & Markdown

| Example | Description | Link |
|---------|-------------|------|
| Content Source | Demonstrates how to work with different content sources in markdown generation. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/markdown/content_source_example.py) |
| Content Source (Short) | A simplified version of content source usage. | [View Code](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/markdown/content_source_short_example.py) |
| Built-in Browser Guide | Guide for using the built-in browser capabilities. | [View Guide](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/README_BUILTIN_BROWSER.md) |

## Running the Examples

To run any of these examples, you'll need to have Crawl4AI installed:

```bash
pip install crawl4ai
```

Then, you can run an example script like this:

```bash
python -m docs.examples.hello_world
```

For examples that require additional dependencies or environment variables, refer to the comments at the top of each file.

Some examples may require:
- API keys (for LLM-based examples)
- Docker setup (for Docker-related examples)
- Additional dependencies (specified in the example files)

## Contributing New Examples

If you've created an interesting example that demonstrates a unique use case or feature of Crawl4AI, we encourage you to contribute it to our examples collection. Please see our [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTORS.md) for more information.
