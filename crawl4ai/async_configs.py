from .config import (
    MIN_WORD_THRESHOLD,
    IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
    SCREENSHOT_HEIGHT_TRESHOLD,
    PAGE_TIMEOUT,
    IMAGE_SCORE_THRESHOLD,
    SOCIAL_MEDIA_DOMAINS,
)
from .user_agent_generator import UserAgentGenerator
from .extraction_strategy import ExtractionStrategy
from .chunking_strategy import ChunkingStrategy, RegexChunking
from .markdown_generation_strategy import MarkdownGenerationStrategy
from .content_scraping_strategy import ContentScrapingStrategy, WebScrapingStrategy
from typing import Optional, Union, List


class BrowserConfig:
    """
    Configuration class for setting up a browser instance and its context in AsyncPlaywrightCrawlerStrategy.

    This class centralizes all parameters that affect browser and context creation. Instead of passing
    scattered keyword arguments, users can instantiate and modify this configuration object. The crawler
    code will then reference these settings to initialize the browser in a consistent, documented manner.

    Attributes:
        browser_type (str): The type of browser to launch. Supported values: "chromium", "firefox", "webkit".
                            Default: "chromium".
        headless (bool): Whether to run the browser in headless mode (no visible GUI).
                         Default: True.
        use_managed_browser (bool): Launch the browser using a managed approach (e.g., via CDP), allowing
                                    advanced manipulation. Default: False.
        debugging_port (int): Port for the browser debugging protocol. Default: 9222.
        use_persistent_context (bool): Use a persistent browser context (like a persistent profile).
                                       Automatically sets use_managed_browser=True. Default: False.
        user_data_dir (str or None): Path to a user data directory for persistent sessions. If None, a
                                     temporary directory may be used. Default: None.
        chrome_channel (str): The Chrome channel to launch (e.g., "chrome", "msedge"). Only applies if browser_type
                              is "chromium". Default: "chromium".
        channel (str): The channel to launch (e.g., "chromium", "chrome", "msedge"). Only applies if browser_type
                              is "chromium". Default: "chromium".
        proxy (Optional[str]): Proxy server URL (e.g., "http://username:password@proxy:port"). If None, no proxy is used.
                             Default: None.
        proxy_config (dict or None): Detailed proxy configuration, e.g. {"server": "...", "username": "..."}.
                                     If None, no additional proxy config. Default: None.
        viewport_width (int): Default viewport width for pages. Default: 1080.
        viewport_height (int): Default viewport height for pages. Default: 600.
        verbose (bool): Enable verbose logging.
                        Default: True.
        accept_downloads (bool): Whether to allow file downloads. If True, requires a downloads_path.
                                 Default: False.
        downloads_path (str or None): Directory to store downloaded files. If None and accept_downloads is True,
                                      a default path will be created. Default: None.
        storage_state (str or dict or None): Path or object describing storage state (cookies, localStorage).
                                             Default: None.
        ignore_https_errors (bool): Ignore HTTPS certificate errors. Default: True.
        java_script_enabled (bool): Enable JavaScript execution in pages. Default: True.
        cookies (list): List of cookies to add to the browser context. Each cookie is a dict with fields like
                        {"name": "...", "value": "...", "url": "..."}.
                        Default: [].
        headers (dict): Extra HTTP headers to apply to all requests in this context.
                        Default: {}.
        user_agent (str): Custom User-Agent string to use. Default: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36".
        user_agent_mode (str or None): Mode for generating the user agent (e.g., "random"). If None, use the provided
                                       user_agent as-is. Default: None.
        user_agent_generator_config (dict or None): Configuration for user agent generation if user_agent_mode is set.
                                                    Default: None.
        text_mode (bool): If True, disables images and other rich content for potentially faster load times.
                          Default: False.
        light_mode (bool): Disables certain background features for performance gains. Default: False.
        extra_args (list): Additional command-line arguments passed to the browser.
                           Default: [].
    """

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        use_managed_browser: bool = False,
        use_persistent_context: bool = False,
        user_data_dir: str = None,
        chrome_channel: str = "chromium",
        channel: str = "chromium",
        proxy: Optional[str] = None,
        proxy_config: dict = None,
        viewport_width: int = 1080,
        viewport_height: int = 600,
        accept_downloads: bool = False,
        downloads_path: str = None,
        storage_state=None,
        ignore_https_errors: bool = True,
        java_script_enabled: bool = True,
        sleep_on_close: bool = False,
        verbose: bool = True,
        cookies: list = None,
        headers: dict = None,
        user_agent: str = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/116.0.5845.187 Safari/604.1 Edg/117.0.2045.47"
        ),
        user_agent_mode: str = None,
        user_agent_generator_config: dict = None,
        text_mode: bool = False,
        light_mode: bool = False,
        extra_args: list = None,
        debugging_port: int = 9222,
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.use_managed_browser = use_managed_browser
        self.use_persistent_context = use_persistent_context
        self.user_data_dir = user_data_dir
        self.chrome_channel = chrome_channel or self.browser_type or "chromium"
        self.channel = channel or self.browser_type or "chromium"
        if self.browser_type in ["firefox", "webkit"]:
            self.channel = ""
            self.chrome_channel = ""
        self.proxy = proxy
        self.proxy_config = proxy_config
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.accept_downloads = accept_downloads
        self.downloads_path = downloads_path
        self.storage_state = storage_state
        self.ignore_https_errors = ignore_https_errors
        self.java_script_enabled = java_script_enabled
        self.cookies = cookies if cookies is not None else []
        self.headers = headers if headers is not None else {}
        self.user_agent = user_agent
        self.user_agent_mode = user_agent_mode
        self.user_agent_generator_config = user_agent_generator_config
        self.text_mode = text_mode
        self.light_mode = light_mode
        self.extra_args = extra_args if extra_args is not None else []
        self.sleep_on_close = sleep_on_close
        self.verbose = verbose
        self.debugging_port = debugging_port

        user_agenr_generator = UserAgentGenerator()
        if self.user_agent_mode != "random" and self.user_agent_generator_config:
            self.user_agent = user_agenr_generator.generate(
                **(self.user_agent_generator_config or {})
            )
        elif self.user_agent_mode == "random":
            self.user_agent = user_agenr_generator.generate()
        else:
            pass

        self.browser_hint = user_agenr_generator.generate_client_hints(self.user_agent)
        self.headers.setdefault("sec-ch-ua", self.browser_hint)

        # If persistent context is requested, ensure managed browser is enabled
        if self.use_persistent_context:
            self.use_managed_browser = True

    @staticmethod
    def from_kwargs(kwargs: dict) -> "BrowserConfig":
        return BrowserConfig(
            browser_type=kwargs.get("browser_type", "chromium"),
            headless=kwargs.get("headless", True),
            use_managed_browser=kwargs.get("use_managed_browser", False),
            use_persistent_context=kwargs.get("use_persistent_context", False),
            user_data_dir=kwargs.get("user_data_dir"),
            chrome_channel=kwargs.get("chrome_channel", "chromium"),
            channel=kwargs.get("channel", "chromium"),
            proxy=kwargs.get("proxy"),
            proxy_config=kwargs.get("proxy_config"),
            viewport_width=kwargs.get("viewport_width", 1080),
            viewport_height=kwargs.get("viewport_height", 600),
            accept_downloads=kwargs.get("accept_downloads", False),
            downloads_path=kwargs.get("downloads_path"),
            storage_state=kwargs.get("storage_state"),
            ignore_https_errors=kwargs.get("ignore_https_errors", True),
            java_script_enabled=kwargs.get("java_script_enabled", True),
            cookies=kwargs.get("cookies", []),
            headers=kwargs.get("headers", {}),
            user_agent=kwargs.get(
                "user_agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            ),
            user_agent_mode=kwargs.get("user_agent_mode"),
            user_agent_generator_config=kwargs.get("user_agent_generator_config"),
            text_mode=kwargs.get("text_mode", False),
            light_mode=kwargs.get("light_mode", False),
            extra_args=kwargs.get("extra_args", []),
        )

    def to_dict(self):
        return {
            "browser_type": self.browser_type,
            "headless": self.headless,
            "use_managed_browser": self.use_managed_browser,
            "use_persistent_context": self.use_persistent_context,
            "user_data_dir": self.user_data_dir,
            "chrome_channel": self.chrome_channel,
            "channel": self.channel,
            "proxy": self.proxy,
            "proxy_config": self.proxy_config,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "accept_downloads": self.accept_downloads,
            "downloads_path": self.downloads_path,
            "storage_state": self.storage_state,
            "ignore_https_errors": self.ignore_https_errors,
            "java_script_enabled": self.java_script_enabled,
            "cookies": self.cookies,
            "headers": self.headers,
            "user_agent": self.user_agent,
            "user_agent_mode": self.user_agent_mode,
            "user_agent_generator_config": self.user_agent_generator_config,
            "text_mode": self.text_mode,
            "light_mode": self.light_mode,
            "extra_args": self.extra_args,
            "sleep_on_close": self.sleep_on_close,
            "verbose": self.verbose,
            "debugging_port": self.debugging_port,
        }

    def clone(self, **kwargs):
        """Create a copy of this configuration with updated values.
        
        Args:
            **kwargs: Key-value pairs of configuration options to update
            
        Returns:
            BrowserConfig: A new instance with the specified updates
        """
        config_dict = self.to_dict()
        config_dict.update(kwargs)
        return BrowserConfig.from_kwargs(config_dict)


class CrawlerRunConfig:
    """
    Configuration class for controlling how the crawler runs each crawl operation.
    This includes parameters for content extraction, page manipulation, waiting conditions,
    caching, and other runtime behaviors.

    This centralizes parameters that were previously scattered as kwargs to `arun()` and related methods.
    By using this class, you have a single place to understand and adjust the crawling options.

    Attributes:
        # Content Processing Parameters
        word_count_threshold (int): Minimum word count threshold before processing content.
                                    Default: MIN_WORD_THRESHOLD (typically 200).
        extraction_strategy (ExtractionStrategy or None): Strategy to extract structured data from crawled pages.
                                                          Default: None (NoExtractionStrategy is used if None).
        chunking_strategy (ChunkingStrategy): Strategy to chunk content before extraction.
                                              Default: RegexChunking().
        markdown_generator (MarkdownGenerationStrategy): Strategy for generating markdown.
                                                         Default: None.
        content_filter (RelevantContentFilter or None): Optional filter to prune irrelevant content.
                                                        Default: None.
        only_text (bool): If True, attempt to extract text-only content where applicable.
                          Default: False.
        css_selector (str or None): CSS selector to extract a specific portion of the page.
                                    Default: None.
        excluded_tags (list of str or None): List of HTML tags to exclude from processing.
                                             Default: None.
        excluded_selector (str or None): CSS selector to exclude from processing.
                                         Default: None.
        keep_data_attributes (bool): If True, retain `data-*` attributes while removing unwanted attributes.
                                     Default: False.
        remove_forms (bool): If True, remove all `<form>` elements from the HTML.
                             Default: False.
        prettiify (bool): If True, apply `fast_format_html` to produce prettified HTML output.
                          Default: False.
        parser_type (str): Type of parser to use for HTML parsing.
                           Default: "lxml".
        scraping_strategy (ContentScrapingStrategy): Scraping strategy to use.
                           Default: WebScrapingStrategy.
        proxy_config (dict or None): Detailed proxy configuration, e.g. {"server": "...", "username": "..."}.
                                     If None, no additional proxy config. Default: None.

        # Caching Parameters
        cache_mode (CacheMode or None): Defines how caching is handled.
                                        If None, defaults to CacheMode.ENABLED internally.
                                        Default: None.
        session_id (str or None): Optional session ID to persist the browser context and the created
                                  page instance. If the ID already exists, the crawler does not
                                  create a new page and uses the current page to preserve the state.
        bypass_cache (bool): Legacy parameter, if True acts like CacheMode.BYPASS.
                             Default: False.
        disable_cache (bool): Legacy parameter, if True acts like CacheMode.DISABLED.
                              Default: False.
        no_cache_read (bool): Legacy parameter, if True acts like CacheMode.WRITE_ONLY.
                              Default: False.
        no_cache_write (bool): Legacy parameter, if True acts like CacheMode.READ_ONLY.
                               Default: False.
        shared_data (dict or None): Shared data to be passed between hooks.
                                     Default: None.

        # Page Navigation and Timing Parameters
        wait_until (str): The condition to wait for when navigating, e.g. "domcontentloaded".
                          Default: "domcontentloaded".
        page_timeout (int): Timeout in ms for page operations like navigation.
                            Default: 60000 (60 seconds).
        wait_for (str or None): A CSS selector or JS condition to wait for before extracting content.
                                Default: None.
        wait_for_images (bool): If True, wait for images to load before extracting content.
                                Default: False.
        delay_before_return_html (float): Delay in seconds before retrieving final HTML.
                                          Default: 0.1.
        mean_delay (float): Mean base delay between requests when calling arun_many.
                            Default: 0.1.
        max_range (float): Max random additional delay range for requests in arun_many.
                           Default: 0.3.
        semaphore_count (int): Number of concurrent operations allowed.
                               Default: 5.

        # Page Interaction Parameters
        js_code (str or list of str or None): JavaScript code/snippets to run on the page.
                                              Default: None.
        js_only (bool): If True, indicates subsequent calls are JS-driven updates, not full page loads.
                        Default: False.
        ignore_body_visibility (bool): If True, ignore whether the body is visible before proceeding.
                                       Default: True.
        scan_full_page (bool): If True, scroll through the entire page to load all content.
                               Default: False.
        scroll_delay (float): Delay in seconds between scroll steps if scan_full_page is True.
                              Default: 0.2.
        process_iframes (bool): If True, attempts to process and inline iframe content.
                                Default: False.
        remove_overlay_elements (bool): If True, remove overlays/popups before extracting HTML.
                                        Default: False.
        simulate_user (bool): If True, simulate user interactions (mouse moves, clicks) for anti-bot measures.
                              Default: False.
        override_navigator (bool): If True, overrides navigator properties for more human-like behavior.
                                   Default: False.
        magic (bool): If True, attempts automatic handling of overlays/popups.
                      Default: False.
        adjust_viewport_to_content (bool): If True, adjust viewport according to the page content dimensions.
                                           Default: False.

        # Media Handling Parameters
        screenshot (bool): Whether to take a screenshot after crawling.
                           Default: False.
        screenshot_wait_for (float or None): Additional wait time before taking a screenshot.
                                             Default: None.
        screenshot_height_threshold (int): Threshold for page height to decide screenshot strategy.
                                           Default: SCREENSHOT_HEIGHT_TRESHOLD (from config, e.g. 20000).
        pdf (bool): Whether to generate a PDF of the page.
                    Default: False.
        image_description_min_word_threshold (int): Minimum words for image description extraction.
                                                    Default: IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD (e.g., 50).
        image_score_threshold (int): Minimum score threshold for processing an image.
                                     Default: IMAGE_SCORE_THRESHOLD (e.g., 3).
        exclude_external_images (bool): If True, exclude all external images from processing.
                                         Default: False.

        # Link and Domain Handling Parameters
        exclude_social_media_domains (list of str): List of domains to exclude for social media links.
                                                    Default: SOCIAL_MEDIA_DOMAINS (from config).
        exclude_external_links (bool): If True, exclude all external links from the results.
                                       Default: False.
        exclude_social_media_links (bool): If True, exclude links pointing to social media domains.
                                           Default: False.
        exclude_domains (list of str): List of specific domains to exclude from results.
                                       Default: [].

        # Debugging and Logging Parameters
        verbose (bool): Enable verbose logging.
                        Default: True.
        log_console (bool): If True, log console messages from the page.
                            Default: False.

        # Streaming Parameters
        stream (bool): If True, enables streaming of crawled URLs as they are processed when used with arun_many.
                      Default: False.

        # Optional Parameters
        stream (bool): If True, stream the page content as it is being loaded.
        url: str = None  # This is not a compulsory parameter
        check_robots_txt (bool): Whether to check robots.txt rules before crawling. Default: False
    """

    def __init__(
        self,
        # Content Processing Parameters
        word_count_threshold: int = MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        markdown_generator: MarkdownGenerationStrategy = None,
        content_filter=None,
        only_text: bool = False,
        css_selector: str = None,
        excluded_tags: list = None,
        excluded_selector: str = None,
        keep_data_attributes: bool = False,
        remove_forms: bool = False,
        prettiify: bool = False,
        parser_type: str = "lxml",
        scraping_strategy: ContentScrapingStrategy = None,
        proxy_config: dict = None,
        # SSL Parameters
        fetch_ssl_certificate: bool = False,
        # Caching Parameters
        cache_mode=None,
        session_id: str = None,
        bypass_cache: bool = False,
        disable_cache: bool = False,
        no_cache_read: bool = False,
        no_cache_write: bool = False,
        shared_data: dict = None,
        # Page Navigation and Timing Parameters
        wait_until: str = "domcontentloaded",
        page_timeout: int = PAGE_TIMEOUT,
        wait_for: str = None,
        wait_for_images: bool = False,
        delay_before_return_html: float = 0.1,
        mean_delay: float = 0.1,
        max_range: float = 0.3,
        semaphore_count: int = 5,
        # Page Interaction Parameters
        js_code: Union[str, List[str]] = None,
        js_only: bool = False,
        ignore_body_visibility: bool = True,
        scan_full_page: bool = False,
        scroll_delay: float = 0.2,
        process_iframes: bool = False,
        remove_overlay_elements: bool = False,
        simulate_user: bool = False,
        override_navigator: bool = False,
        magic: bool = False,
        adjust_viewport_to_content: bool = False,
        # Media Handling Parameters
        screenshot: bool = False,
        screenshot_wait_for: float = None,
        screenshot_height_threshold: int = SCREENSHOT_HEIGHT_TRESHOLD,
        pdf: bool = False,
        image_description_min_word_threshold: int = IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
        image_score_threshold: int = IMAGE_SCORE_THRESHOLD,
        exclude_external_images: bool = False,
        # Link and Domain Handling Parameters
        exclude_social_media_domains: list = None,
        exclude_external_links: bool = False,
        exclude_social_media_links: bool = False,
        exclude_domains: list = None,
        # Debugging and Logging Parameters
        verbose: bool = True,
        log_console: bool = False,
        # Streaming Parameters
        stream: bool = False,
        url: str = None,
        check_robots_txt: bool = False,
    ):
        self.url = url

        # Content Processing Parameters
        self.word_count_threshold = word_count_threshold
        self.extraction_strategy = extraction_strategy
        self.chunking_strategy = chunking_strategy
        self.markdown_generator = markdown_generator
        self.content_filter = content_filter
        self.only_text = only_text
        self.css_selector = css_selector
        self.excluded_tags = excluded_tags or []
        self.excluded_selector = excluded_selector or ""
        self.keep_data_attributes = keep_data_attributes
        self.remove_forms = remove_forms
        self.prettiify = prettiify
        self.parser_type = parser_type
        self.scraping_strategy = scraping_strategy or WebScrapingStrategy()
        self.proxy_config = proxy_config

        # SSL Parameters
        self.fetch_ssl_certificate = fetch_ssl_certificate

        # Caching Parameters
        self.cache_mode = cache_mode
        self.session_id = session_id
        self.bypass_cache = bypass_cache
        self.disable_cache = disable_cache
        self.no_cache_read = no_cache_read
        self.no_cache_write = no_cache_write
        self.shared_data = shared_data

        # Page Navigation and Timing Parameters
        self.wait_until = wait_until
        self.page_timeout = page_timeout
        self.wait_for = wait_for
        self.wait_for_images = wait_for_images
        self.delay_before_return_html = delay_before_return_html
        self.mean_delay = mean_delay
        self.max_range = max_range
        self.semaphore_count = semaphore_count

        # Page Interaction Parameters
        self.js_code = js_code
        self.js_only = js_only
        self.ignore_body_visibility = ignore_body_visibility
        self.scan_full_page = scan_full_page
        self.scroll_delay = scroll_delay
        self.process_iframes = process_iframes
        self.remove_overlay_elements = remove_overlay_elements
        self.simulate_user = simulate_user
        self.override_navigator = override_navigator
        self.magic = magic
        self.adjust_viewport_to_content = adjust_viewport_to_content

        # Media Handling Parameters
        self.screenshot = screenshot
        self.screenshot_wait_for = screenshot_wait_for
        self.screenshot_height_threshold = screenshot_height_threshold
        self.pdf = pdf
        self.image_description_min_word_threshold = image_description_min_word_threshold
        self.image_score_threshold = image_score_threshold
        self.exclude_external_images = exclude_external_images

        # Link and Domain Handling Parameters
        self.exclude_social_media_domains = (
            exclude_social_media_domains or SOCIAL_MEDIA_DOMAINS
        )
        self.exclude_external_links = exclude_external_links
        self.exclude_social_media_links = exclude_social_media_links
        self.exclude_domains = exclude_domains or []

        # Debugging and Logging Parameters
        self.verbose = verbose
        self.log_console = log_console

        # Streaming Parameters
        self.stream = stream

        # Robots.txt Handling Parameters
        self.check_robots_txt = check_robots_txt

        # Validate type of extraction strategy and chunking strategy if they are provided
        if self.extraction_strategy is not None and not isinstance(
            self.extraction_strategy, ExtractionStrategy
        ):
            raise ValueError(
                "extraction_strategy must be an instance of ExtractionStrategy"
            )
        if self.chunking_strategy is not None and not isinstance(
            self.chunking_strategy, ChunkingStrategy
        ):
            raise ValueError(
                "chunking_strategy must be an instance of ChunkingStrategy"
            )

        # Set default chunking strategy if None
        if self.chunking_strategy is None:
            self.chunking_strategy = RegexChunking()

    @staticmethod
    def from_kwargs(kwargs: dict) -> "CrawlerRunConfig":
        return CrawlerRunConfig(
            # Content Processing Parameters
            word_count_threshold=kwargs.get("word_count_threshold", 200),
            extraction_strategy=kwargs.get("extraction_strategy"),
            chunking_strategy=kwargs.get("chunking_strategy", RegexChunking()),
            markdown_generator=kwargs.get("markdown_generator"),
            content_filter=kwargs.get("content_filter"),
            only_text=kwargs.get("only_text", False),
            css_selector=kwargs.get("css_selector"),
            excluded_tags=kwargs.get("excluded_tags", []),
            excluded_selector=kwargs.get("excluded_selector", ""),
            keep_data_attributes=kwargs.get("keep_data_attributes", False),
            remove_forms=kwargs.get("remove_forms", False),
            prettiify=kwargs.get("prettiify", False),
            parser_type=kwargs.get("parser_type", "lxml"),
            scraping_strategy=kwargs.get("scraping_strategy"),
            proxy_config=kwargs.get("proxy_config"),
            # SSL Parameters
            fetch_ssl_certificate=kwargs.get("fetch_ssl_certificate", False),
            # Caching Parameters
            cache_mode=kwargs.get("cache_mode"),
            session_id=kwargs.get("session_id"),
            bypass_cache=kwargs.get("bypass_cache", False),
            disable_cache=kwargs.get("disable_cache", False),
            no_cache_read=kwargs.get("no_cache_read", False),
            no_cache_write=kwargs.get("no_cache_write", False),
            shared_data=kwargs.get("shared_data", None),
            # Page Navigation and Timing Parameters
            wait_until=kwargs.get("wait_until", "domcontentloaded"),
            page_timeout=kwargs.get("page_timeout", 60000),
            wait_for=kwargs.get("wait_for"),
            wait_for_images=kwargs.get("wait_for_images", False),
            delay_before_return_html=kwargs.get("delay_before_return_html", 0.1),
            mean_delay=kwargs.get("mean_delay", 0.1),
            max_range=kwargs.get("max_range", 0.3),
            semaphore_count=kwargs.get("semaphore_count", 5),
            # Page Interaction Parameters
            js_code=kwargs.get("js_code"),
            js_only=kwargs.get("js_only", False),
            ignore_body_visibility=kwargs.get("ignore_body_visibility", True),
            scan_full_page=kwargs.get("scan_full_page", False),
            scroll_delay=kwargs.get("scroll_delay", 0.2),
            process_iframes=kwargs.get("process_iframes", False),
            remove_overlay_elements=kwargs.get("remove_overlay_elements", False),
            simulate_user=kwargs.get("simulate_user", False),
            override_navigator=kwargs.get("override_navigator", False),
            magic=kwargs.get("magic", False),
            adjust_viewport_to_content=kwargs.get("adjust_viewport_to_content", False),
            # Media Handling Parameters
            screenshot=kwargs.get("screenshot", False),
            screenshot_wait_for=kwargs.get("screenshot_wait_for"),
            screenshot_height_threshold=kwargs.get(
                "screenshot_height_threshold", SCREENSHOT_HEIGHT_TRESHOLD
            ),
            pdf=kwargs.get("pdf", False),
            image_description_min_word_threshold=kwargs.get(
                "image_description_min_word_threshold",
                IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
            ),
            image_score_threshold=kwargs.get(
                "image_score_threshold", IMAGE_SCORE_THRESHOLD
            ),
            exclude_external_images=kwargs.get("exclude_external_images", False),
            # Link and Domain Handling Parameters
            exclude_social_media_domains=kwargs.get(
                "exclude_social_media_domains", SOCIAL_MEDIA_DOMAINS
            ),
            exclude_external_links=kwargs.get("exclude_external_links", False),
            exclude_social_media_links=kwargs.get("exclude_social_media_links", False),
            exclude_domains=kwargs.get("exclude_domains", []),
            # Debugging and Logging Parameters
            verbose=kwargs.get("verbose", True),
            log_console=kwargs.get("log_console", False),
            # Streaming Parameters
            stream=kwargs.get("stream", False),
            url=kwargs.get("url"),
            check_robots_txt=kwargs.get("check_robots_txt", False),
        )

    # Create a funciton returns dict of the object
    def to_dict(self):
        return {
            "word_count_threshold": self.word_count_threshold,
            "extraction_strategy": self.extraction_strategy,
            "chunking_strategy": self.chunking_strategy,
            "markdown_generator": self.markdown_generator,
            "content_filter": self.content_filter,
            "only_text": self.only_text,
            "css_selector": self.css_selector,
            "excluded_tags": self.excluded_tags,
            "excluded_selector": self.excluded_selector,
            "keep_data_attributes": self.keep_data_attributes,
            "remove_forms": self.remove_forms,
            "prettiify": self.prettiify,
            "parser_type": self.parser_type,
            "scraping_strategy": self.scraping_strategy,
            "proxy_config": self.proxy_config,
            "fetch_ssl_certificate": self.fetch_ssl_certificate,
            "cache_mode": self.cache_mode,
            "session_id": self.session_id,
            "bypass_cache": self.bypass_cache,
            "disable_cache": self.disable_cache,
            "no_cache_read": self.no_cache_read,
            "no_cache_write": self.no_cache_write,
            "shared_data": self.shared_data,
            "wait_until": self.wait_until,
            "page_timeout": self.page_timeout,
            "wait_for": self.wait_for,
            "wait_for_images": self.wait_for_images,
            "delay_before_return_html": self.delay_before_return_html,
            "mean_delay": self.mean_delay,
            "max_range": self.max_range,
            "semaphore_count": self.semaphore_count,
            "js_code": self.js_code,
            "js_only": self.js_only,
            "ignore_body_visibility": self.ignore_body_visibility,
            "scan_full_page": self.scan_full_page,
            "scroll_delay": self.scroll_delay,
            "process_iframes": self.process_iframes,
            "remove_overlay_elements": self.remove_overlay_elements,
            "simulate_user": self.simulate_user,
            "override_navigator": self.override_navigator,
            "magic": self.magic,
            "adjust_viewport_to_content": self.adjust_viewport_to_content,
            "screenshot": self.screenshot,
            "screenshot_wait_for": self.screenshot_wait_for,
            "screenshot_height_threshold": self.screenshot_height_threshold,
            "pdf": self.pdf,
            "image_description_min_word_threshold": self.image_description_min_word_threshold,
            "image_score_threshold": self.image_score_threshold,
            "exclude_external_images": self.exclude_external_images,
            "exclude_social_media_domains": self.exclude_social_media_domains,
            "exclude_external_links": self.exclude_external_links,
            "exclude_social_media_links": self.exclude_social_media_links,
            "exclude_domains": self.exclude_domains,
            "verbose": self.verbose,
            "log_console": self.log_console,
            "stream": self.stream,
            "url": self.url,
            "check_robots_txt": self.check_robots_txt,
        }

    def clone(self, **kwargs):
        """Create a copy of this configuration with updated values.
        
        Args:
            **kwargs: Key-value pairs of configuration options to update
            
        Returns:
            CrawlerRunConfig: A new instance with the specified updates
            
        Example:
            ```python
            # Create a new config with streaming enabled
            stream_config = config.clone(stream=True)
            
            # Create a new config with multiple updates
            new_config = config.clone(
                stream=True,
                cache_mode=CacheMode.BYPASS,
                verbose=True
            )
            ```
        """
        config_dict = self.to_dict()
        config_dict.update(kwargs)
        return CrawlerRunConfig.from_kwargs(config_dict)
