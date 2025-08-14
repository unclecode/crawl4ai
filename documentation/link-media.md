Link & Media
============

In this tutorial, you’ll learn how to:

1. Extract links (internal, external) from crawled pages
2. Filter or exclude specific domains (e.g., social media or custom domains)
3. Access and ma### 3.2 Excluding Images

#### Excluding External Images

If you're dealing with heavy pages or want to skip third-party images (advertisements, for example), you can turn on:

```
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```

This setting attempts to discard images from outside the primary domain, keeping only those from the site you're crawling.

#### Excluding All Images

If you want to completely remove all images from the page to maximize performance and reduce memory usage, use:

```
crawler_cfg = CrawlerRunConfig(
    exclude_all_images=True
)
```

This setting removes all images very early in the processing pipeline, which significantly improves memory efficiency and processing speed. This is particularly useful when:
- You don't need image data in your results
- You're crawling image-heavy pages that cause memory issues
- You want to focus only on text content
- You need to maximize crawling speeddata (especially images) in the crawl result
4. Configure your crawler to exclude or prioritize certain images

> **Prerequisites**
> - You have completed or are familiar with the [AsyncWebCrawler Basics](../simple-crawling/) tutorial.
> - You can run Crawl4AI in your environment (Playwright, Python, etc.).

---

Below is a revised version of the **Link Extraction** and **Media Extraction** sections that includes example data structures showing how links and media items are stored in `CrawlResult`. Feel free to adjust any field names or descriptions to match your actual output.

---