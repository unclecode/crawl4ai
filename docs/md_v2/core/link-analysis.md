# Link Analysis and Scoring

## Introduction

**Link Analysis** is a powerful feature that extracts, analyzes, and scores all links found on a webpage. This endpoint helps you understand the link structure, identify high-value links, and get insights into the connectivity patterns of any website.

Think of it as a smart link discovery tool that not only extracts links but also evaluates their importance, relevance, and quality through advanced scoring algorithms.

## Key Concepts

### What Link Analysis Does

When you analyze a webpage, the system:

1. **Extracts All Links** - Finds every hyperlink on the page
2. **Scores Links** - Assigns relevance scores based on multiple factors
3. **Categorizes Links** - Groups links by type (internal, external, etc.)
4. **Provides Metadata** - URL text, attributes, and context information
5. **Ranks by Importance** - Orders links from most to least valuable

### Scoring Factors

The link scoring algorithm considers:

- **Text Content**: Link anchor text relevance and descriptiveness
- **URL Structure**: Depth, parameters, and path patterns
- **Context**: Surrounding text and page position
- **Attributes**: Title, rel attributes, and other metadata
- **Link Type**: Internal vs external classification

## Quick Start

### Basic Usage

```python
import requests

# Analyze links on a webpage
response = requests.post(
    "http://localhost:8000/links/analyze",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "url": "https://example.com"
    }
)

result = response.json()
print(f"Found {len(result.get('internal', []))} internal links")
print(f"Found {len(result.get('external', []))} external links")

# Show top 3 links by score
for link_type in ['internal', 'external']:
    if link_type in result:
        top_links = sorted(result[link_type], key=lambda x: x.get('score', 0), reverse=True)[:3]
        print(f"\nTop {link_type} links:")
        for link in top_links:
            print(f"- {link.get('url', 'N/A')} (score: {link.get('score', 0):.2f})")
```

### With Custom Configuration

```python
response = requests.post(
    "http://localhost:8000/links/analyze",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "url": "https://news.example.com",
        "config": {
            "force": False,           # Skip cache
            "wait_for": 2.0,          # Wait for dynamic content
            "simulate_user": True,     # User-like browsing
            "override_navigator": True # Custom user agent
        }
    }
)
```

## Configuration Options

The `config` parameter accepts a `LinkPreviewConfig` dictionary:

### Basic Options

```python
config = {
    "force": False,                    # Force fresh crawl (default: False)
    "wait_for": None,                  # CSS selector or timeout in seconds
    "simulate_user": True,             # Simulate human behavior
    "override_navigator": True,        # Override browser navigator
    "headers": {                       # Custom headers
        "Accept-Language": "en-US,en;q=0.9"
    }
}
```

### Advanced Options

```python
config = {
    # Timing and behavior
    "delay_before_return_html": 0.5,   # Delay before HTML extraction
    "js_code": ["window.scrollTo(0, document.body.scrollHeight)"],  # JS to execute

    # Content processing
    "word_count_threshold": 1,         # Minimum word count
    "exclusion_patterns": [            # Link patterns to exclude
        r".*/logout.*",
        r".*/admin.*"
    ],

    # Caching and session
    "session_id": "my-session-123",    # Session identifier
    "magic": False                     # Magic link processing
}
```

## Response Structure

The endpoint returns a JSON object with categorized links:

```json
{
  "internal": [
    {
      "url": "https://example.com/about",
      "text": "About Us",
      "title": "Learn about our company",
      "score": 0.85,
      "context": "footer navigation",
      "attributes": {
        "rel": ["nofollow"],
        "target": "_blank"
      }
    }
  ],
  "external": [
    {
      "url": "https://partner-site.com",
      "text": "Partner Site",
      "title": "Visit our partner",
      "score": 0.72,
      "context": "main content",
      "attributes": {}
    }
  ],
  "social": [...],
  "download": [...],
  "email": [...],
  "phone": [...]
}
```

### Link Categories

| Category | Description | Example |
|----------|-------------|---------|
| **internal** | Links within the same domain | `/about`, `https://example.com/contact` |
| **external** | Links to different domains | `https://google.com` |
| **social** | Social media platform links | `https://twitter.com/user` |
| **download** | File download links | `/files/document.pdf` |
| **email** | Email addresses | `mailto:contact@example.com` |
| **phone** | Phone numbers | `tel:+1234567890` |

### Link Metadata

Each link object contains:

```python
{
    "url": str,           # The actual href value
    "text": str,          # Anchor text content
    "title": str,         # Title attribute (if any)
    "score": float,       # Relevance score (0.0-1.0)
    "context": str,       # Where the link was found
    "attributes": dict,   # All HTML attributes
    "hash": str,          # URL fragment (if any)
    "domain": str,        # Extracted domain name
    "scheme": str,        # URL scheme (http/https/etc)
}
```

## Practical Examples

### SEO Audit Tool

```python
def seo_audit(url: str):
    """Perform SEO link analysis on a webpage"""
    response = requests.post(
        "http://localhost:8000/links/analyze",
        headers={"Authorization": "Bearer YOUR_TOKEN"},
        json={"url": url}
    )

    result = response.json()

    print(f"📊 SEO Audit for {url}")
    print(f"Internal links: {len(result.get('internal', []))}")
    print(f"External links: {len(result.get('external', []))}")

    # Check for SEO issues
    internal_links = result.get('internal', [])
    external_links = result.get('external', [])

    # Find links with low scores
    low_score_links = [link for link in internal_links if link.get('score', 0) < 0.3]
    if low_score_links:
        print(f"⚠️  Found {len(low_score_links)} low-quality internal links")

    # Find external opportunities
    high_value_external = [link for link in external_links if link.get('score', 0) > 0.7]
    if high_value_external:
        print(f"✅ Found {len(high_value_external)} high-value external links")

    return result

# Usage
audit_result = seo_audit("https://example.com")
```

### Competitor Analysis

```python
def competitor_analysis(urls: list):
    """Analyze link patterns across multiple competitor sites"""
    all_results = {}

    for url in urls:
        response = requests.post(
            "http://localhost:8000/links/analyze",
            headers={"Authorization": "Bearer YOUR_TOKEN"},
            json={"url": url}
        )
        all_results[url] = response.json()

    # Compare external link strategies
    print("🔍 Competitor Link Analysis")
    for url, result in all_results.items():
        external_links = result.get('external', [])
        avg_score = sum(link.get('score', 0) for link in external_links) / len(external_links) if external_links else 0
        print(f"{url}: {len(external_links)} external links (avg score: {avg_score:.2f})")

    return all_results

# Usage
competitors = [
    "https://competitor1.com",
    "https://competitor2.com",
    "https://competitor3.com"
]
analysis = competitor_analysis(competitors)
```

### Content Discovery

```python
def discover_related_content(start_url: str, max_depth: int = 2):
    """Discover related content through link analysis"""
    visited = set()
    queue = [(start_url, 0)]

    while queue and len(visited) < 20:
        current_url, depth = queue.pop(0)

        if current_url in visited or depth > max_depth:
            continue

        visited.add(current_url)

        try:
            response = requests.post(
                "http://localhost:8000/links/analyze",
                headers={"Authorization": "Bearer YOUR_TOKEN"},
                json={"url": current_url}
            )

            result = response.json()
            internal_links = result.get('internal', [])

            # Sort by score and add top links to queue
            top_links = sorted(internal_links, key=lambda x: x.get('score', 0), reverse=True)[:3]

            for link in top_links:
                if link['url'] not in visited:
                    queue.append((link['url'], depth + 1))
                    print(f"🔗 Found: {link['text']} ({link['score']:.2f})")

        except Exception as e:
            print(f"❌ Error analyzing {current_url}: {e}")

    return visited

# Usage
related_pages = discover_related_content("https://blog.example.com")
print(f"Discovered {len(related_pages)} related pages")
```

## Best Practices

### 1. Request Optimization

```python
# ✅ Good: Use appropriate timeouts
response = requests.post(
    "http://localhost:8000/links/analyze",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={"url": url},
    timeout=30  # 30 second timeout
)

# ✅ Good: Configure wait times for dynamic sites
config = {
    "wait_for": 2.0,  # Wait for JavaScript to load
    "simulate_user": True
}
```

### 2. Error Handling

```python
def safe_link_analysis(url: str):
    try:
        response = requests.post(
            "http://localhost:8000/links/analyze",
            headers={"Authorization": "Bearer YOUR_TOKEN"},
            json={"url": url},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print("❌ Invalid request format")
        elif response.status_code == 500:
            print("❌ Server error during analysis")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")

    except requests.Timeout:
        print("⏰ Request timed out")
    except requests.ConnectionError:
        print("🔌 Connection error")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return None
```

### 3. Data Processing

```python
def process_links_data(result: dict):
    """Process and filter link analysis results"""

    # Filter by minimum score
    min_score = 0.5
    high_quality_links = {}

    for category, links in result.items():
        filtered_links = [
            link for link in links
            if link.get('score', 0) >= min_score
        ]
        if filtered_links:
            high_quality_links[category] = filtered_links

    # Extract unique domains
    domains = set()
    for links in result.get('external', []):
        domains.add(links.get('domain', ''))

    return {
        'filtered_links': high_quality_links,
        'unique_domains': list(domains),
        'total_links': sum(len(links) for links in result.values())
    }
```

## Performance Considerations

### Response Times

- **Simple pages**: 2-5 seconds
- **Complex pages**: 5-15 seconds
- **JavaScript-heavy**: 10-30 seconds

### Rate Limiting

The endpoint includes built-in rate limiting. For bulk analysis:

```python
import time

def bulk_link_analysis(urls: list, delay: float = 1.0):
    """Analyze multiple URLs with rate limiting"""
    results = {}

    for url in urls:
        result = safe_link_analysis(url)
        if result:
            results[url] = result

        # Respect rate limits
        time.sleep(delay)

    return results
```

## Error Handling

### Common Errors and Solutions

| Error Code | Cause | Solution |
|------------|-------|----------|
| **400** | Invalid URL or config | Check URL format and config structure |
| **401** | Invalid authentication | Verify your API token |
| **429** | Rate limit exceeded | Add delays between requests |
| **500** | Crawl failure | Check if site is accessible |
| **503** | Service unavailable | Try again later |

### Debug Mode

```python
# Enable verbose logging for debugging
config = {
    "headers": {
        "User-Agent": "Crawl4AI-Debug/1.0"
    }
}

# Include error details in response
try:
    response = requests.post(
        "http://localhost:8000/links/analyze",
        headers={"Authorization": "Bearer YOUR_TOKEN"},
        json={"url": url, "config": config}
    )
    response.raise_for_status()
except requests.HTTPError as e:
    print(f"Error details: {e.response.text}")
```

## API Reference

### Endpoint Details

- **URL**: `/links/analyze`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication**: Bearer token required

### Request Schema

```python
{
    "url": str,                    # Required: URL to analyze
    "config": {                    # Optional: LinkPreviewConfig
        "force": bool,
        "wait_for": float,
        "simulate_user": bool,
        "override_navigator": bool,
        "headers": dict,
        "js_code": list,
        "delay_before_return_html": float,
        "word_count_threshold": int,
        "exclusion_patterns": list,
        "session_id": str,
        "magic": bool
    }
}
```

### Response Schema

```python
{
    "internal": [LinkObject],
    "external": [LinkObject],
    "social": [LinkObject],
    "download": [LinkObject],
    "email": [LinkObject],
    "phone": [LinkObject]
}
```

### LinkObject Schema

```python
{
    "url": str,
    "text": str,
    "title": str,
    "score": float,
    "context": str,
    "attributes": dict,
    "hash": str,
    "domain": str,
    "scheme": str
}
```

## Next Steps

- Learn about [Advanced Link Processing](../advanced/link-processing.md)
- Explore the [Link Preview Configuration](../api/link-preview-config.md)
- See more [Examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples/link-analysis)

## FAQ

**Q: How is the link score calculated?**
A: The score considers multiple factors including anchor text relevance, URL structure, page context, and link attributes. Scores range from 0.0 (lowest quality) to 1.0 (highest quality).

**Q: Can I analyze password-protected pages?**
A: Yes! Use the `js_code` parameter to handle authentication, or include session cookies in the `headers` configuration.

**Q: How many links can I analyze at once?**
A: There's no hard limit on the number of links per page, but very large pages (>10,000 links) may take longer to process.

**Q: Can I filter out certain types of links?**
A: Use the `exclusion_patterns` parameter in the config to filter out unwanted links using regex patterns.

**Q: Does this work with JavaScript-heavy sites?**
A: Absolutely! The crawler waits for JavaScript execution and can even run custom JavaScript using the `js_code` parameter.