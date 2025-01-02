
## `crawl4ai/models.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | models.py | `` |  |
| CLASS | TokenUsage | `class TokenUsage:` |  |
| CLASS | UrlModel | `class UrlModel:` |  |
| CLASS | MarkdownGenerationResult | `class MarkdownGenerationResult:` |  |
| CLASS | CrawlResult | `class CrawlResult:` |  |
| CLASS | AsyncCrawlResponse | `class AsyncCrawlResponse:` |  |

## `crawl4ai/async_configs.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | async_configs.py | `` |  |
| CLASS | BrowserConfig | `class BrowserConfig:` | Configuration class for setting up a browser instance and its context in AsyncPlaywrightCrawlerStrat... (truncated) |
| METHOD | BrowserConfig.__init__ | `def __init__(self, browser_type='chromium', headless=True, use_remote_browser=False, use_persistent_context=False, user_data_dir=None, chrome_channel='chrome', proxy=None, proxy_config=None, viewport_width=1080, viewport_height=600, accept_downloads=False, downloads_path=None, storage_state=None, ignore_https_errors=True, java_script_enabled=True, sleep_on_close=False, verbose=True, cookies=None, headers=None, user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.187 Safari/604.1 Edg/117.0.2045.47', user_agent_mode=None, user_agent_generator_config=None, text_mode=False, light_mode=False, extra_args=None, debugging_port=9222):` |  |
| METHOD | BrowserConfig.from_kwargs | `def from_kwargs(kwargs):` |  |
| CLASS | CrawlerRunConfig | `class CrawlerRunConfig:` | Configuration class for controlling how the crawler runs each crawl operation. This includes paramet... (truncated) |
| METHOD | CrawlerRunConfig.__init__ | `def __init__(self, word_count_threshold=MIN_WORD_THRESHOLD, extraction_strategy=None, chunking_strategy=None, markdown_generator=None, content_filter=None, only_text=False, css_selector=None, excluded_tags=None, excluded_selector=None, keep_data_attributes=False, remove_forms=False, prettiify=False, parser_type='lxml', fetch_ssl_certificate=False, cache_mode=None, session_id=None, bypass_cache=False, disable_cache=False, no_cache_read=False, no_cache_write=False, wait_until='domcontentloaded', page_timeout=PAGE_TIMEOUT, wait_for=None, wait_for_images=True, delay_before_return_html=0.1, mean_delay=0.1, max_range=0.3, semaphore_count=5, js_code=None, js_only=False, ignore_body_visibility=True, scan_full_page=False, scroll_delay=0.2, process_iframes=False, remove_overlay_elements=False, simulate_user=False, override_navigator=False, magic=False, adjust_viewport_to_content=False, screenshot=False, screenshot_wait_for=None, screenshot_height_threshold=SCREENSHOT_HEIGHT_TRESHOLD, pdf=False, image_description_min_word_threshold=IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD, image_score_threshold=IMAGE_SCORE_THRESHOLD, exclude_external_images=False, exclude_social_media_domains=None, exclude_external_links=False, exclude_social_media_links=False, exclude_domains=None, verbose=True, log_console=False, url=None):` |  |
| METHOD | CrawlerRunConfig.from_kwargs | `def from_kwargs(kwargs):` |  |
| METHOD | CrawlerRunConfig.to_dict | `def to_dict(self):` |  |

## `crawl4ai/async_webcrawler.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | async_webcrawler.py | `` |  |
| CLASS | AsyncWebCrawler | `class AsyncWebCrawler:` | Asynchronous web crawler with flexible caching capabilities.  There are two ways to use the crawler:... (truncated) |
| METHOD | AsyncWebCrawler.__init__ | `def __init__(self, crawler_strategy=None, config=None, always_bypass_cache=False, always_by_pass_cache=None, base_directory=str(os.getenv('CRAWL4_AI_BASE_DIRECTORY', Path.home())), thread_safe=False, **kwargs):` | Initialize the AsyncWebCrawler.  Args:     crawler_strategy: Strategy for crawling web pages. If Non... (truncated) |
| METHOD | AsyncWebCrawler.start | `async def start(self):` | Start the crawler explicitly without using context manager. This is equivalent to using 'async with'... (truncated) |
| METHOD | AsyncWebCrawler.close | `async def close(self):` | Close the crawler explicitly without using context manager. This should be called when you're done w... (truncated) |
| METHOD | AsyncWebCrawler.__aenter__ | `async def __aenter__(self):` |  |
| METHOD | AsyncWebCrawler.__aexit__ | `async def __aexit__(self, exc_type, exc_val, exc_tb):` |  |
| METHOD | AsyncWebCrawler.awarmup | `async def awarmup(self):` | Initialize the crawler with warm-up sequence.  This method: 1. Logs initialization info 2. Sets up b... (truncated) |
| METHOD | AsyncWebCrawler.nullcontext | `async def nullcontext(self):` | 异步空上下文管理器 |
| METHOD | AsyncWebCrawler.arun | `async def arun(self, url, config=None, word_count_threshold=MIN_WORD_THRESHOLD, extraction_strategy=None, chunking_strategy=RegexChunking(), content_filter=None, cache_mode=None, bypass_cache=False, disable_cache=False, no_cache_read=False, no_cache_write=False, css_selector=None, screenshot=False, pdf=False, user_agent=None, verbose=True, **kwargs):` | Runs the crawler for a single source: URL (web, local file, or raw HTML).  Migration Guide: Old way ... (truncated) |
| METHOD | AsyncWebCrawler.aprocess_html | `async def aprocess_html(self, url, html, extracted_content, config, screenshot, pdf_data, verbose, **kwargs):` | Process HTML content using the provided configuration.  Args:     url: The URL being processed     h... (truncated) |
| METHOD | AsyncWebCrawler.arun_many | `async def arun_many(self, urls, config=None, word_count_threshold=MIN_WORD_THRESHOLD, extraction_strategy=None, chunking_strategy=RegexChunking(), content_filter=None, cache_mode=None, bypass_cache=False, css_selector=None, screenshot=False, pdf=False, user_agent=None, verbose=True, **kwargs):` | Runs the crawler for multiple URLs concurrently.  Migration Guide: Old way (deprecated):     results... (truncated) |
| METHOD | AsyncWebCrawler.aclear_cache | `async def aclear_cache(self):` | Clear the cache database. |
| METHOD | AsyncWebCrawler.aflush_cache | `async def aflush_cache(self):` | Flush the cache database. |
| METHOD | AsyncWebCrawler.aget_cache_size | `async def aget_cache_size(self):` | Get the total number of cached items. |

## `crawl4ai/async_crawler_strategy.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | async_crawler_strategy.py | `` |  |
| CLASS | RemoteConnector | `class RemoteConnector:` | Manages the browser process and context. This class allows to connect to the browser using CDP proto... (truncated) |
| METHOD | RemoteConnector.__init__ | `def __init__(self, browser_type='chromium', user_data_dir=None, headless=False, logger=None, host='localhost', debugging_port=9222):` | Initialize the RemoteConnector instance.  Args:     browser_type (str): The type of browser to launch... (truncated) |
| METHOD | RemoteConnector.start | `async def start(self):` | Starts the browser process and returns the CDP endpoint URL. If user_data_dir is not provided, creat... (truncated) |
| METHOD | RemoteConnector._monitor_browser_process | `async def _monitor_browser_process(self):` | Monitor the browser process for unexpected termination.  How it works: 1. Read stdout and stderr fro... (truncated) |
| METHOD | RemoteConnector._get_browser_path | `def _get_browser_path(self):` | Returns the browser executable path based on OS and browser type |
| METHOD | RemoteConnector._get_browser_args | `def _get_browser_args(self):` | Returns browser-specific command line arguments |
| METHOD | RemoteConnector.cleanup | `async def cleanup(self):` | Cleanup browser process and temporary directory |
| CLASS | BrowserManager | `class BrowserManager:` | Manages the browser instance and context.  Attributes:      config (BrowserConfig): Configuration ob... (truncated) |
| METHOD | BrowserManager.__init__ | `def __init__(self, browser_config, logger=None):` | Initialize the BrowserManager with a browser configuration.  Args:     browser_config (BrowserConfig... (truncated) |
| METHOD | BrowserManager.start | `async def start(self):` | Start the browser instance and set up the default context.  How it works: 1. Check if Playwright is ... (truncated) |
| METHOD | BrowserManager._build_browser_args | `def _build_browser_args(self):` | Build browser launch arguments from config. |
| METHOD | BrowserManager.setup_context | `async def setup_context(self, context, crawlerRunConfig, is_default=False):` | Set up a browser context with the configured options.  How it works: 1. Set extra HTTP headers if pr... (truncated) |
| METHOD | BrowserManager.create_browser_context | `async def create_browser_context(self):` | Creates and returns a new browser context with configured settings. Applies text-only mode settings ... (truncated) |
| METHOD | BrowserManager.get_page | `async def get_page(self, crawlerRunConfig):` | Get a page for the given session ID, creating a new one if needed.  Args:     crawlerRunConfig (Craw... (truncated) |
| METHOD | BrowserManager.kill_session | `async def kill_session(self, session_id):` | Kill a browser session and clean up resources.    Args:     session_id (str): The session ID to kill... (truncated) |
| METHOD | BrowserManager._cleanup_expired_sessions | `def _cleanup_expired_sessions(self):` | Clean up expired sessions based on TTL. |
| METHOD | BrowserManager.close | `async def close(self):` | Close all browser resources and clean up. |
| CLASS | AsyncCrawlerStrategy | `class AsyncCrawlerStrategy:` | Abstract base class for crawler strategies. Subclasses must implement the crawl method. |
| METHOD | AsyncCrawlerStrategy.crawl | `async def crawl(self, url, **kwargs):` |  |
| CLASS | AsyncPlaywrightCrawlerStrategy | `class AsyncPlaywrightCrawlerStrategy:` | Crawler strategy using Playwright.  Attributes:     browser_config (BrowserConfig): Configuration ob... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.__init__ | `def __init__(self, browser_config=None, logger=None, **kwargs):` | Initialize the AsyncPlaywrightCrawlerStrategy with a browser configuration.  Args:     browser_confi... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.__aenter__ | `async def __aenter__(self):` |  |
| METHOD | AsyncPlaywrightCrawlerStrategy.__aexit__ | `async def __aexit__(self, exc_type, exc_val, exc_tb):` |  |
| METHOD | AsyncPlaywrightCrawlerStrategy.start | `async def start(self):` | Start the browser and initialize the browser manager. |
| METHOD | AsyncPlaywrightCrawlerStrategy.close | `async def close(self):` | Close the browser and clean up resources. |
| METHOD | AsyncPlaywrightCrawlerStrategy.kill_session | `async def kill_session(self, session_id):` | Kill a browser session and clean up resources.  Args:     session_id (str): The ID of the session to... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.set_hook | `def set_hook(self, hook_type, hook):` | Set a hook function for a specific hook type. Following are list of hook types: - on_browser_created... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.execute_hook | `async def execute_hook(self, hook_type, *args, **kwargs):` | Execute a hook function for a specific hook type.  Args:     hook_type (str): The type of the hook. ... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.update_user_agent | `def update_user_agent(self, user_agent):` | Update the user agent for the browser.  Args:     user_agent (str): The new user agent string.      ... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.set_custom_headers | `def set_custom_headers(self, headers):` | Set custom headers for the browser.   Args:     headers (Dict[str, str]): A dictionary of headers to... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.smart_wait | `async def smart_wait(self, page, wait_for, timeout=30000):` | Wait for a condition in a smart way. This functions works as below:  1. If wait_for starts with 'js:... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.csp_compliant_wait | `async def csp_compliant_wait(self, page, user_wait_function, timeout=30000):` | Wait for a condition in a CSP-compliant way.  Args:     page: Playwright page object     user_wait_f... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.process_iframes | `async def process_iframes(self, page):` | Process iframes on a page. This function will extract the content of each iframe and replace it with... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.create_session | `async def create_session(self, **kwargs):` | Creates a new browser session and returns its ID. A browse session is a unique openned page can be r... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.crawl | `async def crawl(self, url, config, **kwargs):` | Crawls a given URL or processes raw HTML/local file content based on the URL prefix.  Args:     url ... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy._crawl_web | `async def _crawl_web(self, url, config):` | Internal method to crawl web URLs with the specified configuration.  Args:     url (str): The web UR... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy._handle_full_page_scan | `async def _handle_full_page_scan(self, page, scroll_delay):` | Helper method to handle full page scanning.   How it works: 1. Get the viewport height. 2. Scroll to... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy._handle_download | `async def _handle_download(self, download):` | Handle file downloads.  How it works: 1. Get the suggested filename. 2. Get the download path. 3. Lo... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.remove_overlay_elements | `async def remove_overlay_elements(self, page):` | Removes popup overlays, modals, cookie notices, and other intrusive elements from the page.  Args:  ... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.export_pdf | `async def export_pdf(self, page):` | Exports the current page as a PDF.  Args:     page (Page): The Playwright page object      Returns: ... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.take_screenshot | `async def take_screenshot(self, page, **kwargs):` | Take a screenshot of the current page.  Args:     page (Page): The Playwright page object     kwargs... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.take_screenshot_from_pdf | `async def take_screenshot_from_pdf(self, pdf_data):` | Convert the first page of the PDF to a screenshot.       Requires pdf2image and poppler.  Args:     ... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.take_screenshot_scroller | `async def take_screenshot_scroller(self, page, **kwargs):` | Attempt to set a large viewport and take a full-page screenshot. If still too large, segment the pag... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.take_screenshot_naive | `async def take_screenshot_naive(self, page):` | Takes a screenshot of the current page.  Args:     page (Page): The Playwright page instance  Return... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.export_storage_state | `async def export_storage_state(self, path=None):` | Exports the current storage state (cookies, localStorage, sessionStorage) to a JSON file at the spec... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.robust_execute_user_script | `async def robust_execute_user_script(self, page, js_code):` | Executes user-provided JavaScript code with proper error handling and context, supporting both synch... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.execute_user_script | `async def execute_user_script(self, page, js_code):` | Executes user-provided JavaScript code with proper error handling and context.  Args:     page: Play... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.check_visibility | `async def check_visibility(self, page):` | Checks if an element is visible on the page.  Args:     page: Playwright page object      Returns:  ... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.safe_scroll | `async def safe_scroll(self, page, x, y):` | Safely scroll the page with rendering time.  Args:     page: Playwright page object     x: Horizonta... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.csp_scroll_to | `async def csp_scroll_to(self, page, x, y):` | Performs a CSP-compliant scroll operation and returns the result status.  Args:     page: Playwright... (truncated) |
| METHOD | AsyncPlaywrightCrawlerStrategy.get_page_dimensions | `async def get_page_dimensions(self, page):` | Get the dimensions of the page.  Args:     page: Playwright page object      Returns:     Dict conta... (truncated) |

## `crawl4ai/content_scraping_strategy.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | content_scraping_strategy.py | `` |  |
| FUNCTION | parse_dimension | `def parse_dimension(dimension):` |  |
| FUNCTION | fetch_image_file_size | `def fetch_image_file_size(img, base_url):` |  |
| CLASS | ContentScrapingStrategy | `class ContentScrapingStrategy:` |  |
| METHOD | ContentScrapingStrategy.scrap | `def scrap(self, url, html, **kwargs):` |  |
| METHOD | ContentScrapingStrategy.ascrap | `async def ascrap(self, url, html, **kwargs):` |  |
| CLASS | WebScrapingStrategy | `class WebScrapingStrategy:` | Class for web content scraping. Perhaps the most important class.   How it works: 1. Extract content... (truncated) |
| METHOD | WebScrapingStrategy.__init__ | `def __init__(self, logger=None):` |  |
| METHOD | WebScrapingStrategy._log | `def _log(self, level, message, tag='SCRAPE', **kwargs):` | Helper method to safely use logger. |
| METHOD | WebScrapingStrategy.scrap | `def scrap(self, url, html, **kwargs):` | Main entry point for content scraping.    Args:     url (str): The URL of the page to scrape.     ht... (truncated) |
| METHOD | WebScrapingStrategy.ascrap | `async def ascrap(self, url, html, **kwargs):` | Main entry point for asynchronous content scraping.  Args:     url (str): The URL of the page to scr... (truncated) |
| METHOD | WebScrapingStrategy._generate_markdown_content | `def _generate_markdown_content(self, cleaned_html, html, url, success, **kwargs):` | Generate markdown content from cleaned HTML.  Args:     cleaned_html (str): The cleaned HTML content... (truncated) |
| METHOD | WebScrapingStrategy.flatten_nested_elements | `def flatten_nested_elements(self, node):` | Flatten nested elements in a HTML tree.  Args:     node (Tag): The root node of the HTML tree.  Retu... (truncated) |
| METHOD | WebScrapingStrategy.find_closest_parent_with_useful_text | `def find_closest_parent_with_useful_text(self, tag, **kwargs):` | Find the closest parent with useful text.  Args:     tag (Tag): The starting tag to search from.    ... (truncated) |
| METHOD | WebScrapingStrategy.remove_unwanted_attributes | `def remove_unwanted_attributes(self, element, important_attrs, keep_data_attributes=False):` | Remove unwanted attributes from an HTML element.  Args:         element (Tag): The HTML element to r... (truncated) |
| METHOD | WebScrapingStrategy.process_image | `def process_image(self, img, url, index, total_images, **kwargs):` | Process an image element.  How it works: 1. Check if the image has valid display and inside undesire... (truncated) |
| METHOD | WebScrapingStrategy.process_element | `def process_element(self, url, element, **kwargs):` | Process an HTML element.  How it works: 1. Check if the element is an image, video, or audio. 2. Ext... (truncated) |
| METHOD | WebScrapingStrategy._process_element | `def _process_element(self, url, element, media, internal_links_dict, external_links_dict, **kwargs):` | Process an HTML element.         |
| METHOD | WebScrapingStrategy._scrap | `def _scrap(self, url, html, word_count_threshold=MIN_WORD_THRESHOLD, css_selector=None, **kwargs):` | Extract content from HTML using BeautifulSoup.  Args:     url (str): The URL of the page to scrape. ... (truncated) |

## `crawl4ai/markdown_generation_strategy.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | markdown_generation_strategy.py | `` |  |
| FUNCTION | fast_urljoin | `def fast_urljoin(base, url):` | Fast URL joining for common cases. |
| CLASS | MarkdownGenerationStrategy | `class MarkdownGenerationStrategy:` | Abstract base class for markdown generation strategies. |
| METHOD | MarkdownGenerationStrategy.__init__ | `def __init__(self, content_filter=None, options=None):` |  |
| METHOD | MarkdownGenerationStrategy.generate_markdown | `def generate_markdown(self, cleaned_html, base_url='', html2text_options=None, content_filter=None, citations=True, **kwargs):` | Generate markdown from cleaned HTML. |
| CLASS | DefaultMarkdownGenerator | `class DefaultMarkdownGenerator:` | Default implementation of markdown generation strategy.  How it works: 1. Generate raw markdown from... (truncated) |
| METHOD | DefaultMarkdownGenerator.__init__ | `def __init__(self, content_filter=None, options=None):` |  |
| METHOD | DefaultMarkdownGenerator.convert_links_to_citations | `def convert_links_to_citations(self, markdown, base_url=''):` | Convert links in markdown to citations.  How it works: 1. Find all links in the markdown. 2. Convert... (truncated) |
| METHOD | DefaultMarkdownGenerator.generate_markdown | `def generate_markdown(self, cleaned_html, base_url='', html2text_options=None, options=None, content_filter=None, citations=True, **kwargs):` | Generate markdown with citations from cleaned HTML.  How it works: 1. Generate raw markdown from cle... (truncated) |

## `crawl4ai/content_filter_strategy.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | content_filter_strategy.py | `` |  |
| CLASS | RelevantContentFilter | `class RelevantContentFilter:` | Abstract base class for content filtering strategies |
| METHOD | RelevantContentFilter.__init__ | `def __init__(self, user_query=None):` |  |
| METHOD | RelevantContentFilter.filter_content | `def filter_content(self, html):` | Abstract method to be implemented by specific filtering strategies |
| METHOD | RelevantContentFilter.extract_page_query | `def extract_page_query(self, soup, body):` | Common method to extract page metadata with fallbacks |
| METHOD | RelevantContentFilter.extract_text_chunks | `def extract_text_chunks(self, body, min_word_threshold=None):` | Extracts text chunks from a BeautifulSoup body element while preserving order. Returns list of tuple... (truncated) |
| METHOD | RelevantContentFilter._deprecated_extract_text_chunks | `def _deprecated_extract_text_chunks(self, soup):` | Common method for extracting text chunks |
| METHOD | RelevantContentFilter.is_excluded | `def is_excluded(self, tag):` | Common method for exclusion logic |
| METHOD | RelevantContentFilter.clean_element | `def clean_element(self, tag):` | Common method for cleaning HTML elements with minimal overhead |
| CLASS | BM25ContentFilter | `class BM25ContentFilter:` | Content filtering using BM25 algorithm with priority tag handling.  How it works: 1. Extracts page m... (truncated) |
| METHOD | BM25ContentFilter.__init__ | `def __init__(self, user_query=None, bm25_threshold=1.0, language='english'):` | Initializes the BM25ContentFilter class, if not provided, falls back to page metadata.  Note: If no ... (truncated) |
| METHOD | BM25ContentFilter.filter_content | `def filter_content(self, html, min_word_threshold=None):` | Implements content filtering using BM25 algorithm with priority tag handling.      Note: This method... (truncated) |
| CLASS | PruningContentFilter | `class PruningContentFilter:` | Content filtering using pruning algorithm with dynamic threshold.  How it works: 1. Extracts page me... (truncated) |
| METHOD | PruningContentFilter.__init__ | `def __init__(self, user_query=None, min_word_threshold=None, threshold_type='fixed', threshold=0.48):` | Initializes the PruningContentFilter class, if not provided, falls back to page metadata.  Note: If ... (truncated) |
| METHOD | PruningContentFilter.filter_content | `def filter_content(self, html, min_word_threshold=None):` | Implements content filtering using pruning algorithm with dynamic threshold.  Note: This method impl... (truncated) |
| METHOD | PruningContentFilter._remove_comments | `def _remove_comments(self, soup):` | Removes HTML comments |
| METHOD | PruningContentFilter._remove_unwanted_tags | `def _remove_unwanted_tags(self, soup):` | Removes unwanted tags |
| METHOD | PruningContentFilter._prune_tree | `def _prune_tree(self, node):` | Prunes the tree starting from the given node.  Args:     node (Tag): The node from which the pruning... (truncated) |
| METHOD | PruningContentFilter._compute_composite_score | `def _compute_composite_score(self, metrics, text_len, tag_len, link_text_len):` | Computes the composite score |
| METHOD | PruningContentFilter._compute_class_id_weight | `def _compute_class_id_weight(self, node):` | Computes the class ID weight |

## `crawl4ai/extraction_strategy.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | extraction_strategy.py | `` |  |
| CLASS | ExtractionStrategy | `class ExtractionStrategy:` | Abstract base class for all extraction strategies. |
| METHOD | ExtractionStrategy.__init__ | `def __init__(self, input_format='markdown', **kwargs):` | Initialize the extraction strategy.  Args:     input_format: Content format to use for extraction.  ... (truncated) |
| METHOD | ExtractionStrategy.extract | `def extract(self, url, html, *q, **kwargs):` | Extract meaningful blocks or chunks from the given HTML.  :param url: The URL of the webpage. :param... (truncated) |
| METHOD | ExtractionStrategy.run | `def run(self, url, sections, *q, **kwargs):` | Process sections of text in parallel by default.  :param url: The URL of the webpage. :param section... (truncated) |
| CLASS | NoExtractionStrategy | `class NoExtractionStrategy:` | A strategy that does not extract any meaningful content from the HTML. It simply returns the entire ... (truncated) |
| METHOD | NoExtractionStrategy.extract | `def extract(self, url, html, *q, **kwargs):` | Extract meaningful blocks or chunks from the given HTML. |
| METHOD | NoExtractionStrategy.run | `def run(self, url, sections, *q, **kwargs):` |  |
| CLASS | LLMExtractionStrategy | `class LLMExtractionStrategy:` | A strategy that uses an LLM to extract meaningful content from the HTML.  Attributes:     provider: ... (truncated) |
| METHOD | LLMExtractionStrategy.__init__ | `def __init__(self, provider=DEFAULT_PROVIDER, api_token=None, instruction=None, schema=None, extraction_type='block', **kwargs):` | Initialize the strategy with clustering parameters.  Args:     provider: The provider to use for ext... (truncated) |
| METHOD | LLMExtractionStrategy.extract | `def extract(self, url, ix, html):` | Extract meaningful blocks or chunks from the given HTML using an LLM.  How it works: 1. Construct a ... (truncated) |
| METHOD | LLMExtractionStrategy._merge | `def _merge(self, documents, chunk_token_threshold, overlap):` | Merge documents into sections based on chunk_token_threshold and overlap. |
| METHOD | LLMExtractionStrategy.run | `def run(self, url, sections):` | Process sections sequentially with a delay for rate limiting issues, specifically for LLMExtractionS... (truncated) |
| METHOD | LLMExtractionStrategy.show_usage | `def show_usage(self):` | Print a detailed token usage report showing total and per-request usage. |
| CLASS | CosineStrategy | `class CosineStrategy:` | Extract meaningful blocks or chunks from the given HTML using cosine similarity.  How it works: 1. P... (truncated) |
| METHOD | CosineStrategy.__init__ | `def __init__(self, semantic_filter=None, word_count_threshold=10, max_dist=0.2, linkage_method='ward', top_k=3, model_name='sentence-transformers/all-MiniLM-L6-v2', sim_threshold=0.3, **kwargs):` | Initialize the strategy with clustering parameters.  Args:     semantic_filter (str): A keyword filt... (truncated) |
| METHOD | CosineStrategy.filter_documents_embeddings | `def filter_documents_embeddings(self, documents, semantic_filter, at_least_k=20):` | Filter and sort documents based on the cosine similarity of their embeddings with the semantic_filte... (truncated) |
| METHOD | CosineStrategy.get_embeddings | `def get_embeddings(self, sentences, batch_size=None, bypass_buffer=False):` | Get BERT embeddings for a list of sentences.  Args:     sentences (List[str]): A list of text chunks... (truncated) |
| METHOD | CosineStrategy.hierarchical_clustering | `def hierarchical_clustering(self, sentences, embeddings=None):` | Perform hierarchical clustering on sentences and return cluster labels.  Args:     sentences (List[s... (truncated) |
| METHOD | CosineStrategy.filter_clusters_by_word_count | `def filter_clusters_by_word_count(self, clusters):` | Filter clusters to remove those with a word count below the threshold.  Args:     clusters (Dict[int... (truncated) |
| METHOD | CosineStrategy.extract | `def extract(self, url, html, *q, **kwargs):` | Extract clusters from HTML content using hierarchical clustering.  Args:     url (str): The URL of t... (truncated) |
| METHOD | CosineStrategy.run | `def run(self, url, sections, *q, **kwargs):` | Process sections using hierarchical clustering.  Args:     url (str): The URL of the webpage.     se... (truncated) |
| CLASS | JsonElementExtractionStrategy | `class JsonElementExtractionStrategy:` |     Abstract base class for extracting structured JSON from HTML content.      How it works:     1. ... (truncated) |
| METHOD | JsonElementExtractionStrategy.__init__ | `def __init__(self, schema, **kwargs):` | Initialize the JSON element extraction strategy with a schema.  Args:     schema (Dict[str, Any]): T... (truncated) |
| METHOD | JsonElementExtractionStrategy.extract | `def extract(self, url, html_content, *q, **kwargs):` | Extract structured data from HTML content.  How it works: 1. Parses the HTML content using the `_par... (truncated) |
| METHOD | JsonElementExtractionStrategy._parse_html | `def _parse_html(self, html_content):` | Parse HTML content into appropriate format |
| METHOD | JsonElementExtractionStrategy._get_base_elements | `def _get_base_elements(self, parsed_html, selector):` | Get all base elements using the selector |
| METHOD | JsonElementExtractionStrategy._get_elements | `def _get_elements(self, element, selector):` | Get child elements using the selector |
| METHOD | JsonElementExtractionStrategy._extract_field | `def _extract_field(self, element, field):` |  |
| METHOD | JsonElementExtractionStrategy._extract_single_field | `def _extract_single_field(self, element, field):` | Extract a single field based on its type.  How it works: 1. Selects the target element using the fie... (truncated) |
| METHOD | JsonElementExtractionStrategy._extract_list_item | `def _extract_list_item(self, element, fields):` |  |
| METHOD | JsonElementExtractionStrategy._extract_item | `def _extract_item(self, element, fields):` | Extracts fields from a given element.  How it works: 1. Iterates through the fields defined in the s... (truncated) |
| METHOD | JsonElementExtractionStrategy._apply_transform | `def _apply_transform(self, value, transform):` | Apply a transformation to a value.  How it works: 1. Checks the transformation type (e.g., `lowercas... (truncated) |
| METHOD | JsonElementExtractionStrategy._compute_field | `def _compute_field(self, item, field):` |  |
| METHOD | JsonElementExtractionStrategy.run | `def run(self, url, sections, *q, **kwargs):` | Run the extraction strategy on a combined HTML content.  How it works: 1. Combines multiple HTML sec... (truncated) |
| METHOD | JsonElementExtractionStrategy._get_element_text | `def _get_element_text(self, element):` | Get text content from element |
| METHOD | JsonElementExtractionStrategy._get_element_html | `def _get_element_html(self, element):` | Get HTML content from element |
| METHOD | JsonElementExtractionStrategy._get_element_attribute | `def _get_element_attribute(self, element, attribute):` | Get attribute value from element |
| CLASS | JsonCssExtractionStrategy | `class JsonCssExtractionStrategy:` | Concrete implementation of `JsonElementExtractionStrategy` using CSS selectors.  How it works: 1. Pa... (truncated) |
| METHOD | JsonCssExtractionStrategy.__init__ | `def __init__(self, schema, **kwargs):` |  |
| METHOD | JsonCssExtractionStrategy._parse_html | `def _parse_html(self, html_content):` |  |
| METHOD | JsonCssExtractionStrategy._get_base_elements | `def _get_base_elements(self, parsed_html, selector):` |  |
| METHOD | JsonCssExtractionStrategy._get_elements | `def _get_elements(self, element, selector):` |  |
| METHOD | JsonCssExtractionStrategy._get_element_text | `def _get_element_text(self, element):` |  |
| METHOD | JsonCssExtractionStrategy._get_element_html | `def _get_element_html(self, element):` |  |
| METHOD | JsonCssExtractionStrategy._get_element_attribute | `def _get_element_attribute(self, element, attribute):` |  |
| CLASS | JsonXPathExtractionStrategy | `class JsonXPathExtractionStrategy:` | Concrete implementation of `JsonElementExtractionStrategy` using XPath selectors.  How it works: 1. ... (truncated) |
| METHOD | JsonXPathExtractionStrategy.__init__ | `def __init__(self, schema, **kwargs):` |  |
| METHOD | JsonXPathExtractionStrategy._parse_html | `def _parse_html(self, html_content):` |  |
| METHOD | JsonXPathExtractionStrategy._get_base_elements | `def _get_base_elements(self, parsed_html, selector):` |  |
| METHOD | JsonXPathExtractionStrategy._css_to_xpath | `def _css_to_xpath(self, css_selector):` | Convert CSS selector to XPath if needed |
| METHOD | JsonXPathExtractionStrategy._basic_css_to_xpath | `def _basic_css_to_xpath(self, css_selector):` | Basic CSS to XPath conversion for common cases |
| METHOD | JsonXPathExtractionStrategy._get_elements | `def _get_elements(self, element, selector):` |  |
| METHOD | JsonXPathExtractionStrategy._get_element_text | `def _get_element_text(self, element):` |  |
| METHOD | JsonXPathExtractionStrategy._get_element_html | `def _get_element_html(self, element):` |  |
| METHOD | JsonXPathExtractionStrategy._get_element_attribute | `def _get_element_attribute(self, element, attribute):` |  |

## `crawl4ai/chunking_strategy.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | chunking_strategy.py | `` |  |
| CLASS | ChunkingStrategy | `class ChunkingStrategy:` | Abstract base class for chunking strategies. |
| METHOD | ChunkingStrategy.chunk | `def chunk(self, text):` | Abstract method to chunk the given text.  Args:     text (str): The text to chunk.  Returns:     lis... (truncated) |
| CLASS | IdentityChunking | `class IdentityChunking:` | Chunking strategy that returns the input text as a single chunk. |
| METHOD | IdentityChunking.chunk | `def chunk(self, text):` |  |
| CLASS | RegexChunking | `class RegexChunking:` | Chunking strategy that splits text based on regular expression patterns. |
| METHOD | RegexChunking.__init__ | `def __init__(self, patterns=None, **kwargs):` | Initialize the RegexChunking object.  Args:     patterns (list): A list of regular expression patter... (truncated) |
| METHOD | RegexChunking.chunk | `def chunk(self, text):` |  |
| CLASS | NlpSentenceChunking | `class NlpSentenceChunking:` | Chunking strategy that splits text into sentences using NLTK's sentence tokenizer. |
| METHOD | NlpSentenceChunking.__init__ | `def __init__(self, **kwargs):` | Initialize the NlpSentenceChunking object. |
| METHOD | NlpSentenceChunking.chunk | `def chunk(self, text):` |  |
| CLASS | TopicSegmentationChunking | `class TopicSegmentationChunking:` | Chunking strategy that segments text into topics using NLTK's TextTilingTokenizer.  How it works: 1.... (truncated) |
| METHOD | TopicSegmentationChunking.__init__ | `def __init__(self, num_keywords=3, **kwargs):` | Initialize the TopicSegmentationChunking object.  Args:     num_keywords (int): The number of keywor... (truncated) |
| METHOD | TopicSegmentationChunking.chunk | `def chunk(self, text):` |  |
| METHOD | TopicSegmentationChunking.extract_keywords | `def extract_keywords(self, text):` |  |
| METHOD | TopicSegmentationChunking.chunk_with_topics | `def chunk_with_topics(self, text):` |  |
| CLASS | FixedLengthWordChunking | `class FixedLengthWordChunking:` | Chunking strategy that splits text into fixed-length word chunks.  How it works: 1. Split the text i... (truncated) |
| METHOD | FixedLengthWordChunking.__init__ | `def __init__(self, chunk_size=100, **kwargs):` | Initialize the fixed-length word chunking strategy with the given chunk size.  Args:     chunk_size ... (truncated) |
| METHOD | FixedLengthWordChunking.chunk | `def chunk(self, text):` |  |
| CLASS | SlidingWindowChunking | `class SlidingWindowChunking:` | Chunking strategy that splits text into overlapping word chunks.  How it works: 1. Split the text in... (truncated) |
| METHOD | SlidingWindowChunking.__init__ | `def __init__(self, window_size=100, step=50, **kwargs):` | Initialize the sliding window chunking strategy with the given window size and step size.  Args:    ... (truncated) |
| METHOD | SlidingWindowChunking.chunk | `def chunk(self, text):` |  |
| CLASS | OverlappingWindowChunking | `class OverlappingWindowChunking:` | Chunking strategy that splits text into overlapping word chunks.  How it works: 1. Split the text in... (truncated) |
| METHOD | OverlappingWindowChunking.__init__ | `def __init__(self, window_size=1000, overlap=100, **kwargs):` | Initialize the overlapping window chunking strategy with the given window size and overlap size.  Ar... (truncated) |
| METHOD | OverlappingWindowChunking.chunk | `def chunk(self, text):` |  |

## `crawl4ai/user_agent_generator.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | user_agent_generator.py | `` |  |
| CLASS | UserAgentGenerator | `class UserAgentGenerator:` | Generate random user agents with specified constraints.  Attributes:     desktop_platforms (dict): A... (truncated) |
| METHOD | UserAgentGenerator.__init__ | `def __init__(self):` |  |
| METHOD | UserAgentGenerator.get_browser_stack | `def get_browser_stack(self, num_browsers=1):` | Get a valid combination of browser versions.  How it works: 1. Check if the number of browsers is su... (truncated) |
| METHOD | UserAgentGenerator.generate | `def generate(self, device_type=None, os_type=None, device_brand=None, browser_type=None, num_browsers=3):` | Generate a random user agent with specified constraints.  Args:     device_type: 'desktop' or 'mobil... (truncated) |
| METHOD | UserAgentGenerator.generate_with_client_hints | `def generate_with_client_hints(self, **kwargs):` | Generate both user agent and matching client hints |
| METHOD | UserAgentGenerator.get_random_platform | `def get_random_platform(self, device_type, os_type, device_brand):` | Helper method to get random platform based on constraints |
| METHOD | UserAgentGenerator.parse_user_agent | `def parse_user_agent(self, user_agent):` | Parse a user agent string to extract browser and version information |
| METHOD | UserAgentGenerator.generate_client_hints | `def generate_client_hints(self, user_agent):` | Generate Sec-CH-UA header value based on user agent string |

## `crawl4ai/ssl_certificate.py`

| Type   | Name                       | Signature                          | Docstring                   |
| ------ | -------------------------- | ---------------------------------- | --------------------------- |
| MODULE | ssl_certificate.py | `` | SSL Certificate class for handling certificate operations. |
| CLASS | SSLCertificate | `class SSLCertificate:` | A class representing an SSL certificate with methods to export in various formats.  Attributes:     ... (truncated) |
| METHOD | SSLCertificate.__init__ | `def __init__(self, cert_info):` |  |
| METHOD | SSLCertificate.from_url | `def from_url(url, timeout=10):` | Create SSLCertificate instance from a URL.  Args:     url (str): URL of the website.     timeout (in... (truncated) |
| METHOD | SSLCertificate._decode_cert_data | `def _decode_cert_data(data):` | Helper method to decode bytes in certificate data. |
| METHOD | SSLCertificate.to_json | `def to_json(self, filepath=None):` | Export certificate as JSON.  Args:     filepath (Optional[str]): Path to save the JSON file (default... (truncated) |
| METHOD | SSLCertificate.to_pem | `def to_pem(self, filepath=None):` | Export certificate as PEM.  Args:     filepath (Optional[str]): Path to save the PEM file (default: ... (truncated) |
| METHOD | SSLCertificate.to_der | `def to_der(self, filepath=None):` | Export certificate as DER.  Args:     filepath (Optional[str]): Path to save the DER file (default: ... (truncated) |
| METHOD | SSLCertificate.issuer | `def issuer(self):` | Get certificate issuer information. |
| METHOD | SSLCertificate.subject | `def subject(self):` | Get certificate subject information. |
| METHOD | SSLCertificate.valid_from | `def valid_from(self):` | Get certificate validity start date. |
| METHOD | SSLCertificate.valid_until | `def valid_until(self):` | Get certificate validity end date. |
| METHOD | SSLCertificate.fingerprint | `def fingerprint(self):` | Get certificate fingerprint. |
