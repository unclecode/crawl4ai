# Network Requests & Console Message Capturing

Crawl4AI can capture all network requests and browser console messages during a crawl, which is invaluable for debugging, security analysis, or understanding page behavior.

## Configuration

To enable network and console capturing, use these configuration options:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Enable both network request capture and console message capture
config = CrawlerRunConfig(
    capture_network_requests=True,  # Capture all network requests and responses
    capture_console_messages=True   # Capture all browser console output
)
```

## Example Usage

```python
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
```

## Captured Data Structure

### Network Requests

The `result.network_requests` contains a list of dictionaries, each representing a network event with these common fields:

| Field | Description |
|-------|-------------|
| `event_type` | Type of event: `"request"`, `"response"`, or `"request_failed"` |
| `url` | The URL of the request |
| `timestamp` | Unix timestamp when the event was captured |

#### Request Event Fields

```json
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
```

#### Response Event Fields

```json
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
```

#### Failed Request Event Fields

```json
{
  "event_type": "request_failed",
  "url": "https://example.com/missing.png",
  "method": "GET",
  "resource_type": "image",
  "failure_text": "net::ERR_ABORTED 404",
  "timestamp": 1633456789.789
}
```

### Console Messages

The `result.console_messages` contains a list of dictionaries, each representing a console message with these common fields:

| Field | Description |
|-------|-------------|
| `type` | Message type: `"log"`, `"error"`, `"warning"`, `"info"`, etc. |
| `text` | The message text |
| `timestamp` | Unix timestamp when the message was captured |

#### Console Message Example

```json
{
  "type": "error",
  "text": "Uncaught TypeError: Cannot read property 'length' of undefined",
  "location": "https://example.com/script.js:123:45",
  "timestamp": 1633456790.123
}
```

## Key Benefits

- **Full Request Visibility**: Capture all network activity including:
  - Requests (URLs, methods, headers, post data)
  - Responses (status codes, headers, timing)
  - Failed requests (with error messages)
  
- **Console Message Access**: View all JavaScript console output:
  - Log messages
  - Warnings
  - Errors with stack traces
  - Developer debugging information

- **Debugging Power**: Identify issues such as:
  - Failed API calls or resource loading
  - JavaScript errors affecting page functionality
  - CORS or other security issues
  - Hidden API endpoints and data flows

- **Security Analysis**: Detect:
  - Unexpected third-party requests
  - Data leakage in request payloads
  - Suspicious script behavior

- **Performance Insights**: Analyze:
  - Request timing data
  - Resource loading patterns
  - Potential bottlenecks

## Use Cases

1. **API Discovery**: Identify hidden endpoints and data flows in single-page applications
2. **Debugging**: Track down JavaScript errors affecting page functionality
3. **Security Auditing**: Detect unwanted third-party requests or data leakage
4. **Performance Analysis**: Identify slow-loading resources
5. **Ad/Tracker Analysis**: Detect and catalog advertising or tracking calls

This capability is especially valuable for complex sites with heavy JavaScript, single-page applications, or when you need to understand the exact communication happening between a browser and servers.