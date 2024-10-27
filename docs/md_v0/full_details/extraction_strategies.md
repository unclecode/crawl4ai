## Extraction Strategies 🧠

Crawl4AI offers powerful extraction strategies to derive meaningful information from web content. Let's dive into two of the most important strategies: `CosineStrategy` and `LLMExtractionStrategy`.

### CosineStrategy

`CosineStrategy` uses hierarchical clustering based on cosine similarity to group text chunks into meaningful clusters. This method converts each chunk into its embedding and then clusters them to form semantical chunks.

#### When to Use
- Ideal for fast, accurate semantic segmentation of text.
- Perfect for scenarios where LLMs might be overkill or too slow.
- Suitable for narrowing down content based on specific queries or keywords.

#### Parameters
- `semantic_filter` (str, optional): Keywords for filtering relevant documents before clustering. Documents are filtered based on their cosine similarity to the keyword filter embedding. Default is `None`.
- `word_count_threshold` (int, optional): Minimum number of words per cluster. Default is `20`.
- `max_dist` (float, optional): Maximum cophenetic distance on the dendrogram to form clusters. Default is `0.2`.
- `linkage_method` (str, optional): Linkage method for hierarchical clustering. Default is `'ward'`.
- `top_k` (int, optional): Number of top categories to extract. Default is `3`.
- `model_name` (str, optional): Model name for embedding generation. Default is `'BAAI/bge-small-en-v1.5'`.

#### Example
```python
from crawl4ai.extraction_strategy import CosineStrategy
from crawl4ai import WebCrawler

crawler = WebCrawler()
crawler.warmup()

# Define extraction strategy
strategy = CosineStrategy(
    semantic_filter="finance economy stock market",
    word_count_threshold=10,
    max_dist=0.2,
    linkage_method='ward',
    top_k=3,
    model_name='BAAI/bge-small-en-v1.5'
)

# Sample URL
url = "https://www.nbcnews.com/business"

# Run the crawler with the extraction strategy
result = crawler.run(url=url, extraction_strategy=strategy)
print(result.extracted_content)
```

### LLMExtractionStrategy

`LLMExtractionStrategy` leverages a Language Model (LLM) to extract meaningful content from HTML. This strategy uses an external provider for LLM completions to perform extraction based on instructions.

#### When to Use
- Suitable for complex extraction tasks requiring nuanced understanding.
- Ideal for scenarios where detailed instructions can guide the extraction process.
- Perfect for extracting specific types of information or content with precise guidelines.

#### Parameters
- `provider` (str, optional): Provider for language model completions (e.g., openai/gpt-4). Default is `DEFAULT_PROVIDER`.
- `api_token` (str, optional): API token for the provider. If not provided, it will try to load from the environment variable `OPENAI_API_KEY`.
- `instruction` (str, optional): Instructions to guide the LLM on how to perform the extraction. Default is `None`.

#### Example Without Instructions
```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import WebCrawler

crawler = WebCrawler()
crawler.warmup()

# Define extraction strategy without instructions
strategy = LLMExtractionStrategy(
    provider='openai',
    api_token='your_api_token'
)

# Sample URL
url = "https://www.nbcnews.com/business"

# Run the crawler with the extraction strategy
result = crawler.run(url=url, extraction_strategy=strategy)
print(result.extracted_content)
```

#### Example With Instructions
```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import WebCrawler

crawler = WebCrawler()
crawler.warmup()

# Define extraction strategy with instructions
strategy = LLMExtractionStrategy(
    provider='openai',
    api_token='your_api_token',
    instruction="Extract only financial news and summarize key points."
)

# Sample URL
url = "https://www.nbcnews.com/business"

# Run the crawler with the extraction strategy
result = crawler.run(url=url, extraction_strategy=strategy)
print(result.extracted_content)
```

#### Use Cases for LLMExtractionStrategy
- Extracting specific data types from structured or semi-structured content.
- Generating summaries, extracting key information, or transforming content into different formats.
- Performing detailed extractions based on custom instructions.

For more detailed examples, please refer to the [Examples section](../examples/index.md) of the documentation.

---

By choosing the right extraction strategy, you can effectively extract the most relevant and useful information from web content. Whether you need fast, accurate semantic segmentation with `CosineStrategy` or nuanced, instruction-based extraction with `LLMExtractionStrategy`, Crawl4AI has you covered. Happy extracting! 🕵️‍♂️✨
