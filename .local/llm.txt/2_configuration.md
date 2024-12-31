# Core Configurations

## BrowserConfig
`BrowserConfig` centralizes all parameters required to set up and manage a browser instance and its context. This configuration ensures consistent and documented browser behavior for the crawler. Below is a detailed explanation of each parameter and its optimal use cases.

### Parameters and Use Cases

#### `browser_type`
- **Description**: Specifies the type of browser to launch.
  - Supported values: `"chromium"`, `"firefox"`, `"webkit"`
  - Default: `"chromium"`
- **Use Case**:
  - Use `"chromium"` for general-purpose crawling with modern web standards.
  - Use `"firefox"` when testing against Firefox-specific behavior.
  - Use `"webkit"` for testing Safari-like environments.

#### `headless`
- **Description**: Determines whether the browser runs in headless mode (no GUI).
  - Default: `True`
- **Use Case**:
  - Enable for faster, automated operations without UI overhead.
  - Disable (`False`) when debugging or inspecting browser behavior visually.

#### `use_managed_browser`
- **Description**: Enables advanced manipulation via a managed browser approach.
  - Default: `False`
- **Use Case**:
  - Use when fine-grained control is needed over browser sessions, such as debugging network requests or reusing sessions.

#### `debugging_port`
- **Description**: Port for remote debugging.
  - Default: 9222
- **Use Case**:
  - Use for debugging browser sessions with DevTools or external tools.

#### `use_persistent_context`
- **Description**: Uses a persistent browser context (e.g., saved profiles).
  - Automatically enables `use_managed_browser`.
  - Default: `False`
- **Use Case**:
  - Persistent login sessions for authenticated crawling.
  - Retaining cookies or local storage across multiple runs.

#### `user_data_dir`
- **Description**: Path to a directory for storing persistent browser data.
  - Default: `None`
- **Use Case**:
  - Specify a directory to save browser profiles for multi-run crawls or debugging.

#### `chrome_channel`
- **Description**: Specifies the Chrome channel to launch (e.g., `"chrome"`, `"msedge"`).
  - Applies only when `browser_type` is `"chromium"`.
  - Default: `"chrome"`
- **Use Case**:
  - Use `"msedge"` for compatibility testing with Edge browsers.

#### `proxy` and `proxy_config`
- **Description**:
  - `proxy`: Proxy server URL for the browser.
  - `proxy_config`: Detailed proxy configuration.
  - Default: `None`
- **Use Case**:
  - Set `proxy` for single-proxy setups.
  - Use `proxy_config` for advanced configurations, such as authenticated proxies or regional routing.

#### `viewport_width` and `viewport_height`
- **Description**: Sets the default browser viewport dimensions.
  - Default: `1080` (width), `600` (height)
- **Use Case**:
  - Adjust for crawling responsive layouts or specific device emulations.

#### `accept_downloads` and `downloads_path`
- **Description**:
  - `accept_downloads`: Allows file downloads.
  - `downloads_path`: Directory for storing downloads.
  - Default: `False`, `None`
- **Use Case**:
  - Use when downloading and analyzing files like PDFs or spreadsheets.

#### `storage_state`
- **Description**: Specifies cookies and local storage state.
  - Default: `None`
- **Use Case**:
  - Provide state data for authenticated or preconfigured sessions.

#### `ignore_https_errors`
- **Description**: Ignores HTTPS certificate errors.
  - Default: `True`
- **Use Case**:
  - Enable for crawling sites with invalid certificates (testing environments).

#### `java_script_enabled`
- **Description**: Toggles JavaScript execution in pages.
  - Default: `True`
- **Use Case**:
  - Disable for simpler, faster crawls where JavaScript is unnecessary.

#### `cookies`
- **Description**: List of cookies to add to the browser context.
  - Default: `[]`
- **Use Case**:
  - Use for authenticated or preconfigured crawling scenarios.

#### `headers`
- **Description**: Extra HTTP headers applied to all requests.
  - Default: `{}`
- **Use Case**:
  - Customize headers for API-like crawling or bypassing bot detections.

#### `user_agent` and `user_agent_mode`
- **Description**:
  - `user_agent`: Custom User-Agent string.
  - `user_agent_mode`: Mode for generating User-Agent (e.g., `"random"`).
  - Default: Standard Chromium-based User-Agent.
- **Use Case**:
  - Set static User-Agent for consistent identification.
  - Use `"random"` mode to reduce bot detection likelihood.

#### `text_mode`
- **Description**: Disables images and other rich content for faster load times.
  - Default: `False`
- **Use Case**:
  - Enable for text-only extraction tasks where speed is prioritized.

#### `light_mode`
- **Description**: Disables background features for performance gains.
  - Default: `False`
- **Use Case**:
  - Enable for high-performance crawls on resource-constrained environments.

#### `extra_args`
- **Description**: Additional command-line arguments for browser execution.
  - Default: `[]`
- **Use Case**:
  - Use for advanced browser configurations like WebRTC or GPU tuning.

#### `verbose`
- **Description**: Enable verbose logging of browser operations.
  - Default: `True`
- **Use Case**:
  - Enable for detailed logging during development and debugging.
  - Disable in production for better performance.

#### `sleep_on_close`
- **Description**: Adds a delay before closing the browser.
  - Default: `False`
- **Use Case**:
  - Enable when you need to ensure all browser operations are complete before closing.

## CrawlerRunConfig
The `CrawlerRunConfig` class centralizes parameters for controlling crawl operations. This configuration covers content extraction, page interactions, caching, and runtime behaviors. Below is an exhaustive breakdown of parameters and their best-use scenarios.

### Parameters and Use Cases

#### Content Processing Parameters

##### `word_count_threshold`
- **Description**: Minimum word count threshold for processing content.
  - Default: `200`
- **Use Case**:
  - Set a higher threshold for content-heavy pages to skip lightweight or irrelevant content.

##### `extraction_strategy`
- **Description**: Strategy for extracting structured data from crawled pages.
  - Default: `None` (uses `NoExtractionStrategy` by default).
- **Use Case**:
  - Use for schema-driven extraction when working with well-defined data models like JSON.

##### `chunking_strategy`
- **Description**: Strategy to chunk content before extraction.
  - Default: `RegexChunking()`.
- **Use Case**:
  - Use NLP-based chunking for semantic extractions or regex for predictable text blocks.

##### `markdown_generator`
- **Description**: Strategy for generating Markdown output.
  - Default: `None`.
- **Use Case**:
  - Use custom Markdown strategies for AI-ready outputs like RAG pipelines.

##### `content_filter`
- **Description**: Optional filter to prune irrelevant content.
  - Default: `None`.
- **Use Case**:
  - Use relevance-based filters for focused crawls, e.g., keyword-specific searches.

##### `only_text`
- **Description**: Extracts text-only content where applicable.
  - Default: `False`.
- **Use Case**:
  - Enable for extracting clean text without HTML tags or rich content.

##### `css_selector`
- **Description**: CSS selector to extract a specific portion of the page.
  - Default: `None`.
- **Use Case**:
  - Use when targeting specific page elements, like articles or headlines.

##### `excluded_tags`
- **Description**: List of HTML tags to exclude from processing.
  - Default: `None`.
- **Use Case**:
  - Remove elements like `<script>` or `<style>` during text extraction.

##### `keep_data_attributes`
- **Description**: Retain `data-*` attributes in the HTML.
  - Default: `False`.
- **Use Case**:
  - Enable for extracting custom attributes in HTML structures.

##### `remove_forms`
- **Description**: Removes all `<form>` elements from the page.
  - Default: `False`.
- **Use Case**:
  - Use when forms are irrelevant and clutter the extracted content.

##### `prettiify`
- **Description**: Beautifies the HTML output.
  - Default: `False`.
- **Use Case**:
  - Enable for generating readable HTML outputs.

---

#### Caching Parameters

##### `cache_mode`
- **Description**: Controls how caching is handled.
  - Default: `CacheMode.ENABLED`.
- **Use Case**:
  - Use `WRITE_ONLY` mode for crawls where fresh content is critical.

##### `session_id`
- **Description**: Specifies a session ID to persist browser context.
  - Default: `None`.
- **Use Case**:
  - Use for maintaining login states or multi-page workflows.

##### `bypass_cache`, `disable_cache`, `no_cache_read`, `no_cache_write`
- **Description**: Legacy parameters for cache handling.
  - Default: `False`.
- **Use Case**:
  - These options provide finer control when overriding default caching behaviors.

---

#### Page Navigation and Timing Parameters

##### `wait_until`
- **Description**: Defines the navigation wait condition (e.g., `"domcontentloaded"`).
  - Default: `"domcontentloaded"`.
- **Use Case**:
  - Adjust to `"networkidle"` for pages with heavy JavaScript rendering.

##### `page_timeout`
- **Description**: Timeout in milliseconds for page operations.
  - Default: `60000` (60 seconds).
- **Use Case**:
  - Increase for slow-loading pages or complex sites.

##### `wait_for`
- **Description**: CSS selector or JS condition to wait for before extraction.
  - Default: `None`.
- **Use Case**:
  - Use for dynamic content that requires specific elements to load.

##### `wait_for_images`
- **Description**: Waits for images to load before content extraction.
  - Default: `True`.
- **Use Case**:
  - Disable for faster crawls when image data isn’t required.

##### `delay_before_return_html`
- **Description**: Delay in seconds before retrieving HTML.
  - Default: `0.1`.
- **Use Case**:
  - Use for ensuring final DOM updates are captured.

##### `mean_delay` and `max_range`
- **Description**: Configures base and random delays between requests.
  - Default: `0.1` (mean), `0.3` (max).
- **Use Case**:
  - Increase for stealthy crawls to avoid bot detection.

##### `semaphore_count`
- **Description**: Number of concurrent operations allowed.
  - Default: `5`.
- **Use Case**:
  - Adjust based on system resources and network limitations.

---

#### Page Interaction Parameters

##### `js_code`
- **Description**: JavaScript code or snippets to execute on the page.
  - Default: `None`.
- **Use Case**:
  - Use for custom interactions like clicking tabs or dynamically loading content.

##### `js_only`
- **Description**: Indicates subsequent calls rely only on JS updates.
  - Default: `False`.
- **Use Case**:
  - Enable for single-page applications (SPAs) with dynamic content.

##### `scan_full_page`
- **Description**: Simulates scrolling to load all content.
  - Default: `False`.
- **Use Case**:
  - Use for infinite-scroll pages or loading all dynamic elements.

##### `adjust_viewport_to_content`
- **Description**: Adjusts viewport to match content dimensions.
  - Default: `False`.
- **Use Case**:
  - Enable for capturing content-heavy pages fully.

---

#### Media Handling Parameters

##### `screenshot`
- **Description**: Captures a screenshot after crawling.
  - Default: `False`.
- **Use Case**:
  - Enable for visual debugging or reporting purposes.

##### `pdf`
- **Description**: Generates a PDF of the page.
  - Default: `False`.
- **Use Case**:
  - Use for archiving or sharing rendered page outputs.

##### `image_description_min_word_threshold` and `image_score_threshold`
- **Description**: Controls thresholds for image description extraction and processing.
  - Default: `50` (words), `3` (score).
- **Use Case**:
  - Adjust for higher relevance or descriptive quality of image metadata.

---

#### Debugging and Logging Parameters

##### `verbose`
- **Description**: Enables detailed logging.
  - Default: `True`.
- **Use Case**:
  - Use for troubleshooting or analyzing crawler behavior.

##### `log_console`
- **Description**: Logs browser console messages.
  - Default: `False`.
- **Use Case**:
  - Enable when debugging JavaScript errors on pages.

##### `parser_type`
- **Description**: Type of parser to use for HTML parsing.
  - Default: `"lxml"`
- **Use Case**:
  - Use when specific HTML parsing requirements are needed.
  - `"lxml"` provides good performance and standards compliance.

##### `prettiify`
- **Description**: Apply `fast_format_html` to produce prettified HTML output.
  - Default: `False`
- **Use Case**:
  - Enable for better readability of extracted HTML content.
  - Useful during development and debugging.

##### `fetch_ssl_certificate`
- **Description**: Fetch and store SSL certificate information during crawling.
  - Default: `False`
- **Use Case**:
  - Enable when SSL certificate analysis is required.
  - Useful for security audits and certificate validation.

##### `url`
- **Description**: Target URL for the crawl operation.
  - Default: `None`
- **Use Case**:
  - Set when initializing a crawler for a specific URL.
  - Can be overridden during actual crawl operations.

##### `log_console`
- **Description**: Log browser console messages during crawling.
  - Default: `False`
- **Use Case**:
  - Enable to capture JavaScript console output.
  - Useful for debugging JavaScript-heavy pages.
