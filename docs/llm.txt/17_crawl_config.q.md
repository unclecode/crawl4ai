content_processing: Configure word count threshold for processing crawled content | minimum words, content length, processing threshold | word_count_threshold=200
extraction_config: Set strategy for extracting structured data from pages | data extraction, content parsing, structured data | extraction_strategy=ExtractionStrategy()
chunking_setup: Configure content chunking strategy for processing | content splitting, text chunks, segmentation | chunking_strategy=RegexChunking()
content_filtering: Filter irrelevant content using RelevantContentFilter | content pruning, filtering, relevance | content_filter=RelevantContentFilter()
text_extraction: Extract only text content from web pages | text-only, content extraction, plain text | only_text=True
css_selection: Target specific page elements using CSS selectors | element selection, content targeting, DOM selection | css_selector=".main-content"
html_cleaning: Configure HTML tag exclusion and attribute handling | tag removal, attribute filtering, HTML cleanup | excluded_tags=["script", "style"], keep_data_attributes=True
caching_config: Control page caching behavior and session persistence | cache settings, session management, cache control | cache_mode=CacheMode.ENABLED, session_id="session1"
page_navigation: Configure page loading and navigation timing | page timeout, loading conditions, navigation settings | wait_until="domcontentloaded", page_timeout=60000
request_timing: Set delays between multiple page requests | request delays, crawl timing, rate limiting | mean_delay=0.1, max_range=0.3
concurrent_ops: Control number of concurrent crawling operations | concurrency, parallel requests, semaphore | semaphore_count=5
page_interaction: Configure JavaScript execution and page scanning | JS execution, page scanning, user simulation | js_code="window.scrollTo(0,1000)", scan_full_page=True
popup_handling: Manage overlay elements and popup removal | overlay removal, popup handling, anti-popup | remove_overlay_elements=True, magic=True
media_capture: Configure screenshot and PDF generation settings | screenshots, PDF export, media capture | screenshot=True, pdf=True
image_processing: Set thresholds for image processing and description | image handling, description extraction, image scoring | image_score_threshold=3, image_description_min_word_threshold=50
link_filtering: Configure domain and link exclusion rules | domain filtering, link exclusion, URL filtering | exclude_external_links=True, exclude_domains=["example.com"]
debug_settings: Control logging and debugging output | logging, debugging, console output | verbose=True, log_console=True