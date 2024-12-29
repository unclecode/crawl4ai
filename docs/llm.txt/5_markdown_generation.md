# 5. Markdown Generation (MEGA Extended Documentation)

## 5.1 Introduction

In modern AI workflows—especially those involving Large Language Models (LLMs)—it’s essential to provide clean, structured, and meaningful textual data. **Crawl4AI** assists with this by extracting web content and converting it into Markdown that is easy to process, fine-tune on, or use for retrieval-augmented generation (RAG).

**What Makes Markdown Outputs Valuable for AI?**  
- **Human-Readable & Machine-Friendly:** Markdown is a simple, text-based format easily parsed by humans and machines alike.  
- **Rich Structure:** Headings, lists, code blocks, and links are preserved and well-organized.  
- **Enhanced Relevance:** Content filtering ensures you focus on the main content while discarding noise, making the data cleaner for LLM training or search.

### Quick Start Example

Here’s a minimal snippet to get started:

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator()
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    print(result.markdown_v2.raw_markdown)
```

*Within a few lines of code, you can fetch a webpage, run it through the Markdown generator, and get a clean, AI-friendly output.*

---

## 5.2 Markdown Generation

The Markdown generation process transforms raw HTML into a structured format. At its core is the `DefaultMarkdownGenerator` class, which uses configurable parameters and optional filters. Let’s explore its functionality in depth.

### Internal Workings

1. **HTML to Markdown Conversion:**  
   The generator relies on an HTML-to-text conversion process that respects various formatting options. It preserves headings, code blocks, and references while removing extraneous tags like scripts and styles.

2. **Link Citation Handling:**  
   By default, the generator can convert links into citation-style references at the bottom of the document. This feature is particularly useful when you need a clean, reference-rich dataset for an LLM.

3. **Optional Content Filters:**  
   You can provide a content filter (like BM25 or Pruning) to generate a “fit_markdown” output that contains only the most relevant or least noisy parts of the page.

### Key Parameters

- **`base_url` (string):**  
  A base URL used to resolve relative links in the content.

- **`html2text_config` (dict):**  
  Controls how HTML is converted to Markdown. If none is provided, default settings ensure a reasonable output. You can customize a wide array of options. These options mirror standard `html2text` configurations with custom enhancements.  
  **Important Options:**
  - `ignore_links` (bool): If `True`, removes all hyperlinks in the output Markdown. Default: `False`
  - `ignore_images` (bool): If `True`, removes all images. Default: `False`
  - `escape_html` (bool): If `True`, escapes raw HTML entities. Default: `True`
  - `body_width` (int): Sets the text wrapping width. Default: unlimited (0 means no wrapping)
  
  **Advanced html2text-related Options from Source:**
  - `inside_pre`/`inside_code` (internal flags): Track whether we are inside `<pre>` or `<code>` blocks.
  - `preserve_tags` (set): A set of tags to preserve. If not empty, content within these tags is kept verbatim.
  - `current_preserved_tag`/`preserve_depth`: Internally manage nesting levels of preserved tags.
  - `handle_code_in_pre` (bool): If `True`, treats code within `<pre>` blocks distinctly, possibly formatting them as code blocks in Markdown.
  - `skip_internal_links` (bool): If `True`, internal links (like `#section`) are skipped.
  - `single_line_break` (bool): If `True`, uses single line breaks instead of double line breaks.
  - `mark_code` (bool): If `True`, adds special markers around code text.
  - `include_sup_sub` (bool): If `True`, tries to include `<sup>` and `<sub>` text in a readable way.
  - `ignore_mailto_links` (bool): If `True`, ignores `mailto:` links.
  - `escape_backslash`, `escape_dot`, `escape_plus`, `escape_dash`, `escape_snob`: Special escaping options to handle characters that might conflict with Markdown syntax.

**Example Custom `html2text_config`:**

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler, CacheMode

config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    markdown_generator=DefaultMarkdownGenerator(
        options={
            "ignore_links": True,
            "escape_html": False,
            "body_width": 80,
            "skip_internal_links": True,
            "mark_code": True,
            "include_sup_sub": True
        }
    )
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com/docs", config=config)
    print(result.markdown_v2.raw_markdown)
```

In this example, we ignore all hyperlinks, do not escape HTML entities, wrap text at 80 characters wide, skip internal links, mark code regions, and include superscript/subscript formatting.

### Using Content Filters

When you need filtered markdown (fit_markdown), configure the content filter with the markdown generator:

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai import CrawlerRunConfig

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(),  # Content filter goes here
        options={
            "ignore_links": True,
            "escape_html": False
        }
    )
)
```

This setup enables:
- Raw markdown generation (always available)
- Filtered markdown (fit_markdown) through PruningContentFilter

### Using Content Filters in Markdown Generation

- **`content_filter` (object):**  
  An optional filter (like `BM25ContentFilter` or `PruningContentFilter`) that refines the content before Markdown generation. When applied:
  - `fit_markdown` is generated: a filtered version of the page focusing on main content.
  - `fit_html` is also available: the filtered HTML that was used to generate `fit_markdown`.

### Example Usage

```python
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=BM25ContentFilter(
            user_query="machine learning",
            bm25_threshold=1.5,
            use_stemming=True
        ),
        options={"ignore_links": True, "escape_html": False}
    )
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://crawl4ai.com/ai-research", config=config)
    print(result.markdown_v2.fit_markdown)  # Filtered Markdown focusing on machine learning
```

### Troubleshooting Markdown Generation

- **Empty Markdown Output?**  
  Check if the crawler successfully fetched HTML. Ensure your filters are not overly strict. If no filter is used and you still get no output, verify the HTML content isn’t empty or malformed.

- **Malformed HTML Content?**  
  The internal parser is robust, but if encountering strange characters, consider adjusting `escape_html` to `True` or removing problematic tags using filters.

- **Performance Considerations:**  
  Complex filters or very large HTML documents can slow down processing. Consider caching results or reducing `body_width` if line-wrapping is unnecessary.

---

### 5.2.1 MarkdownGenerationResult

After running the crawler, `result.markdown_v2` returns a `MarkdownGenerationResult` object.

**Attributes:**
- `raw_markdown` (str): Unfiltered Markdown.
- `markdown_with_citations` (str): Markdown with all links converted into references at the end.
- `references_markdown` (str): A list of extracted references.
- `fit_markdown` (Optional[str]): Markdown after applying filters.
- `fit_html` (Optional[str]): Filtered HTML corresponding to `fit_markdown`.

**Integration Example:**

```python
result = await crawler.arun("https://crawl4ai.com")
print("RAW:", result.markdown_v2.raw_markdown)
print("CITED:", result.markdown_v2.markdown_with_citations)
print("FIT:", result.markdown_v2.fit_markdown)
```

**Use Cases:**
- **RAG Pipelines:** Feed `fit_markdown` into a vector database for semantic search.
- **LLM Fine-Tuning:** Use `raw_markdown` or `fit_markdown` as training data for large models.

---

## 5.3 Filtering Strategies

Filters refine raw HTML to produce cleaner Markdown. They can remove boilerplate sections (headers, footers) or focus on content relevant to a specific query.

**Two Major Strategies:**
1. **BM25ContentFilter:**  
   A relevance-based approach using BM25 scoring to rank content sections according to a user query.

2. **PruningContentFilter (Emphasized):**  
   An unsupervised, clustering-like approach that systematically prunes irrelevant or noisy parts of the HTML. Unlike BM25, which relies on a query for relevance, `PruningContentFilter` attempts to cluster and discard noise based on structural and heuristic metrics. This makes it highly useful for general cleanup without predefined queries.

---

### Relevance-Based Filtering: BM25

BM25 ranks content blocks by relevance to a given query. It’s semi-supervised in the sense that it needs a query (`user_query`).

**Key Parameters:**
- `user_query` (string): The query for content relevance.  
- `bm25_threshold` (float): The minimum relevance score. Increase to get less but more focused content.
- `use_stemming` (bool): When `True`, matches variations of words.  
- `case_sensitive` (bool): Controls case sensitivity.

**If omitted `user_query`,** BM25 just scores content but doesn’t have a specific target. Useful if you need general scoring.

**Example:**
```python
from crawl4ai.content_filter_strategy import BM25ContentFilter

config = CrawlerRunConfig(
    content_filter=BM25ContentFilter(
        user_query="artificial intelligence",
        bm25_threshold=2.0,
        use_stemming=True
    )
)
```

**Troubleshooting BM25:**
- If you get too much irrelevant content, raise `bm25_threshold`.
- If you get too little content, lower it or disable `case_sensitive`.

---

### PruningContentFilter: Unsupervised Content Clustering

`PruningContentFilter` is about intelligently stripping away non-essential parts of a page—ads, navigation bars, repetitive links—without relying on a specific user query. Think of it as an unsupervised clustering method that scores content blocks and removes “noise.”

**Key Features:**
- **Unsupervised Nature:** No query needed. Uses heuristics like text density, link density, tag importance, and HTML structure.  
- **Clustering-Like Behavior:** It effectively “clusters” page sections by their structural and textual qualities, and prunes those that don’t meet thresholds.  
- **Threshold Adjustments:** Dynamically adjusts or uses a fixed threshold to remove or keep content blocks.

**Parameters:**
- `threshold` (float): Score threshold for removing content. Higher values prune more aggressively. Default: `0.5`.
- `threshold_type` (str): `"fixed"` or `"dynamic"`.  
   - **Fixed:** Compares each block’s score directly to a set threshold.  
   - **Dynamic:** Adjusts threshold based on content metrics for a more adaptive approach.
- `min_word_threshold` (int): Minimum word count to keep a content block.  
- Internal metrics consider:
  - **Text Density:** Prefers sections rich in text over code or sparse elements.
  - **Link Density:** Penalizes sections with too many links.
  - **Tag Importance:** Some tags (e.g., `<article>`, `<main>`, `<section>`) are considered more important and less likely to be pruned.
  - **Class/ID patterns:** Looks for signals (like `nav`, `footer`) to identify boilerplate.

**Example:**
```python
from crawl4ai.content_filter_strategy import PruningContentFilter

config = CrawlerRunConfig(
    content_filter=PruningContentFilter(
        threshold=0.7,
        threshold_type="dynamic",
        min_word_threshold=100
    )
)
```

In this example, content blocks under a dynamically adjusted threshold are pruned, and any block under 100 words is discarded, ensuring you keep only substantial textual sections.

**When to Use PruningContentFilter:**
- **General Cleanup:** If you want a broad cleanup of the page without a specific target query, pruning is your go-to.
- **Pre-Processing Large Corpora:** Before applying more specific filters, prune to remove boilerplate, then apply BM25 for query-focused refinement.

**Troubleshooting Pruning Filter:**
- **Too Much Content Gone?** Lower the `threshold` or switch from `dynamic` to `fixed` threshold for more predictable behavior.
- **Not Enough Pruning?** Increase `threshold` to be more aggressive.
- **Mixed Results?** Adjust `min_word_threshold` or try the `dynamic` threshold mode to fine-tune results.

---

## 5.4 Fit Markdown: Bringing It All Together

“Fit Markdown” is the output you get when applying filters to the raw HTML before markdown generation. This produces a final, optimized Markdown that’s noise-free and content-focused.

### Advanced Usage Scenario

**Combining BM25 and Pruning:**  
1. First apply `PruningContentFilter` to remove general junk.  
2. Then apply a `BM25ContentFilter` to focus on query relevance.

*Example:*

```python
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler

combined_filter = BM25ContentFilter(
    user_query="technology advancements",
    bm25_threshold=1.2,
    use_stemming=True
)

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.5)  # First prune
    )
)

async with AsyncWebCrawler() as crawler:
    # First run pruning
    result = await crawler.arun("https://crawl4ai.com", config=config)
    pruned_fit_markdown = result.markdown_v2.fit_markdown

    # Re-run the BM25 filter on the pruned output, or integrate BM25 in a pipeline
    # (In practice, you'd integrate both filters within the crawler or run a second pass.)
```

**Performance Note:**  
Fit Markdown reduces token count, making subsequent LLM operations faster and cheaper.

---

## 5.5 Best Practices

- **Iterative Adjustment:** Start with default parameters, then adjust filters, thresholds, and `html2text_config` based on the quality of output you need.
- **Combining Filters:** Use `PruningContentFilter` first to remove boilerplate, then a `BM25ContentFilter` to target relevance.
- **Check Downstream Applications:** If you’re using fit Markdown for training LLMs, inspect the output to ensure no essential references were pruned.
- **Docker Deployment:**  
  Running Crawl4AI in a Docker container ensures a consistent environment. Just include the required packages in your Dockerfile and run the crawler script inside the container.
- **Caching Results:**  
  To save time, cache the raw HTML or intermediate Markdown. If you know you’ll re-run filters or change parameters often, caching avoids redundant crawling.

**Handling Special Cases:**
- **Authentication-Protected Pages:**  
  If you need to crawl gated content, provide appropriate session tokens or use a headless browser approach before feeding HTML to the generator.
- **Proxies and Timeouts:**  
  Configure the crawler with proxies or increased timeouts for sites that are slow or region-restricted.

---

## 5.6 Troubleshooting & FAQ

**Why am I getting empty Markdown?**  
- Ensure that the URL is correct and the crawler fetched content.
- If using filters, relax your thresholds.

**How to handle JavaScript-heavy sites?**  
- Run a headless browser upstream to render the page. Crawl4AI expects server-rendered HTML.
  
**How to improve formatting for code snippets?**  
- Set `handle_code_in_pre = True` in `html2text_config` to preserve code blocks more accurately.

**Links are cluttering my Markdown.**  
- Use `ignore_links=True` or convert them to citations for a cleaner layout.

---

## 5.7 Real-World Use Cases

1. **Summarizing News Articles:**  
   Use `PruningContentFilter` to strip ads and nav bars, then just the raw output to get a neat summary.

2. **Preparing Data for LLM Fine-Tuning:**  
   For a large corpus, first prune all pages to remove boilerplate, then optionally apply BM25 to focus on specific topics. The resulting Markdown is ideal for training because it’s dense with meaningful content.

3. **RAG Pipelines:**  
   Extract `fit_markdown`, store it in a vector database, and use it for retrieval-augmented generation. The references and structured headings enhance search relevance.

---

## 5.8 Appendix (References)

**Source Code Files:**
- [markdown_generation_strategy.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/markdown_generation_strategy.py)
  - **Key Classes:** `MarkdownGenerationStrategy`, `DefaultMarkdownGenerator`
  - **Key Functions:** `convert_links_to_citations()`, `generate_markdown()`
  
- [content_filter_strategy.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/content_filter_strategy.py)
  - **Key Classes:** `RelevantContentFilter`, `BM25ContentFilter`, `PruningContentFilter`
  - **Metrics & Heuristics:** Examine `PruningContentFilter` code for scoring logic and threshold adjustments.

Exploring the source code will provide deeper insights into how tags are parsed, how scores are computed for pruning, and how BM25 relevance is calculated.

---

**In summary**, Markdown generation in Crawl4AI provides a powerful, configurable pipeline to transform raw HTML into AI-ready Markdown. By leveraging `PruningContentFilter` for general cleanup and `BM25ContentFilter` for query-focused extraction, plus fine-tuning `html2text_config`, you can achieve high-quality outputs for a wide range of AI applications.