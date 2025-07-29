# Amazon R2D2 Product Search Example

A real-world demonstration of Crawl4AI's multi-step crawling with LLM-generated automation scripts.

## 🎯 What This Example Shows

This example demonstrates advanced Crawl4AI features:
- **LLM-Generated Scripts**: Automatically create C4A-Script from HTML snippets
- **Multi-Step Crawling**: Navigate through multiple pages using session persistence
- **Structured Data Extraction**: Extract product data using JSON CSS schemas
- **Visual Automation**: Watch the browser perform the search (headless=False)

## 🚀 How It Works

### 1. **Script Generation Phase**
The example uses `C4ACompiler.generate_script()` to analyze Amazon's HTML and create:
- **Search Script**: Automates filling the search box and clicking search
- **Extraction Schema**: Defines how to extract product information

### 2. **Crawling Workflow**
```
Homepage → Execute Search Script → Extract Products → Save Results
```

All steps use the same `session_id` to maintain browser state.

### 3. **Data Extraction**
Products are extracted with:
- Title, price, rating, reviews
- Delivery information
- Sponsored/Small Business badges
- Direct product URLs

## 📁 Files

- `amazon_r2d2_search.py` - Main example script
- `header.html` - Amazon search bar HTML (provided)
- `product.html` - Product card HTML (provided)
- **Generated files:**
  - `generated_search_script.c4a` - Auto-generated search automation
  - `generated_product_schema.json` - Auto-generated extraction rules
  - `extracted_products.json` - Final scraped data
  - `search_results_screenshot.png` - Visual proof of results

## 🏃 Running the Example

1. **Prerequisites**
   ```bash
   # Ensure Crawl4AI is installed
   pip install crawl4ai
   
   # Set up LLM API key (for script generation)
   export OPENAI_API_KEY="your-key-here"
   ```

2. **Run the scraper**
   ```bash
   python amazon_r2d2_search.py
   ```

3. **Watch the magic!**
   - Browser window opens (not headless)
   - Navigates to Amazon.com
   - Searches for "r2d2"
   - Extracts all products
   - Saves results to JSON

## 📊 Sample Output

```json
[
  {
    "title": "Death Star BB8 R2D2 Golf Balls with 20 Printed tees",
    "price": "29.95",
    "rating": "4.7",
    "reviews_count": "184",
    "delivery": "FREE delivery Thu, Jun 19",
    "url": "https://www.amazon.com/Death-Star-R2D2-Balls-Printed/dp/B081XSYZMS",
    "is_sponsored": true,
    "small_business": true
  },
  ...
]
```

## 🔍 Key Features Demonstrated

### Session Persistence
```python
# Same session_id across multiple arun() calls
config = CrawlerRunConfig(
    session_id="amazon_r2d2_session",
    # ... other settings
)
```

### LLM Script Generation
```python
# Generate automation from natural language + HTML
script = C4ACompiler.generate_script(
    html=header_html,
    query="Find search box, type 'r2d2', click search",
    mode="c4a"
)
```

### JSON CSS Extraction
```python
# Structured data extraction with CSS selectors
schema = {
    "baseSelector": "[data-component-type='s-search-result']",
    "fields": [
        {"name": "title", "selector": "h2 a span", "type": "text"},
        {"name": "price", "selector": ".a-price-whole", "type": "text"}
    ]
}
```

## 🛠️ Customization

### Search Different Products
Change the search term in the script generation:
```python
search_goal = """
...
3. Type "star wars lego" into the search box
...
"""
```

### Extract More Data
Add fields to the extraction schema:
```python
"fields": [
    # ... existing fields
    {"name": "prime", "selector": ".s-prime", "type": "exists"},
    {"name": "image_url", "selector": "img.s-image", "type": "attribute", "attribute": "src"}
]
```

### Use Different Sites
Adapt the approach for other e-commerce sites by:
1. Providing their HTML snippets
2. Adjusting the search goals
3. Updating the extraction schema

## 🎓 Learning Points

1. **No Manual Scripting**: LLM generates all automation code
2. **Session Management**: Maintain state across page navigations
3. **Robust Extraction**: Handle dynamic content and multiple products
4. **Error Handling**: Graceful fallbacks if generation fails

## 🐛 Troubleshooting

- **"No products found"**: Check if Amazon's HTML structure changed
- **"Script generation failed"**: Ensure LLM API key is configured
- **"Page timeout"**: Increase wait times in the config
- **"Session lost"**: Ensure same session_id is used consistently

## 📚 Next Steps

- Try searching for different products
- Add pagination to get more results
- Extract product details pages
- Compare prices across different sellers
- Build a price monitoring system

---

This example shows the power of combining LLM intelligence with web automation. The scripts adapt to HTML changes and natural language instructions make automation accessible to everyone!