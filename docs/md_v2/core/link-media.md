# Link & Media 

In this tutorial, you’ll learn how to:

1. Extract links (internal, external) from crawled pages  
2. Filter or exclude specific domains (e.g., social media or custom domains)  
3. Access and ma### 3.2 Excluding Images

#### Excluding External Images

If you're dealing with heavy pages or want to skip third-party images (advertisements, for example), you can turn on:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```

This setting attempts to discard images from outside the primary domain, keeping only those from the site you're crawling.

#### Excluding All Images

If you want to completely remove all images from the page to maximize performance and reduce memory usage, use:

```python
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

## 2. Advanced Link Head Extraction & Scoring

Ever wanted to not just extract links, but also get the actual content (title, description, metadata) from those linked pages? And score them for relevance? This is exactly what Link Head Extraction does - it fetches the `<head>` section from each discovered link and scores them using multiple algorithms.

### 2.1 Why Link Head Extraction?

When you crawl a page, you get hundreds of links. But which ones are actually valuable? Link Head Extraction solves this by:

1. **Fetching head content** from each link (title, description, meta tags)
2. **Scoring links intrinsically** based on URL quality, text relevance, and context
3. **Scoring links contextually** using BM25 algorithm when you provide a search query
4. **Combining scores intelligently** to give you a final relevance ranking

### 2.2 Complete Working Example

Here's a full example you can copy, paste, and run immediately:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import LinkPreviewConfig

async def extract_link_heads_example():
    """
    Complete example showing link head extraction with scoring.
    This will crawl a documentation site and extract head content from internal links.
    """
    
    # Configure link head extraction
    config = CrawlerRunConfig(
        # Enable link head extraction with detailed configuration
        link_preview_config=LinkPreviewConfig(
            include_internal=True,           # Extract from internal links
            include_external=False,          # Skip external links for this example
            max_links=10,                   # Limit to 10 links for demo
            concurrency=5,                  # Process 5 links simultaneously
            timeout=10,                     # 10 second timeout per link
            query="API documentation guide", # Query for contextual scoring
            score_threshold=0.3,            # Only include links scoring above 0.3
            verbose=True                    # Show detailed progress
        ),
        # Enable intrinsic scoring (URL quality, text relevance)
        score_links=True,
        # Keep output clean
        only_text=True,
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        # Crawl a documentation site (great for testing)
        result = await crawler.arun("https://docs.python.org/3/", config=config)
        
        if result.success:
            print(f"✅ Successfully crawled: {result.url}")
            print(f"📄 Page title: {result.metadata.get('title', 'No title')}")
            
            # Access links (now enhanced with head data and scores)
            internal_links = result.links.get("internal", [])
            external_links = result.links.get("external", [])
            
            print(f"\n🔗 Found {len(internal_links)} internal links")
            print(f"🌍 Found {len(external_links)} external links")
            
            # Count links with head data
            links_with_head = [link for link in internal_links 
                             if link.get("head_data") is not None]
            print(f"🧠 Links with head data extracted: {len(links_with_head)}")
            
            # Show the top 3 scoring links
            print(f"\n🏆 Top 3 Links with Full Scoring:")
            for i, link in enumerate(links_with_head[:3]):
                print(f"\n{i+1}. {link['href']}")
                print(f"   Link Text: '{link.get('text', 'No text')[:50]}...'")
                
                # Show all three score types
                intrinsic = link.get('intrinsic_score')
                contextual = link.get('contextual_score') 
                total = link.get('total_score')
                
                if intrinsic is not None:
                    print(f"   📊 Intrinsic Score: {intrinsic:.2f}/10.0 (URL quality & context)")
                if contextual is not None:
                    print(f"   🎯 Contextual Score: {contextual:.3f} (BM25 relevance to query)")
                if total is not None:
                    print(f"   ⭐ Total Score: {total:.3f} (combined final score)")
                
                # Show extracted head data
                head_data = link.get("head_data", {})
                if head_data:
                    title = head_data.get("title", "No title")
                    description = head_data.get("meta", {}).get("description", "No description")
                    
                    print(f"   📰 Title: {title[:60]}...")
                    if description:
                        print(f"   📝 Description: {description[:80]}...")
                    
                    # Show extraction status
                    status = link.get("head_extraction_status", "unknown")
                    print(f"   ✅ Extraction Status: {status}")
        else:
            print(f"❌ Crawl failed: {result.error_message}")

# Run the example
if __name__ == "__main__":
    asyncio.run(extract_link_heads_example())
```

**Expected Output:**
```
✅ Successfully crawled: https://docs.python.org/3/
📄 Page title: 3.13.5 Documentation
🔗 Found 53 internal links
🌍 Found 1 external links
🧠 Links with head data extracted: 10

🏆 Top 3 Links with Full Scoring:

1. https://docs.python.org/3.15/
   Link Text: 'Python 3.15 (in development)...'
   📊 Intrinsic Score: 4.17/10.0 (URL quality & context)
   🎯 Contextual Score: 1.000 (BM25 relevance to query)
   ⭐ Total Score: 5.917 (combined final score)
   📰 Title: 3.15.0a0 Documentation...
   📝 Description: The official Python documentation...
   ✅ Extraction Status: valid
```

### 2.3 Configuration Deep Dive

The `LinkPreviewConfig` class supports these options:

```python
from crawl4ai import LinkPreviewConfig

link_preview_config = LinkPreviewConfig(
    # BASIC SETTINGS
    verbose=True,                    # Show detailed logs (recommended for learning)
    
    # LINK FILTERING
    include_internal=True,           # Include same-domain links
    include_external=True,           # Include different-domain links
    max_links=50,                   # Maximum links to process (prevents overload)
    
    # PATTERN FILTERING
    include_patterns=[               # Only process links matching these patterns
        "*/docs/*", 
        "*/api/*", 
        "*/reference/*"
    ],
    exclude_patterns=[               # Skip links matching these patterns
        "*/login*",
        "*/admin*"
    ],
    
    # PERFORMANCE SETTINGS
    concurrency=10,                  # How many links to process simultaneously
    timeout=5,                      # Seconds to wait per link
    
    # RELEVANCE SCORING
    query="machine learning API",    # Query for BM25 contextual scoring
    score_threshold=0.3,            # Only include links above this score
)
```

### 2.4 Understanding the Three Score Types

Each extracted link gets three different scores:

#### 1. **Intrinsic Score (0-10)** - URL and Content Quality
Based on URL structure, link text quality, and page context:

```python
# High intrinsic score indicators:
# ✅ Clean URL structure (docs.python.org/api/reference)
# ✅ Meaningful link text ("API Reference Guide")
# ✅ Relevant to page context
# ✅ Not buried deep in navigation

# Low intrinsic score indicators:
# ❌ Random URLs (site.com/x7f9g2h)
# ❌ No link text or generic text ("Click here")
# ❌ Unrelated to page content
```

#### 2. **Contextual Score (0-1)** - BM25 Relevance to Query
Only available when you provide a `query`. Uses BM25 algorithm against head content:

```python
# Example: query = "machine learning tutorial"
# High contextual score: Link to "Complete Machine Learning Guide"
# Low contextual score: Link to "Privacy Policy"
```

#### 3. **Total Score** - Smart Combination
Intelligently combines intrinsic and contextual scores with fallbacks:

```python
# When both scores available: (intrinsic * 0.3) + (contextual * 0.7)
# When only intrinsic: uses intrinsic score
# When only contextual: uses contextual score
# When neither: not calculated
```

### 2.5 Practical Use Cases

#### Use Case 1: Research Assistant
Find the most relevant documentation pages:

```python
async def research_assistant():
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_external=True,
            include_patterns=["*/docs/*", "*/tutorial/*", "*/guide/*"],
            query="machine learning neural networks",
            max_links=20,
            score_threshold=0.5,  # Only high-relevance links
            verbose=True
        ),
        score_links=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://scikit-learn.org/", config=config)
        
        if result.success:
            # Get high-scoring links
            good_links = [link for link in result.links.get("internal", [])
                         if link.get("total_score", 0) > 0.7]
            
            print(f"🎯 Found {len(good_links)} highly relevant links:")
            for link in good_links[:5]:
                print(f"⭐ {link['total_score']:.3f} - {link['href']}")
                print(f"   {link.get('head_data', {}).get('title', 'No title')}")
```

#### Use Case 2: Content Discovery
Find all API endpoints and references:

```python
async def api_discovery():
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_patterns=["*/api/*", "*/reference/*"],
            exclude_patterns=["*/deprecated/*"],
            max_links=100,
            concurrency=15,
            verbose=False  # Clean output
        ),
        score_links=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://docs.example-api.com/", config=config)
        
        if result.success:
            api_links = result.links.get("internal", [])
            
            # Group by endpoint type
            endpoints = {}
            for link in api_links:
                if link.get("head_data"):
                    title = link["head_data"].get("title", "")
                    if "GET" in title:
                        endpoints.setdefault("GET", []).append(link)
                    elif "POST" in title:
                        endpoints.setdefault("POST", []).append(link)
            
            for method, links in endpoints.items():
                print(f"\n{method} Endpoints ({len(links)}):")
                for link in links[:3]:
                    print(f"  • {link['href']}")
```

#### Use Case 3: Link Quality Analysis
Analyze website structure and content quality:

```python
async def quality_analysis():
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            max_links=200,
            concurrency=20,
        ),
        score_links=True
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://your-website.com/", config=config)
        
        if result.success:
            links = result.links.get("internal", [])
            
            # Analyze intrinsic scores
            scores = [link.get('intrinsic_score', 0) for link in links]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            print(f"📊 Link Quality Analysis:")
            print(f"   Average intrinsic score: {avg_score:.2f}/10.0")
            print(f"   High quality links (>7.0): {len([s for s in scores if s > 7.0])}")
            print(f"   Low quality links (<3.0): {len([s for s in scores if s < 3.0])}")
            
            # Find problematic links
            bad_links = [link for link in links 
                        if link.get('intrinsic_score', 0) < 2.0]
            
            if bad_links:
                print(f"\n⚠️  Links needing attention:")
                for link in bad_links[:5]:
                    print(f"   {link['href']} (score: {link.get('intrinsic_score', 0):.1f})")
```

### 2.6 Performance Tips

1. **Start Small**: Begin with `max_links: 10` to understand the feature
2. **Use Patterns**: Filter with `include_patterns` to focus on relevant sections
3. **Adjust Concurrency**: Higher concurrency = faster but more resource usage
4. **Set Timeouts**: Use `timeout: 5` to prevent hanging on slow sites
5. **Use Score Thresholds**: Filter out low-quality links with `score_threshold`

### 2.7 Troubleshooting

**No head data extracted?**
```python
# Check your configuration:
config = CrawlerRunConfig(
    link_preview_config=LinkPreviewConfig(
        verbose=True   # ← Enable to see what's happening
    )
)
```

**Scores showing as None?**
```python
# Make sure scoring is enabled:
config = CrawlerRunConfig(
    score_links=True,  # ← Enable intrinsic scoring
    link_preview_config=LinkPreviewConfig(
        query="your search terms"  # ← For contextual scoring
    )
)
```

**Process taking too long?**
```python
# Optimize performance:
link_preview_config = LinkPreviewConfig(
    max_links=20,      # ← Reduce number
    concurrency=10,    # ← Increase parallelism
    timeout=3,         # ← Shorter timeout
    include_patterns=["*/important/*"]  # ← Focus on key areas
)
```

---

## 3. Domain Filtering

Some websites contain hundreds of third-party or affiliate links. You can filter out certain domains at **crawl time** by configuring the crawler. The most relevant parameters in `CrawlerRunConfig` are:

- **`exclude_external_links`**: If `True`, discard any link pointing outside the root domain.  
- **`exclude_social_media_domains`**: Provide a list of social media platforms (e.g., `["facebook.com", "twitter.com"]`) to exclude from your crawl.  
- **`exclude_social_media_links`**: If `True`, automatically skip known social platforms.  
- **`exclude_domains`**: Provide a list of custom domains you want to exclude (e.g., `["spammyads.com", "tracker.net"]`).

### 3.1 Example: Excluding External & Social Media Links

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

### 3.2 Example: Excluding Specific Domains

If you want to let external links in, but specifically exclude a domain (e.g., `suspiciousads.com`), do this:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_domains=["suspiciousads.com"]
)
```

This approach is handy when you still want external links but need to block certain sites you consider spammy.

---

## 4. Media Extraction

### 4.1 Accessing `result.media`

By default, Crawl4AI collects images, audio and video URLs it finds on the page. These are stored in `result.media`, a dictionary keyed by media type (e.g., `images`, `videos`, `audio`).
**Note: Tables have been moved from `result.media["tables"]` to the new `result.tables` format for better organization and direct access.**

**Basic Example**:

```python
if result.success:
    # Get images
    images_info = result.media.get("images", [])
    print(f"Found {len(images_info)} images in total.")
    for i, img in enumerate(images_info[:3]):  # Inspect just the first 3
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
  ],
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

### 4.2 Excluding External Images

If you’re dealing with heavy pages or want to skip third-party images (advertisements, for example), you can turn on:

```python
crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
```

This setting attempts to discard images from outside the primary domain, keeping only those from the site you’re crawling.

### 4.3 Additional Media Config

- **`screenshot`**: Set to `True` if you want a full-page screenshot stored as `base64` in `result.screenshot`.  
- **`pdf`**: Set to `True` if you want a PDF version of the page in `result.pdf`.  
- **`capture_mhtml`**: Set to `True` if you want an MHTML snapshot of the page in `result.mhtml`. This format preserves the entire web page with all its resources (CSS, images, scripts) in a single file, making it perfect for archiving or offline viewing.
- **`wait_for_images`**: If `True`, attempts to wait until images are fully loaded before final extraction.

#### Example: Capturing Page as MHTML

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    crawler_cfg = CrawlerRunConfig(
        capture_mhtml=True  # Enable MHTML capture
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=crawler_cfg)
        
        if result.success and result.mhtml:
            # Save the MHTML snapshot to a file
            with open("example.mhtml", "w", encoding="utf-8") as f:
                f.write(result.mhtml)
            print("MHTML snapshot saved to example.mhtml")
        else:
            print("Failed to capture MHTML:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

The MHTML format is particularly useful because:
- It captures the complete page state including all resources
- It can be opened in most modern browsers for offline viewing
- It preserves the page exactly as it appeared during crawling
- It's a single file, making it easy to store and transfer

---

## 5. Putting It All Together: Link & Media Filtering

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

## 6. Common Pitfalls & Tips

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
