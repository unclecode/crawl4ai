Extracting JSON (No LLM)
========================

One of Crawl4AI's **most powerful** features is extracting **structured JSON** from websites **without** relying on large language models. Crawl4AI offers several strategies for LLM-free extraction:

1. **Schema-based extraction** with CSS or XPath selectors via `JsonCssExtractionStrategy` and `JsonXPathExtractionStrategy`
2. **Regular expression extraction** with `RegexExtractionStrategy` for fast pattern matching

These approaches let you extract data instantly—even from complex or nested HTML structures—without the cost, latency, or environmental impact of an LLM.

**Why avoid LLM for basic extractions?**

1. **Faster & Cheaper**: No API calls or GPU overhead.
2. **Lower Carbon Footprint**: LLM inference can be energy-intensive. Pattern-based extraction is practically carbon-free.
3. **Precise & Repeatable**: CSS/XPath selectors and regex patterns do exactly what you specify. LLM outputs can vary or hallucinate.
4. **Scales Readily**: For thousands of pages, pattern-based extraction runs quickly and in parallel.

Below, we'll explore how to craft these schemas and use them with **JsonCssExtractionStrategy** (or **JsonXPathExtractionStrategy** if you prefer XPath). We'll also highlight advanced features like **nested fields** and **base element attributes**.

---

1. Intro to Schema-Based Extraction
-----------------------------------

A schema defines:

1. A **base selector** that identifies each "container" element on the page (e.g., a product row, a blog post card).
2. **Fields** describing which CSS/XPath selectors to use for each piece of data you want to capture (text, attribute, HTML block, etc.).
3. **Nested** or **list** types for repeated or hierarchical structures.

For example, if you have a list of products, each one might have a name, price, reviews, and "related products." This approach is faster and more reliable than an LLM for consistent, structured pages.

---