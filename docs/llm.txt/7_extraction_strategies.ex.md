# Structured Data Extraction Strategies

## Extraction Strategies
Structured data extraction strategies are designed to convert raw web content into organized, JSON-formatted data. These strategies handle diverse extraction scenarios, including schema-based, language model-driven, and clustering methods. This section covers models using LLMs or without using them to extract data with precision and flexibility.

###  LLM Extraction Strategy
The **LLM Extraction Strategy** employs a large language model (LLM) to process content dynamically. It supports:
- **Schema-Based Extraction**: Using a defined JSON schema to structure output.
- **Instruction-Based Extraction**: Accepting custom prompts to guide the extraction process.
- **Flexible Model Usage**: Supporting open-source or paid LLMs.

#### Key Features
- Accepts customizable schemas for structured outputs.
- Incorporates user prompts for tailored results.
- Handles large inputs with chunking and overlap for efficient processing.

#### Parameters and Configurations
Below is a detailed explanation of key parameters:

- **`provider`** *(str)*: Specifies the LLM provider (e.g., `openai`, `ollama`).
  - Default: `DEFAULT_PROVIDER`

- **`api_token`** *(Optional[str])*: API token for the LLM provider.
  - Required unless using a provider that doesn’t need authentication.

- **`instruction`** *(Optional[str])*: A prompt guiding the model on extraction specifics.
  - Example: "Extract all prices and model names from the page."

- **`schema`** *(Optional[Dict])*: JSON schema defining the structure of extracted data.
  - If provided, extraction switches to schema mode.

- **`extraction_type`** *(str)*: Determines extraction mode (`block` or `schema`).
  - Default: `block`

- **Chunking Settings**:
  - **`chunk_token_threshold`** *(int)*: Maximum token count per chunk. Default: `CHUNK_TOKEN_THRESHOLD`.
  - **`overlap_rate`** *(float)*: Proportion of overlapping tokens between chunks. Default: `OVERLAP_RATE`.

- **`extra_args`** *(Dict)*: Additional arguments passed to the LLM API sucj as `max_length`, `temperature`, etc.

#### Example Usage

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import AsyncWebCrawler
from crawl4ai.config import CrawlerRunConfig, BrowserConfig

class OpenAIModelFee(BaseModel):
    model_name: str
    input_fee: str
    output_fee: str

async def extract_structured_data():
    browser_config = BrowserConfig(headless=True)
    extraction_strategy = LLMExtractionStrategy(
        provider="openai",
        api_token="your_api_token",
        schema=OpenAIModelFee.model_json_schema(),
        instruction="Extract all model fees from the content."
    )

    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://crawl4ai.com/pricing",
            config=crawler_config
        )
        print(result.extracted_content)
```

#### Workflow and Error Handling
- **Chunk Merging**: Content is divided into manageable chunks based on the token threshold.
- **Backoff and Retries**: Handles API rate limits with backoff strategies.
- **Error Logging**: Extracted blocks include error tags when issues occur.
- **Parallel Execution**: Supports multi-threaded execution for efficiency.

#### Benefits of Using LLM Extraction Strategy
- **Dynamic Adaptability**: Easily switch between schema-based and instruction-based modes.
- **Scalable**: Processes large content efficiently using chunking.
- **Versatile**: Works with various LLM providers and configurations.

This strategy is ideal for extracting structured data from complex web pages, ensuring compatibility with LLM training and fine-tuning workflows.

###  Cosine Strategy

The Cosine Strategy in Crawl4AI uses similarity-based clustering to identify and extract relevant content sections from web pages. This strategy is particularly useful when you need to find and extract content based on semantic similarity rather than structural patterns.

#### How It Works

The Cosine Strategy:
1. Breaks down page content into meaningful chunks
2. Converts text into vector representations
3. Calculates similarity between chunks
4. Clusters similar content together
5. Ranks and filters content based on relevance

#### Basic Usage

```python
from crawl4ai.extraction_strategy import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="product reviews",    # Target content type
    word_count_threshold=10,             # Minimum words per cluster
    sim_threshold=0.3                    # Similarity threshold
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://crawl4ai.com/reviews",
        extraction_strategy=strategy
    )
    
    content = result.extracted_content
```

#### Configuration Options

##### Core Parameters

```python
CosineStrategy(
    # Content Filtering
    semantic_filter: str = None,       # Keywords/topic for content filtering
    word_count_threshold: int = 10,    # Minimum words per cluster
    sim_threshold: float = 0.3,        # Similarity threshold (0.0 to 1.0)
    
    # Clustering Parameters
    max_dist: float = 0.2,            # Maximum distance for clustering
    linkage_method: str = 'ward',      # Clustering linkage method
    top_k: int = 3,                   # Number of top categories to extract
    
    # Model Configuration
    model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',  # Embedding model
    
    verbose: bool = False             # Enable logging
)
```

##### Parameter Details

1. **semantic_filter**
   - Sets the target topic or content type
   - Use keywords relevant to your desired content
   - Example: "technical specifications", "user reviews", "pricing information"

2. **sim_threshold**
   - Controls how similar content must be to be grouped together
   - Higher values (e.g., 0.8) mean stricter matching
   - Lower values (e.g., 0.3) allow more variation
   ```python
   # Strict matching
   strategy = CosineStrategy(sim_threshold=0.8)
   
   # Loose matching
   strategy = CosineStrategy(sim_threshold=0.3)
   ```

3. **word_count_threshold**
   - Filters out short content blocks
   - Helps eliminate noise and irrelevant content
   ```python
   # Only consider substantial paragraphs
   strategy = CosineStrategy(word_count_threshold=50)
   ```

4. **top_k**
   - Number of top content clusters to return
   - Higher values return more diverse content
   ```python
   # Get top 5 most relevant content clusters
   strategy = CosineStrategy(top_k=5)
   ```

#### Use Cases

##### 1. Article Content Extraction
```python
strategy = CosineStrategy(
    semantic_filter="main article content",
    word_count_threshold=100,  # Longer blocks for articles
    top_k=1                   # Usually want single main content
)

result = await crawler.arun(
    url="https://crawl4ai.com/blog/post",
    extraction_strategy=strategy
)
```

##### 2. Product Review Analysis
```python
strategy = CosineStrategy(
    semantic_filter="customer reviews and ratings",
    word_count_threshold=20,   # Reviews can be shorter
    top_k=10,                 # Get multiple reviews
    sim_threshold=0.4         # Allow variety in review content
)
```

##### 3. Technical Documentation
```python
strategy = CosineStrategy(
    semantic_filter="technical specifications documentation",
    word_count_threshold=30,
    sim_threshold=0.6,        # Stricter matching for technical content
    max_dist=0.3             # Allow related technical sections
)
```

#### Advanced Features

##### Custom Clustering
```python
strategy = CosineStrategy(
    linkage_method='complete',  # Alternative clustering method
    max_dist=0.4,              # Larger clusters
    model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'  # Multilingual support
)
```

##### Content Filtering Pipeline
```python
strategy = CosineStrategy(
    semantic_filter="pricing plans features",
    word_count_threshold=15,
    sim_threshold=0.5,
    top_k=3
)

async def extract_pricing_features(url: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=strategy
        )
        
        if result.success:
            content = json.loads(result.extracted_content)
            return {
                'pricing_features': content,
                'clusters': len(content),
                'similarity_scores': [item['score'] for item in content]
            }
```

#### Best Practices

1. **Adjust Thresholds Iteratively**
   - Start with default values
   - Adjust based on results
   - Monitor clustering quality

2. **Choose Appropriate Word Count Thresholds**
   - Higher for articles (100+)
   - Lower for reviews/comments (20+)
   - Medium for product descriptions (50+)

3. **Optimize Performance**
   ```python
   strategy = CosineStrategy(
       word_count_threshold=10,  # Filter early
       top_k=5,                 # Limit results
       verbose=True             # Monitor performance
   )
   ```

4. **Handle Different Content Types**
   ```python
   # For mixed content pages
   strategy = CosineStrategy(
       semantic_filter="product features",
       sim_threshold=0.4,      # More flexible matching
       max_dist=0.3,          # Larger clusters
       top_k=3                # Multiple relevant sections
   )
   ```

#### Error Handling

```python
try:
    result = await crawler.arun(
        url="https://crawl4ai.com",
        extraction_strategy=strategy
    )
    
    if result.success:
        content = json.loads(result.extracted_content)
        if not content:
            print("No relevant content found")
    else:
        print(f"Extraction failed: {result.error_message}")
        
except Exception as e:
    print(f"Error during extraction: {str(e)}")
```

The Cosine Strategy is particularly effective when:
- Content structure is inconsistent
- You need semantic understanding
- You want to find similar content blocks
- Structure-based extraction (CSS/XPath) isn't reliable

It works well with other strategies and can be used as a pre-processing step for LLM-based extraction.


###  JSON-Based Extraction Strategies with AsyncWebCrawler

In many cases, relying on a Large Language Model (LLM) to parse and structure data from web pages is both unnecessary and wasteful. Instead of incurring additional computational overhead, network latency, and even contributing to unnecessary CO2 emissions, you can employ direct HTML parsing strategies. These approaches are faster, simpler, and more environmentally friendly, running efficiently on any computer or device without costly API calls.

Crawl4AI offers two primary declarative extraction strategies that do not depend on LLMs:
- `JsonCssExtractionStrategy`
- `JsonXPathExtractionStrategy`

Of these two, while CSS selectors are often simpler to use, **XPath selectors are generally more robust and flexible**, particularly for large-scale scraping tasks. Modern websites often generate dynamic or ephemeral class names that are subject to frequent change. XPath, on the other hand, allows you to navigate the DOM structure directly, making your selectors less brittle and less dependent on inconsistent class names.

#### Why Use JSON-Based Extraction Instead of LLMs?

1. **Speed & Efficiency**: Direct HTML parsing bypasses the latency of external API calls.
2. **Lower Resource Usage**: No need for large models, GPU acceleration, or network overhead.
3. **Environmentally Friendly**: Reduced energy consumption and carbon footprint compared to LLM inference.
4. **Offline Capability**: Works anywhere you have the HTML, no network needed.
5. **Scalability & Reliability**: Stable and predictable, without dealing with model “hallucinations” or downtime.

#### Advantages of XPath Over CSS

1. **Stability in Dynamic Environments**: Websites change their classes and IDs constantly. XPath allows you to refer to elements by structure and position instead of relying on fragile class names.
2. **Finer-Grained Control**: XPath supports advanced queries like traversing parent/child relationships, filtering based on attributes, and handling complex nested patterns.
3. **Consistency Across Complex Pages**: Even when the front-end framework changes markup or introduces randomized class names, XPath expressions often remain valid if the structural hierarchy stays intact.
4. **More Powerful Selection Logic**: You can write conditions like `//div[@data-test='price']` or `//tr[3]/td[2]` to accurately pinpoint elements.

#### Example Using XPath

Below is an example that extracts cryptocurrency prices from a hypothetical page using `JsonXPathExtractionStrategy`. Here, we avoid depending on class names entirely, focusing on the consistent structure of the HTML. By adjusting XPath expressions, you can overcome dynamic naming schemes that would break fragile CSS selectors.

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy

async def extract_data_using_xpath():
    print("\n--- Using JsonXPathExtractionStrategy for Fast, Reliable Structured Output ---")

    # Define the extraction schema using XPath selectors
    # Example: We know the table rows are always in this structure, regardless of class names
    schema = {
        "name": "Crypto Prices",
        "baseSelector": "//table/tbody/tr",
        "fields": [
            {
                "name": "crypto",
                "selector": ".//td[1]/h2",
                "type": "text",
            },
            {
                "name": "symbol",
                "selector": ".//td[1]/p",
                "type": "text",
            },
            {
                "name": "price",
                "selector": ".//td[2]",
                "type": "text",
            }
        ],
    }

    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        # Use XPath extraction on a page known for frequently changing its class names
        result = await crawler.arun(
            url="https://www.examplecrypto.com/prices",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        assert result.success, "Failed to crawl the page"

        # Parse the extracted content
        crypto_prices = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(crypto_prices)} cryptocurrency prices")
        print(json.dumps(crypto_prices[0], indent=2))

    return crypto_prices

# Run the async function
asyncio.run(extract_data_using_xpath())
```

#### When to Use CSS vs. XPath

- **CSS Selectors**: Good for simpler, stable sites where classes and IDs are fixed and descriptive. Ideal if you’re already familiar with front-end development patterns.
- **XPath Selectors**: Recommended for complex or highly dynamic websites. If classes and IDs are meaningless, random, or prone to frequent changes, XPath provides a more structural and future-proof solution.

#### Handling Dynamic Content

Even on websites that load content asynchronously, you can still rely on XPath extraction. Combine the extraction strategy with JavaScript execution to scroll or wait for certain elements to appear. Using XPath after the page finishes loading ensures you’re targeting elements that are fully rendered and stable.

For example:

```python
async def extract_dynamic_data():
    schema = {
        "name": "Dynamic Crypto Prices",
        "baseSelector": "//tr[contains(@class, 'price-row')]",
        "fields": [
            {"name": "name", "selector": ".//td[1]", "type": "text"},
            {"name": "price", "selector": ".//td[2]", "type": "text"},
        ]
    }

    js_code = """
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(resolve => setTimeout(resolve, 2000));
    """

    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.examplecrypto.com/dynamic-prices",
            extraction_strategy=extraction_strategy,
            js_code=js_code,
            wait_for="//tr[contains(@class, 'price-row')][20]",  # Wait until at least 20 rows load
            bypass_cache=True,
        )

        crypto_data = json.loads(result.extracted_content)
        print(f"Extracted {len(crypto_data)} cryptocurrency entries")
```

#### Best Practices

1. **Avoid LLM-Based Extraction**: If the data is repetitive and structured, direct HTML parsing is faster, cheaper, and more stable.
2. **Start with XPath**: In a constantly changing environment, building XPath selectors from stable structural elements (like table hierarchies, element positions, or unique attributes) ensures you won’t need to frequently rewrite selectors.
3. **Test in Developer Tools**: Use browser consoles or `xmllint` to quickly verify XPath queries before coding.
4. **Focus on Hierarchy, Not Classes**: Avoid relying on class names if they’re dynamic. Instead, use structural approaches like `//table/tbody/tr` or `//div[@data-test='price']`.
5. **Combine with JS Execution**: For dynamic sites, run small snippets of JS to reveal content before extracting with XPath.

By following these guidelines, you can create high-performance, resilient extraction pipelines. You’ll save resources, reduce environmental impact, and enjoy a level of reliability and speed that LLM-based solutions can’t match when parsing repetitive data from complex or ever-changing websites.

### **Automating Schema Generation with a One-Time LLM-Assisted Utility**

While the focus of these extraction strategies is to avoid continuous reliance on LLMs, you can leverage a model once to streamline the creation of complex schemas. Instead of painstakingly determining repetitive patterns, crafting CSS or XPath selectors, and deciding field definitions by hand, you can prompt a language model once with the raw HTML and a brief description of what you need to extract. The result is a ready-to-use schema that you can plug into `JsonCssExtractionStrategy` or `JsonXPathExtractionStrategy` for lightning-fast extraction without further model calls.

**How It Works:**
1. Provide the raw HTML containing your repetitive patterns.
2. Optionally specify a natural language query describing the data you want.
3. Run `generate_schema(html, query)` to let the LLM generate a schema automatically.
4. Take the returned schema and use it directly with `JsonCssExtractionStrategy` or `JsonXPathExtractionStrategy`.
5. After this initial step, no more LLM calls are necessary—you now have a schema that you can reuse as often as you like.

**Code Example:**

Here is a simplified demonstration using the utility function `generate_schema` that you’ve incorporated into your codebase. In this example, we:
- Use a one-time LLM call to derive a schema from the HTML structure of a job board.
- Apply the resulting schema to `JsonXPathExtractionStrategy` (although you can also use `JsonCssExtractionStrategy` if preferred).
- Extract data from the target page at high speed with no subsequent LLM calls.

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy

# Assume generate_schema is integrated and available
from my_schema_utils import generate_schema

async def extract_data_with_generated_schema():
    # Raw HTML snippet representing repetitive patterns in the webpage
    test_html = """
    <div class="company-listings">
        <div class="company" data-company-id="123">
            <div class="company-header">
                <img class="company-logo" src="google.png" alt="Google">
                <h1 class="company-name">Google</h1>
                <div class="company-meta">
                    <span class="company-size">10,000+ employees</span>
                    <span class="company-industry">Technology</span>
                    <a href="https://google.careers" class="careers-link">Careers Page</a>
                </div>
            </div>
            
            <div class="departments">
                <div class="department">
                    <h2 class="department-name">Engineering</h2>
                    <div class="positions">
                        <div class="position-card" data-position-id="eng-1">
                            <h3 class="position-title">Senior Software Engineer</h3>
                            <span class="salary-range">$150,000 - $250,000</span>
                            <div class="position-meta">
                                <span class="location">Mountain View, CA</span>
                                <span class="job-type">Full-time</span>
                                <span class="experience">5+ years</span>
                            </div>
                            <div class="skills-required">
                                <span class="skill">Python</span>
                                <span class="skill">Kubernetes</span>
                                <span class="skill">Machine Learning</span>
                            </div>
                            <p class="position-description">Join our core engineering team...</p>
                            <div class="application-info">
                                <span class="posting-date">Posted: 2024-03-15</span>
                                <button class="apply-btn" data-req-id="REQ12345">Apply Now</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

    # Optional natural language query to guide the schema generation
    query = "Extract company name, position titles, and salaries"

    # One-time call to the LLM to generate a reusable schema
    schema = generate_schema(test_html, query=query)

    # Other exmaples of queries:
    # # Test 1: No query (should extract everything)
    # print("\nTest 1: No Query (Full Schema)")
    # schema1 = generate_schema(test_html)
    # print(json.dumps(schema1, indent=2))
    
    # # Test 2: Query for just basic job info
    # print("\nTest 2: Basic Job Info Query")
    # query2 = "I only need job titles, salaries, and locations"
    # schema2 = generate_schema(test_html, query2)
    # print(json.dumps(schema2, indent=2))
    
    # # Test 3: Query for company and department structure
    # print("\nTest 3: Organizational Structure Query")
    # query3 = "Extract company details and department names, without position details"
    # schema3 = generate_schema(test_html, query3)
    # print(json.dumps(schema3, indent=2))
    
    # # Test 4: Query for specific skills tracking
    # print("\nTest 4: Skills Analysis Query")
    # query4 = "I want to analyze required skills across all positions"
    # schema4 = generate_schema(test_html, query4)
    # print(json.dumps(schema4, indent=2))

    # Now use the generated schema for high-speed extraction without any further LLM calls
    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # URL for demonstration purposes (use any URL that contains a similar structure)
        result = await crawler.arun(
            url="https://crawl4ai.com/jobs",
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )
        
        if not result.success:
            raise Exception("Extraction failed")

        data = json.loads(result.extracted_content)
        print("Extracted data:")
        print(json.dumps(data, indent=2))

# Run the async function
asyncio.run(extract_data_with_generated_schema())
```

**Benefits of the One-Time LLM Approach:**
- **Time-Saving**: Quickly bootstrap your schema creation, especially for complex pages.
- **Once and Done**: Use the LLM once and then rely purely on the ultra-fast, local extraction strategies.
- **Sustainable**: No repeated model calls means less compute, lower cost, and reduced environmental impact.

This approach leverages the strengths of both worlds: a one-time intelligent schema generation step with a language model, followed by a stable, purely local extraction pipeline that runs efficiently on any machine, without further LLM dependencies.
