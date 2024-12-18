# Magic Mode & Anti-Bot Protection

Crawl4AI provides powerful anti-detection capabilities, with Magic Mode being the simplest and most comprehensive solution.

## Magic Mode

The easiest way to bypass anti-bot protections:

```python
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        magic=True  # Enables all anti-detection features
    )
```

Magic Mode automatically:
- Masks browser automation signals
- Simulates human-like behavior
- Overrides navigator properties
- Handles cookie consent popups
- Manages browser fingerprinting
- Randomizes timing patterns

## Manual Anti-Bot Options

While Magic Mode is recommended, you can also configure individual anti-detection features:

```python
result = await crawler.arun(
    url="https://example.com",
    simulate_user=True,        # Simulate human behavior
    override_navigator=True    # Mask automation signals
)
```

Note: When `magic=True` is used, you don't need to set these individual options.

## Example: Handling Protected Sites

```python
async def crawl_protected_site(url: str):
    async with AsyncWebCrawler(headless=True) as crawler:
        result = await crawler.arun(
            url=url,
            magic=True,
            remove_overlay_elements=True,  # Remove popups/modals
            page_timeout=60000            # Increased timeout for protection checks
        )
        
        return result.markdown if result.success else None
```
