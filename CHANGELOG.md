# Changelog

## [v0.3.73] - 2024-10-24

### Added
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
- Added support for parsing Base64 encoded images in WebScrappingStrategy

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
- The `WebScrappingStrategy` class has been updated to accommodate new external content exclusion options

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
- Updated `JsonCssExtractionStrategy` and `JsonXPATHExtractionStrategy` for better JSON-based extraction.

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
   - Enhanced error reporting in WebScrappingStrategy with detailed error messages and suggestions.
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

## Improvements and Optimizations

### 1. AsyncWebCrawler Enhancements
- **Flexible Initialization**: Now accepts arbitrary keyword arguments, passed directly to the crawler strategy.
- Allows for more customized setups.

### 2. Image Processing Optimization
- Enhanced image handling in WebScrappingStrategy.
- Added filtering for small, invisible, or irrelevant images.
- Improved image scoring system for better content relevance.
- Implemented JavaScript-based image dimension updating for more accurate representation.

### 3. Database Schema Auto-updates
- Automatic database schema updates ensure compatibility with the latest version.

### 4. Enhanced Error Handling and Logging
- Improved error messages and logging for easier debugging.

### 5. Content Extraction Refinements
- Refined HTML sanitization process.
- Improved handling of base64 encoded images.
- Enhanced Markdown conversion process.
- Optimized content extraction algorithms.

### 6. Utility Function Enhancements
- `perform_completion_with_backoff` function now supports additional arguments for more customized API calls to LLM providers.

## Bug Fixes
- Fixed an issue where image tags were being prematurely removed during content extraction.

## Examples and Documentation
- Updated `quickstart_async.py` with examples of:
  - Using custom headers in LLM extraction.
  - Different LLM provider usage (OpenAI, Hugging Face, Ollama).
  - Custom browser type usage.

## Developer Notes
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

## [0.2.4] - 2024-06-17
### Fixed
- Fix issue #22: Use MD5 hash for caching HTML files to handle long URLs
