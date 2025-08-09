# Health Check Feature

## Overview

The `health_check` method provides a quick and efficient way to check if a URL is accessible before performing a full crawl. This is useful for validating URLs, handling failures gracefully, and optimizing crawling workflows.

## Features

- **Fast URL validation**: Uses HTTP HEAD requests for minimal overhead
- **Configurable timeouts**: Prevent hanging on slow or unresponsive URLs  
- **SSL flexibility**: Option to disable SSL verification for broader compatibility
- **Comprehensive status info**: Returns accessibility, status codes, response times, redirects, and error details
- **Redirect tracking**: Provides information about any redirects that occurred

## Usage

```python
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        # Basic health check
        result = await crawler.health_check("https://example.com")
        
        if result["accessible"]:
            print(f"URL is accessible (Status: {result['status_code']})")
            print(f"Response time: {result['response_time_ms']:.2f}ms")
        else:
            print(f"URL not accessible: {result['error']}")

        # Custom timeout and SSL settings
        result = await crawler.health_check(
            "https://httpbin.org/status/200",
            timeout=5.0,
            verify_ssl=False
        )
```

## Return Format

```python
{
    "accessible": bool,           # True if URL is accessible (2xx/3xx status)
    "status_code": int | None,    # HTTP status code (None if request failed)
    "response_time_ms": float,    # Response time in milliseconds
    "final_url": str,             # Final URL after redirects
    "redirect_count": int,        # Number of redirects that occurred
    "content_type": str | None,   # Content-Type header value
    "error": str | None,          # Error message if request failed
    "error_type": str | None      # Type of error (TimeoutError, etc.)
}
```

## Use Cases

1. **Batch URL validation**: Check multiple URLs before crawling
2. **Conditional crawling**: Only crawl accessible URLs
3. **Error handling**: Provide user feedback for inaccessible URLs
4. **Performance monitoring**: Track response times across URLs
5. **Redirect analysis**: Understand URL redirect patterns

## Implementation Details

- Uses `aiohttp` for lightweight HTTP HEAD requests
- Follows redirects automatically
- Considers 2xx and 3xx status codes as "accessible"
- Provides detailed error information for debugging
- Uses proper SSL context handling to avoid deprecation warnings

## Testing

The feature includes comprehensive tests covering:
- Accessible URLs (2xx status codes)
- Redirects (3xx status codes)  
- Not found errors (4xx status codes)
- Invalid domains (connection errors)
- Timeout scenarios
- Result structure validation

Run tests with:
```bash
python -m pytest tests/test_health_check.py -v
```

## Examples

See `docs/examples/health_check_example.py` for comprehensive usage examples including:
- Single URL health checks
- Conditional crawling based on health check results
- Batch URL validation
- Custom timeout configurations
