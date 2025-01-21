# Output Formats

Crawl4AI provides multiple output formats to suit different needs, ranging from raw HTML to structured data using LLM or pattern-based extraction, and versatile markdown outputs.

## Basic Formats

```python
result = await crawler.arun(url="https://example.com")

# Access different formats
raw_html = result.html                # Original HTML
clean_html = result.cleaned_html      # Sanitized HTML
markdown_v2 = result.markdown_v2      # Detailed markdown generation results
fit_md = result.markdown_v2.fit_markdown  # Most relevant content in markdown
```

> **Note**: The `markdown_v2` property will soon be replaced by `markdown`. It is recommended to start transitioning to using `markdown` for new implementations.

## Raw HTML

Original, unmodified HTML from the webpage. Useful when you need to:
- Preserve the exact page structure.
- Process HTML with your own tools.
- Debug page issues.

```python
result = await crawler.arun(url="https://example.com")
print(result.html)  # Complete HTML including headers, scripts, etc.
```

## Cleaned HTML

Sanitized HTML with unnecessary elements removed. Automatically:
- Removes scripts and styles.
- Cleans up formatting.
- Preserves semantic structure.

```python
config = CrawlerRunConfig(
    excluded_tags=['form', 'header', 'footer'],  # Additional tags to remove
    keep_data_attributes=False,  # Remove data-* attributes
    keep_aria_label_attribute=False, # Remove aria-label attribute
)
result = await crawler.arun(url="https://example.com", config=config)
print(result.cleaned_html)
```

## Standard Markdown

HTML converted to clean markdown format. This output is useful for:
- Content analysis.
- Documentation.
- Readability.

```python
config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        options={"include_links": True}  # Include links in markdown
    )
)
result = await crawler.arun(url="https://example.com", config=config)
print(result.markdown_v2.raw_markdown)  # Standard markdown with links
```

## Fit Markdown

Extract and convert only the most relevant content into markdown format. Best suited for:
- Article extraction.
- Focusing on the main content.
- Removing boilerplate.

To generate `fit_markdown`, use a content filter like `PruningContentFilter`:

```python
from crawl4ai.content_filter_strategy import PruningContentFilter

config = CrawlerRunConfig(
    content_filter=PruningContentFilter(
        threshold=0.7,
        threshold_type="dynamic",
        min_word_threshold=100
    )
)
result = await crawler.arun(url="https://example.com", config=config)
print(result.markdown_v2.fit_markdown)  # Extracted main content in markdown
```

## Markdown with Citations

Generate markdown that includes citations for links. This format is ideal for:
- Creating structured documentation.
- Including references for extracted content.

```python
config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        options={"citations": True}  # Enable citations
    )
)
result = await crawler.arun(url="https://example.com", config=config)
print(result.markdown_v2.markdown_with_citations)
print(result.markdown_v2.references_markdown)  # Citations section
```
