# Changelog

All notable changes to Crawl4AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

### Changed
Okay, here's a detailed changelog in Markdown format, generated from the provided git diff and commit history. I've focused on user-facing changes, fixes, and features, and grouped them as requested:

## Version 0.4.3b2 (2025-01-21)

This release introduces several powerful new features, including robots.txt compliance, dynamic proxy support, LLM-powered schema generation, and improved documentation.

### Features

-   **Robots.txt Compliance:**
    -   Added robots.txt compliance support with efficient SQLite-based caching.
    -   New `check_robots_txt` parameter in `CrawlerRunConfig` to enable robots.txt checking before crawling a URL.
    -   Automated robots.txt checking is now integrated into `AsyncWebCrawler` with 403 status codes for blocked URLs.
    
-   **Proxy Configuration:**
    -   Added proxy configuration support to `CrawlerRunConfig`, allowing dynamic proxy settings per crawl request.
    -   Updated documentation with examples for using proxy configuration in crawl operations.

-   **LLM-Powered Schema Generation:**
    -   Introduced a new utility for automatic CSS and XPath schema generation using OpenAI or Ollama models.
    -   Added comprehensive documentation and examples for schema generation.
    -   New prompt templates optimized for HTML schema analysis.

-   **URL Redirection Tracking:**
    -   Added URL redirection tracking to capture the final URL after any redirects.
    -   The final URL is now available in the `redirected_url` field of the `AsyncCrawlResponse` object.

-   **Enhanced Streamlined Documentation:**
    -   Refactored and improved the documentation structure for clarity and ease of use.
    -   Added detailed explanations of new features and updated examples.

-   **Improved Browser Context Management:**
    -   Enhanced the management of browser contexts and added shared data support.
    -   Introduced the `shared_data` parameter in `CrawlerRunConfig` to pass data between hooks.

-   **Memory Dispatcher System:**
    -   Migrated to a memory dispatcher system with enhanced monitoring capabilities.
    -   Introduced `MemoryAdaptiveDispatcher` and `SemaphoreDispatcher` for improved resource management.
    -   Added `RateLimiter` for rate limiting support.
    -   New `CrawlerMonitor` for real-time monitoring of crawler operations.

-   **Streaming Support:**
    -   Added streaming support for processing crawled URLs as they are processed.
    -   Enabled streaming mode with the `stream` parameter in `CrawlerRunConfig`.

-   **Content Scraping Strategy:**
    -   Introduced a new `LXMLWebScrapingStrategy` for faster content scraping.
    -   Added support for selecting the scraping strategy via the `scraping_strategy` parameter in `CrawlerRunConfig`.

### Bug Fixes

-   **Browser Path Management:**
    -   Improved browser path management for consistent behavior across different environments.

-   **Memory Threshold:**
    -   Adjusted the default memory threshold to improve resource utilization.

-   **Pydantic Model Fields:**
    -   Made several model fields optional with default values to improve flexibility.

### Refactor

-   **Documentation Structure:**
    -   Reorganized documentation structure to improve navigation and readability.
    -   Updated styles and added new sections for advanced features.

-   **Scraping Mode:**
    -   Replaced the `ScrapingMode` enum with a strategy pattern for more flexible content scraping.

-   **Version Update:**
    -   Updated the version to `0.4.248`.

-   **Code Cleanup:**
    -   Removed unused files and improved type hints.
    -   Applied Ruff corrections for code quality.

-   **Updated dependencies:**
    -   Updated dependencies to their latest versions to ensure compatibility and security.

-   **Ignored certain patterns and directories:**
    -   Updated `.gitignore` and `.codeiumignore` to ignore additional patterns and directories, streamlining the development environment.

-   **Simplified Personal Story in README:**
    -   Streamlined the personal story and project vision in the `README.md` for clarity.

-   **Removed Deprecated Files:**
    -   Deleted several deprecated files and examples that are no longer relevant.

---
**Previous Releases:**

### 0.4.24x (2024-12-31)
-   **Enhanced SSL & Security**: New SSL certificate handling with custom paths and validation options for secure crawling.
-   **Smart Content Filtering**: Advanced filtering system with regex support and efficient chunking strategies.
-   **Improved JSON Extraction**: Support for complex JSONPath, JSON-CSS, and Microdata extraction.
-   **New Field Types**: Added `computed`, `conditional`, `aggregate`, and `template` field types.
-   **Performance Boost**: Optimized caching, parallel processing, and memory management.
-   **Better Error Handling**: Enhanced debugging capabilities with detailed error tracking.
-   **Security Features**: Improved input validation and safe expression evaluation.

### 0.4.247 (2025-01-06)

#### Added
- **Windows Event Loop Configuration**: Introduced a utility function `configure_windows_event_loop` to resolve `NotImplementedError` for asyncio subprocesses on Windows. ([#utils.py](crawl4ai/utils.py), [#tutorials/async-webcrawler-basics.md](docs/md_v3/tutorials/async-webcrawler-basics.md))
- **`page_need_scroll` Method**: Added a method to determine if a page requires scrolling before taking actions in `AsyncPlaywrightCrawlerStrategy`. ([#async_crawler_strategy.py](crawl4ai/async_crawler_strategy.py))

#### Changed
- **Version Bump**: Updated the version from `0.4.246` to `0.4.247`. ([#__version__.py](crawl4ai/__version__.py))
- **Improved Scrolling Logic**: Enhanced scrolling methods in `AsyncPlaywrightCrawlerStrategy` by adding a `scroll_delay` parameter for better control. ([#async_crawler_strategy.py](crawl4ai/async_crawler_strategy.py))
- **Markdown Generation Example**: Updated the `hello_world.py` example to reflect the latest API changes and better illustrate features. ([#examples/hello_world.py](docs/examples/hello_world.py))
- **Documentation Update**: 
  - Added Windows-specific instructions for handling asyncio event loops. ([#async-webcrawler-basics.md](docs/md_v3/tutorials/async-webcrawler-basics.md))

#### Removed
- **Legacy Markdown Generation Code**: Removed outdated and unused code for markdown generation in `content_scraping_strategy.py`. ([#content_scraping_strategy.py](crawl4ai/content_scraping_strategy.py))

#### Fixed
- **Page Closing to Prevent Memory Leaks**:
  - **Description**: Added a `finally` block to ensure pages are closed when no `session_id` is provided.
  - **Impact**: Prevents memory leaks caused by lingering pages after a crawl.
  - **File**: [`async_crawler_strategy.py`](crawl4ai/async_crawler_strategy.py)
  - **Code**:
    ```python
    finally:
        # If no session_id is given we should close the page
        if not config.session_id:
            await page.close()
    ```
- **Multiple Element Selection**: Modified `_get_elements` in `JsonCssExtractionStrategy` to return all matching elements instead of just the first one, ensuring comprehensive extraction. ([#extraction_strategy.py](crawl4ai/extraction_strategy.py))
- **Error Handling in Scrolling**: Added robust error handling to ensure scrolling proceeds safely even if a configuration is missing. ([#async_crawler_strategy.py](crawl4ai/async_crawler_strategy.py))

## [0.4.267] - 2025 - 01 - 06

### Added
- **Windows Event Loop Configuration**: Introduced a utility function `configure_windows_event_loop` to resolve `NotImplementedError` for asyncio subprocesses on Windows. ([#utils.py](crawl4ai/utils.py), [#tutorials/async-webcrawler-basics.md](docs/md_v3/tutorials/async-webcrawler-basics.md))
- **`page_need_scroll` Method**: Added a method to determine if a page requires scrolling before taking actions in `AsyncPlaywrightCrawlerStrategy`. ([#async_crawler_strategy.py](crawl4ai/async_crawler_strategy.py))

## [0.4.24] - 2024-12-31

### Added
- **Browser and SSL Handling**
  - SSL certificate validation options in extraction strategies
  - Custom certificate paths support
  - Configurable certificate validation skipping
  - Enhanced response status code handling with retry logic

- **Content Processing**
  - New content filtering system with regex support
  - Advanced chunking strategies for large content
  - Memory-efficient parallel processing
  - Configurable chunk size optimization

- **JSON Extraction**
  - Complex JSONPath expression support
  - JSON-CSS and Microdata extraction
  - RDFa parsing capabilities
  - Advanced data transformation pipeline

- **Field Types**
  - New field types: `computed`, `conditional`, `aggregate`, `template`
  - Field inheritance system
  - Reusable field definitions
  - Custom validation rules

### Changed
- **Performance**
  - Optimized selector compilation with caching
  - Improved HTML parsing efficiency
  - Enhanced memory management for large documents
  - Batch processing optimizations

- **Error Handling**
  - More detailed error messages and categorization
  - Enhanced debugging capabilities
  - Improved performance metrics tracking
  - Better error recovery mechanisms

### Deprecated
- Old field computation method using `eval`
- Direct browser manipulation without proper SSL handling
- Simple text-based content filtering

### Removed
- Legacy extraction patterns without proper error handling
- Unsafe eval-based field computation
- Direct DOM manipulation without sanitization

### Fixed
- Memory leaks in large document processing
- SSL certificate validation issues
- Incorrect handling of nested JSON structures
- Performance bottlenecks in parallel processing

### Security
- Improved input validation and sanitization
- Safe expression evaluation system
- Enhanced resource protection
- Rate limiting implementation

## [0.4.1] - 2024-12-08

### **File: `crawl4ai/async_crawler_strategy.py`**

#### **New Parameters and Attributes Added**
- **`text_mode` (boolean)**: Enables text-only mode, disables images, JavaScript, and GPU-related features for faster, minimal rendering.
- **`light_mode` (boolean)**: Optimizes the browser by disabling unnecessary background processes and features for efficiency.
- **`viewport_width` and `viewport_height`**: Dynamically adjusts based on `text_mode` mode (default values: 800x600 for `text_mode`, 1920x1080 otherwise).
- **`extra_args`**: Adds browser-specific flags for `text_mode` mode.
- **`adjust_viewport_to_content`**: Dynamically adjusts the viewport to the content size for accurate rendering.

#### **Browser Context Adjustments**
- Added **`viewport` adjustments**: Dynamically computed based on `text_mode` or custom configuration.
- Enhanced support for `light_mode` and `text_mode` by adding specific browser arguments to reduce resource consumption.

#### **Dynamic Content Handling**
- **Full Page Scan Feature**:
  - Scrolls through the entire page while dynamically detecting content changes.
  - Ensures scrolling stops when no new dynamic content is loaded.

#### **Session Management**
- Added **`create_session`** method:
  - Creates a new browser session and assigns a unique ID.
  - Supports persistent and non-persistent contexts with full compatibility for cookies, headers, and proxies.

#### **Improved Content Loading and Adjustment**
- **`adjust_viewport_to_content`**:
  - Automatically adjusts viewport to match content dimensions.
  - Includes scaling via Chrome DevTools Protocol (CDP).
- Enhanced content loading:
  - Waits for images to load and ensures network activity is idle before proceeding.

#### **Error Handling and Logging**
- Improved error handling and detailed logging for:
  - Viewport adjustment (`adjust_viewport_to_content`).
  - Full page scanning (`scan_full_page`).
  - Dynamic content loading.

#### **Refactoring and Cleanup**
- Removed hardcoded viewport dimensions in multiple places, replaced with dynamic values (`self.viewport_width`, `self.viewport_height`).
- Removed commented-out and unused code for better readability.
- Added default value for `delay_before_return_html` parameter.

#### **Optimizations**
- Reduced resource usage in `light_mode` by disabling unnecessary browser features such as extensions, background timers, and sync.
- Improved compatibility for different browser types (`chrome`, `firefox`, `webkit`).

---

### **File: `docs/examples/quickstart_async.py`**

#### **Schema Adjustment**
- Changed schema reference for `LLMExtractionStrategy`:
  - **Old**: `OpenAIModelFee.schema()`
  - **New**: `OpenAIModelFee.model_json_schema()`
  - This likely ensures better compatibility with the `OpenAIModelFee` class and its JSON schema.

#### **Documentation Comments Updated**
- Improved extraction instruction for schema-based LLM strategies.

---

### **New Features Added**
1. **Text-Only Mode**:
   - Focuses on minimal resource usage by disabling non-essential browser features.
2. **Light Mode**:
   - Optimizes browser for performance by disabling background tasks and unnecessary services.
3. **Full Page Scanning**:
   - Ensures the entire content of a page is crawled, including dynamic elements loaded during scrolling.
4. **Dynamic Viewport Adjustment**:
   - Automatically resizes the viewport to match content dimensions, improving compatibility and rendering accuracy.
5. **Session Management**:
   - Simplifies session handling with better support for persistent and non-persistent contexts.

---

### **Bug Fixes**
- Fixed potential viewport mismatches by ensuring consistent use of `self.viewport_width` and `self.viewport_height` throughout the code.
- Improved robustness of dynamic content loading to avoid timeouts and failed evaluations.







## [0.3.75] December 1, 2024

### PruningContentFilter

#### 1. Introduced PruningContentFilter (Dec 01, 2024) (Dec 01, 2024)
A new content filtering strategy that removes less relevant nodes based on metrics like text and link density.

**Affected Files:**
- `crawl4ai/content_filter_strategy.py`: Enhancement of content filtering capabilities.
```diff
Implemented effective pruning algorithm with comprehensive scoring.
```
- `README.md`: Improved documentation regarding new features.
```diff
Updated to include usage and explanation for the PruningContentFilter.
```
- `docs/md_v2/basic/content_filtering.md`: Expanded documentation for users.
```diff
Added detailed section explaining the PruningContentFilter.
```

#### 2. Added Unit Tests for PruningContentFilter (Dec 01, 2024) (Dec 01, 2024)
Comprehensive tests added to ensure correct functionality of PruningContentFilter

**Affected Files:**
- `tests/async/test_content_filter_prune.py`: Increased test coverage for content filtering strategies.
```diff
Created test cases for various scenarios using the PruningContentFilter.
```

### Development Updates

#### 3. Enhanced BM25ContentFilter tests (Dec 01, 2024) (Dec 01, 2024)
Extended testing to cover additional edge cases and performance metrics.

**Affected Files:**
- `tests/async/test_content_filter_bm25.py`: Improved reliability and performance assurance.
```diff
Added tests for new extraction scenarios including malformed HTML.
```

### Infrastructure & Documentation

#### 4. Updated Examples (Dec 01, 2024) (Dec 01, 2024)
Altered examples in documentation to promote the use of PruningContentFilter alongside existing strategies.

**Affected Files:**
- `docs/examples/quickstart_async.py`: Enhanced usability and clarity for new users.
- Revised example to illustrate usage of PruningContentFilter.

## [0.3.746] November 29, 2024

### Major Features
1. Enhanced Docker Support (Nov 29, 2024)
   - Improved GPU support in Docker images.
   - Dockerfile refactored for better platform-specific installations.
   - Introduced new Docker commands for different platforms:
     - `basic-amd64`, `all-amd64`, `gpu-amd64` for AMD64.
     - `basic-arm64`, `all-arm64`, `gpu-arm64` for ARM64.

### Infrastructure & Documentation
- Enhanced README.md to improve user guidance and installation instructions.
- Added installation instructions for Playwright setup in README.
- Created and updated examples in `docs/examples/quickstart_async.py` to be more useful and user-friendly.
- Updated `requirements.txt` with a new `pydantic` dependency.
- Bumped version number in `crawl4ai/__version__.py` to 0.3.746.

### Breaking Changes
- Streamlined application structure:
  - Removed static pages and related code from `main.py` which might affect existing deployments relying on static content.

### Development Updates
- Developed `post_install` method in `crawl4ai/install.py` to streamline post-installation setup tasks.
- Refined migration processes in `crawl4ai/migrations.py` with enhanced logging for better error visibility.
- Updated `docker-compose.yml` to support local and hub services for different architectures, enhancing build and deploy capabilities.
- Refactored example test cases in `docs/examples/docker_example.py` to facilitate comprehensive testing.

### README.md
Updated README with new docker commands and setup instructions.
Enhanced installation instructions and guidance.

### crawl4ai/install.py
Added post-install script functionality.
Introduced `post_install` method for automation of post-installation tasks.

### crawl4ai/migrations.py
Improved migration logging.
Refined migration processes and added better logging.

### docker-compose.yml
Refactored docker-compose for better service management.
Updated to define services for different platforms and versions.

### requirements.txt
Updated dependencies.
Added `pydantic` to requirements file.

### crawler/__version__.py
Updated version number.
Bumped version number to 0.3.746.

### docs/examples/quickstart_async.py
Enhanced example scripts.
Uncommented example usage in async guide for user functionality.

### main.py
Refactored code to improve maintainability.
Streamlined app structure by removing static pages code.

## [0.3.743] November 27, 2024

Enhance features and documentation
- Updated version to 0.3.743
- Improved ManagedBrowser configuration with dynamic host/port
- Implemented fast HTML formatting in web crawler
- Enhanced markdown generation with a new generator class
- Improved sanitization and utility functions
- Added contributor details and pull request acknowledgments
- Updated documentation for clearer usage scenarios
- Adjusted tests to reflect class name changes

### CONTRIBUTORS.md
Added new contributors and pull request details.
Updated community contributions and acknowledged pull requests.

### crawl4ai/__version__.py
Version update.
Bumped version to 0.3.743.

### crawl4ai/async_crawler_strategy.py
Improved ManagedBrowser configuration.
Enhanced browser initialization with configurable host and debugging port; improved hook execution.

### crawl4ai/async_webcrawler.py
Optimized HTML processing.
Implemented 'fast_format_html' for optimized HTML formatting; applied it when 'prettiify' is enabled.

### crawl4ai/content_scraping_strategy.py
Enhanced markdown generation strategy.
Updated to use DefaultMarkdownGenerator and improved markdown generation with filters option.

### crawl4ai/markdown_generation_strategy.py
Refactored markdown generation class.
Renamed DefaultMarkdownGenerationStrategy to DefaultMarkdownGenerator; added content filter handling.

### crawl4ai/utils.py
Enhanced utility functions.
Improved input sanitization and enhanced HTML formatting method.

### docs/md_v2/advanced/hooks-auth.md
Improved documentation for hooks.
Updated code examples to include cookies in crawler strategy initialization.

### tests/async/test_markdown_genertor.py
Refactored tests to match class renaming.
Updated tests to use renamed DefaultMarkdownGenerator class.

## [0.3.74] November 17, 2024

This changelog details the updates and changes introduced in Crawl4AI version 0.3.74. It's designed to inform developers about new features, modifications to existing components, removals, and other important information.

### 1. File Download Processing

- Users can now specify download folders using the `downloads_path` parameter in the `AsyncWebCrawler` constructor or the `arun` method. If not specified, downloads are saved to a "downloads" folder within the `.crawl4ai` directory.
- File download tracking is integrated into the `CrawlResult` object.  Successfully downloaded files are listed in the `downloaded_files` attribute, providing their paths.
- Added `accept_downloads` parameter to the crawler strategies (defaults to `False`). If set to True you can add JS code and `wait_for` parameter for file download.

**Example:**

```python
import asyncio
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler

async def download_example():
    downloads_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
    os.makedirs(downloads_path, exist_ok=True)

    async with AsyncWebCrawler(
        accept_downloads=True, 
        downloads_path=downloads_path, 
        verbose=True
    ) as crawler:
        result = await crawler.arun(
            url="https://www.python.org/downloads/",
            js_code="""
                const downloadLink = document.querySelector('a[href$=".exe"]');
                if (downloadLink) { downloadLink.click(); }
            """,
            wait_for=5 # To ensure download has started
        )

        if result.downloaded_files:
            print("Downloaded files:")
            for file in result.downloaded_files:
                print(f"- {file}")

asyncio.run(download_example())

```

### 2. Refined Content Filtering

- Introduced the `RelevanceContentFilter` strategy (and its implementation `BM25ContentFilter`) for extracting relevant content from web pages, replacing Fit Markdown and other content cleaning strategy. This new strategy leverages the BM25 algorithm to identify chunks of text relevant to the page's title, description, keywords, or a user-provided query.
- The `fit_markdown` flag in the content scraper is used to filter content based on title, meta description, and keywords.

**Example:**

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.content_filter_strategy import BM25ContentFilter

async def filter_content(url, query):
    async with AsyncWebCrawler() as crawler:
        content_filter = BM25ContentFilter(user_query=query)
        result = await crawler.arun(url=url, extraction_strategy=content_filter, fit_markdown=True)
        print(result.extracted_content)  # Or result.fit_markdown for the markdown version
        print(result.fit_html) # Or result.fit_html to show HTML with only the filtered content

asyncio.run(filter_content("https://en.wikipedia.org/wiki/Apple", "fruit nutrition health"))
```

### 3. Raw HTML and Local File Support

- Added support for crawling local files and raw HTML content directly.
- Use the `file://` prefix for local file paths.
- Use the `raw:` prefix for raw HTML strings.

**Example:**

```python
async def crawl_local_or_raw(crawler, content, content_type):
    prefix = "file://" if content_type == "local" else "raw:"
    url = f"{prefix}{content}"
    result = await crawler.arun(url=url)
    if result.success:
        print(f"Markdown Content from {content_type.title()} Source:")
        print(result.markdown)

# Example usage with local file and raw HTML
async def main():
    async with AsyncWebCrawler() as crawler:
        # Local File
        await crawl_local_or_raw(
            crawler, os.path.abspath('tests/async/sample_wikipedia.html'), "local"
        )
        # Raw HTML
        await crawl_raw_html(crawler, "<h1>Raw Test</h1><p>This is raw HTML.</p>")
        

asyncio.run(main())
```

### 4. Browser Management

- New asynchronous crawler strategy implemented using Playwright.
- `ManagedBrowser` class introduced for improved browser session handling, offering features like persistent browser sessions between requests (using  `session_id`  parameter) and browser process monitoring.
- Updated to tf-playwright-stealth for enhanced stealth capabilities.
- Added `use_managed_browser`, `use_persistent_context`, and `chrome_channel` parameters to AsyncPlaywrightCrawlerStrategy.


**Example:**
```python
async def browser_management_demo():
    user_data_dir = os.path.join(Path.home(), ".crawl4ai", "user-data-dir")
    os.makedirs(user_data_dir, exist_ok=True)  # Ensure directory exists
    async with AsyncWebCrawler(
        use_managed_browser=True,
        user_data_dir=user_data_dir,
        use_persistent_context=True,
        verbose=True
    ) as crawler:
        result1 = await crawler.arun(
            url="https://example.com", session_id="my_session"
        )
        result2 = await crawler.arun(
            url="https://example.com/anotherpage", session_id="my_session"
        )

asyncio.run(browser_management_demo())
```


### 5. API Server & Cache Improvements

- Added CORS support to API server.
- Implemented static file serving.
- Enhanced root redirect functionality.
- Cache database updated to store response headers and downloaded files information. It utilizes a file system approach to manage large content efficiently.
- New, more efficient caching database built using xxhash and file system approach.
- Introduced `CacheMode` enum (`ENABLED`, `DISABLED`, `READ_ONLY`, `WRITE_ONLY`, `BYPASS`) and `always_bypass_cache` parameter in AsyncWebCrawler for fine-grained cache control. This replaces `bypass_cache`, `no_cache_read`, `no_cache_write`, and `always_by_pass_cache`.


### 🗑️ Removals

- Removed deprecated: `crawl4ai/content_cleaning_strategy.py`.
- Removed internal class ContentCleaningStrategy
- Removed legacy cache control flags:  `bypass_cache`,  `disable_cache`,  `no_cache_read`,  `no_cache_write`, and `always_by_pass_cache`.  These have been superseded by  `cache_mode`.


### ⚙️ Other Changes

- Moved version file to `crawl4ai/__version__.py`.
- Added `crawl4ai/cache_context.py`.
- Added `crawl4ai/version_manager.py`.
- Added `crawl4ai/migrations.py`.
- Added `crawl4ai-migrate` entry point.
- Added config `NEED_MIGRATION` and `SHOW_DEPRECATION_WARNINGS`.
- API server now requires an API token for authentication, configurable with the `CRAWL4AI_API_TOKEN` environment variable.  This enhances API security.
- Added synchronous crawl endpoint `/crawl_sync` for immediate result retrieval, and direct crawl endpoint `/crawl_direct` bypassing the task queue.


### ⚠️ Deprecation Notices

- The synchronous version of `WebCrawler` is being phased out.  While still available via `crawl4ai[sync]`, it will eventually be removed. Transition to `AsyncWebCrawler` is strongly recommended. Boolean cache control flags in `arun` are also deprecated, migrate to using the `cache_mode` parameter.  See examples in the "New Features" section above for correct usage.


### 🐛 Bug Fixes

- Resolved issue with browser context closing unexpectedly in Docker. This significantly improves stability, particularly within containerized environments. 
- Fixed memory leaks associated with incorrect asynchronous cleanup by removing the `__del__` method and ensuring the browser context is closed explicitly using context managers.
- Improved error handling in `WebScrapingStrategy`. More detailed error messages and suggestions for debugging will minimize frustration when running into unexpected issues.
- Fixed issue with incorrect text parsing in specific HTML structures.


### Example of migrating to the new CacheMode:

**Old way:**

```python
crawler = AsyncWebCrawler(always_by_pass_cache=True)
result = await crawler.arun(url="https://example.com", bypass_cache=True)
```

**New way:**

```python
from crawl4ai import CacheMode

crawler = AsyncWebCrawler(always_bypass_cache=True)
result = await crawler.arun(url="https://example.com", cache_mode=CacheMode.BYPASS)
```


## [0.3.74] - November 13, 2024

1. **File Download Processing** (Nov 14, 2024)
   - Added capability for users to specify download folders
   - Implemented file download tracking in crowd result object
   - Created new file: `tests/async/test_async_doanloader.py`

2. **Content Filtering Improvements** (Nov 14, 2024)
   - Introduced Relevance Content Filter as an improvement over Fit Markdown
   - Implemented BM25 algorithm for content relevance matching
   - Added new file: `crawl4ai/content_filter_strategy.py`
   - Removed deprecated: `crawl4ai/content_cleaning_strategy.py`

3. **Local File and Raw HTML Support** (Nov 13, 2024)
   - Added support for processing local files
   - Implemented raw HTML input handling in AsyncWebCrawler
   - Enhanced `crawl4ai/async_webcrawler.py` with significant performance improvements

4. **Browser Management Enhancements** (Nov 12, 2024)
   - Implemented new async crawler strategy using Playwright
   - Introduced ManagedBrowser for better browser session handling
   - Added support for persistent browser sessions
   - Updated from playwright_stealth to tf-playwright-stealth

5. **API Server Component**
   - Added CORS support
   - Implemented static file serving
   - Enhanced root redirect functionality



## [0.3.731] - November 13, 2024

### Added
- Support for raw HTML and local file crawling via URL prefixes ('raw:', 'file://')
- Browser process monitoring for managed browser instances
- Screenshot capability for raw HTML and local file content
- Response headers storage in cache database
- New `fit_markdown` flag for optional markdown generation

### Changed
- Switched HTML parser from 'html.parser' to 'lxml' for ~4x performance improvement 
- Optimized BeautifulSoup text conversion and element selection
- Pre-compiled regular expressions for better performance
- Improved metadata extraction efficiency
- Response headers now stored alongside HTML in cache

### Removed
- `__del__` method from AsyncPlaywrightCrawlerStrategy to prevent async cleanup issues

### Fixed 
- Issue #256: Added support for crawling raw HTML content
- Issue #253: Implemented file:// protocol handling
- Missing response headers in cached results
- Memory leaks from improper async cleanup

## [v0.3.731] - 2024-11-13 Changelog for Issue 256 Fix
- Fixed: Browser context unexpectedly closing in Docker environment during crawl operations.
- Removed: __del__ method from AsyncPlaywrightCrawlerStrategy to prevent unreliable asynchronous cleanup, ensuring - browser context is closed explicitly within context managers.
- Added: Monitoring for ManagedBrowser subprocess to detect and log unexpected terminations.
- Updated: Dockerfile configurations to expose debugging port (9222) and allocate additional shared memory for improved browser stability.
- Improved: Error handling and resource cleanup processes for browser lifecycle management within the Docker environment.

## [v0.3.73] - 2024-11-05

### Major Features
- **New Doctor Feature**
  - Added comprehensive system diagnostics tool
  - Available through package hub and CLI
  - Provides automated troubleshooting and system health checks
  - Includes detailed reporting of configuration issues

- **Dockerized API Server**
  - Released complete Docker implementation for API server
  - Added comprehensive documentation for Docker deployment
  - Implemented container communication protocols
  - Added environment configuration guides

- **Managed Browser Integration**
  - Added support for user-controlled browser instances
  - Implemented `ManagedBrowser` class for better browser lifecycle management
  - Added ability to connect to existing Chrome DevTools Protocol (CDP) endpoints
  - Introduced user data directory support for persistent browser profiles

- **Enhanced HTML Processing**
  - Added HTML tag preservation feature during markdown conversion
  - Introduced configurable tag preservation system
  - Improved pre-tag and code block handling
  - Added support for nested preserved tags with attribute retention

### Improvements
- **Browser Handling**
  - Added flag to ignore body visibility for problematic pages
  - Improved browser process cleanup and management
  - Enhanced temporary directory handling for browser profiles
  - Added configurable browser launch arguments

- **Database Management**
  - Implemented connection pooling for better performance
  - Added retry logic for database operations
  - Improved error handling and logging
  - Enhanced cleanup procedures for database connections

- **Resource Management**
  - Added memory and CPU monitoring
  - Implemented dynamic task slot allocation based on system resources
  - Added configurable cleanup intervals

### Technical Improvements
- **Code Structure**
  - Moved version management to dedicated _version.py file
  - Improved error handling throughout the codebase
  - Enhanced logging system with better error reporting
  - Reorganized core components for better maintainability

### Bug Fixes
- Fixed issues with browser process termination
- Improved handling of connection timeouts
- Enhanced error recovery in database operations
- Fixed memory leaks in long-running processes

### Dependencies
- Updated Playwright to v1.47
- Updated core dependencies with more flexible version constraints
- Added new development dependencies for testing

### Breaking Changes
- Changed default browser handling behavior
- Modified database connection management approach
- Updated API response structure for better consistency

### Migration Guide
When upgrading to v0.3.73, be aware of the following changes:

1. Docker Deployment:
   - Review Docker documentation for new deployment options
   - Update environment configurations as needed
   - Check container communication settings

2. If using custom browser management:
   - Update browser initialization code to use new ManagedBrowser class
   - Review browser cleanup procedures

3. For database operations:
   - Check custom database queries for compatibility with new connection pooling
   - Update error handling to work with new retry logic

4. Using the Doctor:
   - Run doctor command for system diagnostics: `crawl4ai doctor`
   - Review generated reports for potential issues
   - Follow recommended fixes for any identified problems


## [v0.3.73] - 2024-11-04
This commit introduces several key enhancements, including improved error handling and robust database operations in `async_database.py`, which now features a connection pool and retry logic for better reliability. Updates to the README.md provide clearer instructions and a better user experience with links to documentation sections. The `.gitignore` file has been refined to include additional directories, while the async web crawler now utilizes a managed browser for more efficient crawling. Furthermore, multiple dependency updates and introduction of the `CustomHTML2Text` class enhance text extraction capabilities.

## [v0.3.73] - 2024-10-24

### Added
- preserve_tags: Added support for preserving specific HTML tags during markdown conversion.
- Smart overlay removal system in AsyncPlaywrightCrawlerStrategy:
  - Automatic removal of popups, modals, and cookie notices
  - Detection and removal of fixed/sticky position elements
  - Cleaning of empty block elements
  - Configurable via `remove_overlay_elements` parameter
- Enhanced screenshot capabilities:
  - Added `screenshot_wait_for` parameter to control timing
  - Improved screenshot handling with existing page context
  - Better error handling with fallback error images
- New URL normalization utilities:
  - `normalize_url` function for consistent URL formatting
  - `is_external_url` function for better link classification
- Custom base directory support for cache storage:
  - New `base_directory` parameter in AsyncWebCrawler
  - Allows specifying alternative locations for `.crawl4ai` folder

### Enhanced
- Link handling improvements:
  - Better duplicate link detection
  - Enhanced internal/external link classification
  - Improved handling of special URL protocols
  - Support for anchor links and protocol-relative URLs
- Configuration refinements:
  - Streamlined social media domain list
  - More focused external content filtering
- LLM extraction strategy:
  - Added support for separate API base URL via `api_base` parameter
  - Better handling of base URLs in configuration

### Fixed
- Screenshot functionality:
  - Resolved issues with screenshot timing and context
  - Improved error handling and recovery
- Link processing:
  - Fixed URL normalization edge cases
  - Better handling of invalid URLs
  - Improved error messages for link processing failures

### Developer Notes
- The overlay removal system uses advanced JavaScript injection for better compatibility
- URL normalization handles special cases like mailto:, tel:, and protocol-relative URLs
- Screenshot system now reuses existing page context for better performance
- Link processing maintains separate dictionaries for internal and external links to ensure uniqueness

## [v0.3.72] - 2024-10-22

### Added
- New `ContentCleaningStrategy` class:
  - Smart content extraction based on text density and element scoring
  - Automatic removal of boilerplate content
  - DOM tree analysis for better content identification
  - Configurable thresholds for content detection
- Advanced proxy support:
  - Added `proxy_config` option for authenticated proxy connections
  - Support for username/password in proxy configuration
- New content output formats:
  - `fit_markdown`: Optimized markdown output with main content focus
  - `fit_html`: Clean HTML with only essential content

### Enhanced
- Image source detection:
  - Support for multiple image source attributes (`src`, `data-src`, `srcset`, etc.)
  - Automatic fallback through potential source attributes
  - Smart handling of srcset attribute
- External content handling:
  - Made external link exclusion optional (disabled by default)
  - Improved detection and handling of social media links
  - Better control over external image filtering

### Fixed
- Image extraction reliability with multiple source attribute checks
- External link and image handling logic for better accuracy

### Developer Notes
- The new `ContentCleaningStrategy` uses configurable thresholds for customization
- Proxy configuration now supports more complex authentication scenarios
- Content extraction process now provides both regular and optimized outputs

## [v0.3.72] - 2024-10-20

### Fixed
- Added support for parsing Base64 encoded images in WebScrapingStrategy

### Added
- Forked and integrated a customized version of the html2text library for more control over Markdown generation
- New configuration options for controlling external content:
  - Ability to exclude all external links
  - Option to specify domains to exclude (default includes major social media platforms)
  - Control over excluding external images

### Changed
- Improved Markdown generation process:
  - Added fine-grained control over character escaping in Markdown output
  - Enhanced handling of code blocks and pre-formatted text
- Updated `AsyncPlaywrightCrawlerStrategy.close()` method to use a shorter sleep time (0.5 seconds instead of 500)
- Enhanced flexibility in `CosineStrategy` with a more generic `load_HF_embedding_model` function

### Improved
- Optimized content scraping and processing for better efficiency
- Enhanced error handling and logging in various components

### Developer Notes
- The customized html2text library is now located within the crawl4ai package
- New configuration options are available in the `config.py` file for external content handling
- The `WebScrapingStrategy` class has been updated to accommodate new external content exclusion options

## [v0.3.71] - 2024-10-19

### Added
- New chunking strategies:
  - `OverlappingWindowChunking`: Allows for overlapping chunks of text, useful for maintaining context between chunks.
  - Enhanced `SlidingWindowChunking`: Improved to handle edge cases and last chunks more effectively.

### Changed
- Updated `CHUNK_TOKEN_THRESHOLD` in config to 2048 tokens (2^11) for better compatibility with most LLM models.
- Improved `AsyncPlaywrightCrawlerStrategy.close()` method to use a shorter sleep time (0.5 seconds instead of 500), significantly reducing wait time when closing the crawler.
- Enhanced flexibility in `CosineStrategy`:
  - Now uses a more generic `load_HF_embedding_model` function, allowing for easier swapping of embedding models.
- Updated `JsonCssExtractionStrategy` and `JsonXPathExtractionStrategy` for better JSON-based extraction.

### Fixed
- Addressed potential issues with the sliding window chunking strategy to ensure all text is properly chunked.

### Developer Notes
- Added more comprehensive docstrings to chunking strategies for better code documentation.
- Removed hardcoded device setting in `CosineStrategy`, now using the automatically detected device.
- Added a new example in `quickstart_async.py` for generating a knowledge graph from crawled content.

These updates aim to provide more flexibility in text processing, improve performance, and enhance the overall capabilities of the crawl4ai library. The new chunking strategies, in particular, offer more options for handling large texts in various scenarios.

## [v0.3.71] - 2024-10-18

### Changes
1. **Version Update**:
   - Updated version number from 0.3.7 to 0.3.71.

2. **Crawler Enhancements**:
   - Added `sleep_on_close` option to AsyncPlaywrightCrawlerStrategy for delayed browser closure.
   - Improved context creation with additional options:
     - Enabled `accept_downloads` and `java_script_enabled`.
     - Added a cookie to enable cookies by default.

3. **Error Handling Improvements**:
   - Enhanced error messages in AsyncWebCrawler's `arun` method.
   - Updated error reporting format for better visibility and consistency.

4. **Performance Optimization**:
   - Commented out automatic page and context closure in `crawl` method to potentially improve performance in certain scenarios.

### Documentation
- Updated quickstart notebook:
  - Changed installation command to use the released package instead of GitHub repository.
  - Updated kernel display name.

### Developer Notes
- Minor code refactoring and cleanup.

## [v0.3.7] - 2024-10-17

### New Features
1. **Enhanced Browser Stealth**: 
   - Implemented `playwright_stealth` for improved bot detection avoidance.
   - Added `StealthConfig` for fine-tuned control over stealth parameters.

2. **User Simulation**:
   - New `simulate_user` option to mimic human-like interactions (mouse movements, clicks, keyboard presses).

3. **Navigator Override**:
   - Added `override_navigator` option to modify navigator properties, further improving bot detection evasion.

4. **Improved iframe Handling**:
   - New `process_iframes` parameter to extract and integrate iframe content into the main page.

5. **Flexible Browser Selection**:
   - Support for choosing between Chromium, Firefox, and WebKit browsers.

6. **Include Links in Markdown**:
    - Added support for including links in Markdown content, by definin g a new flag `include_links_on_markdown` in `crawl` method.   

### Improvements
1. **Better Error Handling**:
   - Enhanced error reporting in WebScrapingStrategy with detailed error messages and suggestions.
   - Added console message and error logging for better debugging.

2. **Image Processing Enhancements**:
   - Improved image dimension updating and filtering logic.

3. **Crawling Flexibility**:
   - Added support for custom viewport sizes.
   - Implemented delayed content retrieval with `delay_before_return_html` parameter.

4. **Performance Optimization**:
   - Adjusted default semaphore count for parallel crawling.

### Bug Fixes
- Fixed an issue where the HTML content could be empty after processing.

### Examples
- Added new example `crawl_with_user_simulation()` demonstrating the use of user simulation and navigator override features.

### Developer Notes
- Refactored code for better maintainability and readability.
- Updated browser launch arguments for improved compatibility and performance.

## [v0.3.6] - 2024-10-12 

### 1. Improved Crawling Control
- **New Hook**: Added `before_retrieve_html` hook in `AsyncPlaywrightCrawlerStrategy`.
- **Delayed HTML Retrieval**: Introduced `delay_before_return_html` parameter to allow waiting before retrieving HTML content.
  - Useful for pages with delayed content loading.
- **Flexible Timeout**: `smart_wait` function now uses `page_timeout` (default 60 seconds) instead of a fixed 30-second timeout.
  - Provides better handling for slow-loading pages.
- **How to use**: Set `page_timeout=your_desired_timeout` (in milliseconds) when calling `crawler.arun()`.

### 2. Browser Type Selection
- Added support for different browser types (Chromium, Firefox, WebKit).
- Users can now specify the browser type when initializing AsyncWebCrawler.
- **How to use**: Set `browser_type="firefox"` or `browser_type="webkit"` when initializing AsyncWebCrawler.

### 3. Screenshot Capture
- Added ability to capture screenshots during crawling.
- Useful for debugging and content verification.
- **How to use**: Set `screenshot=True` when calling `crawler.arun()`.

### 4. Enhanced LLM Extraction Strategy
- Added support for multiple LLM providers (OpenAI, Hugging Face, Ollama).
- **Custom Arguments**: Added support for passing extra arguments to LLM providers via `extra_args` parameter.
- **Custom Headers**: Users can now pass custom headers to the extraction strategy.
- **How to use**: Specify the desired provider and custom arguments when using `LLMExtractionStrategy`.

### 5. iframe Content Extraction
- New feature to process and extract content from iframes.
- **How to use**: Set `process_iframes=True` in the crawl method.

### 6. Delayed Content Retrieval
- Introduced `get_delayed_content` method in `AsyncCrawlResponse`.
- Allows retrieval of content after a specified delay, useful for dynamically loaded content.
- **How to use**: Access `result.get_delayed_content(delay_in_seconds)` after crawling.

### Improvements and Optimizations

#### 1. AsyncWebCrawler Enhancements
- **Flexible Initialization**: Now accepts arbitrary keyword arguments, passed directly to the crawler strategy.
- Allows for more customized setups.

#### 2. Image Processing Optimization
- Enhanced image handling in WebScrapingStrategy.
- Added filtering for small, invisible, or irrelevant images.
- Improved image scoring system for better content relevance.
- Implemented JavaScript-based image dimension updating for more accurate representation.

#### 3. Database Schema Auto-updates
- Automatic database schema updates ensure compatibility with the latest version.

#### 4. Enhanced Error Handling and Logging
- Improved error messages and logging for easier debugging.

#### 5. Content Extraction Refinements
- Refined HTML sanitization process.
- Improved handling of base64 encoded images.
- Enhanced Markdown conversion process.
- Optimized content extraction algorithms.

#### 6. Utility Function Enhancements
- `perform_completion_with_backoff` function now supports additional arguments for more customized API calls to LLM providers.

### Bug Fixes
- Fixed an issue where image tags were being prematurely removed during content extraction.

### Examples and Documentation
- Updated `quickstart_async.py` with examples of:
  - Using custom headers in LLM extraction.
  - Different LLM provider usage (OpenAI, Hugging Face, Ollama).
  - Custom browser type usage.

### Developer Notes
- Refactored code for better maintainability, flexibility, and performance.
- Enhanced type hinting throughout the codebase for improved development experience.
- Expanded error handling for more robust operation.

These updates significantly enhance the flexibility, accuracy, and robustness of crawl4ai, providing users with more control and options for their web crawling and content extraction tasks.

## [v0.3.5] - 2024-09-02

Enhance AsyncWebCrawler with smart waiting and screenshot capabilities

- Implement smart_wait function in AsyncPlaywrightCrawlerStrategy
- Add screenshot support to AsyncCrawlResponse and AsyncWebCrawler
- Improve error handling and timeout management in crawling process
- Fix typo in CrawlResult model (responser_headers -> response_headers)

## [v0.2.77] - 2024-08-04

Significant improvements in text processing and performance:

- 🚀 **Dependency reduction**: Removed dependency on spaCy model for text chunk labeling in cosine extraction strategy.
- 🤖 **Transformer upgrade**: Implemented text sequence classification using a transformer model for labeling text chunks.
- ⚡ **Performance enhancement**: Improved model loading speed due to removal of spaCy dependency.
- 🔧 **Future-proofing**: Laid groundwork for potential complete removal of spaCy dependency in future versions.

These changes address issue #68 and provide a foundation for faster, more efficient text processing in Crawl4AI.

## [v0.2.76] - 2024-08-02

Major improvements in functionality, performance, and cross-platform compatibility! 🚀

- 🐳 **Docker enhancements**: Significantly improved Dockerfile for easy installation on Linux, Mac, and Windows.
- 🌐 **Official Docker Hub image**: Launched our first official image on Docker Hub for streamlined deployment.
- 🔧 **Selenium upgrade**: Removed dependency on ChromeDriver, now using Selenium's built-in capabilities for better compatibility.
- 🖼️ **Image description**: Implemented ability to generate textual descriptions for extracted images from web pages.
- ⚡ **Performance boost**: Various improvements to enhance overall speed and performance.

A big shoutout to our amazing community contributors:
- [@aravindkarnam](https://github.com/aravindkarnam) for developing the textual description extraction feature.
- [@FractalMind](https://github.com/FractalMind) for creating the first official Docker Hub image and fixing Dockerfile errors.
- [@ketonkss4](https://github.com/ketonkss4) for identifying Selenium's new capabilities, helping us reduce dependencies.

Your contributions are driving Crawl4AI forward! 🙌

## [v0.2.75] - 2024-07-19

Minor improvements for a more maintainable codebase:

- 🔄 Fixed typos in `chunking_strategy.py` and `crawler_strategy.py` to improve code readability
- 🔄 Removed `.test_pads/` directory from `.gitignore` to keep our repository clean and organized

These changes may seem small, but they contribute to a more stable and sustainable codebase. By fixing typos and updating our `.gitignore` settings, we're ensuring that our code is easier to maintain and scale in the long run.

## [v0.2.74] - 2024-07-08
A slew of exciting updates to improve the crawler's stability and robustness! 🎉

- 💻 **UTF encoding fix**: Resolved the Windows \"charmap\" error by adding UTF encoding.
- 🛡️ **Error handling**: Implemented MaxRetryError exception handling in LocalSeleniumCrawlerStrategy.
- 🧹 **Input sanitization**: Improved input sanitization and handled encoding issues in LLMExtractionStrategy.
- 🚮 **Database cleanup**: Removed existing database file and initialized a new one.


## [v0.2.73] - 2024-07-03

💡 In this release, we've bumped the version to v0.2.73 and refreshed our documentation to ensure you have the best experience with our project.

* Supporting website need "with-head" mode to crawl the website with head.
* Fixing the installation issues for setup.py and dockerfile.
* Resolve multiple issues.

## [v0.2.72] - 2024-06-30

This release brings exciting updates and improvements to our project! 🎉

* 📚 **Documentation Updates**: Our documentation has been revamped to reflect the latest changes and additions.
* 🚀 **New Modes in setup.py**: We've added support for three new modes in setup.py: default, torch, and transformers. This enhances the project's flexibility and usability.
* 🐳 **Docker File Updates**: The Docker file has been updated to ensure seamless compatibility with the new modes and improvements.
* 🕷️ **Temporary Solution for Headless Crawling**: We've implemented a temporary solution to overcome issues with crawling websites in headless mode.

These changes aim to improve the overall user experience, provide more flexibility, and enhance the project's performance. We're thrilled to share these updates with you and look forward to continuing to evolve and improve our project!

## [0.2.71] - 2024-06-26

**Improved Error Handling and Performance** 🚧

* 🚫 Refactored `crawler_strategy.py` to handle exceptions and provide better error messages, making it more robust and reliable.
* 💻 Optimized the `get_content_of_website_optimized` function in `utils.py` for improved performance, reducing potential bottlenecks.
* 💻 Updated `utils.py` with the latest changes, ensuring consistency and accuracy.
* 🚫 Migrated to `ChromeDriverManager` to resolve Chrome driver download issues, providing a smoother user experience.

These changes focus on refining the existing codebase, resulting in a more stable, efficient, and user-friendly experience. With these improvements, you can expect fewer errors and better performance in the crawler strategy and utility functions.

## [0.2.71] - 2024-06-25
### Fixed
- Speed up twice the extraction function.


## [0.2.6] - 2024-06-22
### Fixed
- Fix issue #19: Update Dockerfile to ensure compatibility across multiple platforms.

## [0.2.5] - 2024-06-18
### Added
- Added five important hooks to the crawler:
  - on_driver_created: Called when the driver is ready for initializations.
  - before_get_url: Called right before Selenium fetches the URL.
  - after_get_url: Called after Selenium fetches the URL.
  - before_return_html: Called when the data is parsed and ready.
  - on_user_agent_updated: Called when the user changes the user_agent, causing the driver to reinitialize.
- Added an example in `quickstart.py` in the example folder under the docs.
- Enhancement issue #24: Replaced inline HTML tags (e.g., DEL, INS, SUB, ABBR) with textual format for better context handling in LLM.
- Maintaining the semantic context of inline tags (e.g., abbreviation, DEL, INS) for improved LLM-friendliness.
- Updated Dockerfile to ensure compatibility across multiple platforms (Hopefully!).

## [v0.2.4] - 2024-06-17
### Fixed
- Fix issue #22: Use MD5 hash for caching HTML files to handle long URLs
