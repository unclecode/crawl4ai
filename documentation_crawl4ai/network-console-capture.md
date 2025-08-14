[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/advanced/network-console-capture/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * Network & Console Capture
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Network Requests & Console Message Capturing](https://docs.crawl4ai.com/advanced/network-console-capture/#network-requests-console-message-capturing)
  * [Configuration](https://docs.crawl4ai.com/advanced/network-console-capture/#configuration)
  * [Example Usage](https://docs.crawl4ai.com/advanced/network-console-capture/#example-usage)
  * [Captured Data Structure](https://docs.crawl4ai.com/advanced/network-console-capture/#captured-data-structure)
  * [Key Benefits](https://docs.crawl4ai.com/advanced/network-console-capture/#key-benefits)
  * [Use Cases](https://docs.crawl4ai.com/advanced/network-console-capture/#use-cases)


# Network Requests & Console Message Capturing
Crawl4AI can capture all network requests and browser console messages during a crawl, which is invaluable for debugging, security analysis, or understanding page behavior.
## Configuration
To enable network and console capturing, use these configuration options:
```
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Enable both network request capture and console message capture
config = CrawlerRunConfig(
    capture_network_requests=True,  # Capture all network requests and responses
    capture_console_messages=True   # Capture all browser console output
)
Copy
```

## Example Usage
```
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Enable both network request capture and console message capture
    config = CrawlerRunConfig(
        capture_network_requests=True,
        capture_console_messages=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=config
        )

        if result.success:
            # Analyze network requests
            if result.network_requests:
                print(f"Captured {len(result.network_requests)} network events")

                # Count request types
                request_count = len([r for r in result.network_requests if r.get("event_type") == "request"])
                response_count = len([r for r in result.network_requests if r.get("event_type") == "response"])
                failed_count = len([r for r in result.network_requests if r.get("event_type") == "request_failed"])

                print(f"Requests: {request_count}, Responses: {response_count}, Failed: {failed_count}")

                # Find API calls
                api_calls = [r for r in result.network_requests
                            if r.get("event_type") == "request" and "api" in r.get("url", "")]
                if api_calls:
                    print(f"Detected {len(api_calls)} API calls:")
                    for call in api_calls[:3]:  # Show first 3
                        print(f"  - {call.get('method')} {call.get('url')}")

            # Analyze console messages
            if result.console_messages:
                print(f"Captured {len(result.console_messages)} console messages")

                # Group by type
                message_types = {}
                for msg in result.console_messages:
                    msg_type = msg.get("type", "unknown")
                    message_types[msg_type] = message_types.get(msg_type, 0) + 1

                print("Message types:", message_types)

                # Show errors (often the most important)
                errors = [msg for msg in result.console_messages if msg.get("type") == "error"]
                if errors:
                    print(f"Found {len(errors)} console errors:")
                    for err in errors[:2]:  # Show first 2
                        print(f"  - {err.get('text', '')[:100]}")

            # Export all captured data to a file for detailed analysis
            with open("network_capture.json", "w") as f:
                json.dump({
                    "url": result.url,
                    "network_requests": result.network_requests or [],
                    "console_messages": result.console_messages or []
                }, f, indent=2)

            print("Exported detailed capture data to network_capture.json")

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

## Captured Data Structure
### Network Requests
The `result.network_requests` contains a list of dictionaries, each representing a network event with these common fields:
Field | Description
---|---
`event_type` | Type of event: `"request"`, `"response"`, or `"request_failed"`
`url` | The URL of the request
`timestamp` | Unix timestamp when the event was captured
#### Request Event Fields
```
{
  "event_type": "request",
  "url": "https://example.com/api/data.json",
  "method": "GET",
  "headers": {"User-Agent": "...", "Accept": "..."},
  "post_data": "key=value&otherkey=value",
  "resource_type": "fetch",
  "is_navigation_request": false,
  "timestamp": 1633456789.123
}
Copy
```

#### Response Event Fields
```
{
  "event_type": "response",
  "url": "https://example.com/api/data.json",
  "status": 200,
  "status_text": "OK",
  "headers": {"Content-Type": "application/json", "Cache-Control": "..."},
  "from_service_worker": false,
  "request_timing": {"requestTime": 1234.56, "receiveHeadersEnd": 1234.78},
  "timestamp": 1633456789.456
}
Copy
```

#### Failed Request Event Fields
```
{
  "event_type": "request_failed",
  "url": "https://example.com/missing.png",
  "method": "GET",
  "resource_type": "image",
  "failure_text": "net::ERR_ABORTED 404",
  "timestamp": 1633456789.789
}
Copy
```

### Console Messages
The `result.console_messages` contains a list of dictionaries, each representing a console message with these common fields:
Field | Description
---|---
`type` | Message type: `"log"`, `"error"`, `"warning"`, `"info"`, etc.
`text` | The message text
`timestamp` | Unix timestamp when the message was captured
#### Console Message Example
```
{
  "type": "error",
  "text": "Uncaught TypeError: Cannot read property 'length' of undefined",
  "location": "https://example.com/script.js:123:45",
  "timestamp": 1633456790.123
}
Copy
```

## Key Benefits
  * **Full Request Visibility** : Capture all network activity including:
  * Requests (URLs, methods, headers, post data)
  * Responses (status codes, headers, timing)
  * Failed requests (with error messages)
  * **Console Message Access** : View all JavaScript console output:
  * Log messages
  * Warnings
  * Errors with stack traces
  * Developer debugging information
  * **Debugging Power** : Identify issues such as:
  * Failed API calls or resource loading
  * JavaScript errors affecting page functionality
  * CORS or other security issues
  * Hidden API endpoints and data flows
  * **Security Analysis** : Detect:
  * Unexpected third-party requests
  * Data leakage in request payloads
  * Suspicious script behavior
  * **Performance Insights** : Analyze:
  * Request timing data
  * Resource loading patterns
  * Potential bottlenecks


## Use Cases
  1. **API Discovery** : Identify hidden endpoints and data flows in single-page applications
  2. **Debugging** : Track down JavaScript errors affecting page functionality
  3. **Security Auditing** : Detect unwanted third-party requests or data leakage
  4. **Performance Analysis** : Identify slow-loading resources
  5. **Ad/Tracker Analysis** : Detect and catalog advertising or tracking calls


This capability is especially valuable for complex sites with heavy JavaScript, single-page applications, or when you need to understand the exact communication happening between a browser and servers.
#### On this page
  * [Configuration](https://docs.crawl4ai.com/advanced/network-console-capture/#configuration)
  * [Example Usage](https://docs.crawl4ai.com/advanced/network-console-capture/#example-usage)
  * [Captured Data Structure](https://docs.crawl4ai.com/advanced/network-console-capture/#captured-data-structure)
  * [Network Requests](https://docs.crawl4ai.com/advanced/network-console-capture/#network-requests)
  * [Request Event Fields](https://docs.crawl4ai.com/advanced/network-console-capture/#request-event-fields)
  * [Response Event Fields](https://docs.crawl4ai.com/advanced/network-console-capture/#response-event-fields)
  * [Failed Request Event Fields](https://docs.crawl4ai.com/advanced/network-console-capture/#failed-request-event-fields)
  * [Console Messages](https://docs.crawl4ai.com/advanced/network-console-capture/#console-messages)
  * [Console Message Example](https://docs.crawl4ai.com/advanced/network-console-capture/#console-message-example)
  * [Key Benefits](https://docs.crawl4ai.com/advanced/network-console-capture/#key-benefits)
  * [Use Cases](https://docs.crawl4ai.com/advanced/network-console-capture/#use-cases)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
