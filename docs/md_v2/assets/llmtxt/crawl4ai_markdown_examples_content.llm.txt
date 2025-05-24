# Examples Outline for crawl4ai - markdown Component

**Target Document Type:** Examples Collection
**Target Output Filename Suggestion:** `llm_examples_markdown.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2025-05-24
---

This document provides practical, runnable code examples for the `markdown` component of the `crawl4ai` library, focusing on the `DefaultMarkdownGenerator` and its various configurations.

## 1. Basic Markdown Generation with `DefaultMarkdownGenerator`

### 1.1. Example: Generating Markdown with default `DefaultMarkdownGenerator` settings via `AsyncWebCrawler`.
This example demonstrates the most basic usage of `DefaultMarkdownGenerator` within an `AsyncWebCrawler` run.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode

async def basic_markdown_generation_via_crawler():
    # DefaultMarkdownGenerator will be used by default if markdown_generator is not specified,
    # but we explicitly set it here for clarity.
    md_generator = DefaultMarkdownGenerator()
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS # Use BYPASS for fresh content in examples
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        if result.success and result.markdown:
            print("--- Raw Markdown (First 300 chars) ---")
            print(result.markdown.raw_markdown[:300])
            print("\n--- Markdown with Citations (First 300 chars) ---")
            print(result.markdown.markdown_with_citations[:300])
            print("\n--- References Markdown ---")
            print(result.markdown.references_markdown) # example.com has no outbound links usually
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(basic_markdown_generation_via_crawler())
```
---

### 1.2. Example: Direct instantiation and use of `DefaultMarkdownGenerator`.
You can use `DefaultMarkdownGenerator` directly if you already have HTML content.

```python
from crawl4ai import DefaultMarkdownGenerator

def direct_markdown_generation():
    generator = DefaultMarkdownGenerator()
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Welcome to Example</h1>
            <p>This is a paragraph with a <a href="https://example.org/another-page">link</a>.</p>
            <p>Another paragraph follows.</p>
        </body>
    </html>
    """
    # base_url is important for resolving relative links if any, and for citation context
    result_md = generator.generate_markdown(input_html=html_content, base_url="https://example.com")

    print("--- Raw Markdown (Direct Generation) ---")
    print(result_md.raw_markdown)
    print("\n--- Markdown with Citations (Direct Generation) ---")
    print(result_md.markdown_with_citations)
    print("\n--- References Markdown (Direct Generation) ---")
    print(result_md.references_markdown)

if __name__ == "__main__":
    direct_markdown_generation()
```
---

## 2. Citation Management in Markdown

### 2.1. Example: Default citation behavior (citations enabled).
By default, `DefaultMarkdownGenerator` generates citations for links.

```python
from crawl4ai import DefaultMarkdownGenerator

def default_citation_behavior():
    generator = DefaultMarkdownGenerator()
    html_content = """
    <html><body>
        <p>Check out <a href="https://crawl4ai.com" title="Crawl4ai Homepage">Crawl4ai</a> and
        <a href="/docs">our documentation</a>.</p>
    </body></html>
    """
    result_md = generator.generate_markdown(input_html=html_content, base_url="https://example.com")

    print("--- Raw Markdown ---")
    print(result_md.raw_markdown)
    print("\n--- Markdown with Citations ---")
    print(result_md.markdown_with_citations)
    print("\n--- References Markdown ---")
    print(result_md.references_markdown)

if __name__ == "__main__":
    default_citation_behavior()
```
---

### 2.2. Example: Disabling citations in `DefaultMarkdownGenerator`.
You can disable citation generation by setting `citations=False` in the `generate_markdown` method.

```python
from crawl4ai import DefaultMarkdownGenerator

def disabling_citations():
    generator = DefaultMarkdownGenerator()
    html_content = """
    <html><body>
        <p>A link to <a href="https://anothersite.com">another site</a> will not be cited.</p>
    </body></html>
    """
    # Disable citations for this specific call
    result_md_no_citations = generator.generate_markdown(
        input_html=html_content,
        base_url="https://example.com",
        citations=False
    )

    print("--- Raw Markdown (Citations Disabled) ---")
    print(result_md_no_citations.raw_markdown)
    print("\n--- Markdown with Citations (Citations Disabled) ---")
    # This should be the same as raw_markdown when citations=False
    print(result_md_no_citations.markdown_with_citations)
    print("\n--- References Markdown (Citations Disabled) ---")
    # This should be empty or minimal
    print(result_md_no_citations.references_markdown)

    # For comparison, with citations enabled (default)
    result_md_with_citations = generator.generate_markdown(
        input_html=html_content,
        base_url="https://example.com",
        citations=True # Default
    )
    print("\n--- For Comparison: Markdown with Citations (Enabled) ---")
    print(result_md_with_citations.markdown_with_citations)
    print("\n--- For Comparison: References Markdown (Enabled) ---")
    print(result_md_with_citations.references_markdown)


if __name__ == "__main__":
    disabling_citations()
```
---

### 2.3. Example: Impact of `base_url` on citation links for relative URLs.
The `base_url` parameter is crucial for correctly resolving relative URLs in your HTML content into absolute URLs in the references.

```python
from crawl4ai import DefaultMarkdownGenerator

def base_url_impact_on_citations():
    generator = DefaultMarkdownGenerator()
    html_content = """
    <html><body>
        <p>Links: <a href="/features">Features</a>, <a href="pricing.html">Pricing</a>,
        and an absolute link to <a href="https://external.com/resource">External Resource</a>.</p>
    </body></html>
    """

    print("--- Case 1: With base_url='https://example.com/products/' ---")
    result_md_case1 = generator.generate_markdown(
        input_html=html_content,
        base_url="https://example.com/products/"
    )
    print(result_md_case1.references_markdown)

    print("\n--- Case 2: With base_url='https://another-domain.net/' ---")
    result_md_case2 = generator.generate_markdown(
        input_html=html_content,
        base_url="https://another-domain.net/"
    )
    print(result_md_case2.references_markdown)

    print("\n--- Case 3: Without base_url (relative links might be incomplete) ---")
    result_md_case3 = generator.generate_markdown(input_html=html_content)
    print(result_md_case3.references_markdown)

if __name__ == "__main__":
    base_url_impact_on_citations()
```
---

### 2.4. Example: Handling HTML with no links (empty `references_markdown`).
If the input HTML contains no hyperlinks, the `references_markdown` will be empty.

```python
from crawl4ai import DefaultMarkdownGenerator

def no_links_in_html():
    generator = DefaultMarkdownGenerator()
    html_content = "<html><body><p>This is a paragraph with no links at all.</p><b>Just some bold text.</b></body></html>"
    result_md = generator.generate_markdown(input_html=html_content, base_url="https://example.com")

    print("--- Raw Markdown ---")
    print(result_md.raw_markdown)
    print("\n--- Markdown with Citations ---")
    print(result_md.markdown_with_citations) # Should be same as raw_markdown
    print("\n--- References Markdown ---")
    print(f"'{result_md.references_markdown}'") # Should be empty or contain minimal boilerplate

if __name__ == "__main__":
    no_links_in_html()
```
---

## 3. Controlling `html2text` Conversion Options
The `DefaultMarkdownGenerator` uses the `html2text` library internally. You can pass options to `html2text` either during generator initialization (`options` parameter) or during the `generate_markdown` call (`html2text_options` parameter).

### 3.1. Example: Initializing `DefaultMarkdownGenerator` with `options` to ignore links.
This will prevent links from appearing in the Markdown output altogether (different from `citations=False` which keeps link text but omits citation markers).

```python
from crawl4ai import DefaultMarkdownGenerator

def ignore_links_option():
    # Initialize with html2text option to ignore links
    generator = DefaultMarkdownGenerator(options={"ignore_links": True})
    html_content = "<html><body><p>A link to <a href='https://example.com'>Example Site</a> and some text.</p></body></html>"
    result_md = generator.generate_markdown(input_html=html_content)

    print("--- Markdown (ignore_links=True) ---")
    print(result_md.raw_markdown) # Link text might be present or absent based on html2text behavior
    print("--- Markdown with Citations (ignore_links=True) ---")
    print(result_md.markdown_with_citations) # No citations as links are ignored
    print("--- References (ignore_links=True) ---")
    print(f"'{result_md.references_markdown}'") # Should be empty

if __name__ == "__main__":
    ignore_links_option()
```
---

### 3.2. Example: Initializing `DefaultMarkdownGenerator` with `options` to ignore images.
This will prevent image references (like `![alt text](src)`) from appearing in the Markdown.

```python
from crawl4ai import DefaultMarkdownGenerator

def ignore_images_option():
    generator = DefaultMarkdownGenerator(options={"ignore_images": True})
    html_content = "<html><body><p>An image: <img src='image.png' alt='My Test Image'></p></body></html>"
    result_md = generator.generate_markdown(input_html=html_content)

    print("--- Markdown (ignore_images=True) ---")
    print(result_md.raw_markdown) # Image markdown should be absent

if __name__ == "__main__":
    ignore_images_option()
```
---

### 3.3. Example: Initializing `DefaultMarkdownGenerator` with `options` for `body_width=0` (no line wrapping).
`body_width=0` tells `html2text` not to wrap lines.

```python
from crawl4ai import DefaultMarkdownGenerator

def no_line_wrapping_option():
    generator = DefaultMarkdownGenerator(options={"body_width": 0})
    long_text = "This is a very long line of text that would normally be wrapped by html2text. " * 5
    html_content = f"<html><body><p>{long_text}</p></body></html>"
    result_md = generator.generate_markdown(input_html=html_content)

    print("--- Markdown (body_width=0) ---")
    print(result_md.raw_markdown) # Observe the long line without soft wraps

if __name__ == "__main__":
    no_line_wrapping_option()
```
---

### 3.4. Example: Initializing `DefaultMarkdownGenerator` to disable emphasis.
This will remove formatting for `<em>` and `<strong>` tags.

```python
from crawl4ai import DefaultMarkdownGenerator

def ignore_emphasis_option():
    generator = DefaultMarkdownGenerator(options={"ignore_emphasis": True})
    html_content = "<html><body><p>Normal, <em>emphasized</em>, and <strong>strongly emphasized</strong> text.</p></body></html>"
    result_md = generator.generate_markdown(input_html=html_content)

    print("--- Markdown (ignore_emphasis=True) ---")
    print(result_md.raw_markdown) # Emphasis should be gone

if __name__ == "__main__":
    ignore_emphasis_option()
```
---

### 3.5. Example: Overriding `html2text_options` at `generate_markdown` call time.
Options passed to `generate_markdown` via `html2text_options` take precedence.

```python
from crawl4ai import DefaultMarkdownGenerator

def override_html2text_options():
    # Initial generator might have some defaults
    generator = DefaultMarkdownGenerator(options={"ignore_links": False})
    html_content = "<html><body><p>Link: <a href='https://example.com'>Example</a>.</p></body></html>"

    # Override at call time to protect links
    result_md = generator.generate_markdown(
        input_html=html_content,
        html2text_options={"protect_links": True} # Links will be <URL>
    )

    print("--- Markdown (protect_links=True via call-time override) ---")
    print(result_md.raw_markdown)

if __name__ == "__main__":
    override_html2text_options()
```
---

### 3.6. Example: Combining multiple `html2text` options.
Multiple options can be combined for fine-grained control over the Markdown output.

```python
from crawl4ai import DefaultMarkdownGenerator

def combined_html2text_options():
    generator = DefaultMarkdownGenerator(options={
        "ignore_links": True,
        "ignore_images": True,
        "body_width": 60  # Wrap at 60 characters
    })
    html_content = """
    <html><body>
        <p>This is a paragraph with a <a href='https://example.com'>link to ignore</a> and an
        <img src='image.png' alt='image to ignore'>. It also has some long text to demonstrate wrapping.
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        </p>
    </body></html>
    """
    result_md = generator.generate_markdown(input_html=html_content)

    print("--- Markdown (Combined Options: ignore_links, ignore_images, body_width=60) ---")
    print(result_md.raw_markdown)

if __name__ == "__main__":
    combined_html2text_options()
```
---

## 4. Selecting the HTML Content Source for Markdown Generation
The `DefaultMarkdownGenerator` can generate Markdown from different HTML sources within the `CrawlResult`.

### 4.1. Example: Markdown from `cleaned_html` (default `content_source`).
This is the default behavior. `cleaned_html` is the HTML after `WebScrapingStrategy` (e.g., `LXMLWebScrapingStrategy`) has processed it.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode

async def markdown_from_cleaned_html():
    # Default content_source is "cleaned_html"
    md_generator = DefaultMarkdownGenerator()
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        # Using a more complex page to see the effect of cleaning
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        if result.success and result.markdown:
            print("--- Markdown from Cleaned HTML (Default - First 300 chars) ---")
            print(result.markdown.raw_markdown[:300])
            # For comparison, show a snippet of cleaned_html
            print("\n--- Cleaned HTML (Source - First 300 chars) ---")
            print(result.cleaned_html[:300])
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(markdown_from_cleaned_html())
```
---

### 4.2. Example: Markdown from `raw_html`.
This example uses the original, unprocessed HTML fetched from the URL as the source for Markdown generation.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode

async def markdown_from_raw_html():
    md_generator = DefaultMarkdownGenerator(content_source="raw_html")
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        if result.success and result.markdown:
            print("--- Markdown from Raw HTML (First 300 chars) ---")
            print(result.markdown.raw_markdown[:300])
            print("\n--- Raw Page HTML (Source - First 300 chars for comparison) ---")
            print(result.html[:300]) # result.html contains the raw HTML
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(markdown_from_raw_html())
```
---

### 4.3. Example: Markdown from `fit_html` (requires a `ContentFilterStrategy`).
`fit_html` is the HTML content after a `ContentFilterStrategy` (like `PruningContentFilter`) has processed it.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter

async def markdown_from_fit_html():
    # A content filter must run to produce fit_html
    pruning_filter = PruningContentFilter()
    md_generator = DefaultMarkdownGenerator(
        content_filter=pruning_filter,
        content_source="fit_html" # Explicitly use the output of the filter
    )
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        # Using a news site which PruningContentFilter can work on
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        if result.success and result.markdown:
            print("--- Markdown from Fit HTML (Output of PruningFilter - First 300 chars) ---")
            # When content_source="fit_html", result.markdown.raw_markdown IS from fit_html
            print(result.markdown.raw_markdown[:300])
            print("\n--- Fit HTML itself (Source - First 300 chars for comparison) ---")
            print(result.markdown.fit_html[:300])
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(markdown_from_fit_html())
```
---

## 5. Integration with Content Filters
`DefaultMarkdownGenerator` can work in conjunction with `ContentFilterStrategy` instances. If a filter is provided, it will produce `fit_html` and `fit_markdown`.

### 5.1. Example: `DefaultMarkdownGenerator` with `PruningContentFilter`.
The `PruningContentFilter` attempts to remove boilerplate and keep main content.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter

async def md_with_pruning_filter():
    pruning_filter = PruningContentFilter()
    # By default, raw_markdown is from cleaned_html, fit_markdown is from fit_html
    md_generator = DefaultMarkdownGenerator(content_filter=pruning_filter)
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        if result.success and result.markdown:
            print("--- Raw Markdown (from cleaned_html - First 200 chars) ---")
            print(result.markdown.raw_markdown[:200])
            print("\n--- Fit Markdown (from PruningFilter's fit_html - First 200 chars) ---")
            print(result.markdown.fit_markdown[:200])
            print("\n--- Fit HTML (Source for Fit Markdown - First 200 chars) ---")
            print(result.markdown.fit_html[:200])
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(md_with_pruning_filter())
```
---

### 5.2. Example: `DefaultMarkdownGenerator` with `BM25ContentFilter`.
`BM25ContentFilter` filters content based on relevance to a user query.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode
from crawl4ai.content_filter_strategy import BM25ContentFilter

async def md_with_bm25_filter():
    bm25_filter = BM25ContentFilter(user_query="Python programming language features")
    md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        # Using a relevant page for the query
        result = await crawler.arun(url="https://docs.python.org/3/tutorial/classes.html", config=config)
        if result.success and result.markdown:
            print("--- Fit Markdown (from BM25Filter - First 300 chars) ---")
            print(result.markdown.fit_markdown[:300])
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(md_with_bm25_filter())
```
---

### 5.3. Example: `DefaultMarkdownGenerator` with `LLMContentFilter`.
`LLMContentFilter` uses an LLM to intelligently filter or summarize content based on instructions. (Requires API Key)

```python
import asyncio
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, LLMConfig, CacheMode
from crawl4ai.content_filter_strategy import LLMContentFilter

async def md_with_llm_filter():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("OPENAI_API_KEY not found. Skipping LLMContentFilter example.")
        return

    llm_config = LLMConfig(api_token=openai_api_key, provider="openai/gpt-3.5-turbo")
    llm_filter = LLMContentFilter(
        llm_config=llm_config,
        instruction="Summarize the main arguments presented in this Hacker News discussion thread."
    )
    md_generator = DefaultMarkdownGenerator(content_filter=llm_filter)
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS # Fresh run for LLM
    )

    async with AsyncWebCrawler() as crawler:
        # Example Hacker News discussion
        result = await crawler.arun(url="https://news.ycombinator.com/item?id=39000000", config=config) # A past popular item
        if result.success and result.markdown:
            print("--- Fit Markdown (from LLMContentFilter - First 500 chars) ---")
            print(result.markdown.fit_markdown[:500])
            llm_filter.show_usage() # Show token usage
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(md_with_llm_filter())
```
---

### 5.4. Example: Forcing Markdown generation from `fit_html` when a filter is active.
This example shows how to ensure the `raw_markdown` itself is generated from the `fit_html` (output of the filter) rather than `cleaned_html`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter

async def md_forced_from_fit_html():
    pruning_filter = PruningContentFilter()
    # Explicitly set content_source to "fit_html"
    md_generator = DefaultMarkdownGenerator(
        content_filter=pruning_filter,
        content_source="fit_html"
    )
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        if result.success and result.markdown:
            print("--- Raw Markdown (forced from fit_html - First 300 chars) ---")
            # This raw_markdown is now generated from the output of PruningFilter
            print(result.markdown.raw_markdown[:300])
            print("\n--- Fit HTML (Source for Raw Markdown - First 300 chars) ---")
            print(result.markdown.fit_html[:300])
            print("\n--- Fit Markdown (should be same as Raw Markdown here - First 300 chars) ---")
            print(result.markdown.fit_markdown[:300])
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(md_forced_from_fit_html())
```
---

### 5.5. Example: Markdown generation when no filter is active.
If no `content_filter` is provided to `DefaultMarkdownGenerator`, `fit_markdown` and `fit_html` will be empty or None.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode

async def md_no_filter():
    md_generator = DefaultMarkdownGenerator() # No filter provided
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        if result.success and result.markdown:
            print("--- Raw Markdown (First 300 chars) ---")
            print(result.markdown.raw_markdown[:300])
            print("\n--- Fit Markdown (Expected: None or empty) ---")
            print(result.markdown.fit_markdown)
            print("\n--- Fit HTML (Expected: None or empty) ---")
            print(result.markdown.fit_html)
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(md_no_filter())
```
---

## 6. Understanding `MarkdownGenerationResult` Output Fields

### 6.1. Example: Accessing all fields of `MarkdownGenerationResult`.
This example demonstrates how to access all the different Markdown and HTML outputs available in the `MarkdownGenerationResult` object.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter # Using a filter to populate fit_html/fit_markdown

async def access_all_markdown_fields():
    # Setup with a filter to ensure fit_html and fit_markdown are generated
    content_filter = PruningContentFilter()
    md_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        content_source="cleaned_html" # raw_markdown will be from cleaned_html
    )
    config = CrawlerRunConfig(
        markdown_generator=md_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        # Using a content-rich page
        result = await crawler.arun(url="https://en.wikipedia.org/wiki/Python_(programming_language)", config=config)
        if result.success and result.markdown:
            md_result = result.markdown

            print("--- Accessing MarkdownGenerationResult Fields ---")

            print(f"\n1. Raw Markdown (from '{md_generator.content_source}' - snippet):")
            print(md_result.raw_markdown[:300] + "...")

            print(f"\n2. Markdown with Citations (snippet):")
            print(md_result.markdown_with_citations[:300] + "...")

            print(f"\n3. References Markdown (snippet):")
            print(md_result.references_markdown[:200] + "...")

            print(f"\n4. Fit HTML (from ContentFilter - snippet):")
            if md_result.fit_html:
                print(md_result.fit_html[:300] + "...")
            else:
                print("None (No filter or filter produced no output)")

            print(f"\n5. Fit Markdown (from fit_html - snippet):")
            if md_result.fit_markdown:
                print(md_result.fit_markdown[:300] + "...")
            else:
                print("None (No filter or filter produced no output)")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(access_all_markdown_fields())
```
---

## 7. Advanced and Specific Scenarios

### 7.1. Example: Handling HTML with complex table structures.
`DefaultMarkdownGenerator` (via `html2text`) attempts to render HTML tables into Markdown tables.

```python
from crawl4ai import DefaultMarkdownGenerator

def markdown_for_tables():
    generator = DefaultMarkdownGenerator()
    html_content = """
    <html><body>
        <h3>Product Comparison</h3>
        <table>
            <thead>
                <tr><th>Feature</th><th>Product A</th><th>Product B</th></tr>
            </thead>
            <tbody>
                <tr><td>Price</td><td>$100</td><td>$120</td></tr>
                <tr><td>Rating</td><td>4.5 stars</td><td>4.2 stars</td></tr>
                <tr><td>Multi-row<br/>Feature</td><td colspan="2">Supported by Both</td></tr>
            </tbody>
        </table>
    </body></html>
    """
    result_md = generator.generate_markdown(input_html=html_content)

    print("--- Markdown for Table ---")
    print(result_md.raw_markdown)

if __name__ == "__main__":
    markdown_for_tables()
```
---

### 7.2. Example: Handling HTML with code blocks.
Code blocks are generally preserved in Markdown format.

```python
from crawl4ai import DefaultMarkdownGenerator

def markdown_for_code_blocks():
    generator = DefaultMarkdownGenerator()
    html_content = """
    <html><body>
        <p>Here is some Python code:</p>
        <pre><code class="language-python">
def greet(name):
    print(f"Hello, {name}!")

greet("World")
        </code></pre>
        <p>And an inline <code>example_function()</code>.</p>
    </body></html>
    """
    result_md = generator.generate_markdown(input_html=html_content)

    print("--- Markdown for Code Blocks ---")
    print(result_md.raw_markdown)

if __name__ == "__main__":
    markdown_for_code_blocks()
```
---

### 7.3. Example: Using a custom `MarkdownGenerationStrategy` (conceptual).
You can create your own Markdown generation logic by subclassing `MarkdownGenerationStrategy`.

```python
import asyncio
from crawl4ai import (
    AsyncWebCrawler, CrawlerRunConfig, CacheMode,
    MarkdownGenerationStrategy, MarkdownGenerationResult
)

# Define a minimal custom Markdown generator
class CustomMarkdownGenerator(MarkdownGenerationStrategy):
    def __init__(self, prefix="CUSTOM MD: ", **kwargs):
        super().__init__(**kwargs) # Pass along any other options
        self.prefix = prefix

    def generate_markdown(
        self,
        input_html: str,
        base_url: str = "",
        html2text_options: dict = None, # Can be used by html2text
        citations: bool = True, # Standard param
        **kwargs # For other potential strategy-specific params
    ) -> MarkdownGenerationResult:
        # Simplified custom logic: just prefix and take a snippet
        # A real custom generator would do more sophisticated parsing/conversion
        custom_raw_md = self.prefix + input_html[:100].strip() + "..."

        # For simplicity, we'll just return the custom raw markdown for all fields
        return MarkdownGenerationResult(
            raw_markdown=custom_raw_md,
            markdown_with_citations=custom_raw_md, # No real citation logic here
            references_markdown="",
            fit_markdown=None, # Not implementing filtering here
            fit_html=None
        )

async def use_custom_markdown_generator():
    custom_generator = CustomMarkdownGenerator(prefix="[MyGenerator Says]: ")
    config = CrawlerRunConfig(
        markdown_generator=custom_generator,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        if result.success and result.markdown:
            print("--- Output from CustomMarkdownGenerator ---")
            print(result.markdown.raw_markdown)
            # Since our custom generator doesn't really do citations or filtering:
            print(f"Citations: '{result.markdown.markdown_with_citations}'")
            print(f"References: '{result.markdown.references_markdown}'")
            print(f"Fit Markdown: '{result.markdown.fit_markdown}'")

        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(use_custom_markdown_generator())
```
---
**End of Examples Document**
```