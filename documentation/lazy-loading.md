Handling Lazy-Loaded Images
---------------------------

Many websites now load images **lazily** as you scroll. If you need to ensure they appear in your final crawl (and in `result.media`), consider:

1. **`wait_for_images=True`** – Wait for images to fully load.
2. **`scan_full_page`** – Force the crawler to scroll the entire page, triggering lazy loads.
3. **`scroll_delay`** – Add small delays between scroll steps.

**Note**: If the site requires multiple “Load More” triggers or complex interactions, see the [Page Interaction docs](../../core/page-interaction/). For sites with virtual scrolling (Twitter/Instagram style), see the [Virtual Scroll docs](../virtual-scroll/).

### Example: Ensuring Lazy Images Appear

```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.async_configs import CacheMode

async def main():
    config = CrawlerRunConfig(
        # Force the crawler to wait until images are fully loaded
        wait_for_images=True,

        # Option 1: If you want to automatically scroll the page to load images
        scan_full_page=True,  # Tells the crawler to try scrolling the entire page
        scroll_delay=0.5,     # Delay (seconds) between scroll steps

        # Option 2: If the site uses a 'Load More' or JS triggers for images,
        # you can also specify js_code or wait_for logic here.

        cache_mode=CacheMode.BYPASS,
        verbose=True
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun("https://www.example.com/gallery", config=config)

        if result.success:
            images = result.media.get("images", [])
            print("Images found:", len(images))
            for i, img in enumerate(images[:5]):
                print(f"[Image {i}] URL: {img['src']}, Score: {img.get('score','N/A')}")
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Explanation**:

* **`wait_for_images=True`**
  The crawler tries to ensure images have finished loading before finalizing the HTML.
* **`scan_full_page=True`**
  Tells the crawler to attempt scrolling from top to bottom. Each scroll step helps trigger lazy loading.
* **`scroll_delay=0.5`**
  Pause half a second between each scroll step. Helps the site load images before continuing.

**When to Use**:

* **Lazy-Loading**: If images appear only when the user scrolls into view, `scan_full_page` + `scroll_delay` helps the crawler see them.
* **Heavier Pages**: If a page is extremely long, be mindful that scanning the entire page can be slow. Adjust `scroll_delay` or the max scroll steps as needed.

---

Combining with Other Link & Media Filters
-----------------------------------------

You can still combine **lazy-load** logic with the usual **exclude\_external\_images**, **exclude\_domains**, or link filtration:

```
config = CrawlerRunConfig(
    wait_for_images=True,
    scan_full_page=True,
    scroll_delay=0.5,

    # Filter out external images if you only want local ones
    exclude_external_images=True,

    # Exclude certain domains for links
    exclude_domains=["spammycdn.com"],
)
```

This approach ensures you see **all** images from the main domain while ignoring external ones, and the crawler physically scrolls the entire page so that lazy-loading triggers.

---