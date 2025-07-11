# PDF Processing Strategies

Crawl4AI provides specialized strategies for handling and extracting content from PDF files. These strategies allow you to seamlessly integrate PDF processing into your crawling workflows, whether the PDFs are hosted online or stored locally.

## `PDFCrawlerStrategy`

### Overview
`PDFCrawlerStrategy` is an implementation of `AsyncCrawlerStrategy` designed specifically for PDF documents. Instead of interpreting the input URL as an HTML webpage, this strategy treats it as a pointer to a PDF file. It doesn't perform deep crawling or HTML parsing itself but rather prepares the PDF source for a dedicated PDF scraping strategy. Its primary role is to identify the PDF source (web URL or local file) and pass it along the processing pipeline in a way that `AsyncWebCrawler` can handle.

### When to Use
Use `PDFCrawlerStrategy` when you need to:
- Process PDF files using the `AsyncWebCrawler`.
- Handle PDFs from both web URLs (e.g., `https://example.com/document.pdf`) and local file paths (e.g., `file:///path/to/your/document.pdf`).
- Integrate PDF content extraction into a unified `CrawlResult` object, allowing consistent handling of PDF data alongside web page data.

### Key Methods and Their Behavior
-   **`__init__(self, logger: AsyncLogger = None)`**:
    -   Initializes the strategy.
    -   `logger`: An optional `AsyncLogger` instance (from `crawl4ai.async_logger`) for logging purposes.
-   **`async crawl(self, url: str, **kwargs) -> AsyncCrawlResponse`**:
    -   This method is called by the `AsyncWebCrawler` during the `arun` process.
    -   It takes the `url` (which should point to a PDF) and creates a minimal `AsyncCrawlResponse`.
    -   The `html` attribute of this response is typically empty or a placeholder, as the actual PDF content processing is deferred to the `PDFContentScrapingStrategy` (or a similar PDF-aware scraping strategy).
    -   It sets `response_headers` to indicate "application/pdf" and `status_code` to 200.
-   **`async close(self)`**:
    -   A method for cleaning up any resources used by the strategy. For `PDFCrawlerStrategy`, this is usually minimal.
-   **`async __aenter__(self)` / `async __aexit__(self, exc_type, exc_val, exc_tb)`**:
    -   Enables asynchronous context management for the strategy, allowing it to be used with `async with`.

### Example Usage
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.processors.pdf import PDFCrawlerStrategy, PDFContentScrapingStrategy

async def main():
    # Initialize the PDF crawler strategy
    pdf_crawler_strategy = PDFCrawlerStrategy()

    # PDFCrawlerStrategy is typically used in conjunction with PDFContentScrapingStrategy
    # The scraping strategy handles the actual PDF content extraction
    pdf_scraping_strategy = PDFContentScrapingStrategy()
    run_config = CrawlerRunConfig(scraping_strategy=pdf_scraping_strategy)

    async with AsyncWebCrawler(crawler_strategy=pdf_crawler_strategy) as crawler:
        # Example with a remote PDF URL
        pdf_url = "https://arxiv.org/pdf/2310.06825.pdf" # A public PDF from arXiv
        
        print(f"Attempting to process PDF: {pdf_url}")
        result = await crawler.arun(url=pdf_url, config=run_config)

        if result.success:
            print(f"Successfully processed PDF: {result.url}")
            print(f"Metadata Title: {result.metadata.get('title', 'N/A')}")
            # Further processing of result.markdown, result.media, etc.
            # would be done here, based on what PDFContentScrapingStrategy extracts.
            if result.markdown and hasattr(result.markdown, 'raw_markdown'):
                print(f"Extracted text (first 200 chars): {result.markdown.raw_markdown[:200]}...")
            else:
                print("No markdown (text) content extracted.")
        else:
            print(f"Failed to process PDF: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Pros and Cons
**Pros:**
-   Enables `AsyncWebCrawler` to handle PDF sources directly using familiar `arun` calls.
-   Provides a consistent interface for specifying PDF sources (URLs or local paths).
-   Abstracts the source handling, allowing a separate scraping strategy to focus on PDF content parsing.

**Cons:**
-   Does not perform any PDF data extraction itself; it strictly relies on a compatible scraping strategy (like `PDFContentScrapingStrategy`) to process the PDF.
-   Has limited utility on its own; most of its value comes from being paired with a PDF-specific content scraping strategy.

---

## `PDFContentScrapingStrategy`

### Overview
`PDFContentScrapingStrategy` is an implementation of `ContentScrapingStrategy` designed to extract text, metadata, and optionally images from PDF documents. It is intended to be used in conjunction with a crawler strategy that can provide it with a PDF source, such as `PDFCrawlerStrategy`. This strategy uses the `NaivePDFProcessorStrategy` internally to perform the low-level PDF parsing.

### When to Use
Use `PDFContentScrapingStrategy` when your `AsyncWebCrawler` (often configured with `PDFCrawlerStrategy`) needs to:
-   Extract textual content page by page from a PDF document.
-   Retrieve standard metadata embedded within the PDF (e.g., title, author, subject, creation date, page count).
-   Optionally, extract images contained within the PDF pages. These images can be saved to a local directory or made available for further processing.
-   Produce a `ScrapingResult` that can be converted into a `CrawlResult`, making PDF content accessible in a manner similar to HTML web content (e.g., text in `result.markdown`, metadata in `result.metadata`).

### Key Configuration Attributes
When initializing `PDFContentScrapingStrategy`, you can configure its behavior using the following attributes:
-   **`extract_images: bool = False`**: If `True`, the strategy will attempt to extract images from the PDF.
-   **`save_images_locally: bool = False`**: If `True` (and `extract_images` is also `True`), extracted images will be saved to disk in the `image_save_dir`. If `False`, image data might be available in another form (e.g., base64, depending on the underlying processor) but not saved as separate files by this strategy.
-   **`image_save_dir: str = None`**: Specifies the directory where extracted images should be saved if `save_images_locally` is `True`. If `None`, a default or temporary directory might be used.
-   **`batch_size: int = 4`**: Defines how many PDF pages are processed in a single batch. This can be useful for managing memory when dealing with very large PDF documents.
-   **`logger: AsyncLogger = None`**: An optional `AsyncLogger` instance for logging.

### Key Methods and Their Behavior
-   **`__init__(self, save_images_locally: bool = False, extract_images: bool = False, image_save_dir: str = None, batch_size: int = 4, logger: AsyncLogger = None)`**:
    -   Initializes the strategy with configurations for image handling, batch processing, and logging. It sets up an internal `NaivePDFProcessorStrategy` instance which performs the actual PDF parsing.
-   **`scrap(self, url: str, html: str, **params) -> ScrapingResult`**:
    -   This is the primary synchronous method called by the crawler (via `ascrap`) to process the PDF.
    -   `url`: The path or URL to the PDF file (provided by `PDFCrawlerStrategy` or similar).
    -   `html`: Typically an empty string when used with `PDFCrawlerStrategy`, as the content is a PDF, not HTML.
    -   It first ensures the PDF is accessible locally (downloads it to a temporary file if `url` is remote).
    -   It then uses its internal PDF processor to extract text, metadata, and images (if configured).
    -   The extracted information is compiled into a `ScrapingResult` object:
        -   `cleaned_html`: Contains an HTML-like representation of the PDF, where each page's content is often wrapped in a `<div>` with page number information.
        -   `media`: A dictionary where `media["images"]` will contain information about extracted images if `extract_images` was `True`.
        -   `links`: A dictionary where `links["urls"]` can contain URLs found within the PDF content.
        -   `metadata`: A dictionary holding PDF metadata (e.g., title, author, num_pages).
-   **`async ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult`**:
    -   The asynchronous version of `scrap`. Under the hood, it typically runs the synchronous `scrap` method in a separate thread using `asyncio.to_thread` to avoid blocking the event loop.
-   **`_get_pdf_path(self, url: str) -> str`**:
    -   A private helper method to manage PDF file access. If the `url` is remote (http/https), it downloads the PDF to a temporary local file and returns its path. If `url` indicates a local file (`file://` or a direct path), it resolves and returns the local path.

### Example Usage
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.processors.pdf import PDFCrawlerStrategy, PDFContentScrapingStrategy
import os # For creating image directory

async def main():
    # Define the directory for saving extracted images
    image_output_dir = "./my_pdf_images"
    os.makedirs(image_output_dir, exist_ok=True)

    # Configure the PDF content scraping strategy
    # Enable image extraction and specify where to save them
    pdf_scraping_cfg = PDFContentScrapingStrategy(
        extract_images=True,
        save_images_locally=True,
        image_save_dir=image_output_dir,
        batch_size=2 # Process 2 pages at a time for demonstration
    )

    # The PDFCrawlerStrategy is needed to tell AsyncWebCrawler how to "crawl" a PDF
    pdf_crawler_cfg = PDFCrawlerStrategy()

    # Configure the overall crawl run
    run_cfg = CrawlerRunConfig(
        scraping_strategy=pdf_scraping_cfg # Use our PDF scraping strategy
    )

    # Initialize the crawler with the PDF-specific crawler strategy
    async with AsyncWebCrawler(crawler_strategy=pdf_crawler_cfg) as crawler:
        pdf_url = "https://arxiv.org/pdf/2310.06825.pdf" # Example PDF
        
        print(f"Starting PDF processing for: {pdf_url}")
        result = await crawler.arun(url=pdf_url, config=run_cfg)

        if result.success:
            print("\n--- PDF Processing Successful ---")
            print(f"Processed URL: {result.url}")
            
            print("\n--- Metadata ---")
            for key, value in result.metadata.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")

            if result.markdown and hasattr(result.markdown, 'raw_markdown'):
                print(f"\n--- Extracted Text (Markdown Snippet) ---")
                print(result.markdown.raw_markdown[:500].strip() + "...")
            else:
                print("\nNo text (markdown) content extracted.")

            if result.media and result.media.get("images"):
                print(f"\n--- Image Extraction ---")
                print(f"Extracted {len(result.media['images'])} image(s).")
                for i, img_info in enumerate(result.media["images"][:2]): # Show info for first 2 images
                    print(f"  Image {i+1}:")
                    print(f"    Page: {img_info.get('page')}")
                    print(f"    Format: {img_info.get('format', 'N/A')}")
                    if img_info.get('path'):
                        print(f"    Saved at: {img_info.get('path')}")
            else:
                print("\nNo images were extracted (or extract_images was False).")
        else:
            print(f"\n--- PDF Processing Failed ---")
            print(f"Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Pros and Cons

**Pros:**
-   Provides a comprehensive way to extract text, metadata, and (optionally) images from PDF documents.
-   Handles both remote PDFs (via URL) and local PDF files.
-   Configurable image extraction allows saving images to disk or accessing their data.
-   Integrates smoothly with the `CrawlResult` object structure, making PDF-derived data accessible in a way consistent with web-scraped data.
-   The `batch_size` parameter can help in managing memory consumption when processing large or numerous PDF pages.

**Cons:**
-   Extraction quality and performance can vary significantly depending on the PDF's complexity, encoding, and whether it's image-based (scanned) or text-based.
-   Image extraction can be resource-intensive (both CPU and disk space if `save_images_locally` is true).
-   Relies on `NaivePDFProcessorStrategy` internally, which might have limitations with very complex layouts, encrypted PDFs, or forms compared to more sophisticated PDF parsing libraries. Scanned PDFs will not yield text unless an OCR step is performed (which is not part of this strategy by default).
-   Link extraction from PDFs can be basic and depends on how hyperlinks are embedded in the document.
