# Extracting JSON (No LLM)

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

## 1. Intro to Schema-Based Extraction

A schema defines:

1. A **base selector** that identifies each "container" element on the page (e.g., a product row, a blog post card).  
2. **Fields** describing which CSS/XPath selectors to use for each piece of data you want to capture (text, attribute, HTML block, etc.).  
3. **Nested** or **list** types for repeated or hierarchical structures.  

For example, if you have a list of products, each one might have a name, price, reviews, and "related products." This approach is faster and more reliable than an LLM for consistent, structured pages.

---

## 2. Simple Example: Crypto Prices

Let's begin with a **simple** schema-based extraction using the `JsonCssExtractionStrategy`. Below is a snippet that extracts cryptocurrency prices from a site (similar to the legacy Coinbase example). Notice we **don't** call any LLM:

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def extract_crypto_prices():
    # 1. Define a simple extraction schema
    schema = {
        "name": "Crypto Prices",
        "baseSelector": "div.crypto-row",    # Repeated elements
        "fields": [
            {
                "name": "coin_name",
                "selector": "h2.coin-name",
                "type": "text"
            },
            {
                "name": "price",
                "selector": "span.coin-price",
                "type": "text"
            }
        ]
    }

    # 2. Create the extraction strategy
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    # 3. Set up your crawler config (if needed)
    config = CrawlerRunConfig(
        # e.g., pass js_code or wait_for if the page is dynamic
        # wait_for="css:.crypto-row:nth-child(20)"
        cache_mode = CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        # 4. Run the crawl and extraction
        result = await crawler.arun(
            url="https://example.com/crypto-prices",
            
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        # 5. Parse the extracted JSON
        data = json.loads(result.extracted_content)
        print(f"Extracted {len(data)} coin entries")
        print(json.dumps(data[0], indent=2) if data else "No data found")

asyncio.run(extract_crypto_prices())
```

**Highlights**:

- **`baseSelector`**: Tells us where each "item" (crypto row) is.  
- **`fields`**: Two fields (`coin_name`, `price`) using simple CSS selectors.  
- Each field defines a **`type`** (e.g., `text`, `attribute`, `html`, `regex`, etc.).

No LLM is needed, and the performance is **near-instant** for hundreds or thousands of items.

---

### **XPath Example with `raw://` HTML**

Below is a short example demonstrating **XPath** extraction plus the **`raw://`** scheme. We'll pass a **dummy HTML** directly (no network request) and define the extraction strategy in `CrawlerRunConfig`.

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import JsonXPathExtractionStrategy

async def extract_crypto_prices_xpath():
    # 1. Minimal dummy HTML with some repeating rows
    dummy_html = """
    <html>
      <body>
        <div class='crypto-row'>
          <h2 class='coin-name'>Bitcoin</h2>
          <span class='coin-price'>$28,000</span>
        </div>
        <div class='crypto-row'>
          <h2 class='coin-name'>Ethereum</h2>
          <span class='coin-price'>$1,800</span>
        </div>
      </body>
    </html>
    """

    # 2. Define the JSON schema (XPath version)
    schema = {
        "name": "Crypto Prices via XPath",
        "baseSelector": "//div[@class='crypto-row']",
        "fields": [
            {
                "name": "coin_name",
                "selector": ".//h2[@class='coin-name']",
                "type": "text"
            },
            {
                "name": "price",
                "selector": ".//span[@class='coin-price']",
                "type": "text"
            }
        ]
    }

    # 3. Place the strategy in the CrawlerRunConfig
    config = CrawlerRunConfig(
        extraction_strategy=JsonXPathExtractionStrategy(schema, verbose=True)
    )

    # 4. Use raw:// scheme to pass dummy_html directly
    raw_url = f"raw://{dummy_html}"

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=raw_url,
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        data = json.loads(result.extracted_content)
        print(f"Extracted {len(data)} coin rows")
        if data:
            print("First item:", data[0])

asyncio.run(extract_crypto_prices_xpath())
```

**Key Points**:

1. **`JsonXPathExtractionStrategy`** is used instead of `JsonCssExtractionStrategy`.  
2. **`baseSelector`** and each field's `"selector"` use **XPath** instead of CSS.  
3. **`raw://`** lets us pass `dummy_html` with no real network request—handy for local testing.  
4. Everything (including the extraction strategy) is in **`CrawlerRunConfig`**.  

That's how you keep the config self-contained, illustrate **XPath** usage, and demonstrate the **raw** scheme for direct HTML input—all while avoiding the old approach of passing `extraction_strategy` directly to `arun()`.

---

## 3. Advanced Schema & Nested Structures

Real sites often have **nested** or repeated data—like categories containing products, which themselves have a list of reviews or features. For that, we can define **nested** or **list** (and even **nested_list**) fields.

### Sample E-Commerce HTML

We have a **sample e-commerce** HTML file on GitHub (example):
```
https://gist.githubusercontent.com/githubusercontent/2d7b8ba3cd8ab6cf3c8da771ddb36878/raw/1ae2f90c6861ce7dd84cc50d3df9920dee5e1fd2/sample_ecommerce.html
```
This snippet includes categories, products, features, reviews, and related items. Let's see how to define a schema that fully captures that structure **without LLM**.

```python
schema = {
    "name": "E-commerce Product Catalog",
    "baseSelector": "div.category",
    # (1) We can define optional baseFields if we want to extract attributes 
    # from the category container
    "baseFields": [
        {"name": "data_cat_id", "type": "attribute", "attribute": "data-cat-id"}, 
    ],
    "fields": [
        {
            "name": "category_name",
            "selector": "h2.category-name",
            "type": "text"
        },
        {
            "name": "products",
            "selector": "div.product",
            "type": "nested_list",    # repeated sub-objects
            "fields": [
                {
                    "name": "name",
                    "selector": "h3.product-name",
                    "type": "text"
                },
                {
                    "name": "price",
                    "selector": "p.product-price",
                    "type": "text"
                },
                {
                    "name": "details",
                    "selector": "div.product-details",
                    "type": "nested",  # single sub-object
                    "fields": [
                        {
                            "name": "brand",
                            "selector": "span.brand",
                            "type": "text"
                        },
                        {
                            "name": "model",
                            "selector": "span.model",
                            "type": "text"
                        }
                    ]
                },
                {
                    "name": "features",
                    "selector": "ul.product-features li",
                    "type": "list",
                    "fields": [
                        {"name": "feature", "type": "text"} 
                    ]
                },
                {
                    "name": "reviews",
                    "selector": "div.review",
                    "type": "nested_list",
                    "fields": [
                        {
                            "name": "reviewer", 
                            "selector": "span.reviewer", 
                            "type": "text"
                        },
                        {
                            "name": "rating", 
                            "selector": "span.rating", 
                            "type": "text"
                        },
                        {
                            "name": "comment", 
                            "selector": "p.review-text", 
                            "type": "text"
                        }
                    ]
                },
                {
                    "name": "related_products",
                    "selector": "ul.related-products li",
                    "type": "list",
                    "fields": [
                        {
                            "name": "name", 
                            "selector": "span.related-name", 
                            "type": "text"
                        },
                        {
                            "name": "price", 
                            "selector": "span.related-price", 
                            "type": "text"
                        }
                    ]
                }
            ]
        }
    ]
}
```

Key Takeaways:

- **Nested vs. List**:  
  - **`type: "nested"`** means a **single** sub-object (like `details`).  
  - **`type: "list"`** means multiple items that are **simple** dictionaries or single text fields.  
  - **`type: "nested_list"`** means repeated **complex** objects (like `products` or `reviews`).
- **Base Fields**: We can extract **attributes** from the container element via `"baseFields"`. For instance, `"data_cat_id"` might be `data-cat-id="elect123"`.  
- **Transforms**: We can also define a `transform` if we want to lower/upper case, strip whitespace, or even run a custom function.

### Running the Extraction

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import JsonCssExtractionStrategy

ecommerce_schema = {
    # ... the advanced schema from above ...
}

async def extract_ecommerce_data():
    strategy = JsonCssExtractionStrategy(ecommerce_schema, verbose=True)
    
    config = CrawlerRunConfig()
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://gist.githubusercontent.com/githubusercontent/2d7b8ba3cd8ab6cf3c8da771ddb36878/raw/1ae2f90c6861ce7dd84cc50d3df9920dee5e1fd2/sample_ecommerce.html",
            extraction_strategy=strategy,
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return
        
        # Parse the JSON output
        data = json.loads(result.extracted_content)
        print(json.dumps(data, indent=2) if data else "No data found.")

asyncio.run(extract_ecommerce_data())
```

If all goes well, you get a **structured** JSON array with each "category," containing an array of `products`. Each product includes `details`, `features`, `reviews`, etc. All of that **without** an LLM.

---

## 4. RegexExtractionStrategy - Fast Pattern-Based Extraction

Crawl4AI now offers a powerful new zero-LLM extraction strategy: `RegexExtractionStrategy`. This strategy provides lightning-fast extraction of common data types like emails, phone numbers, URLs, dates, and more using pre-compiled regular expressions.

### Key Features

- **Zero LLM Dependency**: Extracts data without any AI model calls
- **Blazing Fast**: Uses pre-compiled regex patterns for maximum performance
- **Built-in Patterns**: Includes ready-to-use patterns for common data types
- **Custom Patterns**: Add your own regex patterns for domain-specific extraction
- **LLM-Assisted Pattern Generation**: Optionally use an LLM once to generate optimized patterns, then reuse them without further LLM calls

### Simple Example: Extracting Common Entities

The easiest way to start is by using the built-in pattern catalog:

```python
import json
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    RegexExtractionStrategy
)

async def extract_with_regex():
    # Create a strategy using built-in patterns for URLs and currencies
    strategy = RegexExtractionStrategy(
        pattern = RegexExtractionStrategy.Url | RegexExtractionStrategy.Currency
    )
    
    config = CrawlerRunConfig(extraction_strategy=strategy)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=config
        )
        
        if result.success:
            data = json.loads(result.extracted_content)
            for item in data[:5]:  # Show first 5 matches
                print(f"{item['label']}: {item['value']}")
            print(f"Total matches: {len(data)}")

asyncio.run(extract_with_regex())
```

### Available Built-in Patterns

`RegexExtractionStrategy` provides these common patterns as IntFlag attributes for easy combining:

```python
# Use individual patterns
strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Email)

# Combine multiple patterns
strategy = RegexExtractionStrategy(
    pattern = (
        RegexExtractionStrategy.Email | 
        RegexExtractionStrategy.PhoneUS | 
        RegexExtractionStrategy.Url
    )
)

# Use all available patterns
strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.All)
```

Available patterns include:
- `Email` - Email addresses
- `PhoneIntl` - International phone numbers
- `PhoneUS` - US-format phone numbers
- `Url` - HTTP/HTTPS URLs
- `IPv4` - IPv4 addresses
- `IPv6` - IPv6 addresses
- `Uuid` - UUIDs
- `Currency` - Currency values (USD, EUR, etc.)
- `Percentage` - Percentage values
- `Number` - Numeric values
- `DateIso` - ISO format dates
- `DateUS` - US format dates
- `Time24h` - 24-hour format times
- `PostalUS` - US postal codes
- `PostalUK` - UK postal codes
- `HexColor` - HTML hex color codes
- `TwitterHandle` - Twitter handles
- `Hashtag` - Hashtags
- `MacAddr` - MAC addresses
- `Iban` - International bank account numbers
- `CreditCard` - Credit card numbers

### Custom Pattern Example

For more targeted extraction, you can provide custom patterns:

```python
import json
import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    RegexExtractionStrategy
)

async def extract_prices():
    # Define a custom pattern for US Dollar prices
    price_pattern = {"usd_price": r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"}
    
    # Create strategy with custom pattern
    strategy = RegexExtractionStrategy(custom=price_pattern)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.example.com/products",
            config=config
        )
        
        if result.success:
            data = json.loads(result.extracted_content)
            for item in data:
                print(f"Found price: {item['value']}")

asyncio.run(extract_prices())
```

### LLM-Assisted Pattern Generation

For complex or site-specific patterns, you can use an LLM once to generate an optimized pattern, then save and reuse it without further LLM calls:

```python
import json
import asyncio
from pathlib import Path
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    RegexExtractionStrategy,
    LLMConfig
)

async def extract_with_generated_pattern():
    cache_dir = Path("./pattern_cache")
    cache_dir.mkdir(exist_ok=True)
    pattern_file = cache_dir / "price_pattern.json"
    
    # 1. Generate or load pattern
    if pattern_file.exists():
        pattern = json.load(pattern_file.open())
        print(f"Using cached pattern: {pattern}")
    else:
        print("Generating pattern via LLM...")
        
        # Configure LLM
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token="env:OPENAI_API_KEY",
        )
        
        # Get sample HTML for context
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://example.com/products")
            html = result.fit_html
        
        # Generate pattern (one-time LLM usage)
        pattern = RegexExtractionStrategy.generate_pattern(
            label="price",
            html=html,
            query="Product prices in USD format",
            llm_config=llm_config,
        )
        
        # Cache pattern for future use
        json.dump(pattern, pattern_file.open("w"), indent=2)
    
    # 2. Use pattern for extraction (no LLM calls)
    strategy = RegexExtractionStrategy(custom=pattern)
    config = CrawlerRunConfig(extraction_strategy=strategy)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/products",
            config=config
        )
        
        if result.success:
            data = json.loads(result.extracted_content)
            for item in data[:10]:
                print(f"Extracted: {item['value']}")
            print(f"Total matches: {len(data)}")

asyncio.run(extract_with_generated_pattern())
```

This pattern allows you to:
1. Use an LLM once to generate a highly optimized regex for your specific site
2. Save the pattern to disk for reuse 
3. Extract data using only regex (no further LLM calls) in production

### Extraction Results Format

The `RegexExtractionStrategy` returns results in a consistent format:

```json
[
  {
    "url": "https://example.com",
    "label": "email",
    "value": "contact@example.com",
    "span": [145, 163]
  },
  {
    "url": "https://example.com",
    "label": "url",
    "value": "https://support.example.com",
    "span": [210, 235]
  }
]
```

Each match includes:
- `url`: The source URL
- `label`: The pattern name that matched (e.g., "email", "phone_us")
- `value`: The extracted text
- `span`: The start and end positions in the source content

---

## 5. Why "No LLM" Is Often Better

1. **Zero Hallucination**: Pattern-based extraction doesn't guess text. It either finds it or not.  
2. **Guaranteed Structure**: The same schema or regex yields consistent JSON across many pages, so your downstream pipeline can rely on stable keys.  
3. **Speed**: LLM-based extraction can be 10–1000x slower for large-scale crawling.  
4. **Scalable**: Adding or updating a field is a matter of adjusting the schema or regex, not re-tuning a model.

**When might you consider an LLM?** Possibly if the site is extremely unstructured or you want AI summarization. But always try a schema or regex approach first for repeated or consistent data patterns.

---

## 6. Base Element Attributes & Additional Fields

It's easy to **extract attributes** (like `href`, `src`, or `data-xxx`) from your base or nested elements using:

```json
{
  "name": "href",
  "type": "attribute",
  "attribute": "href",
  "default": null
}
```

You can define them in **`baseFields`** (extracted from the main container element) or in each field's sub-lists. This is especially helpful if you need an item's link or ID stored in the parent `<div>`.

---

## 7. Putting It All Together: Larger Example

Consider a blog site. We have a schema that extracts the **URL** from each post card (via `baseFields` with an `"attribute": "href"`), plus the title, date, summary, and author:

```python
schema = {
  "name": "Blog Posts",
  "baseSelector": "a.blog-post-card",
  "baseFields": [
    {"name": "post_url", "type": "attribute", "attribute": "href"}
  ],
  "fields": [
    {"name": "title", "selector": "h2.post-title", "type": "text", "default": "No Title"},
    {"name": "date", "selector": "time.post-date", "type": "text", "default": ""},
    {"name": "summary", "selector": "p.post-summary", "type": "text", "default": ""},
    {"name": "author", "selector": "span.post-author", "type": "text", "default": ""}
  ]
}
```

Then run with `JsonCssExtractionStrategy(schema)` to get an array of blog post objects, each with `"post_url"`, `"title"`, `"date"`, `"summary"`, `"author"`.

---

## 8. Tips & Best Practices

1. **Inspect the DOM** in Chrome DevTools or Firefox's Inspector to find stable selectors.  
2. **Start Simple**: Verify you can extract a single field. Then add complexity like nested objects or lists.  
3. **Test** your schema on partial HTML or a test page before a big crawl.  
4. **Combine with JS Execution** if the site loads content dynamically. You can pass `js_code` or `wait_for` in `CrawlerRunConfig`.  
5. **Look at Logs** when `verbose=True`: if your selectors are off or your schema is malformed, it'll often show warnings.  
6. **Use baseFields** if you need attributes from the container element (e.g., `href`, `data-id`), especially for the "parent" item.  
7. **Performance**: For large pages, make sure your selectors are as narrow as possible.
8. **Consider Using Regex First**: For simple data types like emails, URLs, and dates, `RegexExtractionStrategy` is often the fastest approach.

---

## 9. Schema Generation Utility

While manually crafting schemas is powerful and precise, Crawl4AI now offers a convenient utility to **automatically generate** extraction schemas using LLM. This is particularly useful when:

1. You're dealing with a new website structure and want a quick starting point
2. You need to extract complex nested data structures
3. You want to avoid the learning curve of CSS/XPath selector syntax

### Using the Schema Generator

The schema generator is available as a static method on both `JsonCssExtractionStrategy` and `JsonXPathExtractionStrategy`. You can choose between OpenAI's GPT-4 or the open-source Ollama for schema generation:

```python
from crawl4ai import JsonCssExtractionStrategy, JsonXPathExtractionStrategy
from crawl4ai import LLMConfig

# Sample HTML with product information
html = """
<div class="product-card">
    <h2 class="title">Gaming Laptop</h2>
    <div class="price">$999.99</div>
    <div class="specs">
        <ul>
            <li>16GB RAM</li>
            <li>1TB SSD</li>
        </ul>
    </div>
</div>
"""

# Option 1: Using OpenAI (requires API token)
css_schema = JsonCssExtractionStrategy.generate_schema(
    html,
    schema_type="css", 
    llm_config = LLMConfig(provider="openai/gpt-4o",api_token="your-openai-token")
)

# Option 2: Using Ollama (open source, no token needed)
xpath_schema = JsonXPathExtractionStrategy.generate_schema(
    html,
    schema_type="xpath",
    llm_config = LLMConfig(provider="ollama/llama3.3", api_token=None)  # Not needed for Ollama
)

# Use the generated schema for fast, repeated extractions
strategy = JsonCssExtractionStrategy(css_schema)
```

### LLM Provider Options

1. **OpenAI GPT-4 (`openai/gpt4o`)**
   - Default provider
   - Requires an API token
   - Generally provides more accurate schemas
   - Set via environment variable: `OPENAI_API_KEY`

2. **Ollama (`ollama/llama3.3`)**
   - Open source alternative
   - No API token required
   - Self-hosted option
   - Good for development and testing

### Benefits of Schema Generation

1. **One-Time Cost**: While schema generation uses LLM, it's a one-time cost. The generated schema can be reused for unlimited extractions without further LLM calls.
2. **Smart Pattern Recognition**: The LLM analyzes the HTML structure and identifies common patterns, often producing more robust selectors than manual attempts.
3. **Automatic Nesting**: Complex nested structures are automatically detected and properly represented in the schema.
4. **Learning Tool**: The generated schemas serve as excellent examples for learning how to write your own schemas.

### Best Practices

1. **Review Generated Schemas**: While the generator is smart, always review and test the generated schema before using it in production.
2. **Provide Representative HTML**: The better your sample HTML represents the overall structure, the more accurate the generated schema will be.
3. **Consider Both CSS and XPath**: Try both schema types and choose the one that works best for your specific case.
4. **Cache Generated Schemas**: Since generation uses LLM, save successful schemas for reuse.
5. **API Token Security**: Never hardcode API tokens. Use environment variables or secure configuration management.
6. **Choose Provider Wisely**: 
   - Use OpenAI for production-quality schemas
   - Use Ollama for development, testing, or when you need a self-hosted solution

---

## 10. Conclusion

With Crawl4AI's LLM-free extraction strategies - `JsonCssExtractionStrategy`, `JsonXPathExtractionStrategy`, and now `RegexExtractionStrategy` - you can build powerful pipelines that:

- Scrape any consistent site for structured data.  
- Support nested objects, repeating lists, or pattern-based extraction.  
- Scale to thousands of pages quickly and reliably.

**Choosing the Right Strategy**:

- Use **`RegexExtractionStrategy`** for fast extraction of common data types like emails, phones, URLs, dates, etc.
- Use **`JsonCssExtractionStrategy`** or **`JsonXPathExtractionStrategy`** for structured data with clear HTML patterns
- If you need both: first extract structured data with JSON strategies, then use regex on specific fields

**Remember**: For repeated, structured data, you don't need to pay for or wait on an LLM. Well-crafted schemas and regex patterns get you the data faster, cleaner, and cheaper—**the real power** of Crawl4AI.

**Last Updated**: 2025-05-02

---

That's it for **Extracting JSON (No LLM)**! You've seen how schema-based approaches (either CSS or XPath) and regex patterns can handle everything from simple lists to deeply nested product catalogs—instantly, with minimal overhead. Enjoy building robust scrapers that produce consistent, structured JSON for your data pipelines!