# Development Journal

This journal tracks significant feature additions, bug fixes, and architectural decisions in the crawl4ai project. It serves as both documentation and a historical record of the project's evolution.

## [2025-04-09] Added MHTML Capture Feature

**Feature:** MHTML snapshot capture of crawled pages

**Changes Made:**
1. Added `capture_mhtml: bool = False` parameter to `CrawlerRunConfig` class
2. Added `mhtml: Optional[str] = None` field to `CrawlResult` model
3. Added `mhtml_data: Optional[str] = None` field to `AsyncCrawlResponse` class
4. Implemented `capture_mhtml()` method in `AsyncPlaywrightCrawlerStrategy` class to capture MHTML via CDP
5. Modified the crawler to capture MHTML when enabled and pass it to the result

**Implementation Details:**
- MHTML capture uses Chrome DevTools Protocol (CDP) via Playwright's CDP session API
- The implementation waits for page to fully load before capturing MHTML content
- Enhanced waiting for JavaScript content with requestAnimationFrame for better JS content capture
- We ensure all browser resources are properly cleaned up after capture

**Files Modified:**
- `crawl4ai/models.py`: Added the mhtml field to CrawlResult
- `crawl4ai/async_configs.py`: Added capture_mhtml parameter to CrawlerRunConfig
- `crawl4ai/async_crawler_strategy.py`: Implemented MHTML capture logic
- `crawl4ai/async_webcrawler.py`: Added mapping from AsyncCrawlResponse.mhtml_data to CrawlResult.mhtml

**Testing:**
- Created comprehensive tests in `tests/20241401/test_mhtml.py` covering:
  - Capturing MHTML when enabled
  - Ensuring mhtml is None when disabled explicitly
  - Ensuring mhtml is None by default
  - Capturing MHTML on JavaScript-enabled pages

**Challenges:**
- Had to improve page loading detection to ensure JavaScript content was fully rendered
- Tests needed to be run independently due to Playwright browser instance management
- Modified test expected content to match actual MHTML output

**Why This Feature:**
The MHTML capture feature allows users to capture complete web pages including all resources (CSS, images, etc.) in a single file. This is valuable for:
1. Offline viewing of captured pages
2. Creating permanent snapshots of web content for archival
3. Ensuring consistent content for later analysis, even if the original site changes

**Future Enhancements to Consider:**
- Add option to save MHTML to file
- Support for filtering what resources get included in MHTML
- Add support for specifying MHTML capture options

## [2025-04-10] Added Network Request and Console Message Capturing

**Feature:** Comprehensive capturing of network requests/responses and browser console messages during crawling

**Changes Made:**
1. Added `capture_network_requests: bool = False` and `capture_console_messages: bool = False` parameters to `CrawlerRunConfig` class
2. Added `network_requests: Optional[List[Dict[str, Any]]] = None` and `console_messages: Optional[List[Dict[str, Any]]] = None` fields to both `AsyncCrawlResponse` and `CrawlResult` models
3. Implemented event listeners in `AsyncPlaywrightCrawlerStrategy._crawl_web()` to capture browser network events and console messages
4. Added proper event listener cleanup in the finally block to prevent resource leaks
5. Modified the crawler flow to pass captured data from AsyncCrawlResponse to CrawlResult

**Implementation Details:**
- Network capture uses Playwright event listeners (`request`, `response`, and `requestfailed`) to record all network activity
- Console capture uses Playwright event listeners (`console` and `pageerror`) to record console messages and errors
- Each network event includes metadata like URL, headers, status, and timing information
- Each console message includes type, text content, and source location when available
- All captured events include timestamps for chronological analysis
- Error handling ensures even failed capture attempts won't crash the main crawling process

**Files Modified:**
- `crawl4ai/models.py`: Added new fields to AsyncCrawlResponse and CrawlResult
- `crawl4ai/async_configs.py`: Added new configuration parameters to CrawlerRunConfig
- `crawl4ai/async_crawler_strategy.py`: Implemented capture logic using event listeners
- `crawl4ai/async_webcrawler.py`: Added data transfer from AsyncCrawlResponse to CrawlResult

**Documentation:**
- Created detailed documentation in `docs/md_v2/advanced/network-console-capture.md`
- Added feature to site navigation in `mkdocs.yml`
- Updated CrawlResult documentation in `docs/md_v2/api/crawl-result.md`
- Created comprehensive example in `docs/examples/network_console_capture_example.py`

**Testing:**
- Created `tests/general/test_network_console_capture.py` with tests for:
  - Verifying capture is disabled by default
  - Testing network request capturing
  - Testing console message capturing
  - Ensuring both capture types can be enabled simultaneously
  - Checking correct content is captured in expected formats

**Challenges:**
- Initial implementation had synchronous/asynchronous mismatches in event handlers
- Needed to fix type of property access vs. method calls in handlers
- Required careful cleanup of event listeners to prevent memory leaks

**Why This Feature:**
The network and console capture feature provides deep visibility into web page activity, enabling:
1. Debugging complex web applications by seeing all network requests and errors
2. Security analysis to detect unexpected third-party requests and data flows
3. Performance profiling to identify slow-loading resources
4. API discovery in single-page applications
5. Comprehensive analysis of web application behavior

**Future Enhancements to Consider:**
- Option to filter captured events by type, domain, or content
- Support for capturing response bodies (with size limits)
- Aggregate statistics calculation for performance metrics
- Integration with visualization tools for network waterfall analysis
- Exporting captures in HAR format for use with external tools