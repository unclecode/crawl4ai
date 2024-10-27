# Crawl Result

The `CrawlResult` class is the heart of Crawl4AI's output, encapsulating all the data extracted from a crawling session. This class contains various fields that store the results of the web crawling and extraction process. Let's break down each field and see what it holds. 🎉

## Class Definition

```python
class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    screenshot: Optional[str] = None
    markdown: Optional[str] = None
    extracted_content: Optional[str] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
```

## Fields Explanation

### `url: str`
The URL that was crawled. This field simply stores the URL of the web page that was processed.

### `html: str`
The raw HTML content of the web page. This is the unprocessed HTML source as retrieved by the crawler.

### `success: bool`
A flag indicating whether the crawling and extraction were successful. If any error occurs during the process, this will be `False`.

### `cleaned_html: Optional[str]`
The cleaned HTML content of the web page. This field holds the HTML after removing unwanted tags like `<script>`, `<style>`, and others that do not contribute to the useful content.

### `media: Dict[str, List[Dict]]`
A dictionary containing lists of extracted media elements from the web page. The media elements are categorized into images, videos, and audios. Here’s how they are structured:

- **Images**: Each image is represented as a dictionary with `src` (source URL) and `alt` (alternate text).
- **Videos**: Each video is represented similarly with `src` and `alt`.
- **Audios**: Each audio is represented with `src` and `alt`.

```python
media = {
    'images': [
        {'src': 'image_url1', 'alt': 'description1', "type": "image"},
        {'src': 'image_url2', 'alt': 'description2', "type": "image"}
    ],
    'videos': [
        {'src': 'video_url1', 'alt': 'description1', "type": "video"}
    ],
    'audios': [
        {'src': 'audio_url1', 'alt': 'description1', "type": "audio"}
    ]
}
```

### `links: Dict[str, List[Dict]]`
A dictionary containing lists of internal and external links extracted from the web page. Each link is represented as a dictionary with `href` (URL) and `text` (link text).

- **Internal Links**: Links pointing to the same domain.
- **External Links**: Links pointing to different domains.

```python
links = {
    'internal': [
        {'href': 'internal_link1', 'text': 'link_text1'},
        {'href': 'internal_link2', 'text': 'link_text2'}
    ],
    'external': [
        {'href': 'external_link1', 'text': 'link_text1'}
    ]
}
```

### `screenshot: Optional[str]`
A base64-encoded screenshot of the web page. This field stores the screenshot data if the crawling was configured to take a screenshot.

### `markdown: Optional[str]`
The content of the web page converted to Markdown format. This is useful for generating clean, readable text that retains the structure of the original HTML.

### `extracted_content: Optional[str]`
The content extracted based on the specified extraction strategy. This field holds the meaningful content blocks extracted from the web page, ready for your AI and data processing needs.

### `metadata: Optional[dict]`
A dictionary containing metadata extracted from the web page, such as title, description, keywords, and other meta tags.

### `error_message: Optional[str]`
If an error occurs during crawling, this field will contain the error message, helping you debug and understand what went wrong. 🚨

## Example Usage

Here's a quick example to illustrate how you might use the `CrawlResult` in your code:

```python
from crawl4ai import WebCrawler

# Create the WebCrawler instance
crawler = WebCrawler()

# Run the crawler on a URL
result = crawler.run(url="https://www.example.com")

# Check if the crawl was successful
if result.success:
    print("Crawl succeeded!")
    print("URL:", result.url)
    print("HTML:", result.html[:100])  # Print the first 100 characters of the HTML
    print("Cleaned HTML:", result.cleaned_html[:100])
    print("Media:", result.media)
    print("Links:", result.links)
    print("Screenshot:", result.screenshot)
    print("Markdown:", result.markdown[:100])
    print("Extracted Content:", result.extracted_content)
    print("Metadata:", result.metadata)
else:
    print("Crawl failed with error:", result.error_message)
```

With this setup, you can easily access all the valuable data extracted from the web page and integrate it into your applications. Happy crawling! 🕷️🤖
