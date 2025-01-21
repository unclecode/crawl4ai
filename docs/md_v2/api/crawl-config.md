# CrawlerRunConfig Parameters Documentation

## Content Processing Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `word_count_threshold` | int | 200 | Minimum word count threshold before processing content |
| `extraction_strategy` | ExtractionStrategy | None | Strategy to extract structured data from crawled pages. When None, uses NoExtractionStrategy |
| `chunking_strategy` | ChunkingStrategy | RegexChunking() | Strategy to chunk content before extraction |
| `markdown_generator` | MarkdownGenerationStrategy | None | Strategy for generating markdown from extracted content |
| `content_filter` | RelevantContentFilter | None | Optional filter to prune irrelevant content |
| `only_text` | bool | False | If True, attempt to extract text-only content where applicable |
| `css_selector` | str | None | CSS selector to extract a specific portion of the page |
| `excluded_tags` | list[str] | [] | List of HTML tags to exclude from processing |
| `keep_data_attributes` | bool | False | If True, retain `data-*` attributes while removing unwanted attributes |
| `keep_aria_label_attribute` | bool | False | If True, retain `aria-label` attributes while removing unwanted attributes |
| `remove_forms` | bool | False | If True, remove all `<form>` elements from the HTML |
| `prettiify` | bool | False | If True, apply `fast_format_html` to produce prettified HTML output |

## Caching Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_mode` | CacheMode | None | Defines how caching is handled. Defaults to CacheMode.ENABLED internally |
| `session_id` | str | None | Optional session ID to persist browser context and page instance |
| `bypass_cache` | bool | False | Legacy parameter, if True acts like CacheMode.BYPASS |
| `disable_cache` | bool | False | Legacy parameter, if True acts like CacheMode.DISABLED |
| `no_cache_read` | bool | False | Legacy parameter, if True acts like CacheMode.WRITE_ONLY |
| `no_cache_write` | bool | False | Legacy parameter, if True acts like CacheMode.READ_ONLY |

## Page Navigation and Timing Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `wait_until` | str | "domcontentloaded" | The condition to wait for when navigating |
| `page_timeout` | int | 60000 | Timeout in milliseconds for page operations like navigation |
| `wait_for` | str | None | CSS selector or JS condition to wait for before extracting content |
| `wait_for_images` | bool | True | If True, wait for images to load before extracting content |
| `delay_before_return_html` | float | 0.1 | Delay in seconds before retrieving final HTML |
| `mean_delay` | float | 0.1 | Mean base delay between requests when calling arun_many |
| `max_range` | float | 0.3 | Max random additional delay range for requests in arun_many |
| `semaphore_count` | int | 5 | Number of concurrent operations allowed |

## Page Interaction Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `js_code` | str or list[str] | None | JavaScript code/snippets to run on the page |
| `js_only` | bool | False | If True, indicates subsequent calls are JS-driven updates |
| `ignore_body_visibility` | bool | True | If True, ignore whether the body is visible before proceeding |
| `scan_full_page` | bool | False | If True, scroll through the entire page to load all content |
| `scroll_delay` | float | 0.2 | Delay in seconds between scroll steps if scan_full_page is True |
| `process_iframes` | bool | False | If True, attempts to process and inline iframe content |
| `remove_overlay_elements` | bool | False | If True, remove overlays/popups before extracting HTML |
| `simulate_user` | bool | False | If True, simulate user interactions for anti-bot measures |
| `override_navigator` | bool | False | If True, overrides navigator properties for more human-like behavior |
| `magic` | bool | False | If True, attempts automatic handling of overlays/popups |
| `adjust_viewport_to_content` | bool | False | If True, adjust viewport according to page content dimensions |

## Media Handling Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `screenshot` | bool | False | Whether to take a screenshot after crawling |
| `screenshot_wait_for` | float | None | Additional wait time before taking a screenshot |
| `screenshot_height_threshold` | int | 20000 | Threshold for page height to decide screenshot strategy |
| `pdf` | bool | False | Whether to generate a PDF of the page |
| `image_description_min_word_threshold` | int | 50 | Minimum words for image description extraction |
| `image_score_threshold` | int | 3 | Minimum score threshold for processing an image |
| `exclude_external_images` | bool | False | If True, exclude all external images from processing |

## Link and Domain Handling Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exclude_social_media_domains` | list[str] | SOCIAL_MEDIA_DOMAINS | List of domains to exclude for social media links |
| `exclude_external_links` | bool | False | If True, exclude all external links from the results |
| `exclude_social_media_links` | bool | False | If True, exclude links pointing to social media domains |
| `exclude_domains` | list[str] | [] | List of specific domains to exclude from results |

## Debugging and Logging Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `verbose` | bool | True | Enable verbose logging |
| `log_console` | bool | False | If True, log console messages from the page |