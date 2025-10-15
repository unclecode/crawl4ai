# Docker Server API Reference

The Crawl4AI Docker server provides a comprehensive REST API for web crawling, content extraction, and processing. This guide covers all available endpoints with practical examples.

## 🚀 Quick Start

### Base URL
```
http://localhost:11235
```

### Authentication
Most endpoints require JWT authentication. Get your token first:

```bash
curl -X POST http://localhost:11235/token \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com"}'
```

### Interactive Documentation
Visit `http://localhost:11235/docs` for interactive Swagger UI documentation.

---

## 📑 Table of Contents

### Core Crawling
- [POST /crawl](#post-crawl) - Main crawling endpoint
- [POST /crawl/stream](#post-crawlstream) - Streaming crawl endpoint
- [POST /crawl/http](#post-crawlhttp) - HTTP-only crawling endpoint
- [POST /crawl/http/stream](#post-crawlhttpstream) - HTTP-only streaming crawl endpoint
- [POST /seed](#post-seed) - URL discovery and seeding

### Content Extraction
- [POST /md](#post-md) - Extract markdown from URL
- [POST /html](#post-html) - Get clean HTML content
- [POST /screenshot](#post-screenshot) - Capture page screenshots
- [POST /pdf](#post-pdf) - Export page as PDF
- [POST /execute_js](#post-execute_js) - Execute JavaScript on page

### Dispatcher Management
- [GET /dispatchers](#get-dispatchers) - List available dispatchers
- [GET /dispatchers/default](#get-dispatchersdefault) - Get default dispatcher
- [GET /dispatchers/stats](#get-dispatchersstats) - Get dispatcher statistics

### Adaptive Crawling
- [POST /adaptive/crawl](#post-adaptivecrawl) - Adaptive crawl with auto-discovery
- [GET /adaptive/status/{task_id}](#get-adaptivestatustask_id) - Check adaptive crawl status

### Utility Endpoints
- [POST /token](#post-token) - Get authentication token
- [GET /health](#get-health) - Health check
- [GET /metrics](#get-metrics) - Prometheus metrics
- [GET /schema](#get-schema) - Get API schemas
- [GET /llm/{url}](#get-llmurl) - LLM-friendly format

---

## Core Crawling Endpoints

### POST /crawl

Main endpoint for crawling single or multiple URLs.

#### Request

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <your_token>
```

**Body:**
```json
{
  "urls": ["https://example.com"],
  "browser_config": {
    "headless": true,
    "viewport_width": 1920,
    "viewport_height": 1080
  },
  "crawler_config": {
    "word_count_threshold": 10,
    "wait_until": "networkidle",
    "screenshot": true
  },
  "dispatcher": "memory_adaptive"
}
```

#### Response

```json
{
  "success": true,
  "results": [
    {
      "url": "https://example.com",
      "html": "<html>...</html>",
      "markdown": "# Example Domain\n\nThis domain is for use in...",
      "cleaned_html": "<div>...</div>",
      "screenshot": "base64_encoded_image_data",
      "success": true,
      "status_code": 200,
      "extracted_content": {},
      "metadata": {
        "title": "Example Domain",
        "description": "Example Domain Description"
      },
      "links": {
        "internal": ["https://example.com/about"],
        "external": ["https://other.com"]
      },
      "media": {
        "images": [{"src": "image.jpg", "alt": "Image"}]
      }
    }
  ]
}
```

#### Examples

=== "Python"
    ```python
    import requests
    
    # Get token first
    token_response = requests.post(
        "http://localhost:11235/token",
        json={"email": "your@email.com"}
    )
    token = token_response.json()["access_token"]
    
    # Crawl with basic config
    response = requests.post(
        "http://localhost:11235/crawl",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "urls": ["https://example.com"],
            "browser_config": {"headless": True},
            "crawler_config": {"screenshot": True}
        }
    )
    
    data = response.json()
    if data["success"]:
        result = data["results"][0]
        print(f"Title: {result['metadata']['title']}")
        print(f"Markdown length: {len(result['markdown'])}")
    ```

=== "cURL"
    ```bash
    # Get token
    TOKEN=$(curl -X POST http://localhost:11235/token \
      -H "Content-Type: application/json" \
      -d '{"email": "your@email.com"}' | jq -r '.access_token')
    
    # Crawl URL
    curl -X POST http://localhost:11235/crawl \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "urls": ["https://example.com"],
        "browser_config": {"headless": true},
        "crawler_config": {"screenshot": true}
      }'
    ```

=== "JavaScript"
    ```javascript
    // Get token
    const tokenResponse = await fetch('http://localhost:11235/token', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: 'your@email.com'})
    });
    const {access_token} = await tokenResponse.json();
    
    // Crawl URL
    const response = await fetch('http://localhost:11235/crawl', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        urls: ['https://example.com'],
        browser_config: {headless: true},
        crawler_config: {screenshot: true}
      })
    });
    
    const data = await response.json();
    console.log('Results:', data.results);
    ```

#### Configuration Options

**Browser Config:**
```json
{
  "headless": true,              // Run browser in headless mode
  "viewport_width": 1920,        // Browser viewport width
  "viewport_height": 1080,       // Browser viewport height
  "user_agent": "custom agent",  // Custom user agent
  "accept_downloads": false,     // Enable file downloads
  "use_managed_browser": false,  // Use system browser
  "java_script_enabled": true    // Enable JavaScript execution
}
```

**Crawler Config:**
```json
{
  "word_count_threshold": 10,    // Minimum words per block
  "wait_until": "networkidle",   // When to consider page loaded
  "wait_for": "div.content",     // CSS selector to wait for
  "delay_before_return": 0.5,    // Delay before returning (seconds)
  "screenshot": true,            // Capture screenshot
  "pdf": false,                  // Generate PDF
  "remove_overlay_elements": true,// Remove popups/modals
  "simulate_user": false,        // Simulate user interaction
  "magic": false,                // Auto-handle overlays
  "adjust_viewport_to_content": false, // Auto-adjust viewport
  "page_timeout": 60000,         // Page load timeout (ms)
  "js_code": "console.log('hi')", // Execute custom JS
  "css_selector": ".content",    // Extract specific element
  "excluded_tags": ["nav", "footer"], // Tags to exclude
  "exclude_external_links": true // Remove external links
}
```

**Dispatcher Options:**
- `memory_adaptive` - Dynamically adjusts based on memory (default)
- `semaphore` - Fixed concurrency limit

---

### POST /crawl/stream

Streaming endpoint for real-time crawl progress.

#### Request

Same as `/crawl` endpoint.

#### Response

Server-Sent Events (SSE) stream:

```
data: {"type": "progress", "url": "https://example.com", "status": "started"}

data: {"type": "progress", "url": "https://example.com", "status": "fetching"}

data: {"type": "result", "url": "https://example.com", "data": {...}}

data: {"type": "complete", "success": true}
```

#### Examples

=== "Python"
    ```python
    import requests
    import json
    
    response = requests.post(
        "http://localhost:11235/crawl/stream",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"urls": ["https://example.com"]},
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"Event: {data.get('type')} - {data}")
    ```

=== "JavaScript"
    ```javascript
    const eventSource = new EventSource(
      'http://localhost:11235/crawl/stream'
    );
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Progress:', data);
      
      if (data.type === 'complete') {
        eventSource.close();
      }
    };
    ```

---

### POST /seed

Discover and seed URLs from a website.

#### Request

```json
{
  "url": "https://www.nbcnews.com",
  "config": {
    "max_urls": 20,
    "filter_type": "domain",
    "exclude_external": true
  }
}
```

**Filter Types:**
- `all` - Include all discovered URLs
- `domain` - Only URLs from same domain
- `subdomain` - URLs from same subdomain only

#### Response

```json
{
  "seed_url": [
    "https://www.nbcnews.com/news/page1",
    "https://www.nbcnews.com/news/page2",
    "https://www.nbcnews.com/about"
  ],
  "count": 3
}
```

#### Examples

=== "Python"
    ```python
    response = requests.post(
        "http://localhost:11235/seed",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://www.nbcnews.com",
            "config": {
                "max_urls": 20,
                "filter_type": "domain"
            }
        }
    )
    
    data = response.json()
    urls = data["seed_url"]
    print(f"Found {len(urls)} URLs")
    ```

=== "cURL"
    ```bash
    curl -X POST http://localhost:11235/seed \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "url": "https://www.nbcnews.com",
        "config": {
          "max_urls": 20,
          "filter_type": "domain"
        }
      }'
    ```

---

### POST /crawl/http

Fast HTTP-only crawling endpoint for static content and APIs.

#### Request

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <your_token>
```

**Body:**
```json
{
  "urls": ["https://api.example.com/data"],
  "http_config": {
    "method": "GET",
    "headers": {"Accept": "application/json"},
    "timeout": 30,
    "follow_redirects": true,
    "verify_ssl": true
  },
  "crawler_config": {
    "word_count_threshold": 10,
    "extraction_strategy": "NoExtractionStrategy"
  },
  "dispatcher": "memory_adaptive"
}
```

#### Response

```json
{
  "success": true,
  "results": [
    {
      "url": "https://api.example.com/data",
      "html": "<html>...</html>",
      "markdown": "# API Response\n\n...",
      "cleaned_html": "<div>...</div>",
      "success": true,
      "status_code": 200,
      "metadata": {
        "title": "API Data",
        "description": "JSON response data"
      },
      "links": {
        "internal": [],
        "external": []
      },
      "media": {
        "images": []
      }
    }
  ],
  "server_processing_time_s": 0.15,
  "server_memory_delta_mb": 1.2
}
```

#### Configuration Options

**HTTP Config:**
```json
{
  "method": "GET",                    // HTTP method (GET, POST, PUT, etc.)
  "headers": {                        // Custom HTTP headers
    "User-Agent": "Crawl4AI/1.0",
    "Accept": "application/json"
  },
  "data": "form=data",                // Form data for POST requests
  "json": {"key": "value"},           // JSON data for POST requests
  "timeout": 30,                      // Request timeout in seconds
  "follow_redirects": true,           // Follow HTTP redirects
  "verify_ssl": true,                 // Verify SSL certificates
  "params": {"key": "value"}          // URL query parameters
}
```

**Crawler Config:**
```json
{
  "word_count_threshold": 10,         // Minimum words per block
  "extraction_strategy": "NoExtractionStrategy", // Use lightweight extraction
  "remove_overlay_elements": false,   // No overlays in HTTP responses
  "css_selector": ".content",         // Extract specific elements
  "excluded_tags": ["script", "style"] // Tags to exclude
}
```

#### Examples

=== "Python"
    ```python
    import requests
    
    # Get token first
    token_response = requests.post(
        "http://localhost:11235/token",
        json={"email": "your@email.com"}
    )
    token = token_response.json()["access_token"]
    
    # Fast HTTP-only crawl
    response = requests.post(
        "http://localhost:11235/crawl/http",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "urls": ["https://httpbin.org/json"],
            "http_config": {
                "method": "GET",
                "headers": {"Accept": "application/json"},
                "timeout": 10
            },
            "crawler_config": {
                "extraction_strategy": "NoExtractionStrategy"
            }
        }
    )
    
    data = response.json()
    if data["success"]:
        result = data["results"][0]
        print(f"Status: {result['status_code']}")
        print(f"Response time: {data['server_processing_time_s']:.2f}s")
        print(f"Content length: {len(result['html'])} chars")
    ```

=== "cURL"
    ```bash
    # Get token
    TOKEN=$(curl -X POST http://localhost:11235/token \
      -H "Content-Type: application/json" \
      -d '{"email": "your@email.com"}' | jq -r '.access_token')
    
    # HTTP-only crawl
    curl -X POST http://localhost:11235/crawl/http \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "urls": ["https://httpbin.org/json"],
        "http_config": {
          "method": "GET",
          "headers": {"Accept": "application/json"},
          "timeout": 10
        },
        "crawler_config": {
          "extraction_strategy": "NoExtractionStrategy"
        }
      }'
    ```

=== "JavaScript"
    ```javascript
    // Get token
    const tokenResponse = await fetch('http://localhost:11235/token', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email: 'your@email.com'})
    });
    const {access_token} = await tokenResponse.json();
    
    // HTTP-only crawl
    const response = await fetch('http://localhost:11235/crawl/http', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        urls: ['https://httpbin.org/json'],
        http_config: {
          method: 'GET',
          headers: {'Accept': 'application/json'},
          timeout: 10
        },
        crawler_config: {
          extraction_strategy: 'NoExtractionStrategy'
        }
      })
    });
    
    const data = await response.json();
    console.log('HTTP Crawl Results:', data.results);
    console.log(`Processed in ${data.server_processing_time_s}s`);
    ```

#### Use Cases

- **API Endpoints**: Crawl REST APIs and GraphQL endpoints
- **Static Websites**: Fast crawling of HTML pages without JavaScript
- **JSON/XML Feeds**: Extract data from RSS feeds and API responses
- **Sitemaps**: Process XML sitemaps and structured data
- **Headless CMS**: Crawl content management system APIs

#### Performance Benefits

- **1000x Faster**: No browser startup or JavaScript execution
- **Lower Resource Usage**: Minimal memory and CPU overhead
- **Higher Throughput**: Process thousands of URLs per minute
- **Cost Effective**: Ideal for large-scale data collection

---

### POST /crawl/http/stream

Streaming HTTP-only crawling with real-time progress updates.

#### Request

Same as `/crawl/http` endpoint.

#### Response

Server-Sent Events (SSE) stream:

```
data: {"type": "progress", "url": "https://api.example.com", "status": "started"}

data: {"type": "progress", "url": "https://api.example.com", "status": "fetching"}

data: {"type": "result", "url": "https://api.example.com", "data": {...}}

data: {"type": "complete", "success": true, "total_urls": 1}
```

#### Examples

=== "Python"
    ```python
    import requests
    import json
    
    response = requests.post(
        "http://localhost:11235/crawl/http/stream",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "urls": ["https://httpbin.org/json", "https://httpbin.org/uuid"],
            "http_config": {"timeout": 5}
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"Event: {data.get('type')} - URL: {data.get('url', 'N/A')}")
                
                if data['type'] == 'result':
                    result = data['data']
                    print(f"  Status: {result['status_code']}")
                elif data['type'] == 'complete':
                    print(f"  Total processed: {data['total_urls']}")
                    break
    ```

=== "JavaScript"
    ```javascript
    const eventSource = new EventSource(
      'http://localhost:11235/crawl/http/stream'
    );
    
    // Handle streaming events
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'progress':
          console.log(`Progress: ${data.url} - ${data.status}`);
          break;
        case 'result':
          console.log(`Result: ${data.url} - Status ${data.data.status_code}`);
          break;
        case 'complete':
          console.log(`Complete: ${data.total_urls} URLs processed`);
          eventSource.close();
          break;
      }
    };
    
    // Send the request
    fetch('http://localhost:11235/crawl/http/stream', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        urls: ['https://httpbin.org/json'],
        http_config: {timeout: 5}
      })
    });
    ```

---

## Content Extraction Endpoints

### POST /md

Extract markdown content from a URL.

#### Request

```json
{
  "url": "https://example.com",
  "f": "markdown",
  "q": ""
}
```

#### Response

```json
{
  "markdown": "# Example Domain\n\nThis domain is for use in...",
  "title": "Example Domain",
  "url": "https://example.com"
}
```

#### Examples

=== "Python"
    ```python
    response = requests.post(
        "http://localhost:11235/md",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "https://example.com"}
    )
    
    markdown = response.json()["markdown"]
    print(markdown)
    ```

---

### POST /html

Get clean HTML content.

#### Request

```json
{
  "url": "https://example.com",
  "only_text": false
}
```

#### Response

```json
{
  "html": "<div><h1>Example Domain</h1>...</div>",
  "url": "https://example.com"
}
```

---

### POST /screenshot

Capture page screenshot.

#### Request

```json
{
  "url": "https://example.com",
  "options": {
    "full_page": true,
    "format": "png"
  }
}
```

#### Response

```json
{
  "screenshot": "base64_encoded_image_data",
  "format": "png",
  "url": "https://example.com"
}
```

#### Examples

=== "Python"
    ```python
    import base64
    
    response = requests.post(
        "http://localhost:11235/screenshot",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://example.com",
            "options": {"full_page": True}
        }
    )
    
    screenshot_b64 = response.json()["screenshot"]
    screenshot_data = base64.b64decode(screenshot_b64)
    
    with open("screenshot.png", "wb") as f:
        f.write(screenshot_data)
    ```

---

### POST /pdf

Export page as PDF.

#### Request

```json
{
  "url": "https://example.com",
  "options": {
    "format": "A4",
    "print_background": true
  }
}
```

#### Response

```json
{
  "pdf": "base64_encoded_pdf_data",
  "url": "https://example.com"
}
```

---

### POST /execute_js

Execute JavaScript on a page.

#### Request

```json
{
  "url": "https://example.com",
  "js_code": "document.querySelector('h1').textContent",
  "wait_for": "h1"
}
```

#### Response

```json
{
  "result": "Example Domain",
  "success": true,
  "url": "https://example.com"
}
```

#### Examples

=== "Python"
    ```python
    response = requests.post(
        "http://localhost:11235/execute_js",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://example.com",
            "js_code": "document.title"
        }
    )
    
    result = response.json()["result"]
    print(f"Page title: {result}")
    ```

---

## Dispatcher Management

### GET /dispatchers

List all available dispatcher types.

#### Response

```json
[
  {
    "type": "memory_adaptive",
    "name": "Memory Adaptive Dispatcher",
    "description": "Dynamically adjusts concurrency based on system memory usage",
    "config": {
      "memory_threshold_percent": 70.0,
      "critical_threshold_percent": 85.0,
      "max_session_permit": 20
    },
    "features": [
      "Dynamic concurrency adjustment",
      "Memory pressure monitoring"
    ]
  },
  {
    "type": "semaphore",
    "name": "Semaphore Dispatcher",
    "description": "Fixed concurrency limit using semaphore",
    "config": {
      "semaphore_count": 5,
      "max_session_permit": 10
    },
    "features": [
      "Fixed concurrency limit",
      "Simple semaphore control"
    ]
  }
]
```

#### Examples

=== "Python"
    ```python
    response = requests.get("http://localhost:11235/dispatchers")
    dispatchers = response.json()
    
    for dispatcher in dispatchers:
        print(f"{dispatcher['type']}: {dispatcher['name']}")
    ```

=== "cURL"
    ```bash
    curl http://localhost:11235/dispatchers | jq
    ```

---

### GET /dispatchers/default

Get current default dispatcher information.

#### Response

```json
{
  "default_dispatcher": "memory_adaptive",
  "config": {
    "memory_threshold_percent": 70.0
  }
}
```

---

### GET /dispatchers/stats

Get dispatcher statistics and metrics.

#### Response

```json
{
  "current_dispatcher": "memory_adaptive",
  "active_sessions": 3,
  "queued_requests": 0,
  "memory_usage_percent": 45.2,
  "total_processed": 157
}
```

---

## Adaptive Crawling

### POST /adaptive/crawl

Start an adaptive crawl with automatic URL discovery.

#### Request

```json
{
  "start_url": "https://example.com",
  "config": {
    "max_depth": 2,
    "max_pages": 50,
    "adaptive_threshold": 0.5
  }
}
```

#### Response

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "start_url": "https://example.com"
}
```

---

### GET /adaptive/status/{task_id}

Check status of adaptive crawl task.

#### Response

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "pages_crawled": 23,
  "pages_queued": 15,
  "progress_percent": 46.0
}
```

---

## Utility Endpoints

### POST /token

Get authentication token for API access.

#### Request

```json
{
  "email": "your@email.com"
}
```

#### Response

```json
{
  "email": "your@email.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Examples

=== "Python"
    ```python
    response = requests.post(
        "http://localhost:11235/token",
        json={"email": "your@email.com"}
    )
    
    token = response.json()["access_token"]
    ```

---

### GET /health

Health check endpoint.

#### Response

```json
{
  "status": "healthy",
  "version": "0.7.0",
  "uptime_seconds": 3600
}
```

---

### GET /metrics

Prometheus metrics endpoint (if enabled).

#### Response

```
# HELP crawl4ai_requests_total Total requests processed
# TYPE crawl4ai_requests_total counter
crawl4ai_requests_total 157.0

# HELP crawl4ai_request_duration_seconds Request duration
# TYPE crawl4ai_request_duration_seconds histogram
...
```

---

### GET /schema

Get Pydantic schemas for request/response models.

#### Response

```json
{
  "CrawlerRunConfig": {
    "type": "object",
    "properties": {
      "word_count_threshold": {"type": "integer"},
      ...
    }
  }
}
```

---

### GET /llm/{url}

Get LLM-friendly format of a URL.

#### Example

```bash
curl http://localhost:11235/llm/https://example.com
```

#### Response

```
# Example Domain

This domain is for use in illustrative examples in documents...

[Read more](https://example.com)
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK** - Request successful
- **400 Bad Request** - Invalid request parameters
- **401 Unauthorized** - Missing or invalid authentication token
- **404 Not Found** - Resource not found
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "INVALID_URL",
  "status_code": 400
}
```

---

## Rate Limiting

The API implements rate limiting per IP address:

- Default: 100 requests per minute
- Configurable via `config.yml`
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Best Practices

### 1. Authentication

Always store tokens securely and refresh before expiration:

```python
class Crawl4AIClient:
    def __init__(self, email, base_url="http://localhost:11235"):
        self.email = email
        self.base_url = base_url
        self.token = None
        self.refresh_token()
    
    def refresh_token(self):
        response = requests.post(
            f"{self.base_url}/token",
            json={"email": self.email}
        )
        self.token = response.json()["access_token"]
    
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
```

### 2. Batch Processing

For multiple URLs, use the batch crawl endpoint:

```python
client = Crawl4AIClient("your@email.com")

response = requests.post(
    f"{client.base_url}/crawl",
    headers=client.get_headers(),
    json={
        "urls": [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ],
        "dispatcher": "memory_adaptive"
    }
)
```

### 3. Error Handling

Always implement proper error handling:

```python
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        print("Rate limit exceeded, waiting...")
        time.sleep(60)
    else:
        print(f"HTTP error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### 4. Streaming for Long-Running Tasks

Use streaming endpoint for better progress tracking:

```python
import sseclient

response = requests.post(
    f"{client.base_url}/crawl/stream",
    headers=client.get_headers(),
    json={"urls": urls},
    stream=True
)

client_stream = sseclient.SSEClient(response)
for event in client_stream.events():
    data = json.loads(event.data)
    if data['type'] == 'progress':
        print(f"Progress: {data['status']}")
    elif data['type'] == 'result':
        process_result(data['data'])
```

---

## SDK Examples

### Complete Crawling Workflow

```python
import requests
import json
from typing import List, Dict

class Crawl4AIClient:
    def __init__(self, email: str, base_url: str = "http://localhost:11235"):
        self.base_url = base_url
        self.token = self._get_token(email)
    
    def _get_token(self, email: str) -> str:
        """Get authentication token"""
        response = requests.post(
            f"{self.base_url}/token",
            json={"email": email}
        )
        return response.json()["access_token"]
    
    def _headers(self) -> Dict[str, str]:
        """Get request headers with auth"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def crawl(self, urls: List[str], **config) -> Dict:
        """Crawl one or more URLs"""
        response = requests.post(
            f"{self.base_url}/crawl",
            headers=self._headers(),
            json={"urls": urls, **config}
        )
        response.raise_for_status()
        return response.json()
    
    def seed_urls(self, url: str, max_urls: int = 20, filter_type: str = "domain") -> List[str]:
        """Discover URLs from a website"""
        response = requests.post(
            f"{self.base_url}/seed",
            headers=self._headers(),
            json={
                "url": url,
                "config": {
                    "max_urls": max_urls,
                    "filter_type": filter_type
                }
            }
        )
        return response.json()["seed_url"]
    
    def screenshot(self, url: str, full_page: bool = True) -> bytes:
        """Capture screenshot and return image data"""
        import base64
        
        response = requests.post(
            f"{self.base_url}/screenshot",
            headers=self._headers(),
            json={
                "url": url,
                "options": {"full_page": full_page}
            }
        )
        screenshot_b64 = response.json()["screenshot"]
        return base64.b64decode(screenshot_b64)
    
    def get_markdown(self, url: str) -> str:
        """Extract markdown from URL"""
        response = requests.post(
            f"{self.base_url}/md",
            headers=self._headers(),
            json={"url": url}
        )
        return response.json()["markdown"]

# Usage
client = Crawl4AIClient("your@email.com")

# Seed URLs
urls = client.seed_urls("https://example.com", max_urls=10)
print(f"Found {len(urls)} URLs")

# Crawl URLs
results = client.crawl(
    urls=urls[:5],
    browser_config={"headless": True},
    crawler_config={"screenshot": True}
)

# Process results
for result in results["results"]:
    print(f"Title: {result['metadata']['title']}")
    print(f"Links: {len(result['links']['internal'])}")
    
# Get markdown
markdown = client.get_markdown("https://example.com")
print(markdown[:200])

# Capture screenshot
screenshot_data = client.screenshot("https://example.com")
with open("page.png", "wb") as f:
    f.write(screenshot_data)
```

---

## Configuration Reference

### Server Configuration

The server is configured via `config.yml`:

```yaml
server:
  host: "0.0.0.0"
  port: 11235
  workers: 4

security:
  enabled: true
  jwt_secret: "your-secret-key"
  token_expire_minutes: 60

rate_limiting:
  default_limit: "100/minute"
  storage_uri: "redis://localhost:6379"

observability:
  health_check:
    enabled: true
    endpoint: "/health"
  prometheus:
    enabled: true
    endpoint: "/metrics"
```

---

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
{"detail": "Invalid authentication credentials"}
```
Solution: Refresh your token

**2. Rate Limit Exceeded**
```
{"detail": "Rate limit exceeded"}
```
Solution: Wait or implement exponential backoff

**3. Timeout Errors**
```
{"detail": "Page load timeout"}
```
Solution: Increase `page_timeout` in crawler_config

**4. Memory Issues**
```
{"detail": "Insufficient memory"}
```
Solution: Use `semaphore` dispatcher with lower concurrency

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Additional Resources

- [GitHub Repository](https://github.com/unclecode/crawl4ai)
- [Full Documentation](https://docs.crawl4ai.com)
- [Discord Community](https://discord.gg/crawl4ai)
- [Issue Tracker](https://github.com/unclecode/crawl4ai/issues)

---

**Last Updated**: October 7, 2025  
**API Version**: 0.7.0  
**Status**: Production Ready ✅
