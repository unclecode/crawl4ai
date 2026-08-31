# Virtual Scroll

Modern websites increasingly use **virtual scrolling** (also called windowed rendering or viewport rendering) to handle large datasets efficiently. This technique only renders visible items in the DOM, replacing content as users scroll. Popular examples include Twitter's timeline, Instagram's feed, and many data tables.

Crawl4AI's Virtual Scroll feature automatically detects and handles these scenarios, ensuring you capture **all content**, not just what's initially visible.

## Understanding Virtual Scroll

### The Problem

Traditional infinite scroll **appends** new content to existing content. Virtual scroll **replaces** content to maintain performance:

```
Traditional Scroll:          Virtual Scroll:
┌─────────────┐             ┌─────────────┐
│ Item 1      │             │ Item 11     │  <- Items 1-10 removed
│ Item 2      │             │ Item 12     │  <- Only visible items
│ ...         │             │ Item 13     │     in DOM
│ Item 10     │             │ Item 14     │
│ Item 11 NEW │             │ Item 15     │
│ Item 12 NEW │             └─────────────┘
└─────────────┘             
DOM keeps growing           DOM size stays constant
```

Without proper handling, crawlers only capture the currently visible items, missing the rest of the content.

### Three Scrolling Scenarios

Crawl4AI's Virtual Scroll detects and handles three scenarios:

1. **No Change** - Content doesn't update on scroll (static page or end reached)
2. **Content Appended** - New items added to existing ones (traditional infinite scroll)  
3. **Content Replaced** - Items replaced with new ones (true virtual scroll)

Only scenario 3 requires special handling, which Virtual Scroll automates.

## Basic Usage

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, VirtualScrollConfig

# Configure virtual scroll
virtual_config = VirtualScrollConfig(
    container_selector="#feed",      # CSS selector for scrollable container
    scroll_count=20,                 # Number of scrolls to perform
    scroll_by="container_height",    # How much to scroll each time
    wait_after_scroll=0.5           # Wait time (seconds) after each scroll
)

# Use in crawler configuration
config = CrawlerRunConfig(
    virtual_scroll_config=virtual_config
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com", config=config)
    # result.html contains ALL items from the virtual scroll
```

## Configuration Parameters

### VirtualScrollConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `container_selector` | `str` | Required | CSS selector for the scrollable container |
| `scroll_count` | `int` | `10` | Maximum number of scrolls to perform |
| `scroll_by` | `str` or `int` | `"container_height"` | Scroll amount per step |
| `wait_after_scroll` | `float` | `0.5` | Seconds to wait after each scroll |

### Scroll By Options

- `"container_height"` - Scroll by the container's visible height
- `"page_height"` - Scroll by the viewport height
- `500` (integer) - Scroll by exact pixel amount

## Real-World Examples

### Twitter-like Timeline

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, VirtualScrollConfig, BrowserConfig

async def crawl_twitter_timeline():
    # Twitter replaces tweets as you scroll
    virtual_config = VirtualScrollConfig(
        container_selector="[data-testid='primaryColumn']",
        scroll_count=30,
        scroll_by="container_height",
        wait_after_scroll=1.0  # Twitter needs time to load
    )
    
    browser_config = BrowserConfig(headless=True)  # Set to False to watch it work
    config = CrawlerRunConfig(
        virtual_scroll_config=virtual_config
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://twitter.com/search?q=AI",
            config=config
        )
        
        # Extract tweet count
        import re
        tweets = re.findall(r'data-testid="tweet"', result.html)
        print(f"Captured {len(tweets)} tweets")
```

### Instagram Grid

```python
async def crawl_instagram_grid():
    # Instagram uses virtualized grid for performance
    virtual_config = VirtualScrollConfig(
        container_selector="article",  # Main feed container
        scroll_count=50,               # More scrolls for grid layout
        scroll_by=800,                 # Fixed pixel scrolling
        wait_after_scroll=0.8
    )
    
    config = CrawlerRunConfig(
        virtual_scroll_config=virtual_config,
        screenshot=True  # Capture final state
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.instagram.com/explore/tags/photography/",
            config=config
        )
        
        # Count posts
        posts = result.html.count('class="post"')
        print(f"Captured {posts} posts from virtualized grid")
```

### Mixed Content (News Feed)

Some sites mix static and virtualized content:

```python
async def crawl_mixed_feed():
    # Featured articles stay, regular articles virtualize
    virtual_config = VirtualScrollConfig(
        container_selector=".main-feed",
        scroll_count=25,
        scroll_by="container_height",
        wait_after_scroll=0.5
    )
    
    config = CrawlerRunConfig(
        virtual_scroll_config=virtual_config
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.example.com",
            config=config
        )
        
        # Featured articles remain throughout
        featured = result.html.count('class="featured-article"')
        regular = result.html.count('class="regular-article"')
        
        print(f"Featured (static): {featured}")
        print(f"Regular (virtualized): {regular}")
```

## Virtual Scroll vs scan_full_page

Both features handle dynamic content, but serve different purposes:

| Feature | Virtual Scroll | scan_full_page |
|---------|---------------|----------------|
| **Purpose** | Capture content that's replaced during scroll | Load content that's appended during scroll |
| **Use Case** | Twitter, Instagram, virtual tables | Traditional infinite scroll, lazy-loaded images |
| **DOM Behavior** | Replaces elements | Adds elements |
| **Memory Usage** | Efficient (merges content) | Can grow large |
| **Configuration** | Requires container selector | Works on full page |

### When to Use Which?

Use **Virtual Scroll** when:
- Content disappears as you scroll (Twitter timeline)
- DOM element count stays relatively constant
- You need ALL items from a virtualized list
- Container-based scrolling (not full page)

Use **scan_full_page** when:
- Content accumulates as you scroll
- Images load lazily
- Simple "load more" behavior
- Full page scrolling

## Combining with Extraction

Virtual Scroll works seamlessly with extraction strategies:

```python
from crawl4ai import LLMExtractionStrategy, LLMConfig

# Define extraction schema
schema = {
    "type": "array",
    "items": {
        "type": "object", 
        "properties": {
            "author": {"type": "string"},
            "content": {"type": "string"},
            "timestamp": {"type": "string"}
        }
    }
}

# Configure both virtual scroll and extraction
config = CrawlerRunConfig(
    virtual_scroll_config=VirtualScrollConfig(
        container_selector="#timeline",
        scroll_count=20
    ),
    extraction_strategy=LLMExtractionStrategy(
        llm_config=LLMConfig(provider="openai/gpt-4o-mini"),
        schema=schema
    )
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="...", config=config)
    
    # Extracted data from ALL scrolled content
    import json
    posts = json.loads(result.extracted_content)
    print(f"Extracted {len(posts)} posts from virtual scroll")
```

## Performance Tips

1. **Container Selection**: Be specific with selectors. Using the correct container improves performance.

2. **Scroll Count**: Start conservative and increase as needed:
   ```python
   # Start with fewer scrolls
   virtual_config = VirtualScrollConfig(
       container_selector="#feed",
       scroll_count=10  # Test with 10, increase if needed
   )
   ```

3. **Wait Times**: Adjust based on site speed:
   ```python
   # Fast sites
   wait_after_scroll=0.2
   
   # Slower sites or heavy content
   wait_after_scroll=1.5
   ```

4. **Debug Mode**: Set `headless=False` to watch scrolling:
   ```python
   browser_config = BrowserConfig(headless=False)
   async with AsyncWebCrawler(config=browser_config) as crawler:
       # Watch the scrolling happen
   ```

## How It Works Internally

1. **Detection Phase**: Scrolls and compares HTML to detect behavior
2. **Capture Phase**: For replaced content, stores HTML chunks at each position
3. **Merge Phase**: Combines all chunks, removing duplicates based on text content
4. **Result**: Complete HTML with all unique items

The deduplication uses normalized text (lowercase, no spaces/symbols) to ensure accurate merging without false positives.

## Error Handling

Virtual Scroll handles errors gracefully:

```python
# If container not found or scrolling fails
result = await crawler.arun(url="...", config=config)

if result.success:
    # Virtual scroll worked or wasn't needed
    print(f"Captured {len(result.html)} characters")
else:
    # Crawl failed entirely
    print(f"Error: {result.error_message}")
```

If the container isn't found, crawling continues normally without virtual scroll.

## Complete Example

See our [comprehensive example](/docs/examples/virtual_scroll_example.py) that demonstrates:
- Twitter-like feeds
- Instagram grids  
- Traditional infinite scroll
- Mixed content scenarios
- Performance comparisons

```bash
# Run the examples
cd docs/examples
python virtual_scroll_example.py
```

The example includes a local test server with different scrolling behaviors for experimentation.