[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/core/url-seeding/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * URL Seeding
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [URL Seeding: The Smart Way to Crawl at Scale](https://docs.crawl4ai.com/core/url-seeding/#url-seeding-the-smart-way-to-crawl-at-scale)
  * [Why URL Seeding?](https://docs.crawl4ai.com/core/url-seeding/#why-url-seeding)
  * [Your First URL Seeding Adventure](https://docs.crawl4ai.com/core/url-seeding/#your-first-url-seeding-adventure)
  * [Understanding the URL Seeder](https://docs.crawl4ai.com/core/url-seeding/#understanding-the-url-seeder)
  * [Smart Filtering with BM25 Scoring](https://docs.crawl4ai.com/core/url-seeding/#smart-filtering-with-bm25-scoring)
  * [Scaling Up: Multiple Domains](https://docs.crawl4ai.com/core/url-seeding/#scaling-up-multiple-domains)
  * [Advanced Integration Patterns](https://docs.crawl4ai.com/core/url-seeding/#advanced-integration-patterns)
  * [Best Practices & Tips](https://docs.crawl4ai.com/core/url-seeding/#best-practices-tips)
  * [Quick Reference](https://docs.crawl4ai.com/core/url-seeding/#quick-reference)
  * [Conclusion](https://docs.crawl4ai.com/core/url-seeding/#conclusion)


# URL Seeding: The Smart Way to Crawl at Scale
## Why URL Seeding?
Web crawling comes in different flavors, each with its own strengths. Let's understand when to use URL seeding versus deep crawling.
### Deep Crawling: Real-Time Discovery
Deep crawling is perfect when you need: - **Fresh, real-time data** - discovering pages as they're created - **Dynamic exploration** - following links based on content - **Selective extraction** - stopping when you find what you need
```
# Deep crawling example: Explore a website dynamically
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

async def deep_crawl_example():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,           # Crawl 2 levels deep
            include_external=False, # Stay within domain
            max_pages=50           # Limit for efficiency
        ),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        # Start crawling and follow links dynamically
        results = await crawler.arun("https://example.com", config=config)

        print(f"Discovered and crawled {len(results)} pages")
        for result in results[:3]:
            print(f"Found: {result.url} at depth {result.metadata.get('depth', 0)}")

asyncio.run(deep_crawl_example())
Copy
```

### URL Seeding: Bulk Discovery
URL seeding shines when you want: - **Comprehensive coverage** - get thousands of URLs in seconds - **Bulk processing** - filter before crawling - **Resource efficiency** - know exactly what you'll crawl
```
# URL seeding example: Analyze all documentation
from crawl4ai import AsyncUrlSeeder, SeedingConfig

seeder = AsyncUrlSeeder()
config = SeedingConfig(
    source="sitemap",
    extract_head=True,
    pattern="*/docs/*"
)

# Get ALL documentation URLs instantly
urls = await seeder.urls("example.com", config)
# 1000+ URLs discovered in seconds!
Copy
```

### The Trade-offs
Aspect | Deep Crawling | URL Seeding
---|---|---
**Coverage** | Discovers pages dynamically | Gets most existing URLs instantly
**Freshness** | Finds brand new pages | May miss very recent pages
**Speed** | Slower, page by page | Extremely fast bulk discovery
**Resource Usage** | Higher - crawls to discover | Lower - discovers then crawls
**Control** | Can stop mid-process | Pre-filters before crawling
### When to Use Each
**Choose Deep Crawling when:** - You need the absolute latest content - You're searching for specific information - The site structure is unknown or dynamic - You want to stop as soon as you find what you need
**Choose URL Seeding when:** - You need to analyze large portions of a site - You want to filter URLs before crawling - You're doing comparative analysis - You need to optimize resource usage
The magic happens when you understand both approaches and choose the right tool for your task. Sometimes, you might even combine them - use URL seeding for bulk discovery, then deep crawl specific sections for the latest updates.
## Your First URL Seeding Adventure
Let's see the magic in action. We'll discover blog posts about Python, filter for tutorials, and crawl only those pages.
```
import asyncio
from crawl4ai import AsyncUrlSeeder, AsyncWebCrawler, SeedingConfig, CrawlerRunConfig

async def smart_blog_crawler():
    # Step 1: Create our URL discoverer
    seeder = AsyncUrlSeeder()

    # Step 2: Configure discovery - let's find all blog posts
    config = SeedingConfig(
        source="sitemap",           # Use the website's sitemap
        pattern="*/blog/*.html",    # Only blog posts
        extract_head=True,          # Get page metadata
        max_urls=100               # Limit for this example
    )

    # Step 3: Discover URLs from the Python blog
    print("🔍 Discovering blog posts...")
    urls = await seeder.urls("realpython.com", config)
    print(f"✅ Found {len(urls)} blog posts")

    # Step 4: Filter for Python tutorials (using metadata!)
    tutorials = [
        url for url in urls
        if url["status"] == "valid" and
        any(keyword in str(url["head_data"]).lower()
            for keyword in ["tutorial", "guide", "how to"])
    ]
    print(f"📚 Filtered to {len(tutorials)} tutorials")

    # Step 5: Show what we found
    print("\n🎯 Found these tutorials:")
    for tutorial in tutorials[:5]:  # First 5
        title = tutorial["head_data"].get("title", "No title")
        print(f"  - {title}")
        print(f"    {tutorial['url']}")

    # Step 6: Now crawl ONLY these relevant pages
    print("\n🚀 Crawling tutorials...")
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            only_text=True,
            word_count_threshold=300  # Only substantial articles
        )

        # Extract URLs and crawl them
        tutorial_urls = [t["url"] for t in tutorials[:10]]
        results = await crawler.arun_many(tutorial_urls, config=config)

        successful = 0
        async for result in results:
            if result.success:
                successful += 1
                print(f"✓ Crawled: {result.url[:60]}...")

        print(f"\n✨ Successfully crawled {successful} tutorials!")

# Run it!
asyncio.run(smart_blog_crawler())
Copy
```

**What just happened?**
  1. We discovered all blog URLs from the sitemap
  2. We filtered using metadata (no crawling needed!)
  3. We crawled only the relevant tutorials
  4. We saved tons of time and bandwidth


This is the power of URL seeding - you see everything before you crawl anything.
## Understanding the URL Seeder
Now that you've seen the magic, let's understand how it works.
### Basic Usage
Creating a URL seeder is simple:
```
from crawl4ai import AsyncUrlSeeder

# Method 1: Manual cleanup
seeder = AsyncUrlSeeder()
try:
    config = SeedingConfig(source="sitemap")
    urls = await seeder.urls("example.com", config)
finally:
    await seeder.close()

# Method 2: Context manager (recommended)
async with AsyncUrlSeeder() as seeder:
    config = SeedingConfig(source="sitemap")
    urls = await seeder.urls("example.com", config)
    # Automatically cleaned up on exit
Copy
```

The seeder can discover URLs from two powerful sources:
#### 1. Sitemaps (Fastest)
```
# Discover from sitemap
config = SeedingConfig(source="sitemap")
urls = await seeder.urls("example.com", config)
Copy
```

Sitemaps are XML files that websites create specifically to list all their URLs. It's like getting a menu at a restaurant - everything is listed upfront.
**Sitemap Index Support** : For large websites like TechCrunch that use sitemap indexes (a sitemap of sitemaps), the seeder automatically detects and processes all sub-sitemaps in parallel:
```
<!-- Example sitemap index -->
<sitemapindex>
  <sitemap>
    <loc>https://techcrunch.com/sitemap-1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://techcrunch.com/sitemap-2.xml</loc>
  </sitemap>
  <!-- ... more sitemaps ... -->
</sitemapindex>
Copy
```

The seeder handles this transparently - you'll get all URLs from all sub-sitemaps automatically!
#### 2. Common Crawl (Most Comprehensive)
```
# Discover from Common Crawl
config = SeedingConfig(source="cc")
urls = await seeder.urls("example.com", config)
Copy
```

Common Crawl is a massive public dataset that regularly crawls the entire web. It's like having access to a pre-built index of the internet.
#### 3. Both Sources (Maximum Coverage)
```
# Use both sources
config = SeedingConfig(source="sitemap+cc")
urls = await seeder.urls("example.com", config)
Copy
```

### Configuration Magic: SeedingConfig
The `SeedingConfig` object is your control panel. Here's everything you can configure:
Parameter | Type | Default | Description
---|---|---|---
`source` | str | "sitemap+cc" | URL source: "cc" (Common Crawl), "sitemap", or "sitemap+cc"
`pattern` | str | "*" | URL pattern filter (e.g., "_/blog/_ ", "*.html")
`extract_head` | bool | False | Extract metadata from page `<head>`
`live_check` | bool | False | Verify URLs are accessible
`max_urls` | int | -1 | Maximum URLs to return (-1 = unlimited)
`concurrency` | int | 10 | Parallel workers for fetching
`hits_per_sec` | int | 5 | Rate limit for requests
`force` | bool | False | Bypass cache, fetch fresh data
`verbose` | bool | False | Show detailed progress
`query` | str | None | Search query for BM25 scoring
`scoring_method` | str | None | Scoring method (currently "bm25")
`score_threshold` | float | None | Minimum score to include URL
`filter_nonsense_urls` | bool | True | Filter out utility URLs (robots.txt, etc.)
#### Pattern Matching Examples
```
# Match all blog posts
config = SeedingConfig(pattern="*/blog/*")

# Match only HTML files
config = SeedingConfig(pattern="*.html")

# Match product pages
config = SeedingConfig(pattern="*/product/*")

# Match everything except admin pages
config = SeedingConfig(pattern="*")
# Then filter: urls = [u for u in urls if "/admin/" not in u["url"]]
Copy
```

### URL Validation: Live Checking
Sometimes you need to know if URLs are actually accessible. That's where live checking comes in:
```
config = SeedingConfig(
    source="sitemap",
    live_check=True,  # Verify each URL is accessible
    concurrency=20    # Check 20 URLs in parallel
)

urls = await seeder.urls("example.com", config)

# Now you can filter by status
live_urls = [u for u in urls if u["status"] == "valid"]
dead_urls = [u for u in urls if u["status"] == "not_valid"]

print(f"Live URLs: {len(live_urls)}")
print(f"Dead URLs: {len(dead_urls)}")
Copy
```

**When to use live checking:** - Before a large crawling operation - When working with older sitemaps - When data freshness is critical
**When to skip it:** - Quick explorations - When you trust the source - When speed is more important than accuracy
### The Power of Metadata: Head Extraction
This is where URL seeding gets really powerful. Instead of crawling entire pages, you can extract just the metadata:
```
config = SeedingConfig(
    extract_head=True  # Extract metadata from <head> section
)

urls = await seeder.urls("example.com", config)

# Now each URL has rich metadata
for url in urls[:3]:
    print(f"\nURL: {url['url']}")
    print(f"Title: {url['head_data'].get('title')}")

    meta = url['head_data'].get('meta', {})
    print(f"Description: {meta.get('description')}")
    print(f"Keywords: {meta.get('keywords')}")

    # Even Open Graph data!
    print(f"OG Image: {meta.get('og:image')}")
Copy
```

#### What Can We Extract?
The head extraction gives you a treasure trove of information:
```
# Example of extracted head_data
{
    "title": "10 Python Tips for Beginners",
    "charset": "utf-8",
    "lang": "en",
    "meta": {
        "description": "Learn essential Python tips...",
        "keywords": "python, programming, tutorial",
        "author": "Jane Developer",
        "viewport": "width=device-width, initial-scale=1",

        # Open Graph tags
        "og:title": "10 Python Tips for Beginners",
        "og:description": "Essential Python tips for new programmers",
        "og:image": "https://example.com/python-tips.jpg",
        "og:type": "article",

        # Twitter Card tags
        "twitter:card": "summary_large_image",
        "twitter:title": "10 Python Tips",

        # Dublin Core metadata
        "dc.creator": "Jane Developer",
        "dc.date": "2024-01-15"
    },
    "link": {
        "canonical": [{"href": "https://example.com/blog/python-tips"}],
        "alternate": [{"href": "/feed.xml", "type": "application/rss+xml"}]
    },
    "jsonld": [
        {
            "@type": "Article",
            "headline": "10 Python Tips for Beginners",
            "datePublished": "2024-01-15",
            "author": {"@type": "Person", "name": "Jane Developer"}
        }
    ]
}
Copy
```

This metadata is gold for filtering! You can find exactly what you need without crawling a single page.
### Smart URL-Based Filtering (No Head Extraction)
When `extract_head=False` but you still provide a query, the seeder uses intelligent URL-based scoring:
```
# Fast filtering based on URL structure alone
config = SeedingConfig(
    source="sitemap",
    extract_head=False,  # Don't fetch page metadata
    query="python tutorial async",
    scoring_method="bm25",
    score_threshold=0.3
)

urls = await seeder.urls("example.com", config)

# URLs are scored based on:
# 1. Domain parts matching (e.g., 'python' in python.example.com)
# 2. Path segments (e.g., '/tutorials/python-async/')
# 3. Query parameters (e.g., '?topic=python')
# 4. Fuzzy matching using character n-grams

# Example URL scoring:
# https://example.com/tutorials/python/async-guide.html - High score
# https://example.com/blog/javascript-tips.html - Low score
Copy
```

This approach is much faster than head extraction while still providing intelligent filtering!
### Understanding Results
Each URL in the results has this structure:
```
{
    "url": "https://example.com/blog/python-tips.html",
    "status": "valid",        # "valid", "not_valid", or "unknown"
    "head_data": {            # Only if extract_head=True
        "title": "Page Title",
        "meta": {...},
        "link": {...},
        "jsonld": [...]
    },
    "relevance_score": 0.85   # Only if using BM25 scoring
}
Copy
```

Let's see a real example:
```
config = SeedingConfig(
    source="sitemap",
    extract_head=True,
    live_check=True
)

urls = await seeder.urls("blog.example.com", config)

# Analyze the results
for url in urls[:5]:
    print(f"\n{'='*60}")
    print(f"URL: {url['url']}")
    print(f"Status: {url['status']}")

    if url['head_data']:
        data = url['head_data']
        print(f"Title: {data.get('title', 'No title')}")

        # Check content type
        meta = data.get('meta', {})
        content_type = meta.get('og:type', 'unknown')
        print(f"Content Type: {content_type}")

        # Publication date
        pub_date = None
        for jsonld in data.get('jsonld', []):
            if isinstance(jsonld, dict):
                pub_date = jsonld.get('datePublished')
                if pub_date:
                    break

        if pub_date:
            print(f"Published: {pub_date}")

        # Word count (if available)
        word_count = meta.get('word_count')
        if word_count:
            print(f"Word Count: {word_count}")
Copy
```

## Smart Filtering with BM25 Scoring
Now for the really cool part - intelligent filtering based on relevance!
### Introduction to Relevance Scoring
BM25 is a ranking algorithm that scores how relevant a document is to a search query. With URL seeding, we can score URLs based on their metadata _before_ crawling them.
Think of it like this: - Traditional way: Read every book in the library to find ones about Python - Smart way: Check the titles and descriptions, score them, read only the most relevant
### Query-Based Discovery
Here's how to use BM25 scoring:
```
config = SeedingConfig(
    source="sitemap",
    extract_head=True,           # Required for scoring
    query="python async tutorial",  # What we're looking for
    scoring_method="bm25",       # Use BM25 algorithm
    score_threshold=0.3          # Minimum relevance score
)

urls = await seeder.urls("realpython.com", config)

# Results are automatically sorted by relevance!
for url in urls[:5]:
    print(f"Score: {url['relevance_score']:.2f} - {url['url']}")
    print(f"  Title: {url['head_data']['title']}")
Copy
```

### Real Examples
#### Finding Documentation Pages
```
# Find API documentation
config = SeedingConfig(
    source="sitemap",
    extract_head=True,
    query="API reference documentation endpoints",
    scoring_method="bm25",
    score_threshold=0.5,
    max_urls=20
)

urls = await seeder.urls("docs.example.com", config)

# The highest scoring URLs will be API docs!
Copy
```

#### Discovering Product Pages
```
# Find specific products
config = SeedingConfig(
    source="sitemap+cc",  # Use both sources
    extract_head=True,
    query="wireless headphones noise canceling",
    scoring_method="bm25",
    score_threshold=0.4,
    pattern="*/product/*"  # Combine with pattern matching
)

urls = await seeder.urls("shop.example.com", config)

# Filter further by price (from metadata)
affordable = [
    u for u in urls
    if float(u['head_data'].get('meta', {}).get('product:price', '0')) < 200
]
Copy
```

#### Filtering News Articles
```
# Find recent news about AI
config = SeedingConfig(
    source="sitemap",
    extract_head=True,
    query="artificial intelligence machine learning breakthrough",
    scoring_method="bm25",
    score_threshold=0.35
)

urls = await seeder.urls("technews.com", config)

# Filter by date
from datetime import datetime, timedelta

recent = []
cutoff = datetime.now() - timedelta(days=7)

for url in urls:
    # Check JSON-LD for publication date
    for jsonld in url['head_data'].get('jsonld', []):
        if 'datePublished' in jsonld:
            pub_date = datetime.fromisoformat(jsonld['datePublished'].replace('Z', '+00:00'))
            if pub_date > cutoff:
                recent.append(url)
                break
Copy
```

#### Complex Query Patterns
```
# Multi-concept queries
queries = [
    "python async await concurrency tutorial",
    "data science pandas numpy visualization",
    "web scraping beautifulsoup selenium automation",
    "machine learning tensorflow keras deep learning"
]

all_tutorials = []

for query in queries:
    config = SeedingConfig(
        source="sitemap",
        extract_head=True,
        query=query,
        scoring_method="bm25",
        score_threshold=0.4,
        max_urls=10  # Top 10 per topic
    )

    urls = await seeder.urls("learning-platform.com", config)
    all_tutorials.extend(urls)

# Remove duplicates while preserving order
seen = set()
unique_tutorials = []
for url in all_tutorials:
    if url['url'] not in seen:
        seen.add(url['url'])
        unique_tutorials.append(url)

print(f"Found {len(unique_tutorials)} unique tutorials across all topics")
Copy
```

## Scaling Up: Multiple Domains
When you need to discover URLs across multiple websites, URL seeding really shines.
### The `many_urls` Method
```
# Discover URLs from multiple domains in parallel
domains = ["site1.com", "site2.com", "site3.com"]

config = SeedingConfig(
    source="sitemap",
    extract_head=True,
    query="python tutorial",
    scoring_method="bm25",
    score_threshold=0.3
)

# Returns a dictionary: {domain: [urls]}
results = await seeder.many_urls(domains, config)

# Process results
for domain, urls in results.items():
    print(f"\n{domain}: Found {len(urls)} relevant URLs")
    if urls:
        top = urls[0]  # Highest scoring
        print(f"  Top result: {top['url']}")
        print(f"  Score: {top['relevance_score']:.2f}")
Copy
```

### Cross-Domain Examples
#### Competitor Analysis
```
# Analyze content strategies across competitors
competitors = [
    "competitor1.com",
    "competitor2.com",
    "competitor3.com"
]

config = SeedingConfig(
    source="sitemap",
    extract_head=True,
    pattern="*/blog/*",
    max_urls=100
)

results = await seeder.many_urls(competitors, config)

# Analyze content types
for domain, urls in results.items():
    content_types = {}

    for url in urls:
        # Extract content type from metadata
        og_type = url['head_data'].get('meta', {}).get('og:type', 'unknown')
        content_types[og_type] = content_types.get(og_type, 0) + 1

    print(f"\n{domain} content distribution:")
    for ctype, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ctype}: {count}")
Copy
```

#### Industry Research
```
# Research Python tutorials across educational sites
educational_sites = [
    "realpython.com",
    "pythontutorial.net",
    "learnpython.org",
    "python.org"
]

config = SeedingConfig(
    source="sitemap",
    extract_head=True,
    query="beginner python tutorial basics",
    scoring_method="bm25",
    score_threshold=0.3,
    max_urls=20  # Per site
)

results = await seeder.many_urls(educational_sites, config)

# Find the best beginner tutorials
all_tutorials = []
for domain, urls in results.items():
    for url in urls:
        url['domain'] = domain  # Add domain info
        all_tutorials.append(url)

# Sort by relevance across all domains
all_tutorials.sort(key=lambda x: x['relevance_score'], reverse=True)

print("Top 10 Python tutorials for beginners across all sites:")
for i, tutorial in enumerate(all_tutorials[:10], 1):
    print(f"{i}. [{tutorial['relevance_score']:.2f}] {tutorial['head_data']['title']}")
    print(f"   {tutorial['url']}")
    print(f"   From: {tutorial['domain']}")
Copy
```

#### Multi-Site Monitoring
```
# Monitor news about your company across multiple sources
news_sites = [
    "techcrunch.com",
    "theverge.com",
    "wired.com",
    "arstechnica.com"
]

company_name = "YourCompany"

config = SeedingConfig(
    source="cc",  # Common Crawl for recent content
    extract_head=True,
    query=f"{company_name} announcement news",
    scoring_method="bm25",
    score_threshold=0.5,  # High threshold for relevance
    max_urls=10
)

results = await seeder.many_urls(news_sites, config)

# Collect all mentions
mentions = []
for domain, urls in results.items():
    mentions.extend(urls)

if mentions:
    print(f"Found {len(mentions)} mentions of {company_name}:")
    for mention in mentions:
        print(f"\n- {mention['head_data']['title']}")
        print(f"  {mention['url']}")
        print(f"  Score: {mention['relevance_score']:.2f}")
else:
    print(f"No recent mentions of {company_name} found")
Copy
```

## Advanced Integration Patterns
Let's put everything together in a real-world example.
### Building a Research Assistant
Here's a complete example that discovers, scores, filters, and crawls intelligently:
```
import asyncio
from datetime import datetime
from crawl4ai import AsyncUrlSeeder, AsyncWebCrawler, SeedingConfig, CrawlerRunConfig

class ResearchAssistant:
    def __init__(self):
        self.seeder = None

    async def __aenter__(self):
        self.seeder = AsyncUrlSeeder()
        await self.seeder.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.seeder:
            await self.seeder.__aexit__(exc_type, exc_val, exc_tb)

    async def research_topic(self, topic, domains, max_articles=20):
        """Research a topic across multiple domains."""

        print(f"🔬 Researching '{topic}' across {len(domains)} domains...")

        # Step 1: Discover relevant URLs
        config = SeedingConfig(
            source="sitemap+cc",     # Maximum coverage
            extract_head=True,       # Get metadata
            query=topic,             # Research topic
            scoring_method="bm25",   # Smart scoring
            score_threshold=0.4,     # Quality threshold
            max_urls=10,             # Per domain
            concurrency=20,          # Fast discovery
            verbose=True
        )

        # Discover across all domains
        discoveries = await self.seeder.many_urls(domains, config)

        # Step 2: Collect and rank all articles
        all_articles = []
        for domain, urls in discoveries.items():
            for url in urls:
                url['domain'] = domain
                all_articles.append(url)

        # Sort by relevance
        all_articles.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Take top articles
        top_articles = all_articles[:max_articles]

        print(f"\n📊 Found {len(all_articles)} relevant articles")
        print(f"📌 Selected top {len(top_articles)} for deep analysis")

        # Step 3: Show what we're about to crawl
        print("\n🎯 Articles to analyze:")
        for i, article in enumerate(top_articles[:5], 1):
            print(f"\n{i}. {article['head_data']['title']}")
            print(f"   Score: {article['relevance_score']:.2f}")
            print(f"   Source: {article['domain']}")
            print(f"   URL: {article['url'][:60]}...")

        # Step 4: Crawl the selected articles
        print(f"\n🚀 Deep crawling {len(top_articles)} articles...")

        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                only_text=True,
                word_count_threshold=200,  # Substantial content only
                stream=True
            )

            # Extract URLs and crawl all articles
            article_urls = [article['url'] for article in top_articles]
            results = []
            crawl_results = await crawler.arun_many(article_urls, config=config)
            async for result in crawl_results:
                if result.success:
                    results.append({
                        'url': result.url,
                        'title': result.metadata.get('title', 'No title'),
                        'content': result.markdown.raw_markdown,
                        'domain': next(a['domain'] for a in top_articles if a['url'] == result.url),
                        'score': next(a['relevance_score'] for a in top_articles if a['url'] == result.url)
                    })
                    print(f"✓ Crawled: {result.url[:60]}...")

        # Step 5: Analyze and summarize
        print(f"\n📝 Analysis complete! Crawled {len(results)} articles")

        return self.create_research_summary(topic, results)

    def create_research_summary(self, topic, articles):
        """Create a research summary from crawled articles."""

        summary = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(articles),
            'sources': {}
        }

        # Group by domain
        for article in articles:
            domain = article['domain']
            if domain not in summary['sources']:
                summary['sources'][domain] = []

            summary['sources'][domain].append({
                'title': article['title'],
                'url': article['url'],
                'score': article['score'],
                'excerpt': article['content'][:500] + '...' if len(article['content']) > 500 else article['content']
            })

        return summary

# Use the research assistant
async def main():
    async with ResearchAssistant() as assistant:
        # Research Python async programming across multiple sources
        topic = "python asyncio best practices performance optimization"
        domains = [
            "realpython.com",
            "python.org",
            "stackoverflow.com",
            "medium.com"
        ]

        summary = await assistant.research_topic(topic, domains, max_articles=15)

    # Display results
    print("\n" + "="*60)
    print("RESEARCH SUMMARY")
    print("="*60)
    print(f"Topic: {summary['topic']}")
    print(f"Date: {summary['timestamp']}")
    print(f"Total Articles Analyzed: {summary['total_articles']}")

    print("\nKey Findings by Source:")
    for domain, articles in summary['sources'].items():
        print(f"\n📚 {domain} ({len(articles)} articles)")
        for article in articles[:2]:  # Top 2 per domain
            print(f"\n  Title: {article['title']}")
            print(f"  Relevance: {article['score']:.2f}")
            print(f"  Preview: {article['excerpt'][:200]}...")

asyncio.run(main())
Copy
```

### Performance Optimization Tips
  1. **Use caching wisely**
```
# First run - populate cache
config = SeedingConfig(source="sitemap", extract_head=True, force=True)
urls = await seeder.urls("example.com", config)

# Subsequent runs - use cache (much faster)
config = SeedingConfig(source="sitemap", extract_head=True, force=False)
urls = await seeder.urls("example.com", config)
Copy
```

  2. **Optimize concurrency**
```
# For many small requests (like HEAD checks)
config = SeedingConfig(concurrency=50, hits_per_sec=20)

# For fewer large requests (like full head extraction)
config = SeedingConfig(concurrency=10, hits_per_sec=5)
Copy
```

  3. **Stream large result sets**
```
# When crawling many URLs
async with AsyncWebCrawler() as crawler:
    # Assuming urls is a list of URL strings
    crawl_results = await crawler.arun_many(urls, config=config)

    # Process as they arrive
    async for result in crawl_results:
        process_immediately(result)  # Don't wait for all
Copy
```

  4. **Memory protection for large domains**


The seeder uses bounded queues to prevent memory issues when processing domains with millions of URLs:
```
# Safe for domains with 1M+ URLs
config = SeedingConfig(
    source="cc+sitemap",
    concurrency=50,  # Queue size adapts to concurrency
    max_urls=100000  # Process in batches if needed
)

# The seeder automatically manages memory by:
# - Using bounded queues (prevents RAM spikes)
# - Applying backpressure when queue is full
# - Processing URLs as they're discovered
Copy
```

## Best Practices & Tips
### Cache Management
The seeder automatically caches results to speed up repeated operations:
  * **Common Crawl cache** : `~/.crawl4ai/seeder_cache/[index]_[domain]_[hash].jsonl`
  * **Sitemap cache** : `~/.crawl4ai/seeder_cache/sitemap_[domain]_[hash].jsonl`
  * **HEAD data cache** : `~/.cache/url_seeder/head/[hash].json`


Cache expires after 7 days by default. Use `force=True` to refresh.
### Pattern Matching Strategies
```
# Be specific when possible
good_pattern = "*/blog/2024/*.html"  # Specific
bad_pattern = "*"                     # Too broad

# Combine patterns with metadata filtering
config = SeedingConfig(
    pattern="*/articles/*",
    extract_head=True
)
urls = await seeder.urls("news.com", config)

# Further filter by publish date, author, category, etc.
recent = [u for u in urls if is_recent(u['head_data'])]
Copy
```

### Rate Limiting Considerations
```
# Be respectful of servers
config = SeedingConfig(
    hits_per_sec=10,      # Max 10 requests per second
    concurrency=20        # But use 20 workers
)

# For your own servers
config = SeedingConfig(
    hits_per_sec=None,    # No limit
    concurrency=100       # Go fast
)
Copy
```

## Quick Reference
### Common Patterns
```
# Blog post discovery
config = SeedingConfig(
    source="sitemap",
    pattern="*/blog/*",
    extract_head=True,
    query="your topic",
    scoring_method="bm25"
)

# E-commerce product discovery
config = SeedingConfig(
    source="sitemap+cc",
    pattern="*/product/*",
    extract_head=True,
    live_check=True
)

# Documentation search
config = SeedingConfig(
    source="sitemap",
    pattern="*/docs/*",
    extract_head=True,
    query="API reference",
    scoring_method="bm25",
    score_threshold=0.5
)

# News monitoring
config = SeedingConfig(
    source="cc",
    extract_head=True,
    query="company name",
    scoring_method="bm25",
    max_urls=50
)
Copy
```

### Troubleshooting Guide
Issue | Solution
---|---
No URLs found | Try `source="cc+sitemap"`, check domain spelling
Slow discovery | Reduce `concurrency`, add `hits_per_sec` limit
Missing metadata | Ensure `extract_head=True`
Low relevance scores | Refine query, lower `score_threshold`
Rate limit errors | Reduce `hits_per_sec` and `concurrency`
Memory issues with large sites | Use `max_urls` to limit results, reduce `concurrency`
Connection not closed | Use context manager or call `await seeder.close()`
### Performance Benchmarks
Typical performance on a standard connection:
  * **Sitemap discovery** : 100-1,000 URLs/second
  * **Common Crawl discovery** : 50-500 URLs/second
  * **HEAD checking** : 10-50 URLs/second
  * **Head extraction** : 5-20 URLs/second
  * **BM25 scoring** : 10,000+ URLs/second


## Conclusion
URL seeding transforms web crawling from a blind expedition into a surgical strike. By discovering and analyzing URLs before crawling, you can:
  * Save hours of crawling time
  * Reduce bandwidth usage by 90%+
  * Find exactly what you need
  * Scale across multiple domains effortlessly


Whether you're building a research tool, monitoring competitors, or creating a content aggregator, URL seeding gives you the intelligence to crawl smarter, not harder.
### Smart URL Filtering
The seeder automatically filters out nonsense URLs that aren't useful for content crawling:
```
# Enabled by default
config = SeedingConfig(
    source="sitemap",
    filter_nonsense_urls=True  # Default: True
)

# URLs that get filtered:
# - robots.txt, sitemap.xml, ads.txt
# - API endpoints (/api/, /v1/, .json)
# - Media files (.jpg, .mp4, .pdf)
# - Archives (.zip, .tar.gz)
# - Source code (.js, .css)
# - Admin/login pages
# - And many more...
Copy
```

To disable filtering (not recommended):
```
config = SeedingConfig(
    source="sitemap",
    filter_nonsense_urls=False  # Include ALL URLs
)
Copy
```

### Key Features Summary
  1. **Parallel Sitemap Index Processing** : Automatically detects and processes sitemap indexes in parallel
  2. **Memory Protection** : Bounded queues prevent RAM issues with large domains (1M+ URLs)
  3. **Context Manager Support** : Automatic cleanup with `async with` statement
  4. **URL-Based Scoring** : Smart filtering even without head extraction
  5. **Smart URL Filtering** : Automatically excludes utility/nonsense URLs
  6. **Dual Caching** : Separate caches for URL lists and metadata


Now go forth and seed intelligently! 🌱🚀
#### On this page
  * [Why URL Seeding?](https://docs.crawl4ai.com/core/url-seeding/#why-url-seeding)
  * [Deep Crawling: Real-Time Discovery](https://docs.crawl4ai.com/core/url-seeding/#deep-crawling-real-time-discovery)
  * [URL Seeding: Bulk Discovery](https://docs.crawl4ai.com/core/url-seeding/#url-seeding-bulk-discovery)
  * [The Trade-offs](https://docs.crawl4ai.com/core/url-seeding/#the-trade-offs)
  * [When to Use Each](https://docs.crawl4ai.com/core/url-seeding/#when-to-use-each)
  * [Your First URL Seeding Adventure](https://docs.crawl4ai.com/core/url-seeding/#your-first-url-seeding-adventure)
  * [Understanding the URL Seeder](https://docs.crawl4ai.com/core/url-seeding/#understanding-the-url-seeder)
  * [Basic Usage](https://docs.crawl4ai.com/core/url-seeding/#basic-usage)
  * [1. Sitemaps (Fastest)](https://docs.crawl4ai.com/core/url-seeding/#1-sitemaps-fastest)
  * [2. Common Crawl (Most Comprehensive)](https://docs.crawl4ai.com/core/url-seeding/#2-common-crawl-most-comprehensive)
  * [3. Both Sources (Maximum Coverage)](https://docs.crawl4ai.com/core/url-seeding/#3-both-sources-maximum-coverage)
  * [Configuration Magic: SeedingConfig](https://docs.crawl4ai.com/core/url-seeding/#configuration-magic-seedingconfig)
  * [Pattern Matching Examples](https://docs.crawl4ai.com/core/url-seeding/#pattern-matching-examples)
  * [URL Validation: Live Checking](https://docs.crawl4ai.com/core/url-seeding/#url-validation-live-checking)
  * [The Power of Metadata: Head Extraction](https://docs.crawl4ai.com/core/url-seeding/#the-power-of-metadata-head-extraction)
  * [What Can We Extract?](https://docs.crawl4ai.com/core/url-seeding/#what-can-we-extract)
  * [Smart URL-Based Filtering (No Head Extraction)](https://docs.crawl4ai.com/core/url-seeding/#smart-url-based-filtering-no-head-extraction)
  * [Understanding Results](https://docs.crawl4ai.com/core/url-seeding/#understanding-results)
  * [Smart Filtering with BM25 Scoring](https://docs.crawl4ai.com/core/url-seeding/#smart-filtering-with-bm25-scoring)
  * [Introduction to Relevance Scoring](https://docs.crawl4ai.com/core/url-seeding/#introduction-to-relevance-scoring)
  * [Query-Based Discovery](https://docs.crawl4ai.com/core/url-seeding/#query-based-discovery)
  * [Real Examples](https://docs.crawl4ai.com/core/url-seeding/#real-examples)
  * [Finding Documentation Pages](https://docs.crawl4ai.com/core/url-seeding/#finding-documentation-pages)
  * [Discovering Product Pages](https://docs.crawl4ai.com/core/url-seeding/#discovering-product-pages)
  * [Filtering News Articles](https://docs.crawl4ai.com/core/url-seeding/#filtering-news-articles)
  * [Complex Query Patterns](https://docs.crawl4ai.com/core/url-seeding/#complex-query-patterns)
  * [Scaling Up: Multiple Domains](https://docs.crawl4ai.com/core/url-seeding/#scaling-up-multiple-domains)
  * [The many_urls Method](https://docs.crawl4ai.com/core/url-seeding/#the-many_urls-method)
  * [Cross-Domain Examples](https://docs.crawl4ai.com/core/url-seeding/#cross-domain-examples)
  * [Competitor Analysis](https://docs.crawl4ai.com/core/url-seeding/#competitor-analysis)
  * [Industry Research](https://docs.crawl4ai.com/core/url-seeding/#industry-research)
  * [Multi-Site Monitoring](https://docs.crawl4ai.com/core/url-seeding/#multi-site-monitoring)
  * [Advanced Integration Patterns](https://docs.crawl4ai.com/core/url-seeding/#advanced-integration-patterns)
  * [Building a Research Assistant](https://docs.crawl4ai.com/core/url-seeding/#building-a-research-assistant)
  * [Performance Optimization Tips](https://docs.crawl4ai.com/core/url-seeding/#performance-optimization-tips)
  * [Best Practices & Tips](https://docs.crawl4ai.com/core/url-seeding/#best-practices-tips)
  * [Cache Management](https://docs.crawl4ai.com/core/url-seeding/#cache-management)
  * [Pattern Matching Strategies](https://docs.crawl4ai.com/core/url-seeding/#pattern-matching-strategies)
  * [Rate Limiting Considerations](https://docs.crawl4ai.com/core/url-seeding/#rate-limiting-considerations)
  * [Quick Reference](https://docs.crawl4ai.com/core/url-seeding/#quick-reference)
  * [Common Patterns](https://docs.crawl4ai.com/core/url-seeding/#common-patterns)
  * [Troubleshooting Guide](https://docs.crawl4ai.com/core/url-seeding/#troubleshooting-guide)
  * [Performance Benchmarks](https://docs.crawl4ai.com/core/url-seeding/#performance-benchmarks)
  * [Conclusion](https://docs.crawl4ai.com/core/url-seeding/#conclusion)
  * [Smart URL Filtering](https://docs.crawl4ai.com/core/url-seeding/#smart-url-filtering)
  * [Key Features Summary](https://docs.crawl4ai.com/core/url-seeding/#key-features-summary)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
