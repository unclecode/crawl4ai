# Table Extraction API Documentation

## Overview

The Crawl4AI Docker Server provides powerful table extraction capabilities through both **integrated** and **dedicated** endpoints. Extract structured data from HTML tables using multiple strategies: default (fast regex-based), LLM-powered (semantic understanding), or financial (specialized for financial data).

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Extraction Strategies](#extraction-strategies)
3. [Integrated Extraction (with /crawl)](#integrated-extraction)
4. [Dedicated Endpoints (/tables)](#dedicated-endpoints)
5. [Batch Processing](#batch-processing)
6. [Configuration Options](#configuration-options)
7. [Response Format](#response-format)
8. [Error Handling](#error-handling)

---

## Quick Start

### Extract Tables During Crawl

```bash
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/financial-data"],
    "table_extraction": {
      "strategy": "default"
    }
  }'
```

### Extract Tables from HTML

```bash
curl -X POST http://localhost:11235/tables/extract \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<table><tr><th>Name</th><th>Value</th></tr><tr><td>A</td><td>100</td></tr></table>",
    "config": {
      "strategy": "default"
    }
  }'
```

---

## Extraction Strategies

### 1. **Default Strategy** (Fast, Regex-Based)

Best for general-purpose table extraction with high performance.

```json
{
  "strategy": "default"
}
```

**Use Cases:**
- General web scraping
- Simple data tables
- High-volume extraction

### 2. **LLM Strategy** (AI-Powered)

Uses Large Language Models for semantic understanding and complex table structures.

```json
{
  "strategy": "llm",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "llm_api_key": "your-api-key",
  "llm_prompt": "Extract and structure the financial data"
}
```

**Use Cases:**
- Complex nested tables
- Tables with irregular structure
- Semantic data extraction

**Supported Providers:**
- `openai` (GPT-3.5, GPT-4)
- `anthropic` (Claude)
- `huggingface` (Open models)

### 3. **Financial Strategy** (Specialized)

Optimized for financial tables with proper numerical formatting.

```json
{
  "strategy": "financial",
  "preserve_formatting": true,
  "extract_metadata": true
}
```

**Use Cases:**
- Stock data
- Financial statements
- Accounting tables
- Price lists

### 4. **None Strategy** (No Extraction)

Disables table extraction.

```json
{
  "strategy": "none"
}
```

---

## Integrated Extraction

Add table extraction to any crawl request by including the `table_extraction` configuration.

### Example: Basic Integration

```python
import requests

response = requests.post("http://localhost:11235/crawl", json={
    "urls": ["https://finance.yahoo.com/quote/AAPL"],
    "browser_config": {
        "headless": True
    },
    "crawler_config": {
        "wait_until": "networkidle"
    },
    "table_extraction": {
        "strategy": "financial",
        "preserve_formatting": True
    }
})

data = response.json()
for result in data["results"]:
    if result["success"]:
        print(f"Found {len(result.get('tables', []))} tables")
        for table in result.get("tables", []):
            print(f"Table: {table['headers']}")
```

### Example: Multiple URLs with Table Extraction

```javascript
// Node.js example
const axios = require('axios');

const response = await axios.post('http://localhost:11235/crawl', {
  urls: [
    'https://example.com/page1',
    'https://example.com/page2',
    'https://example.com/page3'
  ],
  table_extraction: {
    strategy: 'default'
  }
});

response.data.results.forEach((result, index) => {
  console.log(`Page ${index + 1}:`);
  console.log(`  Tables found: ${result.tables?.length || 0}`);
});
```

### Example: LLM-Based Extraction with Custom Prompt

```bash
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com/complex-data"],
    "table_extraction": {
      "strategy": "llm",
      "llm_provider": "openai",
      "llm_model": "gpt-4",
      "llm_api_key": "sk-...",
      "llm_prompt": "Extract product pricing information, including discounts and availability"
    }
  }'
```

---

## Dedicated Endpoints

### `/tables/extract` - Single Extraction

Extract tables from HTML content or by fetching a URL.

#### Extract from HTML

```python
import requests

html_content = """
<table>
  <thead>
    <tr><th>Product</th><th>Price</th><th>Stock</th></tr>
  </thead>
  <tbody>
    <tr><td>Widget A</td><td>$19.99</td><td>In Stock</td></tr>
    <tr><td>Widget B</td><td>$29.99</td><td>Out of Stock</td></tr>
  </tbody>
</table>
"""

response = requests.post("http://localhost:11235/tables/extract", json={
    "html": html_content,
    "config": {
        "strategy": "default"
    }
})

data = response.json()
print(f"Success: {data['success']}")
print(f"Tables found: {data['table_count']}")
print(f"Strategy used: {data['strategy']}")

for table in data['tables']:
    print("\nTable:")
    print(f"  Headers: {table['headers']}")
    print(f"  Rows: {len(table['rows'])}")
```

#### Extract from URL

```python
response = requests.post("http://localhost:11235/tables/extract", json={
    "url": "https://example.com/data-page",
    "config": {
        "strategy": "financial",
        "preserve_formatting": True
    }
})

data = response.json()
for table in data['tables']:
    print(f"Table with {len(table['rows'])} rows")
```

---

## Batch Processing

### `/tables/extract/batch` - Batch Extraction

Extract tables from multiple HTML contents or URLs in a single request.

#### Batch from HTML List

```python
import requests

html_contents = [
    "<table><tr><th>A</th></tr><tr><td>1</td></tr></table>",
    "<table><tr><th>B</th></tr><tr><td>2</td></tr></table>",
    "<table><tr><th>C</th></tr><tr><td>3</td></tr></table>",
]

response = requests.post("http://localhost:11235/tables/extract/batch", json={
    "html_list": html_contents,
    "config": {
        "strategy": "default"
    }
})

data = response.json()
print(f"Total processed: {data['summary']['total_processed']}")
print(f"Successful: {data['summary']['successful']}")
print(f"Failed: {data['summary']['failed']}")
print(f"Total tables: {data['summary']['total_tables_extracted']}")

for result in data['results']:
    if result['success']:
        print(f"  {result['source']}: {result['table_count']} tables")
    else:
        print(f"  {result['source']}: Error - {result['error']}")
```

#### Batch from URL List

```python
response = requests.post("http://localhost:11235/tables/extract/batch", json={
    "url_list": [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ],
    "config": {
        "strategy": "financial"
    }
})

data = response.json()
for result in data['results']:
    print(f"URL: {result['source']}")
    if result['success']:
        print(f"  ✓ Found {result['table_count']} tables")
    else:
        print(f"  ✗ Failed: {result['error']}")
```

#### Mixed Batch (HTML + URLs)

```python
response = requests.post("http://localhost:11235/tables/extract/batch", json={
    "html_list": [
        "<table><tr><th>Local</th></tr></table>"
    ],
    "url_list": [
        "https://example.com/remote"
    ],
    "config": {
        "strategy": "default"
    }
})
```

**Batch Limits:**
- Maximum 50 items per batch request
- Items are processed independently (partial failures allowed)

---

## Configuration Options

### TableExtractionConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategy` | `"none"` \| `"default"` \| `"llm"` \| `"financial"` | `"default"` | Extraction strategy to use |
| `llm_provider` | `string` | `null` | LLM provider (required for `llm` strategy) |
| `llm_model` | `string` | `null` | Model name (required for `llm` strategy) |
| `llm_api_key` | `string` | `null` | API key (required for `llm` strategy) |
| `llm_prompt` | `string` | `null` | Custom extraction prompt |
| `preserve_formatting` | `boolean` | `false` | Keep original number/date formatting |
| `extract_metadata` | `boolean` | `false` | Include table metadata (id, class, etc.) |

### Example: Full Configuration

```json
{
  "strategy": "llm",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "llm_api_key": "sk-...",
  "llm_prompt": "Extract structured product data",
  "preserve_formatting": true,
  "extract_metadata": true
}
```

---

## Response Format

### Single Extraction Response

```json
{
  "success": true,
  "table_count": 2,
  "strategy": "default",
  "tables": [
    {
      "headers": ["Product", "Price", "Stock"],
      "rows": [
        ["Widget A", "$19.99", "In Stock"],
        ["Widget B", "$29.99", "Out of Stock"]
      ],
      "metadata": {
        "id": "product-table",
        "class": "data-table",
        "row_count": 2,
        "column_count": 3
      }
    }
  ]
}
```

### Batch Extraction Response

```json
{
  "success": true,
  "summary": {
    "total_processed": 3,
    "successful": 2,
    "failed": 1,
    "total_tables_extracted": 5
  },
  "strategy": "default",
  "results": [
    {
      "success": true,
      "source": "html_0",
      "table_count": 2,
      "tables": [...]
    },
    {
      "success": true,
      "source": "https://example.com",
      "table_count": 3,
      "tables": [...]
    },
    {
      "success": false,
      "source": "html_2",
      "error": "Invalid HTML structure"
    }
  ]
}
```

### Integrated Crawl Response

Tables are included in the standard crawl result:

```json
{
  "success": true,
  "results": [
    {
      "url": "https://example.com",
      "success": true,
      "html": "...",
      "markdown": "...",
      "tables": [
        {
          "headers": [...],
          "rows": [...]
        }
      ]
    }
  ]
}
```

---

## Error Handling

### Common Errors

#### 400 Bad Request

```json
{
  "detail": "Must provide either 'html' or 'url' for table extraction."
}
```

**Cause:** Invalid request parameters

**Solution:** Ensure you provide exactly one of `html` or `url`

#### 400 Bad Request (LLM)

```json
{
  "detail": "Invalid table extraction config: LLM strategy requires llm_provider, llm_model, and llm_api_key"
}
```

**Cause:** Missing required LLM configuration

**Solution:** Provide all required LLM fields

#### 500 Internal Server Error

```json
{
  "detail": "Failed to fetch and extract from URL: Connection timeout"
}
```

**Cause:** URL fetch failure or extraction error

**Solution:** Check URL accessibility and HTML validity

### Handling Partial Failures in Batch

```python
response = requests.post("http://localhost:11235/tables/extract/batch", json={
    "url_list": urls,
    "config": {"strategy": "default"}
})

data = response.json()

successful_results = [r for r in data['results'] if r['success']]
failed_results = [r for r in data['results'] if not r['success']]

print(f"Successful: {len(successful_results)}")
for result in failed_results:
    print(f"Failed: {result['source']} - {result['error']}")
```

---

## Best Practices

### 1. **Choose the Right Strategy**

- **Default**: Fast, reliable for most tables
- **LLM**: Complex structures, semantic extraction
- **Financial**: Numerical data with formatting

### 2. **Batch Processing**

- Use batch endpoints for multiple pages
- Keep batch size under 50 items
- Handle partial failures gracefully

### 3. **Performance Optimization**

- Use `default` strategy for high-volume extraction
- Enable `preserve_formatting` only when needed
- Limit `extract_metadata` to reduce payload size

### 4. **LLM Strategy Tips**

- Use specific prompts for better results
- GPT-4 for complex tables, GPT-3.5 for simple ones
- Cache results to reduce API costs

### 5. **Error Handling**

- Always check `success` field
- Log errors for debugging
- Implement retry logic for transient failures

---

## Examples by Use Case

### Financial Data Extraction

```python
response = requests.post("http://localhost:11235/crawl", json={
    "urls": ["https://finance.site.com/stocks"],
    "table_extraction": {
        "strategy": "financial",
        "preserve_formatting": True,
        "extract_metadata": True
    }
})

for result in response.json()["results"]:
    for table in result.get("tables", []):
        # Financial tables with preserved formatting
        print(table["rows"])
```

### Product Catalog Scraping

```python
response = requests.post("http://localhost:11235/tables/extract/batch", json={
    "url_list": [
        "https://shop.com/category/electronics",
        "https://shop.com/category/clothing",
        "https://shop.com/category/books",
    ],
    "config": {"strategy": "default"}
})

all_products = []
for result in response.json()["results"]:
    if result["success"]:
        for table in result["tables"]:
            all_products.extend(table["rows"])

print(f"Total products: {len(all_products)}")
```

### Complex Table with LLM

```python
response = requests.post("http://localhost:11235/tables/extract", json={
    "url": "https://complex-data.com/report",
    "config": {
        "strategy": "llm",
        "llm_provider": "openai",
        "llm_model": "gpt-4",
        "llm_api_key": "sk-...",
        "llm_prompt": "Extract quarterly revenue breakdown by region and product category"
    }
})

structured_data = response.json()["tables"]
```

---

## API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/crawl` | POST | Crawl with integrated table extraction |
| `/crawl/stream` | POST | Stream crawl with table extraction |
| `/tables/extract` | POST | Extract tables from HTML or URL |
| `/tables/extract/batch` | POST | Batch extract from multiple sources |

For complete API documentation, visit: `/docs` (Swagger UI)

---

## Support

For issues, feature requests, or questions:
- GitHub: https://github.com/unclecode/crawl4ai
- Documentation: https://crawl4ai.com/docs
- Discord: https://discord.gg/crawl4ai
