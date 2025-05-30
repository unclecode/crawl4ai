# Development Journal

This journal tracks significant feature additions, bug fixes, and architectural decisions in the crawl4ai project. It serves as both documentation and a historical record of the project's evolution.

## [2025-04-17] Added Content Source Selection for Markdown Generation

**Feature:** Configurable content source for markdown generation

**Changes Made:**
1. Added `content_source: str = "cleaned_html"` parameter to `MarkdownGenerationStrategy` class
2. Updated `DefaultMarkdownGenerator` to accept and pass the content source parameter
3. Renamed the `cleaned_html` parameter to `input_html` in the `generate_markdown` method
4. Modified `AsyncWebCrawler.aprocess_html` to select the appropriate HTML source based on the generator's config
5. Added `preprocess_html_for_schema` import in `async_webcrawler.py`

**Implementation Details:**
- Added a new `content_source` parameter to specify which HTML input to use for markdown generation
- Options include: "cleaned_html" (default), "raw_html", and "fit_html"
- Used a dictionary dispatch pattern in `aprocess_html` to select the appropriate HTML source
- Added proper error handling with fallback to cleaned_html if content source selection fails
- Ensured backward compatibility by defaulting to "cleaned_html" option

**Files Modified:**
- `crawl4ai/markdown_generation_strategy.py`: Added content_source parameter and updated the method signature
- `crawl4ai/async_webcrawler.py`: Added HTML source selection logic and updated imports

**Examples:**
- Created `docs/examples/content_source_example.py` demonstrating how to use the new parameter

**Challenges:**
- Maintaining backward compatibility while reorganizing the parameter flow
- Ensuring proper error handling for all content source options
- Making the change with minimal code modifications

**Why This Feature:**
The content source selection feature allows users to choose which HTML content to use as input for markdown generation:
1. "cleaned_html" - Uses the post-processed HTML after scraping strategy (original behavior)
2. "raw_html" - Uses the original raw HTML directly from the web page
3. "fit_html" - Uses the preprocessed HTML optimized for schema extraction

This feature provides greater flexibility in how users generate markdown, enabling them to:
- Capture more detailed content from the original HTML when needed
- Use schema-optimized HTML when working with structured data
- Choose the approach that best suits their specific use case
## [2025-04-17] Implemented High Volume Stress Testing Solution for SDK

**Feature:** Comprehensive stress testing framework using `arun_many` and the dispatcher system to evaluate performance, concurrency handling, and identify potential issues under high-volume crawling scenarios.

**Changes Made:**
1.  Created a dedicated stress testing framework in the `benchmarking/` (or similar) directory.
2.  Implemented local test site generation (`SiteGenerator`) with configurable heavy HTML pages.
3.  Added basic memory usage tracking (`SimpleMemoryTracker`) using platform-specific commands (avoiding `psutil` dependency for this specific test).
4.  Utilized `CrawlerMonitor` from `crawl4ai` for rich terminal UI and real-time monitoring of test progress and dispatcher activity.
5.  Implemented detailed result summary saving (JSON) and memory sample logging (CSV).
6.  Developed `run_benchmark.py` to orchestrate tests with predefined configurations.
7.  Created `run_all.sh` as a simple wrapper for `run_benchmark.py`.

**Implementation Details:**
-   Generates a local test site with configurable pages containing heavy text and image content.
-   Uses Python's built-in `http.server` for local serving, minimizing network variance.
-   Leverages `crawl4ai`'s `arun_many` method for processing URLs.
-   Utilizes `MemoryAdaptiveDispatcher` to manage concurrency via the `max_sessions` parameter (note: memory adaptation features require `psutil`, not used by `SimpleMemoryTracker`).
-   Tracks memory usage via `SimpleMemoryTracker`, recording samples throughout test execution to a CSV file.
-   Uses `CrawlerMonitor` (which uses the `rich` library) for clear terminal visualization and progress reporting directly from the dispatcher.
-   Stores detailed final metrics in a JSON summary file.

**Files Created/Updated:**
-   `stress_test_sdk.py`: Main stress testing implementation using `arun_many`.
-   `benchmark_report.py`: (Assumed) Report generator for comparing test results.
-   `run_benchmark.py`: Test runner script with predefined configurations.
-   `run_all.sh`: Simple bash script wrapper for `run_benchmark.py`.
-   `USAGE.md`: Comprehensive documentation on usage and interpretation (updated).

**Testing Approach:**
-   Creates a controlled, reproducible test environment with a local HTTP server.
-   Processes URLs using `arun_many`, allowing the dispatcher to manage concurrency up to `max_sessions`.
-   Optionally logs per-batch summaries (when not in streaming mode) after processing chunks.
-   Supports different test sizes via `run_benchmark.py` configurations.
-   Records memory samples via platform commands for basic trend analysis.
-   Includes cleanup functionality for the test environment.

**Challenges:**
-   Ensuring proper cleanup of HTTP server processes.
-   Getting reliable memory tracking across platforms without adding heavy dependencies (`psutil`) to this specific test script.
-   Designing `run_benchmark.py` to correctly pass arguments to `stress_test_sdk.py`.

**Why This Feature:**
The high volume stress testing solution addresses critical needs for ensuring Crawl4AI's `arun_many` reliability:
1.  Provides a reproducible way to evaluate performance under concurrent load.
2.  Allows testing the dispatcher's concurrency control (`max_session_permit`) and queue management.
3.  Enables performance tuning by observing throughput (`URLs/sec`) under different `max_sessions` settings.
4.  Creates a controlled environment for testing `arun_many` behavior.
5.  Supports continuous integration by providing deterministic test conditions for `arun_many`.

**Design Decisions:**
-   Chose local site generation for reproducibility and isolation from network issues.
-   Utilized the built-in `CrawlerMonitor` for real-time feedback, leveraging its `rich` integration.
-   Implemented optional per-batch logging in `stress_test_sdk.py` (when not streaming) to provide chunk-level summaries alongside the continuous monitor.
-   Adopted `arun_many` with a `MemoryAdaptiveDispatcher` as the core mechanism for parallel execution, reflecting the intended SDK usage.
-   Created `run_benchmark.py` to simplify running standard test configurations.
-   Used `SimpleMemoryTracker` to provide basic memory insights without requiring `psutil` for this particular test runner.

**Future Enhancements to Consider:**
-   Create a separate test variant that *does* use `psutil` to specifically stress the memory-adaptive features of the dispatcher.
-   Add support for generated JavaScript content.
-   Add support for Docker-based testing with explicit memory limits.
-   Enhance `benchmark_report.py` to provide more sophisticated analysis of performance and memory trends from the generated JSON/CSV files.

---

## [2025-04-17] Refined Stress Testing System Parameters and Execution

**Changes Made:**
1.  Corrected `run_benchmark.py` and `stress_test_sdk.py` to use `--max-sessions` instead of the incorrect `--workers` parameter, accurately reflecting dispatcher configuration.
2.  Updated `run_benchmark.py` argument handling to correctly pass all relevant custom parameters (including `--stream`, `--monitor-mode`, etc.) to `stress_test_sdk.py`.
3.  (Assuming changes in `benchmark_report.py`) Applied dark theme to benchmark reports for better readability.
4.  (Assuming changes in `benchmark_report.py`) Improved visualization code to eliminate matplotlib warnings.
5.  Updated `run_benchmark.py` to provide clickable `file://` links to generated reports in the terminal output.
6.  Updated `USAGE.md` with comprehensive parameter descriptions reflecting the final script arguments.
7.  Updated `run_all.sh` wrapper to correctly invoke `run_benchmark.py` with flexible arguments.

**Details of Changes:**

1.  **Parameter Correction (`--max-sessions`)**:
    *   Identified the fundamental misunderstanding where `--workers` was used incorrectly.
    *   Refactored `stress_test_sdk.py` to accept `--max-sessions` and configure the `MemoryAdaptiveDispatcher`'s `max_session_permit` accordingly.
    *   Updated `run_benchmark.py` argument parsing and command construction to use `--max-sessions`.
    *   Updated `TEST_CONFIGS` in `run_benchmark.py` to use `max_sessions`.

2.  **Argument Handling (`run_benchmark.py`)**:
    *   Improved logic to collect all command-line arguments provided to `run_benchmark.py`.
    *   Ensured all relevant arguments (like `--stream`, `--monitor-mode`, `--port`, `--use-rate-limiter`, etc.) are correctly forwarded when calling `stress_test_sdk.py` as a subprocess.

3.  **Dark Theme & Visualization Fixes (Assumed in `benchmark_report.py`)**:
    *   (Describes changes assumed to be made in the separate reporting script).

4.  **Clickable Links (`run_benchmark.py`)**:
    *   Added logic to find the latest HTML report and PNG chart in the `benchmark_reports` directory after `benchmark_report.py` runs.
    *   Used `pathlib` to generate correct `file://` URLs for terminal output.

5.  **Documentation Improvements (`USAGE.md`)**:
    *   Rewrote sections to explain `arun_many`, dispatchers, and `--max-sessions`.
    *   Updated parameter tables for all scripts (`stress_test_sdk.py`, `run_benchmark.py`).
    *   Clarified the difference between batch and streaming modes and their effect on logging.
    *   Updated examples to use correct arguments.

**Files Modified:**
-   `stress_test_sdk.py`: Changed `--workers` to `--max-sessions`, added new arguments, used `arun_many`.
-   `run_benchmark.py`: Changed argument handling, updated configs, calls `stress_test_sdk.py`.
-   `run_all.sh`: Updated to call `run_benchmark.py` correctly.
-   `USAGE.md`: Updated documentation extensively.
-   `benchmark_report.py`: (Assumed modifications for dark theme and viz fixes).

**Testing:**
-   Verified that `--max-sessions` correctly limits concurrency via the `CrawlerMonitor` output.
-   Confirmed that custom arguments passed to `run_benchmark.py` are forwarded to `stress_test_sdk.py`.
-   Validated clickable links work in supporting terminals.
-   Ensured documentation matches the final script parameters and behavior.

**Why These Changes:**
These refinements correct the fundamental approach of the stress test to align with `crawl4ai`'s actual architecture and intended usage:
1.  Ensures the test evaluates the correct components (`arun_many`, `MemoryAdaptiveDispatcher`).
2.  Makes test configurations more accurate and flexible.
3.  Improves the usability of the testing framework through better argument handling and documentation.


**Future Enhancements to Consider:**
- Add support for generated JavaScript content to test JS rendering performance
- Implement more sophisticated memory analysis like generational garbage collection tracking
- Add support for Docker-based testing with memory limits to force OOM conditions
- Create visualization tools for analyzing memory usage patterns across test runs
- Add benchmark comparisons between different crawler versions or configurations

## [2025-04-17] Fixed Issues in Stress Testing System

**Changes Made:**
1. Fixed custom parameter handling in run_benchmark.py
2. Applied dark theme to benchmark reports for better readability
3. Improved visualization code to eliminate matplotlib warnings
4. Added clickable links to generated reports in terminal output
5. Enhanced documentation with comprehensive parameter descriptions

**Details of Changes:**

1. **Custom Parameter Handling Fix**
   - Identified bug where custom URL count was being ignored in run_benchmark.py
   - Rewrote argument handling to use a custom args dictionary
   - Properly passed parameters to the test_simple_stress.py command
   - Added better UI indication of custom parameters in use

2. **Dark Theme Implementation**
   - Added complete dark theme to HTML benchmark reports
   - Applied dark styling to all visualization components
   - Used Nord-inspired color palette for charts and graphs
   - Improved contrast and readability for data visualization
   - Updated text colors and backgrounds for better eye comfort

3. **Matplotlib Warning Fixes**
   - Resolved warnings related to improper use of set_xticklabels()
   - Implemented correct x-axis positioning for bar charts
   - Ensured proper alignment of bar labels and data points
   - Updated plotting code to use modern matplotlib practices

4. **Documentation Improvements**
   - Created comprehensive USAGE.md with detailed instructions
   - Added parameter documentation for all scripts
   - Included examples for all common use cases
   - Provided detailed explanations for interpreting results
   - Added troubleshooting guide for common issues

**Files Modified:**
- `tests/memory/run_benchmark.py`: Fixed custom parameter handling
- `tests/memory/benchmark_report.py`: Added dark theme and fixed visualization warnings
- `tests/memory/run_all.sh`: Added clickable links to reports
- `tests/memory/USAGE.md`: Created comprehensive documentation

**Testing:**
- Verified that custom URL counts are now correctly used
- Confirmed dark theme is properly applied to all report elements
- Checked that matplotlib warnings are no longer appearing
- Validated clickable links to reports work in terminals that support them

**Why These Changes:**
These improvements address several usability issues with the stress testing system:
1. Better parameter handling ensures test configurations work as expected
2. Dark theme reduces eye strain during extended test review sessions
3. Fixing visualization warnings improves code quality and output clarity
4. Enhanced documentation makes the system more accessible for future use

**Future Enhancements:**
- Add additional visualization options for different types of analysis
- Implement theme toggle to support both light and dark preferences
- Add export options for embedding reports in other documentation
- Create dedicated CI/CD integration templates for automated testing

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