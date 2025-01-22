# Link & Media 

In this tutorial, you’ll learn how to:

1. Extract links (internal, external) from crawled pages  
2. Filter or exclude specific domains (e.g., social media or custom domains)  
3. Access and manage media data (especially images) in the crawl result  
4. Configure your crawler to exclude or prioritize certain images

> **Prerequisites**  
> - You have completed or are familiar with the [AsyncWebCrawler Basics](../core/simple-crawling.md) tutorial.  
> - You can run Crawl4AI in your environment (Playwright, Python, etc.).

---

Below is a revised version of the **Link Extraction** and **Media Extraction** sections that includes example data structures showing how links and media items are stored in `CrawlResult`. Feel free to adjust any field names or descriptions to match your actual output.

---

## 1. Link Extraction

### 1.1 `result.links`

When you call `arun()` or `arun_many()` on a URL, Crawl4AI automatically extracts links and stores them in the `links` field of `CrawlResult`. By default, the crawler tries to distinguish **internal** links (same domain) from **external** links (different domains).

**Basic Example**:

```python
from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://www.example.com")
    if result.success:
        internal_links = result.links.get("internal", [])
        external_links = result.links.get("external", [])
        print(f"Found {len(internal_links)} internal links.")
        print(f"Found {len(internal_links)} external links.")
        print(f"Found {len(result.media)} media items.")

        # Each link is typically a dictionary with fields like:
        # { "href": "...", "text": "...", "title": "...", "base_domain": "..." }
        if internal_links:
            print("Sample Internal Link:", internal_links[0])
    else:
        print("Crawl failed:", result.error_message)
```

**Structure Example**:

```python
result.links = {
  "internal": [
    {
      "href": "https://kidocode.com/",
      "text": "",
      "title": "",
      "base_domain": "kidocode.com"
    },
    {
      "href": "https://kidocode.com/degrees/technology",
      "text": "Technology Degree",
      "title": "KidoCode Tech Program",
      "base_domain": "kidocode.com"
    },
    # ...
  ],
  "external": [
    # possibly other links leading to third-party sites
  ]
}
```

- **`href`**: The raw hyperlink URL.  
- **`text`**: The link text (if any) within the `<a>` tag.  
- **`title`**: The `title` attribute of the link (if present).  
- **`base_domain`**: The domain extracted from `href`. Helpful for filtering or grouping by domain.

---

## 2. Domain Filtering

Some websites contain hundreds of third-party or affiliate links. You can filter out certain domains at **crawl time** by configuring the crawler. The most relevant parameters in `CrawlerRunConfig` are:

- **`exclude_external_links`**: If `True`, discard any link pointing outside the root domain.  
- **`exclude_social_media_domains`**: Provide a list of social media platforms (e.g., `["facebook.com", "twitter.com"]`) to exclude from your crawl.  
- **`exclude_social_media_links`**: If `True`, automatically skip known social platforms.  
- **`exclude_domains`**: Provide a list of custom domains you want to exclude (e.g., `["spammyads.com", "tracker.net"]`).

### 2.1 Example: Excluding External & Social Media Links

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    crawler_cfg = CrawlerRunConfig(
        exclude_external_links=True,          # No links outside primary domain
        exclude_social_media_links=True       # Skip recognized social media domains
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://www.example.com",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Crawled:", result.url)
            print("Internal links count:", len(result.links.get("internal", [])))
            print("External links count:", len(result.links.get("external", [])))  
            # Likely zero external links in this scenario
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 Example: Excluding Specific Domains

If you want to let external links in, but specifically exclude a domain (e.g., `suspiciousads.com`), do this:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_domains=["suspiciousads.com"]
)
```

This approach is handy when you still want external links but need to block certain sites you consider spammy.

---

## 3. Media Extraction

### 3.1 Accessing `result.media`

By default, Crawl4AI collects images, audio, and video URLs it finds on the page. These are stored in `result.media`, a dictionary keyed by media type (e.g., `images`, `videos`, `audio`).

**Basic Example**:

```python
if result.success:
    images_info = result.media.get("images", [])
    print(f"Found {len(images_info)} images in total.")
    for i, img in enumerate(images_info[:5]):  # Inspect just the first 5
        print(f"[Image {i}] URL: {img['src']}")
        print(f"           Alt text: {img.get('alt', '')}")
        print(f"           Score: {img.get('score')}")
        print(f"           Description: {img.get('desc', '')}\n")
```

**Structure Example**:

```python
result.media = {
  "images": [
    {
      "src": "https://cdn.prod.website-files.com/.../Group%2089.svg",
      "alt": "coding school for kids",
      "desc": "Trial Class Degrees degrees All Degrees AI Degree Technology ...",
      "score": 3,
      "type": "image",
      "group_id": 0,
      "format": None,
      "width": None,
      "height": None
    },
    # ...
  ],
  "videos": [
    # Similar structure but with video-specific fields
  ],
  "audio": [
    # Similar structure but with audio-specific fields
  ]
}
```

Depending on your Crawl4AI version or scraping strategy, these dictionaries can include fields like:

- **`src`**: The media URL (e.g., image source)  
- **`alt`**: The alt text for images (if present)  
- **`desc`**: A snippet of nearby text or a short description (optional)  
- **`score`**: A heuristic relevance score if you’re using content-scoring features  
- **`width`**, **`height`**: If the crawler detects dimensions for the image/video  
- **`type`**: Usually `"image"`, `"video"`, or `"audio"`  
- **`group_id`**: If you’re grouping related media items, the crawler might assign an ID  

With these details, you can easily filter out or focus on certain images (for instance, ignoring images with very low scores or a different domain), or gather metadata for analytics.

### 3.2 Excluding External Images

If you’re dealing with heavy pages or want to skip third-party images (advertisements, for example), you can turn on:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```

This setting attempts to discard images from outside the primary domain, keeping only those from the site you’re crawling.

### 3.3 Additional Media Config

- **`screenshot`**: Set to `True` if you want a full-page screenshot stored as `base64` in `result.screenshot`.  
- **`pdf`**: Set to `True` if you want a PDF version of the page in `result.pdf`.  
- **`wait_for_images`**: If `True`, attempts to wait until images are fully loaded before final extraction.

---

## 4. Putting It All Together: Link & Media Filtering

Here’s a combined example demonstrating how to filter out external links, skip certain domains, and exclude external images:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    # Suppose we want to keep only internal links, remove certain domains, 
    # and discard external images from the final crawl data.
    crawler_cfg = CrawlerRunConfig(
        exclude_external_links=True,
        exclude_domains=["spammyads.com"],
        exclude_social_media_links=True,   # skip Twitter, Facebook, etc.
        exclude_external_images=True,      # keep only images from main domain
        wait_for_images=True,             # ensure images are loaded
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://www.example.com", config=crawler_cfg)

        if result.success:
            print("[OK] Crawled:", result.url)
            
            # 1. Links
            in_links = result.links.get("internal", [])
            ext_links = result.links.get("external", [])
            print("Internal link count:", len(in_links))
            print("External link count:", len(ext_links))  # should be zero with exclude_external_links=True
            
            # 2. Images
            images = result.media.get("images", [])
            print("Images found:", len(images))
            
            # Let's see a snippet of these images
            for i, img in enumerate(images[:3]):
                print(f"  - {img['src']} (alt={img.get('alt','')}, score={img.get('score','N/A')})")
        else:
            print("[ERROR] Failed to crawl. Reason:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. Common Pitfalls & Tips

1. **Conflicting Flags**:  
   - `exclude_external_links=True` but then also specifying `exclude_social_media_links=True` is typically fine, but understand that the first setting already discards *all* external links. The second becomes somewhat redundant.  
   - `exclude_external_images=True` but want to keep some external images? Currently no partial domain-based setting for images, so you might need a custom approach or hook logic.

2. **Relevancy Scores**:  
   - If your version of Crawl4AI or your scraping strategy includes an `img["score"]`, it’s typically a heuristic based on size, position, or content analysis. Evaluate carefully if you rely on it.

3. **Performance**:  
   - Excluding certain domains or external images can speed up your crawl, especially for large, media-heavy pages.  
   - If you want a “full” link map, do *not* exclude them. Instead, you can post-filter in your own code.

4. **Social Media Lists**:  
   - `exclude_social_media_links=True` typically references an internal list of known social domains like Facebook, Twitter, LinkedIn, etc. If you need to add or remove from that list, look for library settings or a local config file (depending on your version).

---

**That’s it for Link & Media Analysis!** You’re now equipped to filter out unwanted sites and zero in on the images and videos that matter for your project.