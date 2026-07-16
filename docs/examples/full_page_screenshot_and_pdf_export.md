# Capturing Full-Page Screenshots and PDFs from Massive Webpages with Crawl4AI

When dealing with very long web pages, traditional full-page screenshots can be slow or fail entirely. For large pages (like extensive Wikipedia articles), generating a single massive screenshot often leads to delays, memory issues, or style differences.

**The New Approach:**
We’ve introduced a new feature that effortlessly handles even the biggest pages by first exporting them as a PDF, then converting that PDF into a high-quality image. This approach leverages the browser’s built-in PDF rendering, making it both stable and efficient for very long content. You also have the option to directly save the PDF for your own usage—no need for multiple passes or complex stitching logic.

**Key Benefits:**
- **Reliability:** The PDF export never times out and works regardless of page length.
- **Versatility:** Get both the PDF and a screenshot in one crawl, without reloading or reprocessing.
- **Performance:** Skips manual scrolling and stitching images, reducing complexity and runtime.

**Simple Example:**
```python
import os
import sys
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

# Adjust paths as needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

async def main():
    async with AsyncWebCrawler() as crawler:
        # Request both PDF and screenshot
        result = await crawler.arun(
            url='https://en.wikipedia.org/wiki/List_of_common_misconceptions',
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                pdf=True,
                screenshot=True
            )
        )
        
        if result.success:
            # Save screenshot
            if result.screenshot:
                from base64 import b64decode
                with open(os.path.join(__location__, "screenshot.png"), "wb") as f:
                    f.write(b64decode(result.screenshot))
            
            # Save PDF
            if result.pdf:
                with open(os.path.join(__location__, "page.pdf"), "wb") as f:
                    f.write(result.pdf)

if __name__ == "__main__":
    asyncio.run(main())
```

**What Happens Under the Hood:**
- Crawl4AI navigates to the target page.
- If `pdf=True`, it exports the current page as a full PDF, capturing all of its content no matter the length.
- If `screenshot=True`, and a PDF is already available, it directly converts the first page of that PDF to an image for you—no repeated loading or scrolling.
- Finally, you get your PDF and/or screenshot ready to use.

**Controlling scroll speed for full-page screenshots:**  
When a page is taller than `screenshot_height_threshold` (default ~20,000px) and no PDF is available, Crawl4AI scrolls through the page to capture a stitched full-page screenshot. Use `scroll_delay` to control the pause between scroll steps:

```python
config = CrawlerRunConfig(
    screenshot=True,
    scroll_delay=0.5,  # Wait 0.5s between scroll steps (default: 0.2)
)
```

This is particularly useful for pages with lazy-loaded images or animations that need time to render during scrolling.

---

## Viewport-Only Screenshots

If you only need a screenshot of the visible viewport (not the entire page), use the `force_viewport_screenshot` option. This is significantly faster and produces smaller images, especially for long pages.

```python
import os
import asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url='https://en.wikipedia.org/wiki/List_of_common_misconceptions',
            config=CrawlerRunConfig(
                screenshot=True,
                force_viewport_screenshot=True  # Only capture the visible viewport
            )
        )

        if result.success and result.screenshot:
            with open("viewport_screenshot.png", "wb") as f:
                f.write(b64decode(result.screenshot))
            print("Viewport screenshot saved!")

if __name__ == "__main__":
    asyncio.run(main())
```

**When to use viewport-only screenshots:**
- You only need what's visible above the fold
- You want faster screenshot capture on long pages
- You need smaller image sizes for thumbnails or previews

**Conclusion:**
With this feature, Crawl4AI becomes even more robust and versatile for large-scale content extraction. Whether you need a PDF snapshot or a quick screenshot, you now have a reliable solution for even the most extensive webpages.