# Content Processing

Crawl4AI provides powerful content processing capabilities that help you extract clean, relevant content from web pages. This guide covers content cleaning, media handling, link analysis, and metadata extraction.

## Content Cleaning

### Understanding Clean Content
When crawling web pages, you often encounter a lot of noise - advertisements, navigation menus, footers, popups, and other irrelevant content. Crawl4AI automatically cleans this noise using several approaches:

1. **Basic Cleaning**: Removes unwanted HTML elements and attributes
2. **Content Relevance**: Identifies and preserves meaningful content blocks
3. **Layout Analysis**: Understands page structure to identify main content areas

```python
result = await crawler.arun(
    url="https://example.com",
    word_count_threshold=10,        # Remove blocks with fewer words
    excluded_tags=['form', 'nav'],  # Remove specific HTML tags
    remove_overlay_elements=True    # Remove popups/modals
)

# Get clean content
print(result.cleaned_html)  # Cleaned HTML
print(result.markdown)      # Clean markdown version
```

### Fit Markdown: Smart Content Extraction
One of Crawl4AI's most powerful features is `fit_markdown`. This feature uses advanced heuristics to identify and extract the main content from a webpage while excluding irrelevant elements.

#### How Fit Markdown Works
- Analyzes content density and distribution
- Identifies content patterns and structures
- Removes boilerplate content (headers, footers, sidebars)
- Preserves the most relevant content blocks
- Maintains content hierarchy and formatting

#### Perfect For:
- Blog posts and articles
- News content
- Documentation pages
- Any page with a clear main content area

#### Not Recommended For:
- E-commerce product listings
- Search results pages
- Social media feeds
- Pages with multiple equal-weight content sections

```python
result = await crawler.arun(url="https://example.com")

# Get the most relevant content
main_content = result.fit_markdown

# Compare with regular markdown
all_content = result.markdown

print(f"Fit Markdown Length: {len(main_content)}")
print(f"Regular Markdown Length: {len(all_content)}")
```

#### Example Use Case
```python
async def extract_article_content(url: str) -> str:
    """Extract main article content from a blog or news site."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        
        # fit_markdown will focus on the article content,
        # excluding navigation, ads, and other distractions
        return result.fit_markdown
```

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
result = await crawler.arun(url="https://example.com")

for image in result.media["images"]:
    # Each image includes rich metadata
    print(f"Source: {image['src']}")
    print(f"Alt text: {image['alt']}")
    print(f"Description: {image['desc']}")
    print(f"Context: {image['context']}")  # Surrounding text
    print(f"Relevance score: {image['score']}")  # 0-10 score
```

### Handling Lazy-Loaded Content
Crawl4aai already handles lazy loading for media elements. You can also customize the wait time for lazy-loaded content:

```python
result = await crawler.arun(
    url="https://example.com",
    wait_for="css:img[data-src]",  # Wait for lazy images
    delay_before_return_html=2.0   # Additional wait time
)
```

### Video and Audio Content
The library extracts video and audio elements with their metadata:

```python
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
result = await crawler.arun(url="https://example.com")

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
Control which links are included in the results:

```python
result = await crawler.arun(
    url="https://example.com",
    exclude_external_links=True,          # Remove external links
    exclude_social_media_links=True,      # Remove social media links
    exclude_social_media_domains=[                # Custom social media domains
        "facebook.com", "twitter.com", "instagram.com"
    ],
    exclude_domains=["ads.example.com"]   # Exclude specific domains
)
```

## Metadata Extraction

Crawl4AI automatically extracts and processes page metadata, providing valuable information about the content:

```python
result = await crawler.arun(url="https://example.com")

metadata = result.metadata
print(f"Title: {metadata['title']}")
print(f"Description: {metadata['description']}")
print(f"Keywords: {metadata['keywords']}")
print(f"Author: {metadata['author']}")
print(f"Published Date: {metadata['published_date']}")
print(f"Modified Date: {metadata['modified_date']}")
print(f"Language: {metadata['language']}")
```

## Best Practices

1. **Use Fit Markdown for Articles**
   ```python
   # Perfect for blog posts, news articles, documentation
   content = result.fit_markdown
   ```

2. **Handle Media Appropriately**
   ```python
   # Filter by relevance score
   relevant_images = [
       img for img in result.media["images"]
       if img['score'] > 5
   ]
   ```

3. **Combine Link Analysis with Content**
   ```python
   # Get content links with context
   content_links = [
       link for link in result.links["internal"]
       if link['type'] == 'content'
   ]
   ```

4. **Clean Content with Purpose**
   ```python
   # Customize cleaning based on your needs
   result = await crawler.arun(
       url=url,
       word_count_threshold=20,      # Adjust based on content type
       keep_data_attributes=False,   # Remove data attributes
       process_iframes=True         # Include iframe content
   )
   ```