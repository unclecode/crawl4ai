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
import os, sys
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode

# Adjust paths as needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

async def main():
    async with AsyncWebCrawler() as crawler:
        # Request both PDF and screenshot
        result = await crawler.arun(
            url='https://en.wikipedia.org/wiki/List_of_common_misconceptions',
            cache_mode=CacheMode.BYPASS,
            pdf=True,
            screenshot=True
        )
        
        if result.success:
            # Save screenshot
            if result.screenshot:
                from base64 import b64decode
                with open(os.path.join(__location__, "screenshot.png"), "wb") as f:
                    f.write(b64decode(result.screenshot))
            
            # Save PDF
            if result.pdf:
                pdf_bytes = b64decode(result.pdf)
                with open(os.path.join(__location__, "page.pdf"), "wb") as f:
                    f.write(pdf_bytes)

if __name__ == "__main__":
    asyncio.run(main())
```

**What Happens Under the Hood:**
- Crawl4AI navigates to the target page.
- If `pdf=True`, it exports the current page as a full PDF, capturing all of its content no matter the length.
- If `screenshot=True`, and a PDF is already available, it directly converts the first page of that PDF to an image for you—no repeated loading or scrolling.
- Finally, you get your PDF and/or screenshot ready to use.

**Conclusion:**
With this feature, Crawl4AI becomes even more robust and versatile for large-scale content extraction. Whether you need a PDF snapshot or a quick screenshot, you now have a reliable solution for even the most extensive webpages.