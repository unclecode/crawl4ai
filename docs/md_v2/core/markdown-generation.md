# Markdown Generation Basics

One of Crawl4AI’s core features is generating **clean, structured markdown** from web pages. Originally built to solve the problem of extracting only the “actual” content and discarding boilerplate or noise, Crawl4AI’s markdown system remains one of its biggest draws for AI workflows.

In this tutorial, you’ll learn:

1. How to configure the **Default Markdown Generator**  
2. How **content filters** (BM25 or Pruning) help you refine markdown and discard junk  
3. The difference between raw markdown (`result.markdown`) and filtered markdown (`fit_markdown`)  

> **Prerequisites**  
> - You’ve completed or read [AsyncWebCrawler Basics](../core/simple-crawling.md) to understand how to run a simple crawl.  
> - You know how to configure `CrawlerRunConfig`.

---

## 1. Quick Example

Here’s a minimal code snippet that uses the **DefaultMarkdownGenerator** with no additional filtering:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator()
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        
        if result.success:
            print("Raw Markdown Output:\n")
            print(result.markdown)  # The unfiltered markdown from the page
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**What’s happening?**  
- `CrawlerRunConfig( markdown_generator = DefaultMarkdownGenerator() )` instructs Crawl4AI to convert the final HTML into markdown at the end of each crawl.  
- The resulting markdown is accessible via `result.markdown`.

---

## 2. How Markdown Generation Works

### 2.1 HTML-to-Text Conversion (Forked & Modified)

Under the hood, **DefaultMarkdownGenerator** uses a specialized HTML-to-text approach that:

- Preserves headings, code blocks, bullet points, etc.  
- Removes extraneous tags (scripts, styles) that don’t add meaningful content.  
- Can optionally generate references for links or skip them altogether.

A set of **options** (passed as a dict) allows you to customize precisely how HTML converts to markdown. These map to standard html2text-like configuration plus your own enhancements (e.g., ignoring internal links, preserving certain tags verbatim, or adjusting line widths).

### 2.2 Link Citations & References

By default, the generator can convert `<a href="...">` elements into `[text][1]` citations, then place the actual links at the bottom of the document. This is handy for research workflows that demand references in a structured manner.

### 2.3 Optional Content Filters

Before or after the HTML-to-Markdown step, you can apply a **content filter** (like BM25 or Pruning) to reduce noise and produce a “fit_markdown”—a heavily pruned version focusing on the page’s main text. We’ll cover these filters shortly.

---

## 3. Configuring the Default Markdown Generator

You can tweak the output by passing an `options` dict to `DefaultMarkdownGenerator`. For example:

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Example: ignore all links, don't escape HTML, and wrap text at 80 characters
    md_generator = DefaultMarkdownGenerator(
        options={
            "ignore_links": True,
            "escape_html": False,
            "body_width": 80
        }
    )

    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com/docs", config=config)
        if result.success:
            print("Markdown:\n", result.markdown[:500])  # Just a snippet
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

Some commonly used `options`:

- **`ignore_links`** (bool): Whether to remove all hyperlinks in the final markdown.  
- **`ignore_images`** (bool): Remove all `![image]()` references.  
- **`escape_html`** (bool): Turn HTML entities into text (default is often `True`).  
- **`body_width`** (int): Wrap text at N characters. `0` or `None` means no wrapping.  
- **`skip_internal_links`** (bool): If `True`, omit `#localAnchors` or internal links referencing the same page.  
- **`include_sup_sub`** (bool): Attempt to handle `<sup>` / `<sub>` in a more readable way.

---

## 4. Content Filters

**Content filters** selectively remove or rank sections of text before turning them into Markdown. This is especially helpful if your page has ads, nav bars, or other clutter you don’t want.

### 4.1 BM25ContentFilter

If you have a **search query**, BM25 is a good choice:

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai import CrawlerRunConfig

bm25_filter = BM25ContentFilter(
    user_query="machine learning",
    bm25_threshold=1.2,
    use_stemming=True
)

md_generator = DefaultMarkdownGenerator(
    content_filter=bm25_filter,
    options={"ignore_links": True}
)

config = CrawlerRunConfig(markdown_generator=md_generator)
```

- **`user_query`**: The term you want to focus on. BM25 tries to keep only content blocks relevant to that query.  
- **`bm25_threshold`**: Raise it to keep fewer blocks; lower it to keep more.  
- **`use_stemming`**: If `True`, variations of words match (e.g., “learn,” “learning,” “learnt”).

**No query provided?** BM25 tries to glean a context from page metadata, or you can simply treat it as a scorched-earth approach that discards text with low generic score. Realistically, you want to supply a query for best results.

### 4.2 PruningContentFilter

If you **don’t** have a specific query, or if you just want a robust “junk remover,” use `PruningContentFilter`. It analyzes text density, link density, HTML structure, and known patterns (like “nav,” “footer”) to systematically prune extraneous or repetitive sections.

```python
from crawl4ai.content_filter_strategy import PruningContentFilter

prune_filter = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",  # or "dynamic"
    min_word_threshold=50
)
```

- **`threshold`**: Score boundary. Blocks below this score get removed.  
- **`threshold_type`**:  
    - `"fixed"`: Straight comparison (`score >= threshold` keeps the block).  
    - `"dynamic"`: The filter adjusts threshold in a data-driven manner.  
- **`min_word_threshold`**: Discard blocks under N words as likely too short or unhelpful.

**When to Use PruningContentFilter**  
- You want a broad cleanup without a user query.  
- The page has lots of repeated sidebars, footers, or disclaimers that hamper text extraction.

### 4.3 LLMContentFilter

For intelligent content filtering and high-quality markdown generation, you can use the **LLMContentFilter**. This filter leverages LLMs to generate relevant markdown while preserving the original content's meaning and structure:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import LLMContentFilter

async def main():
    # Initialize LLM filter with specific instruction
    filter = LLMContentFilter(
        provider="openai/gpt-4o",  # or your preferred provider
        api_token="your-api-token",  # or use environment variable
        instruction="""
        Focus on extracting the core educational content.
        Include:
        - Key concepts and explanations
        - Important code examples
        - Essential technical details
        Exclude:
        - Navigation elements
        - Sidebars
        - Footer content
        Format the output as clean markdown with proper code blocks and headers.
        """,
        chunk_token_threshold=4096,  # Adjust based on your needs
        verbose=True
    )

    config = CrawlerRunConfig(
        content_filter=filter
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        print(result.fit_markdown)  # Filtered markdown content
```

**Key Features:**
- **Intelligent Filtering**: Uses LLMs to understand and extract relevant content while maintaining context
- **Customizable Instructions**: Tailor the filtering process with specific instructions
- **Chunk Processing**: Handles large documents by processing them in chunks (controlled by `chunk_token_threshold`)
- **Parallel Processing**: For better performance, use smaller `chunk_token_threshold` (e.g., 2048 or 4096) to enable parallel processing of content chunks

**Two Common Use Cases:**

1. **Exact Content Preservation**:
```python
filter = LLMContentFilter(
    instruction="""
    Extract the main educational content while preserving its original wording and substance completely.
    1. Maintain the exact language and terminology
    2. Keep all technical explanations and examples intact
    3. Preserve the original flow and structure
    4. Remove only clearly irrelevant elements like navigation menus and ads
    """,
    chunk_token_threshold=4096
)
```

2. **Focused Content Extraction**:
```python
filter = LLMContentFilter(
    instruction="""
    Focus on extracting specific types of content:
    - Technical documentation
    - Code examples
    - API references
    Reformat the content into clear, well-structured markdown
    """,
    chunk_token_threshold=4096
)
```

> **Performance Tip**: Set a smaller `chunk_token_threshold` (e.g., 2048 or 4096) to enable parallel processing of content chunks. The default value is infinity, which processes the entire content as a single chunk.

---

## 5. Using Fit Markdown

When a content filter is active, the library produces two forms of markdown inside `result.markdown_v2` or (if using the simplified field) `result.markdown`:

1. **`raw_markdown`**: The full unfiltered markdown.  
2. **`fit_markdown`**: A “fit” version where the filter has removed or trimmed noisy segments.

**Note**:  
> In earlier examples, you may see references to `result.markdown_v2`. Depending on your library version, you might access `result.markdown`, `result.markdown_v2`, or an object named `MarkdownGenerationResult`. The idea is the same: you’ll have a raw version and a filtered (“fit”) version if a filter is used.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def main():
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.6),
            options={"ignore_links": True}
        )
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://news.example.com/tech", config=config)
        if result.success:
            print("Raw markdown:\n", result.markdown)
            
            # If a filter is used, we also have .fit_markdown:
            md_object = result.markdown_v2  # or your equivalent
            print("Filtered markdown:\n", md_object.fit_markdown)
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. The `MarkdownGenerationResult` Object

If your library stores detailed markdown output in an object like `MarkdownGenerationResult`, you’ll see fields such as:

- **`raw_markdown`**: The direct HTML-to-markdown transformation (no filtering).  
- **`markdown_with_citations`**: A version that moves links to reference-style footnotes.  
- **`references_markdown`**: A separate string or section containing the gathered references.  
- **`fit_markdown`**: The filtered markdown if you used a content filter.  
- **`fit_html`**: The corresponding HTML snippet used to generate `fit_markdown` (helpful for debugging or advanced usage).

**Example**:

```python
md_obj = result.markdown_v2  # your library’s naming may vary
print("RAW:\n", md_obj.raw_markdown)
print("CITED:\n", md_obj.markdown_with_citations)
print("REFERENCES:\n", md_obj.references_markdown)
print("FIT:\n", md_obj.fit_markdown)
```

**Why Does This Matter?**  
- You can supply `raw_markdown` to an LLM if you want the entire text.  
- Or feed `fit_markdown` into a vector database to reduce token usage.  
- `references_markdown` can help you keep track of link provenance.

---

Below is a **revised section** under “Combining Filters (BM25 + Pruning)” that demonstrates how you can run **two** passes of content filtering without re-crawling, by taking the HTML (or text) from a first pass and feeding it into the second filter. It uses real code patterns from the snippet you provided for **BM25ContentFilter**, which directly accepts **HTML** strings (and can also handle plain text with minimal adaptation).

---

## 7. Combining Filters (BM25 + Pruning) in Two Passes

You might want to **prune out** noisy boilerplate first (with `PruningContentFilter`), and then **rank what’s left** against a user query (with `BM25ContentFilter`). You don’t have to crawl the page twice. Instead:

1. **First pass**: Apply `PruningContentFilter` directly to the raw HTML from `result.html` (the crawler’s downloaded HTML).  
2. **Second pass**: Take the pruned HTML (or text) from step 1, and feed it into `BM25ContentFilter`, focusing on a user query.

### Two-Pass Example

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from bs4 import BeautifulSoup

async def main():
    # 1. Crawl with minimal or no markdown generator, just get raw HTML
    config = CrawlerRunConfig(
        # If you only want raw HTML, you can skip passing a markdown_generator
        # or provide one but focus on .html in this example
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com/tech-article", config=config)

        if not result.success or not result.html:
            print("Crawl failed or no HTML content.")
            return
        
        raw_html = result.html
        
        # 2. First pass: PruningContentFilter on raw HTML
        pruning_filter = PruningContentFilter(threshold=0.5, min_word_threshold=50)
        
        # filter_content returns a list of "text chunks" or cleaned HTML sections
        pruned_chunks = pruning_filter.filter_content(raw_html)
        # This list is basically pruned content blocks, presumably in HTML or text form
        
        # For demonstration, let's combine these chunks back into a single HTML-like string
        # or you could do further processing. It's up to your pipeline design.
        pruned_html = "\n".join(pruned_chunks)
        
        # 3. Second pass: BM25ContentFilter with a user query
        bm25_filter = BM25ContentFilter(
            user_query="machine learning",
            bm25_threshold=1.2,
            language="english"
        )
        
        # returns a list of text chunks
        bm25_chunks = bm25_filter.filter_content(pruned_html)  
        
        if not bm25_chunks:
            print("Nothing matched the BM25 query after pruning.")
            return
        
        # 4. Combine or display final results
        final_text = "\n---\n".join(bm25_chunks)
        
        print("==== PRUNED OUTPUT (first pass) ====")
        print(pruned_html[:500], "... (truncated)")  # preview

        print("\n==== BM25 OUTPUT (second pass) ====")
        print(final_text[:500], "... (truncated)")

if __name__ == "__main__":
    asyncio.run(main())
```

### What’s Happening?

1. **Raw HTML**: We crawl once and store the raw HTML in `result.html`.  
2. **PruningContentFilter**: Takes HTML + optional parameters. It extracts blocks of text or partial HTML, removing headings/sections deemed “noise.” It returns a **list of text chunks**.  
3. **Combine or Transform**: We join these pruned chunks back into a single HTML-like string. (Alternatively, you could store them in a list for further logic—whatever suits your pipeline.)  
4. **BM25ContentFilter**: We feed the pruned string into `BM25ContentFilter` with a user query. This second pass further narrows the content to chunks relevant to “machine learning.”

**No Re-Crawling**: We used `raw_html` from the first pass, so there’s no need to run `arun()` again—**no second network request**.

### Tips & Variations

- **Plain Text vs. HTML**: If your pruned output is mostly text, BM25 can still handle it; just keep in mind it expects a valid string input. If you supply partial HTML (like `"<p>some text</p>"`), it will parse it as HTML.  
- **Chaining in a Single Pipeline**: If your code supports it, you can chain multiple filters automatically. Otherwise, manual two-pass filtering (as shown) is straightforward.  
- **Adjust Thresholds**: If you see too much or too little text in step one, tweak `threshold=0.5` or `min_word_threshold=50`. Similarly, `bm25_threshold=1.2` can be raised/lowered for more or fewer chunks in step two.

### One-Pass Combination?

If your codebase or pipeline design allows applying multiple filters in one pass, you could do so. But often it’s simpler—and more transparent—to run them sequentially, analyzing each step’s result.

**Bottom Line**: By **manually chaining** your filtering logic in two passes, you get powerful incremental control over the final content. First, remove “global” clutter with Pruning, then refine further with BM25-based query relevance—without incurring a second network crawl.

---

## 8. Common Pitfalls & Tips

1. **No Markdown Output?**  
   - Make sure the crawler actually retrieved HTML. If the site is heavily JS-based, you may need to enable dynamic rendering or wait for elements.  
   - Check if your content filter is too aggressive. Lower thresholds or disable the filter to see if content reappears.

2. **Performance Considerations**  
   - Very large pages with multiple filters can be slower. Consider `cache_mode` to avoid re-downloading.  
   - If your final use case is LLM ingestion, consider summarizing further or chunking big texts.

3. **Take Advantage of `fit_markdown`**  
   - Great for RAG pipelines, semantic search, or any scenario where extraneous boilerplate is unwanted.  
   - Still verify the textual quality—some sites have crucial data in footers or sidebars.

4. **Adjusting `html2text` Options**  
   - If you see lots of raw HTML slipping into the text, turn on `escape_html`.  
   - If code blocks look messy, experiment with `mark_code` or `handle_code_in_pre`.

---

## 9. Summary & Next Steps

In this **Markdown Generation Basics** tutorial, you learned to:

- Configure the **DefaultMarkdownGenerator** with HTML-to-text options.  
- Use **BM25ContentFilter** for query-specific extraction or **PruningContentFilter** for general noise removal.  
- Distinguish between raw and filtered markdown (`fit_markdown`).  
- Leverage the `MarkdownGenerationResult` object to handle different forms of output (citations, references, etc.).

Now you can produce high-quality Markdown from any website, focusing on exactly the content you need—an essential step for powering AI models, summarization pipelines, or knowledge-base queries.

**Last Updated**: 2025-01-01
