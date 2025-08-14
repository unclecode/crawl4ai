[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/core/fit-markdown/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * Fit Markdown
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Fit Markdown with Pruning & BM25](https://docs.crawl4ai.com/core/fit-markdown/#fit-markdown-with-pruning-bm25)
  * [1. How “Fit Markdown” Works](https://docs.crawl4ai.com/core/fit-markdown/#1-how-fit-markdown-works)
  * [2. PruningContentFilter](https://docs.crawl4ai.com/core/fit-markdown/#2-pruningcontentfilter)
  * [3. BM25ContentFilter](https://docs.crawl4ai.com/core/fit-markdown/#3-bm25contentfilter)
  * [4. Accessing the “Fit” Output](https://docs.crawl4ai.com/core/fit-markdown/#4-accessing-the-fit-output)
  * [5. Code Patterns Recap](https://docs.crawl4ai.com/core/fit-markdown/#5-code-patterns-recap)
  * [6. Combining with “word_count_threshold” & Exclusions](https://docs.crawl4ai.com/core/fit-markdown/#6-combining-with-word_count_threshold-exclusions)
  * [7. Custom Filters](https://docs.crawl4ai.com/core/fit-markdown/#7-custom-filters)
  * [8. Final Thoughts](https://docs.crawl4ai.com/core/fit-markdown/#8-final-thoughts)


# Fit Markdown with Pruning & BM25
**Fit Markdown** is a specialized **filtered** version of your page’s markdown, focusing on the most relevant content. By default, Crawl4AI converts the entire HTML into a broad **raw_markdown**. With fit markdown, we apply a **content filter** algorithm (e.g., **Pruning** or **BM25**) to remove or rank low-value sections—such as repetitive sidebars, shallow text blocks, or irrelevancies—leaving a concise textual “core.”
* * *
## 1. How “Fit Markdown” Works
### 1.1 The `content_filter`
In **`CrawlerRunConfig`**, you can specify a**`content_filter`**to shape how content is pruned or ranked before final markdown generation. A filter’s logic is applied**before** or **during** the HTML→Markdown process, producing:
  * **`result.markdown.raw_markdown`**(unfiltered)
  * **`result.markdown.fit_markdown`**(filtered or “fit” version)
  * **`result.markdown.fit_html`**(the corresponding HTML snippet that produced`fit_markdown`)


### 1.2 Common Filters
1. **PruningContentFilter** – Scores each node by text density, link density, and tag importance, discarding those below a threshold.
2. **BM25ContentFilter** – Focuses on textual relevance using BM25 ranking, especially useful if you have a specific user query (e.g., “machine learning” or “food nutrition”).
* * *
## 2. PruningContentFilter
**Pruning** discards less relevant nodes based on **text density, link density, and tag importance**. It’s a heuristic-based approach—if certain sections appear too “thin” or too “spammy,” they’re pruned.
### 2.1 Usage Example
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # Step 1: Create a pruning filter
    prune_filter = PruningContentFilter(
        # Lower → more content retained, higher → more content pruned
        threshold=0.45,
        # "fixed" or "dynamic"
        threshold_type="dynamic",
        # Ignore nodes with <5 words
        min_word_threshold=5
    )

    # Step 2: Insert it into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    # Step 3: Pass it to CrawlerRunConfig
    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )

        if result.success:
            # 'fit_markdown' is your pruned content, focusing on "denser" text
            print("Raw Markdown length:", len(result.markdown.raw_markdown))
            print("Fit Markdown length:", len(result.markdown.fit_markdown))
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

### 2.2 Key Parameters
  * **`min_word_threshold`**(int): If a block has fewer words than this, it’s pruned.
  * **`threshold_type`**(str):
  * `"fixed"` → each node must exceed `threshold` (0–1).
  * `"dynamic"` → node scoring adjusts according to tag type, text/link density, etc.
  * **`threshold`**(float, default ~0.48): The base or “anchor” cutoff.


**Algorithmic Factors** :
  * **Text density** – Encourages blocks that have a higher ratio of text to overall content.
  * **Link density** – Penalizes sections that are mostly links.
  * **Tag importance** – e.g., an `<article>` or `<p>` might be more important than a `<div>`.
  * **Structural context** – If a node is deeply nested or in a suspected sidebar, it might be deprioritized.


* * *
## 3. BM25ContentFilter
**BM25** is a classical text ranking algorithm often used in search engines. If you have a **user query** or rely on page metadata to derive a query, BM25 can identify which text chunks best match that query.
### 3.1 Usage Example
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # 1) A BM25 filter with a user query
    bm25_filter = BM25ContentFilter(
        user_query="startup fundraising tips",
        # Adjust for stricter or looser results
        bm25_threshold=1.2
    )

    # 2) Insert into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)

    # 3) Pass to crawler config
    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        if result.success:
            print("Fit Markdown (BM25 query-based):")
            print(result.markdown.fit_markdown)
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

### 3.2 Parameters
  * **`user_query`**(str, optional): E.g.`"machine learning"`. If blank, the filter tries to glean a query from page metadata.
  * **`bm25_threshold`**(float, default 1.0):
  * Higher → fewer chunks but more relevant.
  * Lower → more inclusive.


> In more advanced scenarios, you might see parameters like `language`, `case_sensitive`, or `priority_tags` to refine how text is tokenized or weighted.
* * *
## 4. Accessing the “Fit” Output
After the crawl, your “fit” content is found in **`result.markdown.fit_markdown`**.
```
fit_md = result.markdown.fit_markdown
fit_html = result.markdown.fit_html
Copy
```

If the content filter is **BM25** , you might see additional logic or references in `fit_markdown` that highlight relevant segments. If it’s **Pruning** , the text is typically well-cleaned but not necessarily matched to a query.
* * *
## 5. Code Patterns Recap
### 5.1 Pruning
```
prune_filter = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",
    min_word_threshold=10
)
md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
config = CrawlerRunConfig(markdown_generator=md_generator)
Copy
```

### 5.2 BM25
```
bm25_filter = BM25ContentFilter(
    user_query="health benefits fruit",
    bm25_threshold=1.2
)
md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)
config = CrawlerRunConfig(markdown_generator=md_generator)
Copy
```

* * *
## 6. Combining with “word_count_threshold” & Exclusions
Remember you can also specify:
```
config = CrawlerRunConfig(
    word_count_threshold=10,
    excluded_tags=["nav", "footer", "header"],
    exclude_external_links=True,
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.5)
    )
)
Copy
```

Thus, **multi-level** filtering occurs:
  1. The crawler’s `excluded_tags` are removed from the HTML first.
  2. The content filter (Pruning, BM25, or custom) prunes or ranks the remaining text blocks.
  3. The final “fit” content is generated in `result.markdown.fit_markdown`.


* * *
## 7. Custom Filters
If you need a different approach (like a specialized ML model or site-specific heuristics), you can create a new class inheriting from `RelevantContentFilter` and implement `filter_content(html)`. Then inject it into your **markdown generator** :
```
from crawl4ai.content_filter_strategy import RelevantContentFilter

class MyCustomFilter(RelevantContentFilter):
    def filter_content(self, html, min_word_threshold=None):
        # parse HTML, implement custom logic
        return [block for block in ... if ... some condition...]
Copy
```

**Steps** :
  1. Subclass `RelevantContentFilter`.
  2. Implement `filter_content(...)`.
  3. Use it in your `DefaultMarkdownGenerator(content_filter=MyCustomFilter(...))`.


* * *
## 8. Final Thoughts
**Fit Markdown** is a crucial feature for:
  * **Summaries** : Quickly get the important text from a cluttered page.
  * **Search** : Combine with **BM25** to produce content relevant to a query.
  * **AI Pipelines** : Filter out boilerplate so LLM-based extraction or summarization runs on denser text.


**Key Points** : - **PruningContentFilter** : Great if you just want the “meatiest” text without a user query.
- **BM25ContentFilter** : Perfect for query-based extraction or searching.
- Combine with **`excluded_tags`,`exclude_external_links` , `word_count_threshold`** to refine your final “fit” text.
- Fit markdown ends up in **`result.markdown.fit_markdown`**; eventually**`result.markdown.fit_markdown`**in future versions.
With these tools, you can **zero in** on the text that truly matters, ignoring spammy or boilerplate content, and produce a concise, relevant “fit markdown” for your AI or data pipelines. Happy pruning and searching!
  * Last Updated: 2025-01-01


#### On this page
  * [1. How “Fit Markdown” Works](https://docs.crawl4ai.com/core/fit-markdown/#1-how-fit-markdown-works)
  * [1.1 The content_filter](https://docs.crawl4ai.com/core/fit-markdown/#11-the-content_filter)
  * [1.2 Common Filters](https://docs.crawl4ai.com/core/fit-markdown/#12-common-filters)
  * [2. PruningContentFilter](https://docs.crawl4ai.com/core/fit-markdown/#2-pruningcontentfilter)
  * [2.1 Usage Example](https://docs.crawl4ai.com/core/fit-markdown/#21-usage-example)
  * [2.2 Key Parameters](https://docs.crawl4ai.com/core/fit-markdown/#22-key-parameters)
  * [3. BM25ContentFilter](https://docs.crawl4ai.com/core/fit-markdown/#3-bm25contentfilter)
  * [3.1 Usage Example](https://docs.crawl4ai.com/core/fit-markdown/#31-usage-example)
  * [3.2 Parameters](https://docs.crawl4ai.com/core/fit-markdown/#32-parameters)
  * [4. Accessing the “Fit” Output](https://docs.crawl4ai.com/core/fit-markdown/#4-accessing-the-fit-output)
  * [5. Code Patterns Recap](https://docs.crawl4ai.com/core/fit-markdown/#5-code-patterns-recap)
  * [5.1 Pruning](https://docs.crawl4ai.com/core/fit-markdown/#51-pruning)
  * [5.2 BM25](https://docs.crawl4ai.com/core/fit-markdown/#52-bm25)
  * [6. Combining with “word_count_threshold” & Exclusions](https://docs.crawl4ai.com/core/fit-markdown/#6-combining-with-word_count_threshold-exclusions)
  * [7. Custom Filters](https://docs.crawl4ai.com/core/fit-markdown/#7-custom-filters)
  * [8. Final Thoughts](https://docs.crawl4ai.com/core/fit-markdown/#8-final-thoughts)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
