Extracting JSON (LLM)
=====================

In some cases, you need to extract **complex or unstructured** information from a webpage that a simple CSS/XPath schema cannot easily parse. Or you want **AI**-driven insights, classification, or summarization. For these scenarios, Crawl4AI provides an **LLM-based extraction strategy** that:

1. Works with **any** large language model supported by [LiteLLM](https://github.com/BerriAI/litellm) (Ollama, OpenAI, Claude, and more).
2. Automatically splits content into chunks (if desired) to handle token limits, then combines results.
3. Lets you define a **schema** (like a Pydantic model) or a simpler “block” extraction approach.

**Important**: LLM-based extraction can be slower and costlier than schema-based approaches. If your page data is highly structured, consider using [`JsonCssExtractionStrategy`](../no-llm-strategies/) or [`JsonXPathExtractionStrategy`](../no-llm-strategies/) first. But if you need AI to interpret or reorganize content, read on!

---

1. Why Use an LLM?
------------------

* **Complex Reasoning**: If the site’s data is unstructured, scattered, or full of natural language context.
* **Semantic Extraction**: Summaries, knowledge graphs, or relational data that require comprehension.
* **Flexible**: You can pass instructions to the model to do more advanced transformations or classification.

---