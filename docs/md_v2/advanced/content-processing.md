# Content Processing

Crawl4AI provides powerful content processing capabilities that help you extract clean, relevant content from web pages. This guide covers content cleaning, media handling, link analysis, and metadata extraction.

## Media Processing

Crawl4AI provides comprehensive media extraction and analysis capabilities. It automatically detects and processes various types of media elements while maintaining their context and relevance.

### Image Processing

The library handles various image scenarios, including:
- Regular images
- Lazy-loaded images
- Background images
- Responsive images
- Image metadata and context

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

for image in result.media["images"]:
    # Each image includes rich metadata
    print(f"Source: {image['src']}")
    print(f"Alt text: {image['alt']}")
    print(f"Description: {image['desc']}")
    print(f"Context: {image['context']}")  # Surrounding text
    print(f"Relevance score: {image['score']}")  # 0-10 score
```

### Handling Lazy-Loaded Content

Crawl4AI already handles lazy loading for media elements. You can customize the wait time for lazy-loaded content with `CrawlerRunConfig`:

```python
config = CrawlerRunConfig(
    wait_for="css:img[data-src]",  # Wait for lazy images
    delay_before_return_html=2.0   # Additional wait time
)
result = await crawler.arun(url="https://example.com", config=config)
```

### Video and Audio Content

The library extracts video and audio elements with their metadata:

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

# Process videos
for video in result.media["videos"]:
    print(f"Video source: {video['src']}")
    print(f"Type: {video['type']}")
    print(f"Duration: {video.get('duration')}")
    print(f"Thumbnail: {video.get('poster')}")

# Process audio
for audio in result.media["audios"]:
    print(f"Audio source: {audio['src']}")
    print(f"Type: {audio['type']}")
    print(f"Duration: {audio.get('duration')}")
```

## Link Analysis

Crawl4AI provides sophisticated link analysis capabilities, helping you understand the relationship between pages and identify important navigation patterns.

### Link Classification

The library automatically categorizes links into:
- Internal links (same domain)
- External links (different domains)
- Social media links
- Navigation links
- Content links

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

# Analyze internal links
for link in result.links["internal"]:
    print(f"Internal: {link['href']}")
    print(f"Link text: {link['text']}")
    print(f"Context: {link['context']}")  # Surrounding text
    print(f"Type: {link['type']}")  # nav, content, etc.

# Analyze external links
for link in result.links["external"]:
    print(f"External: {link['href']}")
    print(f"Domain: {link['domain']}")
    print(f"Type: {link['type']}")
```

### Smart Link Filtering

Control which links are included in the results with `CrawlerRunConfig`:

```python
config = CrawlerRunConfig(
    exclude_external_links=True,          # Remove external links
    exclude_social_media_links=True,      # Remove social media links
    exclude_social_media_domains=[        # Custom social media domains
        "facebook.com", "twitter.com", "instagram.com"
    ],
    exclude_domains=["ads.example.com"]   # Exclude specific domains
)
result = await crawler.arun(url="https://example.com", config=config)
```

## Metadata Extraction

Crawl4AI automatically extracts and processes page metadata, providing valuable information about the content:

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

metadata = result.metadata
print(f"Title: {metadata['title']}")
print(f"Description: {metadata['description']}")
print(f"Keywords: {metadata['keywords']}")
print(f"Author: {metadata['author']}")
print(f"Published Date: {metadata['published_date']}")
print(f"Modified Date: {metadata['modified_date']}")
print(f"Language: {metadata['language']}")
```
