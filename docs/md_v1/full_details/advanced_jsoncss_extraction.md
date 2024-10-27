# Advanced Usage of JsonCssExtractionStrategy

While the basic usage of JsonCssExtractionStrategy is powerful for simple structures, its true potential shines when dealing with complex, nested HTML structures. This section will explore advanced usage scenarios, demonstrating how to extract nested objects, lists, and nested lists.

## Hypothetical Website Example

Let's consider a hypothetical e-commerce website that displays product categories, each containing multiple products. Each product has details, reviews, and related items. This complex structure will allow us to demonstrate various advanced features of JsonCssExtractionStrategy.

Assume the HTML structure looks something like this:

```html
<div class="category">
  <h2 class="category-name">Electronics</h2>
  <div class="product">
    <h3 class="product-name">Smartphone X</h3>
    <p class="product-price">$999</p>
    <div class="product-details">
      <span class="brand">TechCorp</span>
      <span class="model">X-2000</span>
    </div>
    <ul class="product-features">
      <li>5G capable</li>
      <li>6.5" OLED screen</li>
      <li>128GB storage</li>
    </ul>
    <div class="product-reviews">
      <div class="review">
        <span class="reviewer">John D.</span>
        <span class="rating">4.5</span>
        <p class="review-text">Great phone, love the camera!</p>
      </div>
      <div class="review">
        <span class="reviewer">Jane S.</span>
        <span class="rating">5</span>
        <p class="review-text">Best smartphone I've ever owned.</p>
      </div>
    </div>
    <ul class="related-products">
      <li>
        <span class="related-name">Phone Case</span>
        <span class="related-price">$29.99</span>
      </li>
      <li>
        <span class="related-name">Screen Protector</span>
        <span class="related-price">$9.99</span>
      </li>
    </ul>
  </div>
  <!-- More products... -->
</div>
```

Now, let's create a schema to extract this complex structure:

```python
schema = {
    "name": "E-commerce Product Catalog",
    "baseSelector": "div.category",
    "fields": [
        {
            "name": "category_name",
            "selector": "h2.category-name",
            "type": "text"
        },
        {
            "name": "products",
            "selector": "div.product",
            "type": "nested_list",
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
                    "type": "nested",
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
                        {
                            "name": "feature",
                            "type": "text"
                        }
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

This schema demonstrates several advanced features:

1. **Nested Objects**: The `details` field is a nested object within each product.
2. **Simple Lists**: The `features` field is a simple list of text items.
3. **Nested Lists**: The `products` field is a nested list, where each item is a complex object.
4. **Lists of Objects**: The `reviews` and `related_products` fields are lists of objects.

Let's break down the key concepts:

### Nested Objects

To create a nested object, use `"type": "nested"` and provide a `fields` array for the nested structure:

```python
{
    "name": "details",
    "selector": "div.product-details",
    "type": "nested",
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
}
```

### Simple Lists

For a simple list of identical items, use `"type": "list"`:

```python
{
    "name": "features",
    "selector": "ul.product-features li",
    "type": "list",
    "fields": [
        {
            "name": "feature",
            "type": "text"
        }
    ]
}
```

### Nested Lists

For a list of complex objects, use `"type": "nested_list"`:

```python
{
    "name": "products",
    "selector": "div.product",
    "type": "nested_list",
    "fields": [
        // ... fields for each product
    ]
}
```

### Lists of Objects

Similar to nested lists, but typically used for simpler objects within the list:

```python
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
```

## Using the Advanced Schema

To use this advanced schema with AsyncWebCrawler:

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_complex_product_data():
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://gist.githubusercontent.com/githubusercontent/2d7b8ba3cd8ab6cf3c8da771ddb36878/raw/1ae2f90c6861ce7dd84cc50d3df9920dee5e1fd2/sample_ecommerce.html",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        assert result.success, "Failed to crawl the page"

        product_data = json.loads(result.extracted_content)
        print(json.dumps(product_data, indent=2))

asyncio.run(extract_complex_product_data())
```

This will produce a structured JSON output that captures the complex hierarchy of the product catalog, including nested objects, lists, and nested lists.

## Tips for Advanced Usage

1. **Start Simple**: Begin with a basic schema and gradually add complexity.
2. **Test Incrementally**: Test each part of your schema separately before combining them.
3. **Use Chrome DevTools**: The Element Inspector is invaluable for identifying the correct selectors.
4. **Handle Missing Data**: Use the `default` key in your field definitions to handle cases where data might be missing.
5. **Leverage Transforms**: Use the `transform` key to clean or format extracted data (e.g., converting prices to numbers).
6. **Consider Performance**: Very complex schemas might slow down extraction. Balance complexity with performance needs.

By mastering these advanced techniques, you can use JsonCssExtractionStrategy to extract highly structured data from even the most complex web pages, making it a powerful tool for web scraping and data analysis tasks.