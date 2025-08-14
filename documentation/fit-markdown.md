Fit Markdown with Pruning & BM25
================================

**Fit Markdown** is a specialized **filtered** version of your page’s markdown, focusing on the most relevant content. By default, Crawl4AI converts the entire HTML into a broad **raw\_markdown**. With fit markdown, we apply a **content filter** algorithm (e.g., **Pruning** or **BM25**) to remove or rank low-value sections—such as repetitive sidebars, shallow text blocks, or irrelevancies—leaving a concise textual “core.”

---

1. How “Fit Markdown” Works
---------------------------

### 1.1 The `content_filter`

In **`CrawlerRunConfig`**, you can specify a **`content_filter`** to shape how content is pruned or ranked before final markdown generation. A filter’s logic is applied **before** or **during** the HTML→Markdown process, producing:

* **`result.markdown.raw_markdown`** (unfiltered)
* **`result.markdown.fit_markdown`** (filtered or “fit” version)
* **`result.markdown.fit_html`** (the corresponding HTML snippet that produced `fit_markdown`)

### 1.2 Common Filters

1. **PruningContentFilter** – Scores each node by text density, link density, and tag importance, discarding those below a threshold.
2. **BM25ContentFilter** – Focuses on textual relevance using BM25 ranking, especially useful if you have a specific user query (e.g., “machine learning” or “food nutrition”).

---