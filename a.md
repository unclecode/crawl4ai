diff --git a/.gitignore b/.gitignore
index 02c75b3..432b5aa 100644
--- a/.gitignore
+++ b/.gitignore
@@ -206,6 +206,7 @@ pypi_build.sh
 git_issues.py
 git_issues.md
 
+.next/
 .tests/
 .issues/
 .docs/
diff --git a/README.sync.md b/README.sync.md
deleted file mode 100644
index 6bbef7e..0000000
--- a/README.sync.md
+++ /dev/null
@@ -1,244 +0,0 @@
-# Crawl4AI v0.2.77 🕷️🤖
-
-[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
-[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)
-[![GitHub Issues](https://img.shields.io/github/issues/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/issues)
-[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/pulls)
-[![License](https://img.shields.io/github/license/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)
-
-Crawl4AI simplifies web crawling and data extraction, making it accessible for large language models (LLMs) and AI applications. 🆓🌐
-
-#### [v0.2.77] - 2024-08-02
-
-Major improvements in functionality, performance, and cross-platform compatibility! 🚀
-
-- 🐳 **Docker enhancements**:
-  - Significantly improved Dockerfile for easy installation on Linux, Mac, and Windows.
-- 🌐 **Official Docker Hub image**:
-  - Launched our first official image on Docker Hub for streamlined deployment (unclecode/crawl4ai).
-- 🔧 **Selenium upgrade**:
-  - Removed dependency on ChromeDriver, now using Selenium's built-in capabilities for better compatibility.
-- 🖼️ **Image description**:
-  - Implemented ability to generate textual descriptions for extracted images from web pages.
-- ⚡ **Performance boost**:
-  - Various improvements to enhance overall speed and performance.
-  
-## Try it Now!
-
-✨ Play around with this [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1sJPAmeLj5PMrg2VgOwMJ2ubGIcK0cJeX?usp=sharing)
-
-✨ visit our [Documentation Website](https://crawl4ai.com/mkdocs/)
-
-✨ Check [Demo](https://crawl4ai.com/mkdocs/demo)
-
-## Features ✨
-
-- 🆓 Completely free and open-source
-- 🤖 LLM-friendly output formats (JSON, cleaned HTML, markdown)
-- 🌍 Supports crawling multiple URLs simultaneously
-- 🎨 Extracts and returns all media tags (Images, Audio, and Video)
-- 🔗 Extracts all external and internal links
-- 📚 Extracts metadata from the page
-- 🔄 Custom hooks for authentication, headers, and page modifications before crawling
-- 🕵️ User-agent customization
-- 🖼️ Takes screenshots of the page
-- 📜 Executes multiple custom JavaScripts before crawling
-- 📚 Various chunking strategies: topic-based, regex, sentence, and more
-- 🧠 Advanced extraction strategies: cosine clustering, LLM, and more
-- 🎯 CSS selector support
-- 📝 Passes instructions/keywords to refine extraction
-
-# Crawl4AI
-
-## 🌟 Shoutout to Contributors of v0.2.77!
-
-A big thank you to the amazing contributors who've made this release possible:
-
-- [@aravindkarnam](https://github.com/aravindkarnam) for the new image description feature
-- [@FractalMind](https://github.com/FractalMind) for our official Docker Hub image
-- [@ketonkss4](https://github.com/ketonkss4) for helping streamline our Selenium setup
-
-Your contributions are driving Crawl4AI forward! 🚀
-
-## Cool Examples 🚀
-
-### Quick Start
-
-```python
-from crawl4ai import WebCrawler
-
-# Create an instance of WebCrawler
-crawler = WebCrawler()
-
-# Warm up the crawler (load necessary models)
-crawler.warmup()
-
-# Run the crawler on a URL
-result = crawler.run(url="https://www.nbcnews.com/business")
-
-# Print the extracted content
-print(result.markdown)
-```
-
-## How to install 🛠 
-
-### Using pip 🐍
-```bash
-virtualenv venv
-source venv/bin/activate
-pip install "crawl4ai @ git+https://github.com/unclecode/crawl4ai.git"
-```
-
-### Using Docker 🐳
-
-```bash
-# For Mac users (M1/M2)
-# docker build --platform linux/amd64 -t crawl4ai .
-docker build -t crawl4ai .
-docker run -d -p 8000:80 crawl4ai
-```
-
-### Using Docker Hub 🐳
-
-```bash
-docker pull unclecode/crawl4ai:latest
-docker run -d -p 8000:80 unclecode/crawl4ai:latest
-```
-
-
-## Speed-First Design 🚀
-
-Perhaps the most important design principle for this library is speed. We need to ensure it can handle many links and resources in parallel as quickly as possible. By combining this speed with fast LLMs like Groq, the results will be truly amazing.
-
-```python
-import time
-from crawl4ai.web_crawler import WebCrawler
-crawler = WebCrawler()
-crawler.warmup()
-
-start = time.time()
-url = r"https://www.nbcnews.com/business"
-result = crawler.run( url, word_count_threshold=10, bypass_cache=True)
-end = time.time()
-print(f"Time taken: {end - start}")
-```
-
-Let's take a look the calculated time for the above code snippet:
-
-```bash
-[LOG] 🚀 Crawling done, success: True, time taken: 1.3623387813568115 seconds
-[LOG] 🚀 Content extracted, success: True, time taken: 0.05715131759643555 seconds
-[LOG] 🚀 Extraction, time taken: 0.05750393867492676 seconds.
-Time taken: 1.439958095550537
-```
-Fetching the content from the page took 1.3623 seconds, and extracting the content took 0.0575 seconds. 🚀
-
-### Extract Structured Data from Web Pages 📊
-
-Crawl all OpenAI models and their fees from the official page.
-
-```python
-import os
-from crawl4ai import WebCrawler
-from crawl4ai.extraction_strategy import LLMExtractionStrategy
-from pydantic import BaseModel, Field
-
-class OpenAIModelFee(BaseModel):
-    model_name: str = Field(..., description="Name of the OpenAI model.")
-    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
-    output_fee: str = Field(..., description="Fee for output token ßfor the OpenAI model.")
-
-url = 'https://openai.com/api/pricing/'
-crawler = WebCrawler()
-crawler.warmup()
-
-result = crawler.run(
-        url=url,
-        word_count_threshold=1,
-        extraction_strategy= LLMExtractionStrategy(
-            provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY'), 
-            schema=OpenAIModelFee.schema(),
-            extraction_type="schema",
-            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
-            Do not miss any models in the entire content. One extracted model JSON format should look like this: 
-            {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}."""
-        ),            
-        bypass_cache=True,
-    )
-
-print(result.extracted_content)
-```
-
-### Execute JS, Filter Data with CSS Selector, and Clustering
-
-```python
-from crawl4ai import WebCrawler
-from crawl4ai.chunking_strategy import CosineStrategy
-
-js_code = ["const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"]
-
-crawler = WebCrawler()
-crawler.warmup()
-
-result = crawler.run(
-    url="https://www.nbcnews.com/business",
-    js=js_code,
-    css_selector="p",
-    extraction_strategy=CosineStrategy(semantic_filter="technology")
-)
-
-print(result.extracted_content)
-```
-
-### Extract Structured Data from Web Pages With Proxy and BaseUrl
-
-```python
-from crawl4ai import WebCrawler
-from crawl4ai.extraction_strategy import LLMExtractionStrategy
-
-def create_crawler():
-    crawler = WebCrawler(verbose=True, proxy="http://127.0.0.1:7890")
-    crawler.warmup()
-    return crawler
-
-crawler = create_crawler()
-
-crawler.warmup()
-
-result = crawler.run(
-    url="https://www.nbcnews.com/business",
-    extraction_strategy=LLMExtractionStrategy(
-        provider="openai/gpt-4o",
-        api_token="sk-",
-        base_url="https://api.openai.com/v1"
-    )
-)
-
-print(result.markdown)
-```
-
-## Documentation 📚
-
-For detailed documentation, including installation instructions, advanced features, and API reference, visit our [Documentation Website](https://crawl4ai.com/mkdocs/).
-
-## Contributing 🤝
-
-We welcome contributions from the open-source community. Check out our [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTING.md) for more information.
-
-## License 📄
-
-Crawl4AI is released under the [Apache 2.0 License](https://github.com/unclecode/crawl4ai/blob/main/LICENSE).
-
-## Contact 📧
-
-For questions, suggestions, or feedback, feel free to reach out:
-
-- GitHub: [unclecode](https://github.com/unclecode)
-- Twitter: [@unclecode](https://twitter.com/unclecode)
-- Website: [crawl4ai.com](https://crawl4ai.com)
-
-Happy Crawling! 🕸️🚀
-
-## Star History
-
-[![Star History Chart](https://api.star-history.com/svg?repos=unclecode/crawl4ai&type=Date)](https://star-history.com/#unclecode/crawl4ai&Date)
\ No newline at end of file
diff --git a/crawl4ai/__init__.py b/crawl4ai/__init__.py
index cee7c25..d297dfc 100644
--- a/crawl4ai/__init__.py
+++ b/crawl4ai/__init__.py
@@ -1,7 +1,11 @@
 # __init__.py
 
 from .async_webcrawler import AsyncWebCrawler, CacheMode
-
+from .async_configs import BrowserConfig, CrawlerRunConfig
+from .extraction_strategy import ExtractionStrategy, LLMExtractionStrategy, CosineStrategy, JsonCssExtractionStrategy
+from .chunking_strategy import ChunkingStrategy, RegexChunking
+from .markdown_generation_strategy import DefaultMarkdownGenerator
+from .content_filter_strategy import PruningContentFilter, BM25ContentFilter
 from .models import CrawlResult
 from .__version__ import __version__
 
@@ -9,6 +13,17 @@ __all__ = [
     "AsyncWebCrawler",
     "CrawlResult",
     "CacheMode",
+    'BrowserConfig',
+    'CrawlerRunConfig',
+    'ExtractionStrategy',
+    'LLMExtractionStrategy',
+    'CosineStrategy',
+    'JsonCssExtractionStrategy',
+    'ChunkingStrategy',
+    'RegexChunking',
+    'DefaultMarkdownGenerator',
+    'PruningContentFilter',
+    'BM25ContentFilter',
 ]
 
 def is_sync_version_installed():
diff --git a/crawl4ai/async_crawler_strategy.current.py b/crawl4ai/async_crawler_strategy.current.py
deleted file mode 100644
index 6302447..0000000
--- a/crawl4ai/async_crawler_strategy.current.py
+++ /dev/null
@@ -1,1475 +0,0 @@
-import asyncio
-import base64
-import time
-from abc import ABC, abstractmethod
-from typing import Callable, Dict, Any, List, Optional, Awaitable
-import os, sys, shutil
-import tempfile, subprocess
-from playwright.async_api import async_playwright, Page, Browser, Error
-from playwright.async_api import TimeoutError as PlaywrightTimeoutError
-from io import BytesIO
-from PIL import Image, ImageDraw, ImageFont
-from pathlib import Path
-from playwright.async_api import ProxySettings
-from pydantic import BaseModel
-import hashlib
-import json
-import uuid
-from .models import AsyncCrawlResponse
-from .utils import create_box_message
-from .user_agent_generator import UserAgentGenerator
-from playwright_stealth import StealthConfig, stealth_async
-
-stealth_config = StealthConfig(
-    webdriver=True,
-    chrome_app=True,
-    chrome_csi=True,
-    chrome_load_times=True,
-    chrome_runtime=True,
-    navigator_languages=True,
-    navigator_plugins=True,
-    navigator_permissions=True,
-    webgl_vendor=True,
-    outerdimensions=True,
-    navigator_hardware_concurrency=True,
-    media_codecs=True,
-)
-
-BROWSER_DISABLE_OPTIONS = [
-    "--disable-background-networking",
-    "--disable-background-timer-throttling",
-    "--disable-backgrounding-occluded-windows",
-    "--disable-breakpad",
-    "--disable-client-side-phishing-detection",
-    "--disable-component-extensions-with-background-pages",
-    "--disable-default-apps",
-    "--disable-extensions",
-    "--disable-features=TranslateUI",
-    "--disable-hang-monitor",
-    "--disable-ipc-flooding-protection",
-    "--disable-popup-blocking",
-    "--disable-prompt-on-repost",
-    "--disable-sync",
-    "--force-color-profile=srgb",
-    "--metrics-recording-only",
-    "--no-first-run",
-    "--password-store=basic",
-    "--use-mock-keychain"
-]
-
-
-class ManagedBrowser:
-    def __init__(self, browser_type: str = "chromium", user_data_dir: Optional[str] = None, headless: bool = False, logger = None, host: str = "localhost", debugging_port: int = 9222):
-        self.browser_type = browser_type
-        self.user_data_dir = user_data_dir
-        self.headless = headless
-        self.browser_process = None
-        self.temp_dir = None
-        self.debugging_port = debugging_port
-        self.host = host
-        self.logger = logger
-        self.shutting_down = False
-
-    async def start(self) -> str:
-        """
-        Starts the browser process and returns the CDP endpoint URL.
-        If user_data_dir is not provided, creates a temporary directory.
-        """
-        
-        # Create temp dir if needed
-        if not self.user_data_dir:
-            self.temp_dir = tempfile.mkdtemp(prefix="browser-profile-")
-            self.user_data_dir = self.temp_dir
-
-        # Get browser path and args based on OS and browser type
-        browser_path = self._get_browser_path()
-        args = self._get_browser_args()
-
-        # Start browser process
-        try:
-            self.browser_process = subprocess.Popen(
-                args,
-                stdout=subprocess.PIPE,
-                stderr=subprocess.PIPE
-            )
-            # Monitor browser process output for errors
-            asyncio.create_task(self._monitor_browser_process())
-            await asyncio.sleep(2)  # Give browser time to start
-            return f"http://{self.host}:{self.debugging_port}"
-        except Exception as e:
-            await self.cleanup()
-            raise Exception(f"Failed to start browser: {e}")
-
-    async def _monitor_browser_process(self):
-        """Monitor the browser process for unexpected termination."""
-        if self.browser_process:
-            try:
-                stdout, stderr = await asyncio.gather(
-                    asyncio.to_thread(self.browser_process.stdout.read),
-                    asyncio.to_thread(self.browser_process.stderr.read)
-                )
-                
-                # Check shutting_down flag BEFORE logging anything
-                if self.browser_process.poll() is not None:
-                    if not self.shutting_down:
-                        self.logger.error(
-                            message="Browser process terminated unexpectedly | Code: {code} | STDOUT: {stdout} | STDERR: {stderr}",
-                            tag="ERROR",
-                            params={
-                                "code": self.browser_process.returncode,
-                                "stdout": stdout.decode(),
-                                "stderr": stderr.decode()
-                            }
-                        )                
-                        await self.cleanup()
-                    else:
-                        self.logger.info(
-                            message="Browser process terminated normally | Code: {code}",
-                            tag="INFO",
-                            params={"code": self.browser_process.returncode}
-                        )
-            except Exception as e:
-                if not self.shutting_down:
-                    self.logger.error(
-                        message="Error monitoring browser process: {error}",
-                        tag="ERROR",
-                        params={"error": str(e)}
-                    )
-
-    def _get_browser_path(self) -> str:
-        """Returns the browser executable path based on OS and browser type"""
-        if sys.platform == "darwin":  # macOS
-            paths = {
-                "chromium": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
-                "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
-                "webkit": "/Applications/Safari.app/Contents/MacOS/Safari"
-            }
-        elif sys.platform == "win32":  # Windows
-            paths = {
-                "chromium": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
-                "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
-                "webkit": None  # WebKit not supported on Windows
-            }
-        else:  # Linux
-            paths = {
-                "chromium": "google-chrome",
-                "firefox": "firefox",
-                "webkit": None  # WebKit not supported on Linux
-            }
-        
-        return paths.get(self.browser_type)
-
-    def _get_browser_args(self) -> List[str]:
-        """Returns browser-specific command line arguments"""
-        base_args = [self._get_browser_path()]
-        
-        if self.browser_type == "chromium":
-            args = [
-                f"--remote-debugging-port={self.debugging_port}",
-                f"--user-data-dir={self.user_data_dir}",
-            ]
-            if self.headless:
-                args.append("--headless=new")
-        elif self.browser_type == "firefox":
-            args = [
-                "--remote-debugging-port", str(self.debugging_port),
-                "--profile", self.user_data_dir,
-            ]
-            if self.headless:
-                args.append("--headless")
-        else:
-            raise NotImplementedError(f"Browser type {self.browser_type} not supported")
-            
-        return base_args + args
-
-    async def cleanup(self):
-        """Cleanup browser process and temporary directory"""
-        # Set shutting_down flag BEFORE any termination actions
-        self.shutting_down = True
-        
-        if self.browser_process:
-            try:
-                self.browser_process.terminate()
-                # Wait for process to end gracefully
-                for _ in range(10):  # 10 attempts, 100ms each
-                    if self.browser_process.poll() is not None:
-                        break
-                    await asyncio.sleep(0.1)
-                
-                # Force kill if still running
-                if self.browser_process.poll() is None:
-                    self.browser_process.kill()
-                    await asyncio.sleep(0.1)  # Brief wait for kill to take effect
-                    
-            except Exception as e:
-                self.logger.error(
-                    message="Error terminating browser: {error}",
-                    tag="ERROR",
-                    params={"error": str(e)}
-                )
-
-        if self.temp_dir and os.path.exists(self.temp_dir):
-            try:
-                shutil.rmtree(self.temp_dir)
-            except Exception as e:
-                self.logger.error(
-                    message="Error removing temporary directory: {error}",
-                    tag="ERROR",
-                    params={"error": str(e)}
-                )
-
-
-class AsyncCrawlerStrategy(ABC):
-    @abstractmethod
-    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
-        pass
-    
-    @abstractmethod
-    async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
-        pass
-    
-    @abstractmethod
-    async def take_screenshot(self, **kwargs) -> str:
-        pass
-    
-    @abstractmethod
-    def update_user_agent(self, user_agent: str):
-        pass
-    
-    @abstractmethod
-    def set_hook(self, hook_type: str, hook: Callable):
-        pass
-
-class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
-    def __init__(self, use_cached_html=False, js_code=None, logger = None, **kwargs):
-        self.text_only = kwargs.get("text_only", False) 
-        self.light_mode = kwargs.get("light_mode", False)
-        self.logger = logger
-        self.use_cached_html = use_cached_html
-        self.viewport_width = kwargs.get("viewport_width", 800 if self.text_only else 1920)
-        self.viewport_height = kwargs.get("viewport_height", 600 if self.text_only else 1080)   
-        
-        if self.text_only:
-           self.extra_args = kwargs.get("extra_args", []) + [
-               '--disable-images',
-               '--disable-javascript',
-               '--disable-gpu',
-               '--disable-software-rasterizer',
-               '--disable-dev-shm-usage'
-           ]
-             
-        self.user_agent = kwargs.get(
-            "user_agent",
-            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.187 Safari/604.1 Edg/117.0.2045.47"
-            # "Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
-        )
-        user_agenr_generator = UserAgentGenerator()
-        if kwargs.get("user_agent_mode") == "random":
-            self.user_agent = user_agenr_generator.generate(
-                 **kwargs.get("user_agent_generator_config", {})
-            )
-        self.proxy = kwargs.get("proxy")
-        self.proxy_config = kwargs.get("proxy_config")
-        self.headless = kwargs.get("headless", True)
-        self.browser_type = kwargs.get("browser_type", "chromium")
-        self.headers = kwargs.get("headers", {})
-        self.browser_hint = user_agenr_generator.generate_client_hints(self.user_agent)
-        self.headers.setdefault("sec-ch-ua", self.browser_hint)
-        self.cookies = kwargs.get("cookies", [])
-        self.storage_state = kwargs.get("storage_state", None)
-        self.sessions = {}
-        self.session_ttl = 1800 
-        self.js_code = js_code
-        self.verbose = kwargs.get("verbose", False)
-        self.playwright = None
-        self.browser = None
-        self.sleep_on_close = kwargs.get("sleep_on_close", False)
-        self.use_managed_browser = kwargs.get("use_managed_browser", False)
-        self.user_data_dir = kwargs.get("user_data_dir", None)
-        self.use_persistent_context = kwargs.get("use_persistent_context", False)
-        self.chrome_channel = kwargs.get("chrome_channel", "chrome")
-        self.managed_browser = None
-        self.default_context = None
-        self.hooks = {
-            'on_browser_created': None,
-            'on_user_agent_updated': None,
-            'on_execution_started': None,
-            'before_goto': None,
-            'after_goto': None,
-            'before_return_html': None,
-            'before_retrieve_html': None
-        }
-        self.extra_args = kwargs.get("extra_args", [])
-        self.ignore_https_errors = kwargs.get("ignore_https_errors", True)
-        self.java_script_enabled = kwargs.get("java_script_enabled", True)
-        self.accept_downloads = kwargs.get("accept_downloads", False)
-        self.downloads_path = kwargs.get("downloads_path")
-        self._downloaded_files = []  # Track downloaded files for current crawl
-        if self.accept_downloads and not self.downloads_path:
-            self.downloads_path = os.path.join(os.getcwd(), "downloads")
-            os.makedirs(self.downloads_path, exist_ok=True)        
-        
-
-    async def __aenter__(self):
-        await self.start()
-        return self
-
-    async def __aexit__(self, exc_type, exc_val, exc_tb):
-        await self.close()
-
-    async def start(self):
-        if self.playwright is None:
-            self.playwright = await async_playwright().start()
-        if self.browser is None:
-            if self.use_managed_browser:
-                # Use managed browser approach
-                self.managed_browser = ManagedBrowser(
-                    browser_type=self.browser_type,
-                    user_data_dir=self.user_data_dir,
-                    headless=self.headless,
-                    logger=self.logger
-                )
-                cdp_url = await self.managed_browser.start()
-                self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
-                
-                # Get the default context that maintains the user profile
-                contexts = self.browser.contexts
-                if contexts:
-                    self.default_context = contexts[0]
-                else:
-                    # If no default context exists, create one
-                    self.default_context = await self.browser.new_context(
-                        viewport={"width": self.viewport_width, "height": self.viewport_height},
-                        storage_state=self.storage_state,
-                        user_agent= self.user_agent,
-                        accept_downloads=self.accept_downloads,
-                        ignore_https_errors=self.ignore_https_errors,
-                        java_script_enabled=self.java_script_enabled,
-                    )
-                
-                # Set up the default context
-                if self.default_context:
-                    await self.default_context.set_extra_http_headers(self.headers)
-                    if self.cookies:
-                        await self.default_context.add_cookies(self.cookies)                    
-                    if self.storage_state:
-                        # If storage_state is a dictionary or file path, Playwright will handle it.
-                        await self.default_context.storage_state(path=None)  # Just ensuring default_context is ready
-                    if self.accept_downloads:
-                        await self.default_context.set_default_timeout(60000)
-                        await self.default_context.set_default_navigation_timeout(60000)
-                        self.default_context._impl_obj._options["accept_downloads"] = True
-                        self.default_context._impl_obj._options["downloads_path"] = self.downloads_path
-                        
-                    if self.user_agent:
-                        await self.default_context.set_extra_http_headers({
-                            "User-Agent": self.user_agent,
-                            "sec-ch-ua": self.browser_hint,
-                            # **self.headers
-                        })
-            else:
-                # Base browser arguments
-                browser_args = {
-                    "headless": self.headless,
-                    "args": [
-                        "--no-sandbox",
-                        "--disable-dev-shm-usage",
-                        "--no-first-run",
-                        "--no-default-browser-check",
-                        "--disable-infobars",
-                        "--window-position=0,0",
-                        "--ignore-certificate-errors",
-                        "--ignore-certificate-errors-spki-list",
-                        "--disable-blink-features=AutomationControlled",
-                        "--window-position=400,0",
-                        f"--window-size={self.viewport_width},{self.viewport_height}",     
-                    ]
-                }
-                
-                if self.light_mode:
-                    browser_args["args"].extend(BROWSER_DISABLE_OPTIONS)              
-                
-                if self.text_only:
-                   browser_args["args"].extend([
-                       '--blink-settings=imagesEnabled=false',
-                       '--disable-remote-fonts'
-                   ])
-                
-                # Add channel if specified (try Chrome first)
-                if self.chrome_channel:
-                    browser_args["channel"] = self.chrome_channel
-                
-                # Add extra args if provided
-                if self.extra_args:
-                    browser_args["args"].extend(self.extra_args)
-                    
-                # Add downloads path if downloads are enabled
-                if self.accept_downloads:
-                    browser_args["downloads_path"] = self.downloads_path
-                
-                # Add proxy settings if a proxy is specified
-                if self.proxy:
-                    proxy_settings = ProxySettings(server=self.proxy)
-                    browser_args["proxy"] = proxy_settings
-                elif self.proxy_config:
-                    proxy_settings = ProxySettings(
-                        server=self.proxy_config.get("server"),
-                        username=self.proxy_config.get("username"),
-                        password=self.proxy_config.get("password")
-                    )
-                    browser_args["proxy"] = proxy_settings
-                    
-                try:
-                    # Select the appropriate browser based on the browser_type
-                    if self.browser_type == "firefox":
-                        self.browser = await self.playwright.firefox.launch(**browser_args)
-                    elif self.browser_type == "webkit":
-                        if "viewport" not in browser_args:
-                            browser_args["viewport"] = {"width": self.viewport_width, "height": self.viewport_height}                        
-                        self.browser = await self.playwright.webkit.launch(**browser_args)
-                    else:
-                        if self.use_persistent_context and self.user_data_dir:
-                            self.browser = await self.playwright.chromium.launch_persistent_context(
-                                user_data_dir=self.user_data_dir,
-                                accept_downloads=self.accept_downloads,
-                                downloads_path=self.downloads_path if self.accept_downloads else None,                                
-                                **browser_args
-                            )
-                            self.default_context = self.browser
-                        else:
-                            self.browser = await self.playwright.chromium.launch(**browser_args)
-                            self.default_context = self.browser
-                                
-                except Exception as e:
-                    # Fallback to chromium if Chrome channel fails
-                    if "chrome" in str(e) and browser_args.get("channel") == "chrome":
-                        browser_args["channel"] = "chromium"
-                        if self.use_persistent_context and self.user_data_dir:
-                            self.browser = await self.playwright.chromium.launch_persistent_context(
-                                user_data_dir=self.user_data_dir,
-                                **browser_args
-                            )
-                            self.default_context = self.browser
-                        else:
-                            self.browser = await self.playwright.chromium.launch(**browser_args)
-                    else:
-                        raise
-
-            await self.execute_hook('on_browser_created', self.browser)
-
-    async def close(self):
-        if self.sleep_on_close:
-            await asyncio.sleep(0.5)
-            
-        # Close all active sessions
-        session_ids = list(self.sessions.keys())
-        for session_id in session_ids:
-            await self.kill_session(session_id)
-            
-        if self.browser:
-            await self.browser.close()
-            self.browser = None
-            
-        if self.managed_browser:
-            await asyncio.sleep(0.5)
-            await self.managed_browser.cleanup()
-            self.managed_browser = None
-            
-        if self.playwright:
-            await self.playwright.stop()
-            self.playwright = None
-
-    # Issue #256: Remove __del__ method to avoid potential issues with async cleanup
-    # def __del__(self):
-    #     if self.browser or self.playwright:
-    #         asyncio.get_event_loop().run_until_complete(self.close())
-
-    def set_hook(self, hook_type: str, hook: Callable):
-        if hook_type in self.hooks:
-            self.hooks[hook_type] = hook
-        else:
-            raise ValueError(f"Invalid hook type: {hook_type}")
-
-    async def execute_hook(self, hook_type: str, *args, **kwargs):
-        hook = self.hooks.get(hook_type)
-        if hook:
-            if asyncio.iscoroutinefunction(hook):
-                return await hook(*args, **kwargs)
-            else:
-                return hook(*args, **kwargs)
-        return args[0] if args else None
-
-    def update_user_agent(self, user_agent: str):
-        self.user_agent = user_agent
-
-    def set_custom_headers(self, headers: Dict[str, str]):
-        self.headers = headers
-
-    async def kill_session(self, session_id: str):
-        if session_id in self.sessions:
-            context, page, _ = self.sessions[session_id]
-            await page.close()
-            if not self.use_managed_browser:
-                await context.close()
-            del self.sessions[session_id]
-
-    def _cleanup_expired_sessions(self):
-        current_time = time.time()
-        expired_sessions = [
-            sid for sid, (_, _, last_used) in self.sessions.items() 
-            if current_time - last_used > self.session_ttl
-        ]
-        for sid in expired_sessions:
-            asyncio.create_task(self.kill_session(sid))
-            
-    async def smart_wait(self, page: Page, wait_for: str, timeout: float = 30000):
-        wait_for = wait_for.strip()
-        
-        if wait_for.startswith('js:'):
-            # Explicitly specified JavaScript
-            js_code = wait_for[3:].strip()
-            return await self.csp_compliant_wait(page, js_code, timeout)
-        elif wait_for.startswith('css:'):
-            # Explicitly specified CSS selector
-            css_selector = wait_for[4:].strip()
-            try:
-                await page.wait_for_selector(css_selector, timeout=timeout)
-            except Error as e:
-                if 'Timeout' in str(e):
-                    raise TimeoutError(f"Timeout after {timeout}ms waiting for selector '{css_selector}'")
-                else:
-                    raise ValueError(f"Invalid CSS selector: '{css_selector}'")
-        else:
-            # Auto-detect based on content
-            if wait_for.startswith('()') or wait_for.startswith('function'):
-                # It's likely a JavaScript function
-                return await self.csp_compliant_wait(page, wait_for, timeout)
-            else:
-                # Assume it's a CSS selector first
-                try:
-                    await page.wait_for_selector(wait_for, timeout=timeout)
-                except Error as e:
-                    if 'Timeout' in str(e):
-                        raise TimeoutError(f"Timeout after {timeout}ms waiting for selector '{wait_for}'")
-                    else:
-                        # If it's not a timeout error, it might be an invalid selector
-                        # Let's try to evaluate it as a JavaScript function as a fallback
-                        try:
-                            return await self.csp_compliant_wait(page, f"() => {{{wait_for}}}", timeout)
-                        except Error:
-                            raise ValueError(f"Invalid wait_for parameter: '{wait_for}'. "
-                                             "It should be either a valid CSS selector, a JavaScript function, "
-                                             "or explicitly prefixed with 'js:' or 'css:'.")
-    
-    async def csp_compliant_wait(self, page: Page, user_wait_function: str, timeout: float = 30000):
-        wrapper_js = f"""
-        async () => {{
-            const userFunction = {user_wait_function};
-            const startTime = Date.now();
-            while (true) {{
-                if (await userFunction()) {{
-                    return true;
-                }}
-                if (Date.now() - startTime > {timeout}) {{
-                    throw new Error('Timeout waiting for condition');
-                }}
-                await new Promise(resolve => setTimeout(resolve, 100));
-            }}
-        }}
-        """
-        
-        try:
-            await page.evaluate(wrapper_js)
-        except TimeoutError:
-            raise TimeoutError(f"Timeout after {timeout}ms waiting for condition")
-        except Exception as e:
-            raise RuntimeError(f"Error in wait condition: {str(e)}")
-
-    async def process_iframes(self, page):
-        # Find all iframes
-        iframes = await page.query_selector_all('iframe')
-        
-        for i, iframe in enumerate(iframes):
-            try:
-                # Add a unique identifier to the iframe
-                await iframe.evaluate(f'(element) => element.id = "iframe-{i}"')
-                
-                # Get the frame associated with this iframe
-                frame = await iframe.content_frame()
-                
-                if frame:
-                    # Wait for the frame to load
-                    await frame.wait_for_load_state('load', timeout=30000)  # 30 seconds timeout
-                    
-                    # Extract the content of the iframe's body
-                    iframe_content = await frame.evaluate('() => document.body.innerHTML')
-                    
-                    # Generate a unique class name for this iframe
-                    class_name = f'extracted-iframe-content-{i}'
-                    
-                    # Replace the iframe with a div containing the extracted content
-                    _iframe = iframe_content.replace('`', '\\`')
-                    await page.evaluate(f"""
-                        () => {{
-                            const iframe = document.getElementById('iframe-{i}');
-                            const div = document.createElement('div');
-                            div.innerHTML = `{_iframe}`;
-                            div.className = '{class_name}';
-                            iframe.replaceWith(div);
-                        }}
-                    """)
-                else:
-                    # print(f"Warning: Could not access content frame for iframe {i}")
-                    self.logger.warning(
-                        message="Could not access content frame for iframe {index}",
-                        tag="SCRAPE",
-                        params={"index": i}
-                    )                    
-            except Exception as e:
-                self.logger.error(
-                    message="Error processing iframe {index}: {error}",
-                    tag="ERROR",
-                    params={"index": i, "error": str(e)}
-                )                
-                # print(f"Error processing iframe {i}: {str(e)}")
-
-        # Return the page object
-        return page  
-    
-    async def create_session(self, **kwargs) -> str:
-        """Creates a new browser session and returns its ID."""
-        if not self.browser:
-            await self.start()
-            
-        session_id = kwargs.get('session_id') or str(uuid.uuid4())
-        
-        if self.use_managed_browser:
-            page = await self.default_context.new_page()
-            self.sessions[session_id] = (self.default_context, page, time.time())
-        else:
-            if self.use_persistent_context and self.browser_type in ["chrome", "chromium"]:
-                context = self.browser
-                page = await context.new_page()
-            else:
-                context = await self.browser.new_context(
-                    user_agent=kwargs.get("user_agent", self.user_agent),
-                    viewport={"width": self.viewport_width, "height": self.viewport_height},
-                    proxy={"server": self.proxy} if self.proxy else None,
-                    accept_downloads=self.accept_downloads,
-                    storage_state=self.storage_state,
-                    ignore_https_errors=True
-                )
-                
-                if self.cookies:
-                    await context.add_cookies(self.cookies)
-                await context.set_extra_http_headers(self.headers)
-                page = await context.new_page()
-                
-            self.sessions[session_id] = (context, page, time.time())
-        
-        return session_id
-    
-    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
-        """
-        Crawls a given URL or processes raw HTML/local file content based on the URL prefix.
-
-        Args:
-            url (str): The URL to crawl. Supported prefixes:
-                - 'http://' or 'https://': Web URL to crawl.
-                - 'file://': Local file path to process.
-                - 'raw:': Raw HTML content to process.
-            **kwargs: Additional parameters:
-                - 'screenshot' (bool): Whether to take a screenshot.
-                - ... [other existing parameters]
-
-        Returns:
-            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional screenshot.
-        """
-        response_headers = {}
-        status_code = 200  # Default to 200 for local/raw HTML
-        screenshot_requested = kwargs.get('screenshot', False)
-        screenshot_data = None
-
-        if url.startswith(('http://', 'https://')):
-            # Proceed with standard web crawling
-            return await self._crawl_web(url, **kwargs)
-
-        elif url.startswith('file://'):
-            # Process local file
-            local_file_path = url[7:]  # Remove 'file://' prefix
-            if not os.path.exists(local_file_path):
-                raise FileNotFoundError(f"Local file not found: {local_file_path}")
-            with open(local_file_path, 'r', encoding='utf-8') as f:
-                html = f.read()
-            if screenshot_requested:
-                screenshot_data = await self._generate_screenshot_from_html(html)
-            return AsyncCrawlResponse(
-                html=html,
-                response_headers=response_headers,
-                status_code=status_code,
-                screenshot=screenshot_data,
-                get_delayed_content=None
-            )
-
-        elif url.startswith('raw:'):
-            # Process raw HTML content
-            raw_html = url[4:]  # Remove 'raw:' prefix
-            html = raw_html
-            if screenshot_requested:
-                screenshot_data = await self._generate_screenshot_from_html(html)
-            return AsyncCrawlResponse(
-                html=html,
-                response_headers=response_headers,
-                status_code=status_code,
-                screenshot=screenshot_data,
-                get_delayed_content=None
-            )
-        else:
-            raise ValueError("URL must start with 'http://', 'https://', 'file://', or 'raw:'")
-
-
-    async def _crawl_web(self, url: str, **kwargs) -> AsyncCrawlResponse:
-        """
-        Existing web crawling logic remains unchanged.
-
-        Args:
-            url (str): The web URL to crawl.
-            **kwargs: Additional parameters.
-
-        Returns:
-            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional screenshot.
-        """
-        response_headers = {}
-        status_code = None
-        
-        # Reset downloaded files list for new crawl
-        self._downloaded_files = []
-        
-        self._cleanup_expired_sessions()
-        session_id = kwargs.get("session_id")
-        
-        # Check if in kwargs we have user_agent that will override the default user_agent
-        user_agent = kwargs.get("user_agent", self.user_agent)
-        
-        # Generate random user agent if magic mode is enabled and user_agent_mode is not random
-        if kwargs.get("user_agent_mode") != "random" and kwargs.get("magic", False):
-            user_agent = UserAgentGenerator().generate(
-                **kwargs.get("user_agent_generator_config", {})
-            )
-        
-        # Handle page creation differently for managed browser
-        context = None
-        if self.use_managed_browser:
-            if session_id:
-                # Reuse existing session if available
-                context, page, _ = self.sessions.get(session_id, (None, None, None))
-                if not page:
-                    # Create new page in default context if session doesn't exist
-                    page = await self.default_context.new_page()
-                    self.sessions[session_id] = (self.default_context, page, time.time())
-            else:
-                # Create new page in default context for non-session requests
-                page = await self.default_context.new_page()
-        else:
-            if session_id:
-                context, page, _ = self.sessions.get(session_id, (None, None, None))
-                if not context:
-                    if self.use_persistent_context and self.browser_type in ["chrome", "chromium"]:
-                        # In persistent context, browser is the context
-                        context = self.browser
-                    else:
-                        # Normal context creation for non-persistent or non-Chrome browsers
-                        context = await self.browser.new_context(
-                            user_agent=user_agent,
-                            viewport={"width": self.viewport_width, "height": self.viewport_height},
-                            proxy={"server": self.proxy} if self.proxy else None,
-                            java_script_enabled=True,
-                            accept_downloads=self.accept_downloads,
-                            storage_state=self.storage_state,
-                            # downloads_path=self.downloads_path if self.accept_downloads else None
-                        )
-                        await context.add_cookies([{"name": "cookiesEnabled", "value": "true", "url": url}])
-                        if self.cookies:
-                            await context.add_cookies(self.cookies)
-                        await context.set_extra_http_headers(self.headers)
-
-                    page = await context.new_page()
-                    self.sessions[session_id] = (context, page, time.time())
-            else:
-                if self.use_persistent_context and self.browser_type in ["chrome", "chromium"]:
-                    # In persistent context, browser is the context
-                    context = self.browser
-                else:
-                    # Normal context creation
-                    context = await self.browser.new_context(
-                        user_agent=user_agent,
-                        # viewport={"width": 1920, "height": 1080},
-                        viewport={"width": self.viewport_width, "height": self.viewport_height},
-                        proxy={"server": self.proxy} if self.proxy else None,
-                        accept_downloads=self.accept_downloads,
-                        storage_state=self.storage_state,
-                        ignore_https_errors=True  # Add this line
-                    )
-                    if self.cookies:
-                            await context.add_cookies(self.cookies)
-                    await context.set_extra_http_headers(self.headers)
-                
-                if kwargs.get("override_navigator", False) or kwargs.get("simulate_user", False) or kwargs.get("magic", False):
-                    # Inject scripts to override navigator properties
-                    await context.add_init_script("""
-                        // Pass the Permissions Test.
-                        const originalQuery = window.navigator.permissions.query;
-                        window.navigator.permissions.query = (parameters) => (
-                            parameters.name === 'notifications' ?
-                                Promise.resolve({ state: Notification.permission }) :
-                                originalQuery(parameters)
-                        );
-                        Object.defineProperty(navigator, 'webdriver', {
-                            get: () => undefined
-                        });
-                        window.navigator.chrome = {
-                            runtime: {},
-                            // Add other properties if necessary
-                        };
-                        Object.defineProperty(navigator, 'plugins', {
-                            get: () => [1, 2, 3, 4, 5],
-                        });
-                        Object.defineProperty(navigator, 'languages', {
-                            get: () => ['en-US', 'en'],
-                        });
-                        Object.defineProperty(document, 'hidden', {
-                            get: () => false
-                        });
-                        Object.defineProperty(document, 'visibilityState', {
-                            get: () => 'visible'
-                        });
-                    """)
-                
-                page = await context.new_page()
-                if kwargs.get("magic", False):
-                    await stealth_async(page, stealth_config)
-
-        # Add console message and error logging
-        if kwargs.get("log_console", False):
-            page.on("console", lambda msg: print(f"Console: {msg.text}"))
-            page.on("pageerror", lambda exc: print(f"Page Error: {exc}"))
-        
-        try:
-            # Set up download handling if enabled
-            if self.accept_downloads:
-                page.on("download", lambda download: asyncio.create_task(self._handle_download(download)))
-
-            if self.use_cached_html:
-                cache_file_path = os.path.join(
-                    os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
-                )
-                if os.path.exists(cache_file_path):
-                    html = ""
-                    with open(cache_file_path, "r") as f:
-                        html = f.read()
-                    # retrieve response headers and status code from cache
-                    with open(cache_file_path + ".meta", "r") as f:
-                        meta = json.load(f)
-                        response_headers = meta.get("response_headers", {})
-                        status_code = meta.get("status_code")
-                    response = AsyncCrawlResponse(
-                        html=html, response_headers=response_headers, status_code=status_code
-                    )
-                    return response
-
-            if not kwargs.get("js_only", False):
-                await self.execute_hook('before_goto', page, context = context, **kwargs)
-
-                try:
-                    response = await page.goto(
-                        url,
-                        # wait_until=kwargs.get("wait_until", ["domcontentloaded", "networkidle"]),
-                        wait_until=kwargs.get("wait_until", "domcontentloaded"),
-                        timeout=kwargs.get("page_timeout", 60000),
-                    )
-                except Error as e:
-                    raise RuntimeError(f"Failed on navigating ACS-GOTO :\n{str(e)}")
-                
-                await self.execute_hook('after_goto', page, context = context, **kwargs)
-                
-                # Get status code and headers
-                status_code = response.status
-                response_headers = response.headers
-            else:
-                status_code = 200
-                response_headers = {}
-
-            # Replace the current wait_for_selector line with this more robust check:
-            try:
-                # First wait for body to exist, regardless of visibility
-                await page.wait_for_selector('body', state='attached', timeout=30000)
-                
-                # Then wait for it to become visible by checking CSS
-                await page.wait_for_function("""
-                    () => {
-                        const body = document.body;
-                        const style = window.getComputedStyle(body);
-                        return style.display !== 'none' && 
-                            style.visibility !== 'hidden' && 
-                            style.opacity !== '0';
-                    }
-                """, timeout=30000)
-                
-            except Error as e:
-                # If waiting fails, let's try to diagnose the issue
-                visibility_info = await page.evaluate("""
-                    () => {
-                        const body = document.body;
-                        const style = window.getComputedStyle(body);
-                        return {
-                            display: style.display,
-                            visibility: style.visibility,
-                            opacity: style.opacity,
-                            hasContent: body.innerHTML.length,
-                            classList: Array.from(body.classList)
-                        }
-                    }
-                """)
-                
-                if self.verbose:
-                    print(f"Body visibility debug info: {visibility_info}")
-                
-                # Even if body is hidden, we might still want to proceed
-                if kwargs.get('ignore_body_visibility', True):
-                    if self.verbose:
-                        print("Proceeding despite hidden body...")
-                    pass
-                else:
-                    raise Error(f"Body element is hidden: {visibility_info}")
-            
-            # CONTENT LOADING ASSURANCE
-            if not self.text_only and (kwargs.get("wait_for_images", True) or kwargs.get("adjust_viewport_to_content", False)):
-                # Wait for network idle after initial load and images to load
-                # await page.wait_for_load_state("networkidle")
-                await page.wait_for_load_state("domcontentloaded")
-                await asyncio.sleep(0.1)
-                from playwright.async_api import TimeoutError as PlaywrightTimeoutError
-                try:
-                    await page.wait_for_function("Array.from(document.images).every(img => img.complete)", timeout=1000)
-                # Check for TimeoutError and ignore it
-                except PlaywrightTimeoutError:
-                    pass
-            
-            # After initial load, adjust viewport to content size
-            if not self.text_only and kwargs.get("adjust_viewport_to_content", False):
-                try:                       
-                    # Get actual page dimensions                        
-                    page_width = await page.evaluate("document.documentElement.scrollWidth")
-                    page_height = await page.evaluate("document.documentElement.scrollHeight")
-                    
-                    target_width = self.viewport_width
-                    target_height = int(target_width * page_width / page_height * 0.95)
-                    await page.set_viewport_size({"width": target_width, "height": target_height})
-
-                    # Compute scale factor
-                    # We want the entire page visible: the scale should make both width and height fit
-                    scale = min(target_width / page_width, target_height / page_height)
-
-                    # Now we call CDP to set metrics. 
-                    # We tell Chrome that the "device" is page_width x page_height in size, 
-                    # but we scale it down so everything fits within the real viewport.
-                    cdp = await page.context.new_cdp_session(page)
-                    await cdp.send('Emulation.setDeviceMetricsOverride', {
-                        'width': page_width,          # full page width
-                        'height': page_height,        # full page height
-                        'deviceScaleFactor': 1,       # keep normal DPR
-                        'mobile': False,
-                        'scale': scale                # scale the entire rendered content
-                    })
-                                    
-                except Exception as e:
-                    self.logger.warning(
-                        message="Failed to adjust viewport to content: {error}",
-                        tag="VIEWPORT",
-                        params={"error": str(e)}
-                    )                
-            
-            # After viewport adjustment, handle page scanning if requested
-            if kwargs.get("scan_full_page", False):
-                try:
-                    viewport_height = page.viewport_size.get("height", self.viewport_height)
-                    current_position = viewport_height  # Start with one viewport height
-                    scroll_delay = kwargs.get("scroll_delay", 0.2)
-                    
-                    # Initial scroll
-                    await page.evaluate(f"window.scrollTo(0, {current_position})")
-                    await asyncio.sleep(scroll_delay)
-                    
-                    # Get height after first scroll to account for any dynamic content
-                    total_height = await page.evaluate("document.documentElement.scrollHeight")
-                    
-                    while current_position < total_height:
-                        current_position = min(current_position + viewport_height, total_height)
-                        await page.evaluate(f"window.scrollTo(0, {current_position})")
-                        await asyncio.sleep(scroll_delay)
-                        
-                        # Check for dynamic content
-                        new_height = await page.evaluate("document.documentElement.scrollHeight")
-                        if new_height > total_height:
-                            total_height = new_height
-                    
-                    # Scroll back to top
-                    await page.evaluate("window.scrollTo(0, 0)")
-                    
-                except Exception as e:
-                    self.logger.warning(
-                        message="Failed to perform full page scan: {error}",
-                        tag="PAGE_SCAN", 
-                        params={"error": str(e)}
-                    )
-                else:
-                    # Scroll to the bottom of the page
-                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
-
-            js_code = kwargs.get("js_code", kwargs.get("js", self.js_code))
-            if js_code:
-                if isinstance(js_code, str):
-                    await page.evaluate(js_code)
-                elif isinstance(js_code, list):
-                    for js in js_code:
-                        await page.evaluate(js)
-                
-                # await page.wait_for_timeout(100)
-                
-                # Check for on execution event
-                await self.execute_hook('on_execution_started', page, context = context, **kwargs)
-                
-            if kwargs.get("simulate_user", False) or kwargs.get("magic", False):
-                # Simulate user interactions
-                await page.mouse.move(100, 100)
-                await page.mouse.down()
-                await page.mouse.up()
-                await page.keyboard.press('ArrowDown')
-
-            # Handle the wait_for parameter
-            wait_for = kwargs.get("wait_for")
-            if wait_for:
-                try:
-                    await self.smart_wait(page, wait_for, timeout=kwargs.get("page_timeout", 60000))
-                except Exception as e:
-                    raise RuntimeError(f"Wait condition failed: {str(e)}")
-            
-            # if not wait_for and js_code:
-            #     await page.wait_for_load_state('networkidle', timeout=5000)
-
-            # Update image dimensions
-            if not self.text_only:
-                update_image_dimensions_js = """
-            () => {
-                return new Promise((resolve) => {
-                    const filterImage = (img) => {
-                        // Filter out images that are too small
-                        if (img.width < 100 && img.height < 100) return false;
-                        
-                        // Filter out images that are not visible
-                        const rect = img.getBoundingClientRect();
-                        if (rect.width === 0 || rect.height === 0) return false;
-                        
-                        // Filter out images with certain class names (e.g., icons, thumbnails)
-                        if (img.classList.contains('icon') || img.classList.contains('thumbnail')) return false;
-                        
-                        // Filter out images with certain patterns in their src (e.g., placeholder images)
-                        if (img.src.includes('placeholder') || img.src.includes('icon')) return false;
-                        
-                        return true;
-                    };
-
-                    const images = Array.from(document.querySelectorAll('img')).filter(filterImage);
-                    let imagesLeft = images.length;
-                    
-                    if (imagesLeft === 0) {
-                        resolve();
-                        return;
-                    }
-
-                    const checkImage = (img) => {
-                        if (img.complete && img.naturalWidth !== 0) {
-                            img.setAttribute('width', img.naturalWidth);
-                            img.setAttribute('height', img.naturalHeight);
-                            imagesLeft--;
-                            if (imagesLeft === 0) resolve();
-                        }
-                    };
-
-                    images.forEach(img => {
-                        checkImage(img);
-                        if (!img.complete) {
-                            img.onload = () => {
-                                checkImage(img);
-                            };
-                            img.onerror = () => {
-                                imagesLeft--;
-                                if (imagesLeft === 0) resolve();
-                            };
-                        }
-                    });
-
-                    // Fallback timeout of 5 seconds
-                    // setTimeout(() => resolve(), 5000);
-                    resolve();
-                });
-            }
-            """
-            
-                try:
-                    try:
-                        await page.wait_for_load_state(
-                            # state="load",
-                            state="domcontentloaded",
-                            timeout=5
-                        )
-                    except PlaywrightTimeoutError:
-                        pass
-                    await page.evaluate(update_image_dimensions_js)
-                except Exception as e:
-                    self.logger.error(
-                        message="Error updating image dimensions ACS-UPDATE_IMAGE_DIMENSIONS_JS: {error}",
-                        tag="ERROR",
-                        params={"error": str(e)}
-                    )
-                    # raise RuntimeError(f"Error updating image dimensions ACS-UPDATE_IMAGE_DIMENSIONS_JS: {str(e)}")
-
-            # Wait a bit for any onload events to complete
-            # await page.wait_for_timeout(100)
-
-            # Process iframes
-            if kwargs.get("process_iframes", False):
-                page = await self.process_iframes(page)
-            
-            await self.execute_hook('before_retrieve_html', page, context = context, **kwargs)
-            # Check if delay_before_return_html is set then wait for that time
-            delay_before_return_html = kwargs.get("delay_before_return_html", 0.1)
-            if delay_before_return_html:
-                await asyncio.sleep(delay_before_return_html)
-                
-            # Check for remove_overlay_elements parameter
-            if kwargs.get("remove_overlay_elements", False):
-                await self.remove_overlay_elements(page)
-            
-            html = await page.content()
-            await self.execute_hook('before_return_html', page, html, context = context, **kwargs)
-            
-            # Check if kwargs has screenshot=True then take screenshot
-            screenshot_data = None
-            if kwargs.get("screenshot"):
-                # Check we have screenshot_wait_for parameter, if we have simply wait for that time
-                screenshot_wait_for = kwargs.get("screenshot_wait_for")
-                if screenshot_wait_for:
-                    await asyncio.sleep(screenshot_wait_for)
-                screenshot_data = await self.take_screenshot(page)          
-
-            # if self.verbose:
-            #     print(f"[LOG] ✅ Crawled {url} successfully!")
-           
-            if self.use_cached_html:
-                cache_file_path = os.path.join(
-                    os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
-                )
-                with open(cache_file_path, "w", encoding="utf-8") as f:
-                    f.write(html)
-                # store response headers and status code in cache
-                with open(cache_file_path + ".meta", "w", encoding="utf-8") as f:
-                    json.dump({
-                        "response_headers": response_headers,
-                        "status_code": status_code
-                    }, f)
-
-            async def get_delayed_content(delay: float = 5.0) -> str:
-                if self.verbose:
-                    print(f"[LOG] Waiting for {delay} seconds before retrieving content for {url}")
-                await asyncio.sleep(delay)
-                return await page.content()
-                
-            response = AsyncCrawlResponse(
-                html=html, 
-                response_headers=response_headers, 
-                status_code=status_code,
-                screenshot=screenshot_data,
-                get_delayed_content=get_delayed_content,
-                downloaded_files=self._downloaded_files if self._downloaded_files else None
-            )
-            return response
-        except Error as e:
-            raise Error(f"async_crawler_strategy.py:_crawleb(): {str(e)}")
-        # finally:
-        #     if not session_id:
-        #         await page.close()
-        #         await context.close()
-
-    async def _handle_download(self, download):
-        """Handle file downloads."""
-        try:
-            suggested_filename = download.suggested_filename
-            download_path = os.path.join(self.downloads_path, suggested_filename)
-            
-            self.logger.info(
-                message="Downloading {filename} to {path}",
-                tag="FETCH",
-                params={"filename": suggested_filename, "path": download_path}
-            )
-                
-            start_time = time.perf_counter()
-            await download.save_as(download_path)
-            end_time = time.perf_counter()
-            self._downloaded_files.append(download_path)
-
-            self.logger.success(
-                message="Downloaded {filename} successfully",
-                tag="COMPLETE",
-                params={"filename": suggested_filename, "path": download_path, "duration": f"{end_time - start_time:.2f}s"}
-            )            
-        except Exception as e:
-            self.logger.error(
-                message="Failed to handle download: {error}",
-                tag="ERROR",
-                params={"error": str(e)}
-            )
-            
-            # if self.verbose:
-            #     print(f"[ERROR] Failed to handle download: {str(e)}")
-    
-    async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
-        semaphore_count = kwargs.get('semaphore_count', 5)  # Adjust as needed
-        semaphore = asyncio.Semaphore(semaphore_count)
-
-        async def crawl_with_semaphore(url):
-            async with semaphore:
-                return await self.crawl(url, **kwargs)
-
-        tasks = [crawl_with_semaphore(url) for url in urls]
-        results = await asyncio.gather(*tasks, return_exceptions=True)
-        return [result if not isinstance(result, Exception) else str(result) for result in results]
-
-    async def remove_overlay_elements(self, page: Page) -> None:
-        """
-        Removes popup overlays, modals, cookie notices, and other intrusive elements from the page.
-        
-        Args:
-            page (Page): The Playwright page instance
-        """
-        remove_overlays_js = """
-        async () => {
-            // Function to check if element is visible
-            const isVisible = (elem) => {
-                const style = window.getComputedStyle(elem);
-                return style.display !== 'none' && 
-                       style.visibility !== 'hidden' && 
-                       style.opacity !== '0';
-            };
-
-            // Common selectors for popups and overlays
-            const commonSelectors = [
-                // Close buttons first
-                'button[class*="close" i]', 'button[class*="dismiss" i]', 
-                'button[aria-label*="close" i]', 'button[title*="close" i]',
-                'a[class*="close" i]', 'span[class*="close" i]',
-                
-                // Cookie notices
-                '[class*="cookie-banner" i]', '[id*="cookie-banner" i]',
-                '[class*="cookie-consent" i]', '[id*="cookie-consent" i]',
-                
-                // Newsletter/subscription dialogs
-                '[class*="newsletter" i]', '[class*="subscribe" i]',
-                
-                // Generic popups/modals
-                '[class*="popup" i]', '[class*="modal" i]', 
-                '[class*="overlay" i]', '[class*="dialog" i]',
-                '[role="dialog"]', '[role="alertdialog"]'
-            ];
-
-            // Try to click close buttons first
-            for (const selector of commonSelectors.slice(0, 6)) {
-                const closeButtons = document.querySelectorAll(selector);
-                for (const button of closeButtons) {
-                    if (isVisible(button)) {
-                        try {
-                            button.click();
-                            await new Promise(resolve => setTimeout(resolve, 100));
-                        } catch (e) {
-                            console.log('Error clicking button:', e);
-                        }
-                    }
-                }
-            }
-
-            // Remove remaining overlay elements
-            const removeOverlays = () => {
-                // Find elements with high z-index
-                const allElements = document.querySelectorAll('*');
-                for (const elem of allElements) {
-                    const style = window.getComputedStyle(elem);
-                    const zIndex = parseInt(style.zIndex);
-                    const position = style.position;
-                    
-                    if (
-                        isVisible(elem) && 
-                        (zIndex > 999 || position === 'fixed' || position === 'absolute') &&
-                        (
-                            elem.offsetWidth > window.innerWidth * 0.5 ||
-                            elem.offsetHeight > window.innerHeight * 0.5 ||
-                            style.backgroundColor.includes('rgba') ||
-                            parseFloat(style.opacity) < 1
-                        )
-                    ) {
-                        elem.remove();
-                    }
-                }
-
-                // Remove elements matching common selectors
-                for (const selector of commonSelectors) {
-                    const elements = document.querySelectorAll(selector);
-                    elements.forEach(elem => {
-                        if (isVisible(elem)) {
-                            elem.remove();
-                        }
-                    });
-                }
-            };
-
-            // Remove overlay elements
-            removeOverlays();
-
-            // Remove any fixed/sticky position elements at the top/bottom
-            const removeFixedElements = () => {
-                const elements = document.querySelectorAll('*');
-                elements.forEach(elem => {
-                    const style = window.getComputedStyle(elem);
-                    if (
-                        (style.position === 'fixed' || style.position === 'sticky') &&
-                        isVisible(elem)
-                    ) {
-                        elem.remove();
-                    }
-                });
-            };
-
-            removeFixedElements();
-            
-            // Remove empty block elements as: div, p, span, etc.
-            const removeEmptyBlockElements = () => {
-                const blockElements = document.querySelectorAll('div, p, span, section, article, header, footer, aside, nav, main, ul, ol, li, dl, dt, dd, h1, h2, h3, h4, h5, h6');
-                blockElements.forEach(elem => {
-                    if (elem.innerText.trim() === '') {
-                        elem.remove();
-                    }
-                });
-            };
-
-            // Remove margin-right and padding-right from body (often added by modal scripts)
-            document.body.style.marginRight = '0px';
-            document.body.style.paddingRight = '0px';
-            document.body.style.overflow = 'auto';
-
-            // Wait a bit for any animations to complete
-            await new Promise(resolve => setTimeout(resolve, 100));
-        }
-        """
-        
-        try:
-            await page.evaluate(remove_overlays_js)
-            await page.wait_for_timeout(500)  # Wait for any animations to complete
-        except Exception as e:
-            self.logger.warning(
-                message="Failed to remove overlay elements: {error}",
-                tag="SCRAPE",
-                params={"error": str(e)}
-            )            
-            # if self.verbose:
-            #     print(f"Warning: Failed to remove overlay elements: {str(e)}")
-
-    async def take_screenshot(self, page: Page) -> str:
-        """
-        Takes a screenshot of the current page.
-        
-        Args:
-            page (Page): The Playwright page instance
-            
-        Returns:
-            str: Base64-encoded screenshot image
-        """
-        try:
-            # The page is already loaded, just take the screenshot
-            screenshot = await page.screenshot(full_page=True)
-            return base64.b64encode(screenshot).decode('utf-8')
-        except Exception as e:
-            error_message = f"Failed to take screenshot: {str(e)}"
-            self.logger.error(
-                message="Screenshot failed: {error}",
-                tag="ERROR",
-                params={"error": error_message}
-            )
-            
-
-            # Generate an error image
-            img = Image.new('RGB', (800, 600), color='black')
-            draw = ImageDraw.Draw(img)
-            font = ImageFont.load_default()
-            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
-            
-            buffered = BytesIO()
-            img.save(buffered, format="JPEG")
-            return base64.b64encode(buffered.getvalue()).decode('utf-8')
-        finally:
-            await page.close()
-     
-    async def export_storage_state(self, path: str = None) -> dict:
-        """
-        Exports the current storage state (cookies, localStorage, sessionStorage)
-        to a JSON file at the specified path.
-        """
-        if self.default_context:
-            state = await self.default_context.storage_state(path=path)
-            self.logger.info(
-                message="Exported storage state to {path}",
-                tag="INFO",
-                params={"path": path}
-            )
-            return state
-        else:
-            self.logger.warning(
-                message="No default_context available to export storage state.",
-                tag="WARNING"
-            )
-            
-    async def _generate_screenshot_from_html(self, html: str) -> Optional[str]:
-        """
-        Generates a screenshot from raw HTML content.
-
-        Args:
-            html (str): The HTML content to render and capture.
-
-        Returns:
-            Optional[str]: Base64-encoded screenshot image or an error image if failed.
-        """
-        try:
-            if not self.browser:
-                await self.start()
-            page = await self.browser.new_page()
-            await page.set_content(html, wait_until='networkidle')
-            screenshot = await page.screenshot(full_page=True)
-            await page.close()
-            return base64.b64encode(screenshot).decode('utf-8')
-        except Exception as e:
-            error_message = f"Failed to take screenshot: {str(e)}"
-            # print(error_message)
-            self.logger.error(
-                message="Screenshot failed: {error}",
-                tag="ERROR",
-                params={"error": error_message}
-            )            
-
-            # Generate an error image
-            img = Image.new('RGB', (800, 600), color='black')
-            draw = ImageDraw.Draw(img)
-            font = ImageFont.load_default()
-            draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
-
-            buffered = BytesIO()
-            img.save(buffered, format="JPEG")
-            return base64.b64encode(buffered.getvalue()).decode('utf-8')
-
diff --git a/crawl4ai/async_crawler_strategy.py b/crawl4ai/async_crawler_strategy.py
index 553e9df..3f040e1 100644
--- a/crawl4ai/async_crawler_strategy.py
+++ b/crawl4ai/async_crawler_strategy.py
@@ -17,9 +17,10 @@ import json
 import uuid
 from .js_snippet import load_js_script
 from .models import AsyncCrawlResponse
-from .utils import create_box_message
+from .utils import get_error_context
 from .user_agent_generator import UserAgentGenerator
-from .config import SCREENSHOT_HEIGHT_TRESHOLD
+from .config import SCREENSHOT_HEIGHT_TRESHOLD, DOWNLOAD_PAGE_TIMEOUT
+from .async_configs import BrowserConfig, CrawlerRunConfig
 from playwright_stealth import StealthConfig, stealth_async
 
 
@@ -64,7 +65,6 @@ BROWSER_DISABLE_OPTIONS = [
     "--use-mock-keychain"
 ]
 
-
 class ManagedBrowser:
     def __init__(self, browser_type: str = "chromium", user_data_dir: Optional[str] = None, headless: bool = False, logger = None, host: str = "localhost", debugging_port: int = 9222):
         self.browser_type = browser_type
@@ -225,50 +225,44 @@ class ManagedBrowser:
                     params={"error": str(e)}
                 )
 
-
 class BrowserManager:
-    def __init__(self, use_managed_browser: bool, user_data_dir: Optional[str], headless: bool, logger, browser_type: str, proxy, proxy_config, chrome_channel: str, viewport_width: int, viewport_height: int, accept_downloads: bool, storage_state, ignore_https_errors: bool, java_script_enabled: bool, cookies: List[dict], headers: dict, extra_args: List[str], text_only: bool, light_mode: bool, user_agent: str, browser_hint: str, downloads_path: Optional[str]):
-        self.use_managed_browser = use_managed_browser
-        self.user_data_dir = user_data_dir
-        self.headless = headless
+    def __init__(self, browser_config: BrowserConfig, logger=None):
+        """
+        Initialize the BrowserManager with a browser configuration.
+        
+        Args:
+            browser_config (BrowserConfig): Configuration object containing all browser settings
+            logger: Logger instance for recording events and errors
+        """
+        self.config = browser_config
         self.logger = logger
-        self.browser_type = browser_type
-        self.proxy = proxy
-        self.proxy_config = proxy_config
-        self.chrome_channel = chrome_channel
-        self.viewport_width = viewport_width
-        self.viewport_height = viewport_height
-        self.accept_downloads = accept_downloads
-        self.storage_state = storage_state
-        self.ignore_https_errors = ignore_https_errors
-        self.java_script_enabled = java_script_enabled
-        self.cookies = cookies or []
-        self.headers = headers or {}
-        self.extra_args = extra_args or []
-        self.text_only = text_only
-        self.light_mode = light_mode
+        
+        # Browser state
         self.browser = None
-        self.default_context : BrowserContext = None
+        self.default_context = None
         self.managed_browser = None
-        self.sessions = {}
-        self.session_ttl = 1800
         self.playwright = None
-        self.user_agent = user_agent
-        self.browser_hint = browser_hint
-        self.downloads_path = downloads_path        
+        
+        # Session management
+        self.sessions = {}
+        self.session_ttl = 1800  # 30 minutes
+        
+        # Initialize ManagedBrowser if needed
+        if self.config.use_managed_browser:
+            self.managed_browser = ManagedBrowser(
+                browser_type=self.config.browser_type,
+                user_data_dir=self.config.user_data_dir,
+                headless=self.config.headless,
+                logger=self.logger
+            )
 
     async def start(self):
+        """Start the browser instance and set up the default context."""
         if self.playwright is None:
             from playwright.async_api import async_playwright
             self.playwright = await async_playwright().start()
 
-        if self.use_managed_browser:
-            self.managed_browser = ManagedBrowser(
-                browser_type=self.browser_type,
-                user_data_dir=self.user_data_dir,
-                headless=self.headless,
-                logger=self.logger
-            )
+        if self.config.use_managed_browser:
             cdp_url = await self.managed_browser.start()
             self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
             contexts = self.browser.contexts
@@ -276,142 +270,126 @@ class BrowserManager:
                 self.default_context = contexts[0]
             else:
                 self.default_context = await self.browser.new_context(
-                    viewport={"width": self.viewport_width, "height": self.viewport_height},
-                    storage_state=self.storage_state,
-                    user_agent=self.headers.get("User-Agent"),
-                    accept_downloads=self.accept_downloads,
-                    ignore_https_errors=self.ignore_https_errors,
-                    java_script_enabled=self.java_script_enabled
+                    viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
+                    storage_state=self.config.storage_state,
+                    user_agent=self.config.headers.get("User-Agent", self.config.user_agent),
+                    accept_downloads=self.config.accept_downloads,
+                    ignore_https_errors=self.config.ignore_https_errors,
+                    java_script_enabled=self.config.java_script_enabled
                 )
             await self.setup_context(self.default_context)
         else:
-            browser_args = {
-                "headless": self.headless,
-                "args": [
-                    "--no-sandbox",
-                    "--disable-dev-shm-usage",
-                    "--no-first-run",
-                    "--no-default-browser-check",
-                    "--disable-infobars",
-                    "--window-position=0,0",
-                    "--ignore-certificate-errors",
-                    "--ignore-certificate-errors-spki-list",
-                    "--disable-blink-features=AutomationControlled",
-                    "--window-position=400,0",
-                    f"--window-size={self.viewport_width},{self.viewport_height}",
-                ]
-            }
-
-            if self.light_mode:
-                browser_args["args"].extend(BROWSER_DISABLE_OPTIONS)
+            browser_args = self._build_browser_args()
+            
+            # Launch appropriate browser type
+            if self.config.browser_type == "firefox":
+                self.browser = await self.playwright.firefox.launch(**browser_args)
+            elif self.config.browser_type == "webkit":
+                self.browser = await self.playwright.webkit.launch(**browser_args)
+            else:
+                self.browser = await self.playwright.chromium.launch(**browser_args)
 
-            if self.text_only:
-                browser_args["args"].extend(['--blink-settings=imagesEnabled=false','--disable-remote-fonts'])
+            self.default_context = self.browser
 
-            if self.chrome_channel:
-                browser_args["channel"] = self.chrome_channel
+    def _build_browser_args(self) -> dict:
+        """Build browser launch arguments from config."""
+        args = [
+            "--no-sandbox",
+            "--disable-dev-shm-usage",
+            "--no-first-run",
+            "--no-default-browser-check",
+            "--disable-infobars",
+            "--window-position=0,0",
+            "--ignore-certificate-errors",
+            "--ignore-certificate-errors-spki-list",
+            "--disable-blink-features=AutomationControlled",
+            "--window-position=400,0",
+            f"--window-size={self.config.viewport_width},{self.config.viewport_height}",
+        ]
 
-            if self.extra_args:
-                browser_args["args"].extend(self.extra_args)
+        if self.config.light_mode:
+            args.extend(BROWSER_DISABLE_OPTIONS)
 
-            if self.accept_downloads:
-                browser_args["downloads_path"] = os.path.join(os.getcwd(), "downloads")
-                os.makedirs(browser_args["downloads_path"], exist_ok=True)
+        if self.config.text_only:
+            args.extend(['--blink-settings=imagesEnabled=false', '--disable-remote-fonts'])
 
-            if self.proxy:
-                from playwright.async_api import ProxySettings
-                proxy_settings = ProxySettings(server=self.proxy)
-                browser_args["proxy"] = proxy_settings
-            elif self.proxy_config:
-                from playwright.async_api import ProxySettings
-                proxy_settings = ProxySettings(
-                    server=self.proxy_config.get("server"),
-                    username=self.proxy_config.get("username"),
-                    password=self.proxy_config.get("password")
-                )
-                browser_args["proxy"] = proxy_settings
+        if self.config.extra_args:
+            args.extend(self.config.extra_args)
 
-            if self.browser_type == "firefox":
-                self.browser = await self.playwright.firefox.launch(**browser_args)
-            elif self.browser_type == "webkit":
-                self.browser = await self.playwright.webkit.launch(**browser_args)
-            else:
-                self.browser = await self.playwright.chromium.launch(**browser_args)
+        browser_args = {
+            "headless": self.config.headless,
+            "args": args
+        }
 
-            self.default_context = self.browser
-            # Since default_context in non-managed mode is the browser, no setup needed here.
+        if self.config.chrome_channel:
+            browser_args["channel"] = self.config.chrome_channel
+
+        if self.config.accept_downloads:
+            browser_args["downloads_path"] = (self.config.downloads_path or 
+                                           os.path.join(os.getcwd(), "downloads"))
+            os.makedirs(browser_args["downloads_path"], exist_ok=True)
+
+        if self.config.proxy or self.config.proxy_config:
+            from playwright.async_api import ProxySettings
+            proxy_settings = (
+                ProxySettings(server=self.config.proxy) if self.config.proxy else
+                ProxySettings(
+                    server=self.config.proxy_config.get("server"),
+                    username=self.config.proxy_config.get("username"),
+                    password=self.config.proxy_config.get("password")
+                )
+            )
+            browser_args["proxy"] = proxy_settings
 
+        return browser_args
 
-    async def setup_context(self, context : BrowserContext, is_default=False):
-        # Set extra headers
-        if self.headers:
-            await context.set_extra_http_headers(self.headers)
+    async def setup_context(self, context: BrowserContext, is_default=False):
+        """Set up a browser context with the configured options."""
+        if self.config.headers:
+            await context.set_extra_http_headers(self.config.headers)
 
-        # Add cookies if any
-        if self.cookies:
-            await context.add_cookies(self.cookies)
+        if self.config.cookies:
+            await context.add_cookies(self.config.cookies)
 
-        # Ensure storage_state if provided
-        if self.storage_state:
-            # If storage_state is a dictionary or file path, Playwright will handle it.
+        if self.config.storage_state:
             await context.storage_state(path=None)
 
-        # If accept_downloads, set timeouts and ensure properties
-        if self.accept_downloads:
-            await context.set_default_timeout(60000)
-            await context.set_default_navigation_timeout(60000)
-            if self.downloads_path:
+        if self.config.accept_downloads:
+            context.set_default_timeout(DOWNLOAD_PAGE_TIMEOUT)
+            context.set_default_navigation_timeout(DOWNLOAD_PAGE_TIMEOUT)
+            if self.config.downloads_path:
                 context._impl_obj._options["accept_downloads"] = True
-                context._impl_obj._options["downloads_path"] = self.downloads_path
+                context._impl_obj._options["downloads_path"] = self.config.downloads_path
 
-        # If we have a user_agent, override it along with sec-ch-ua
-        if self.user_agent:
-            # Merge headers if needed
-            combined_headers = {"User-Agent": self.user_agent, "sec-ch-ua": self.browser_hint}
-            combined_headers.update(self.headers)
+        # Handle user agent and browser hints
+        if self.config.user_agent:
+            combined_headers = {
+                "User-Agent": self.config.user_agent,
+                "sec-ch-ua": self.config.browser_hint
+            }
+            combined_headers.update(self.config.headers)
             await context.set_extra_http_headers(combined_headers)
-            
-    async def close(self):
-        # Close all active sessions
-        session_ids = list(self.sessions.keys())
-        for session_id in session_ids:
-            await self.kill_session(session_id)
-
-        if self.browser:
-            await self.browser.close()
-            self.browser = None
-
-        if self.managed_browser:
-            await asyncio.sleep(0.5)
-            await self.managed_browser.cleanup()
-            self.managed_browser = None
-
-        if self.playwright:
-            await self.playwright.stop()
-            self.playwright = None
 
     async def get_page(self, session_id: Optional[str], user_agent: str):
-        # Cleanup expired sessions
+        """Get a page for the given session ID, creating a new one if needed."""
         self._cleanup_expired_sessions()
 
-        if session_id:
-            context, page, _ = self.sessions.get(session_id, (None, None, None))
-            if context and page:
-                self.sessions[session_id] = (context, page, time.time())
-                return page, context
+        if session_id and session_id in self.sessions:
+            context, page, _ = self.sessions[session_id]
+            self.sessions[session_id] = (context, page, time.time())
+            return page, context
 
-        # Create a new context/page pair
-        if self.use_managed_browser:
+        if self.config.use_managed_browser:
             context = self.default_context
             page = await context.new_page()
         else:
             context = await self.browser.new_context(
                 user_agent=user_agent,
-                viewport={"width": self.viewport_width, "height": self.viewport_height},
-                proxy={"server": self.proxy} if self.proxy else None,
-                accept_downloads=self.accept_downloads,
-                storage_state=self.storage_state,
-                ignore_https_errors=self.ignore_https_errors
+                viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
+                proxy={"server": self.config.proxy} if self.config.proxy else None,
+                accept_downloads=self.config.accept_downloads,
+                storage_state=self.config.storage_state,
+                ignore_https_errors=self.config.ignore_https_errors
             )
             await self.setup_context(context)
             page = await context.new_page()
@@ -422,14 +400,16 @@ class BrowserManager:
         return page, context
 
     async def kill_session(self, session_id: str):
+        """Kill a browser session and clean up resources."""
         if session_id in self.sessions:
             context, page, _ = self.sessions[session_id]
             await page.close()
-            if not self.use_managed_browser:
+            if not self.config.use_managed_browser:
                 await context.close()
             del self.sessions[session_id]
 
     def _cleanup_expired_sessions(self):
+        """Clean up expired sessions based on TTL."""
         current_time = time.time()
         expired_sessions = [
             sid for sid, (_, _, last_used) in self.sessions.items()
@@ -438,6 +418,28 @@ class BrowserManager:
         for sid in expired_sessions:
             asyncio.create_task(self.kill_session(sid))
 
+    async def close(self):
+        """Close all browser resources and clean up."""
+        if self.config.sleep_on_close:
+            await asyncio.sleep(0.5)
+            
+        session_ids = list(self.sessions.keys())
+        for session_id in session_ids:
+            await self.kill_session(session_id)
+
+        if self.browser:
+            await self.browser.close()
+            self.browser = None
+
+        if self.managed_browser:
+            await asyncio.sleep(0.5)
+            await self.managed_browser.cleanup()
+            self.managed_browser = None
+
+        if self.playwright:
+            await self.playwright.stop()
+            self.playwright = None
+
 class AsyncCrawlerStrategy(ABC):
     @abstractmethod
     async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
@@ -460,60 +462,24 @@ class AsyncCrawlerStrategy(ABC):
         pass
 
 class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
-    def __init__(self, use_cached_html=False, js_code=None, logger = None, **kwargs):
-        self.text_only = kwargs.get("text_only", False) 
-        self.light_mode = kwargs.get("light_mode", False)
+    def __init__(self, browser_config: BrowserConfig = None, logger = None, **kwargs):
+        """
+        Initialize the AsyncPlaywrightCrawlerStrategy with a browser configuration.
+        
+        Args:
+            browser_config (BrowserConfig): Configuration object containing browser settings.
+                                          If None, will be created from kwargs for backwards compatibility.
+            logger: Logger instance for recording events and errors.
+            **kwargs: Additional arguments for backwards compatibility and extending functionality.
+        """
+        # Initialize browser config, either from provided object or kwargs
+        self.browser_config = browser_config or BrowserConfig.from_kwargs(kwargs)
         self.logger = logger
-        self.use_cached_html = use_cached_html
-        self.viewport_width = kwargs.get("viewport_width", 800 if self.text_only else 1920)
-        self.viewport_height = kwargs.get("viewport_height", 600 if self.text_only else 1080)   
         
-        if self.text_only:
-           self.extra_args = kwargs.get("extra_args", []) + [
-               '--disable-images',
-               '--disable-javascript',
-               '--disable-gpu',
-               '--disable-software-rasterizer',
-               '--disable-dev-shm-usage'
-           ]
-             
-        self.user_agent = kwargs.get(
-            "user_agent",
-            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.187 Safari/604.1 Edg/117.0.2045.47"
-            # "Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
-        )
-        user_agenr_generator = UserAgentGenerator()
-        if kwargs.get("user_agent_mode") == "random":
-            self.user_agent = user_agenr_generator.generate(
-                 **kwargs.get("user_agent_generator_config", {})
-            )
-        self.pdf = kwargs.get("pdf", False)  # New flag
-        self.screenshot_requested = kwargs.get('screenshot', False)
+        # Initialize session management
+        self._downloaded_files = []
         
-        self.proxy = kwargs.get("proxy")
-        self.proxy_config = kwargs.get("proxy_config")
-        self.headless = kwargs.get("headless", True)
-        self.browser_type = kwargs.get("browser_type", "chromium")
-        self.headers = kwargs.get("headers", {})
-        self.browser_hint = user_agenr_generator.generate_client_hints(self.user_agent)
-        self.headers.setdefault("sec-ch-ua", self.browser_hint)
-        self.cookies = kwargs.get("cookies", [])
-        self.storage_state = kwargs.get("storage_state", None)
-        self.sessions = {}
-        self.session_ttl = 1800 
-        self.js_code = js_code
-        self.verbose = kwargs.get("verbose", False)
-        self.playwright = None
-        self.browser = None
-        self.sleep_on_close = kwargs.get("sleep_on_close", False)
-        self.use_managed_browser = kwargs.get("use_managed_browser", False)
-        self.user_data_dir = kwargs.get("user_data_dir", None)
-        self.use_persistent_context = kwargs.get("use_persistent_context", False)
-        if self.use_persistent_context:
-            self.use_managed_browser = True
-        self.chrome_channel = kwargs.get("chrome_channel", "chrome")
-        self.managed_browser = None
-        self.default_context = None
+        # Initialize hooks system
         self.hooks = {
             'on_browser_created': None,
             'on_user_agent_updated': None,
@@ -523,40 +489,12 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
             'before_return_html': None,
             'before_retrieve_html': None
         }
-        self.extra_args = kwargs.get("extra_args", [])
-        self.ignore_https_errors = kwargs.get("ignore_https_errors", True)
-        self.java_script_enabled = kwargs.get("java_script_enabled", True)
-        self.accept_downloads = kwargs.get("accept_downloads", False)
-        self.downloads_path = kwargs.get("downloads_path")
-        self._downloaded_files = []  # Track downloaded files for current crawl
-        if self.accept_downloads and not self.downloads_path:
-            self.downloads_path = os.path.join(os.getcwd(), "downloads")
-            os.makedirs(self.downloads_path, exist_ok=True)        
-
+        
+        # Initialize browser manager with config
         self.browser_manager = BrowserManager(
-            use_managed_browser=self.use_managed_browser,
-            user_data_dir=self.user_data_dir,
-            headless=self.headless,
-            logger=self.logger,
-            browser_type=self.browser_type,
-            proxy=self.proxy,
-            proxy_config=self.proxy_config,
-            chrome_channel=self.chrome_channel,
-            viewport_width=self.viewport_width,
-            viewport_height=self.viewport_height,
-            accept_downloads=self.accept_downloads,
-            storage_state=self.storage_state,
-            ignore_https_errors=self.ignore_https_errors,
-            java_script_enabled=self.java_script_enabled,
-            cookies=self.cookies,
-            headers=self.headers,
-            extra_args=self.extra_args,
-            text_only=self.text_only,
-            light_mode=self.light_mode,
-            user_agent=self.user_agent,
-            browser_hint=self.browser_hint,
-            downloads_path=self.downloads_path            
-        )        
+            browser_config=self.browser_config,
+            logger=self.logger
+        )
 
     async def __aenter__(self):
         await self.start()
@@ -570,15 +508,15 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
         await self.execute_hook('on_browser_created', self.browser_manager.browser, context = self.browser_manager.default_context)
         
     async def close(self):
-        if self.sleep_on_close:
-            await asyncio.sleep(0.5)
-            
         await self.browser_manager.close()
-
-    # Issue #256: Remove __del__ method to avoid potential issues with async cleanup
-    # def __del__(self):
-    #     if self.browser or self.playwright:
-    #         asyncio.get_event_loop().run_until_complete(self.close())
+        
+    async def kill_session(self, session_id: str):
+        # Log a warning message and no need kill session, in new version auto kill session
+        self.logger.warning(
+            message="Session auto-kill is enabled in the new version. No need to manually kill sessions.",
+            tag="WARNING"
+        )
+        await self.browser_manager.kill_session(session_id)
 
     def set_hook(self, hook_type: str, hook: Callable):
         if hook_type in self.hooks:
@@ -600,23 +538,6 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
 
     def set_custom_headers(self, headers: Dict[str, str]):
         self.headers = headers
-
-    async def kill_session(self, session_id: str):
-        if session_id in self.sessions:
-            context, page, _ = self.sessions[session_id]
-            await page.close()
-            if not self.use_managed_browser:
-                await context.close()
-            del self.sessions[session_id]
-
-    def _cleanup_expired_sessions(self):
-        current_time = time.time()
-        expired_sessions = [
-            sid for sid, (_, _, last_used) in self.sessions.items() 
-            if current_time - last_used > self.session_ttl
-        ]
-        for sid in expired_sessions:
-            asyncio.create_task(self.kill_session(sid))
             
     async def smart_wait(self, page: Page, wait_for: str, timeout: float = 30000):
         wait_for = wait_for.strip()
@@ -715,7 +636,6 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
                         }}
                     """)
                 else:
-                    # print(f"Warning: Could not access content frame for iframe {i}")
                     self.logger.warning(
                         message="Could not access content frame for iframe {index}",
                         tag="SCRAPE",
@@ -727,7 +647,6 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
                     tag="ERROR",
                     params={"index": i, "error": str(e)}
                 )                
-                # print(f"Error processing iframe {i}: {str(e)}")
 
         # Return the page object
         return page  
@@ -743,7 +662,7 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
         page, context = await self.browser_manager.get_page(session_id, user_agent)
         return session_id
     
-    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
+    async def crawl(self, url: str, config: CrawlerRunConfig,  **kwargs) -> AsyncCrawlResponse:
         """
         Crawls a given URL or processes raw HTML/local file content based on the URL prefix.
 
@@ -759,15 +678,13 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
         Returns:
             AsyncCrawlResponse: The response containing HTML, headers, status code, and optional screenshot.
         """
+        config = config or CrawlerRunConfig.from_kwargs(kwargs)
         response_headers = {}
-        status_code = 200  # Default to 200 for local/raw HTML
-        screenshot_requested = kwargs.get("screenshot", self.screenshot_requested)
-        pdf_requested = kwargs.get("pdf", self.pdf)
+        status_code = 200  # Default for local/raw HTML
         screenshot_data = None
 
         if url.startswith(('http://', 'https://')):
-            # Proceed with standard web crawling
-            return await self._crawl_web(url, **kwargs)
+            return await self._crawl_web(url, config)
 
         elif url.startswith('file://'):
             # Process local file
@@ -776,7 +693,7 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
                 raise FileNotFoundError(f"Local file not found: {local_file_path}")
             with open(local_file_path, 'r', encoding='utf-8') as f:
                 html = f.read()
-            if screenshot_requested:
+            if config.screenshot:
                 screenshot_data = await self._generate_screenshot_from_html(html)
             return AsyncCrawlResponse(
                 html=html,
@@ -790,7 +707,7 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
             # Process raw HTML content
             raw_html = url[4:]  # Remove 'raw:' prefix
             html = raw_html
-            if screenshot_requested:
+            if config.screenshot:
                 screenshot_data = await self._generate_screenshot_from_html(html)
             return AsyncCrawlResponse(
                 html=html,
@@ -802,92 +719,85 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
         else:
             raise ValueError("URL must start with 'http://', 'https://', 'file://', or 'raw:'")
 
-    async def _crawl_web(self, url: str, **kwargs) -> AsyncCrawlResponse:
+    async def _crawl_web(self, url: str, config: CrawlerRunConfig) -> AsyncCrawlResponse:
+        """
+        Internal method to crawl web URLs with the specified configuration.
+        
+        Args:
+            url (str): The web URL to crawl
+            config (CrawlerRunConfig): Configuration object controlling the crawl behavior
+        
+        Returns:
+            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional data
+        """
         response_headers = {}
         status_code = None
         
-        screenshot_requested = kwargs.get("screenshot", self.screenshot_requested)
-        pdf_requested = kwargs.get("pdf", self.pdf)
-        
         # Reset downloaded files list for new crawl
         self._downloaded_files = []
         
-        self._cleanup_expired_sessions()
-        session_id = kwargs.get("session_id")
-        
-        # Check if in kwargs we have user_agent that will override the default user_agent
-        user_agent = kwargs.get("user_agent", self.user_agent)
-        
-        # Generate random user agent if magic mode is enabled and user_agent_mode is not random
-        if kwargs.get("user_agent_mode") != "random" and kwargs.get("magic", False):
+        # Handle user agent with magic mode
+        user_agent = self.browser_config.user_agent
+        if config.magic and self.browser_config.user_agent_mode != "random":
             user_agent = UserAgentGenerator().generate(
-                **kwargs.get("user_agent_generator_config", {})
+                **(self.browser_config.user_agent_generator_config or {})
             )
         
-        # Handle page creation differently for managed browser
-        page, context = await self.browser_manager.get_page(session_id, user_agent)
+        # Get page for session
+        page, context = await self.browser_manager.get_page(
+            session_id=config.session_id,
+            user_agent=user_agent
+        )
+        
+        # Add default cookie
         await context.add_cookies([{"name": "cookiesEnabled", "value": "true", "url": url}])
         
-        if kwargs.get("override_navigator", False) or kwargs.get("simulate_user", False) or kwargs.get("magic", False):
-            # Inject scripts to override navigator properties
+        # Handle navigator overrides
+        if config.override_navigator or config.simulate_user or config.magic:
             await context.add_init_script(load_js_script("navigator_overrider"))
         
-        # Add console message and error logging
-        if kwargs.get("log_console", False):
-            page.on("console", lambda msg: print(f"Console: {msg.text}"))
-            page.on("pageerror", lambda exc: print(f"Page Error: {exc}"))
+        # Set up console logging if requested
+        if config.log_console:
+            page.on("console", lambda msg: self.logger.debug(
+                message="Console: {msg}",
+                tag="CONSOLE",
+                params={"msg": msg.text}
+            ))
+            page.on("pageerror", lambda exc: self.logger.error(
+                message="Page error: {exc}",
+                tag="ERROR",
+                params={"exc": exc}
+            ))
         
         try:
-            # Set up download handling if enabled
-            if self.accept_downloads:
+            # Set up download handling
+            if self.browser_config.accept_downloads:
                 page.on("download", lambda download: asyncio.create_task(self._handle_download(download)))
 
-            if self.use_cached_html:
-                cache_file_path = os.path.join(
-                    os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
-                )
-                if os.path.exists(cache_file_path):
-                    html = ""
-                    with open(cache_file_path, "r") as f:
-                        html = f.read()
-                    # retrieve response headers and status code from cache
-                    with open(cache_file_path + ".meta", "r") as f:
-                        meta = json.load(f)
-                        response_headers = meta.get("response_headers", {})
-                        status_code = meta.get("status_code")
-                    response = AsyncCrawlResponse(
-                        html=html, response_headers=response_headers, status_code=status_code
-                    )
-                    return response
-
-            if not kwargs.get("js_only", False):
-                await self.execute_hook('before_goto', page, context = context, **kwargs)
+            # Handle page navigation and content loading
+            if not config.js_only:
+                await self.execute_hook('before_goto', page, context=context)
 
                 try:
                     response = await page.goto(
                         url,
-                        # wait_until=kwargs.get("wait_until", ["domcontentloaded", "networkidle"]),
-                        wait_until=kwargs.get("wait_until", "domcontentloaded"),
-                        timeout=kwargs.get("page_timeout", 60000),
+                        wait_until=config.wait_until,
+                        timeout=config.page_timeout
                     )
                 except Error as e:
-                    raise RuntimeError(f"Failed on navigating ACS-GOTO :\n{str(e)}")
+                    raise RuntimeError(f"Failed on navigating ACS-GOTO:\n{str(e)}")
                 
-                await self.execute_hook('after_goto', page, context = context, **kwargs)
+                await self.execute_hook('after_goto', page, context=context)
                 
-                # Get status code and headers
                 status_code = response.status
                 response_headers = response.headers
             else:
                 status_code = 200
                 response_headers = {}
 
-            # Replace the current wait_for_selector line with this more robust check:
+            # Wait for body element and visibility
             try:
-                # First wait for body to exist, regardless of visibility
                 await page.wait_for_selector('body', state='attached', timeout=30000)
-                
-                # Then wait for it to become visible by checking CSS
                 await page.wait_for_function("""
                     () => {
                         const body = document.body;
@@ -897,9 +807,7 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
                             style.opacity !== '0';
                     }
                 """, timeout=30000)
-                
             except Error as e:
-                # If waiting fails, let's try to diagnose the issue
                 visibility_info = await page.evaluate("""
                     () => {
                         const body = document.body;
@@ -914,233 +822,195 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
                     }
                 """)
                 
-                if self.verbose:
-                    print(f"Body visibility debug info: {visibility_info}")
+                if self.config.verbose:
+                    self.logger.debug(
+                        message="Body visibility info: {info}",
+                        tag="DEBUG",
+                        params={"info": visibility_info}
+                    )
                 
-                # Even if body is hidden, we might still want to proceed
-                if kwargs.get('ignore_body_visibility', True):
-                    if self.verbose:
-                        print("Proceeding despite hidden body...")
-                    pass
-                else:
+                if not config.ignore_body_visibility:
                     raise Error(f"Body element is hidden: {visibility_info}")
-            
-            # CONTENT LOADING ASSURANCE
-            if not self.text_only and (kwargs.get("wait_for_images", True) or kwargs.get("adjust_viewport_to_content", False)):
-                # Wait for network idle after initial load and images to load
-                # await page.wait_for_load_state("networkidle")
+
+            # Handle content loading and viewport adjustment
+            if not self.browser_config.text_only and (config.wait_for_images or config.adjust_viewport_to_content):
                 await page.wait_for_load_state("domcontentloaded")
                 await asyncio.sleep(0.1)
-                from playwright.async_api import TimeoutError as PlaywrightTimeoutError
                 try:
-                    await page.wait_for_function("Array.from(document.images).every(img => img.complete)", timeout=1000)
-                # Check for TimeoutError and ignore it
+                    await page.wait_for_function(
+                        "Array.from(document.images).every(img => img.complete)",
+                        timeout=1000
+                    )
                 except PlaywrightTimeoutError:
                     pass
-            
-            # After initial load, adjust viewport to content size
-            if not self.text_only and kwargs.get("adjust_viewport_to_content", False):
-                try:                       
-                    # Get actual page dimensions                        
+
+            # Adjust viewport if needed
+            if not self.browser_config.text_only and config.adjust_viewport_to_content:
+                try:
                     page_width = await page.evaluate("document.documentElement.scrollWidth")
                     page_height = await page.evaluate("document.documentElement.scrollHeight")
                     
-                    target_width = self.viewport_width
+                    target_width = self.browser_config.viewport_width
                     target_height = int(target_width * page_width / page_height * 0.95)
                     await page.set_viewport_size({"width": target_width, "height": target_height})
 
-                    # Compute scale factor
-                    # We want the entire page visible: the scale should make both width and height fit
                     scale = min(target_width / page_width, target_height / page_height)
-
-                    # Now we call CDP to set metrics. 
-                    # We tell Chrome that the "device" is page_width x page_height in size, 
-                    # but we scale it down so everything fits within the real viewport.
                     cdp = await page.context.new_cdp_session(page)
                     await cdp.send('Emulation.setDeviceMetricsOverride', {
-                        'width': page_width,          # full page width
-                        'height': page_height,        # full page height
-                        'deviceScaleFactor': 1,       # keep normal DPR
+                        'width': page_width,
+                        'height': page_height,
+                        'deviceScaleFactor': 1,
                         'mobile': False,
-                        'scale': scale                # scale the entire rendered content
+                        'scale': scale
                     })
-                                    
                 except Exception as e:
                     self.logger.warning(
                         message="Failed to adjust viewport to content: {error}",
                         tag="VIEWPORT",
                         params={"error": str(e)}
-                    )                
-            
-            # After viewport adjustment, handle page scanning if requested
-            if kwargs.get("scan_full_page", False):
-                try:
-                    viewport_height = page.viewport_size.get("height", self.viewport_height)
-                    current_position = viewport_height  # Start with one viewport height
-                    scroll_delay = kwargs.get("scroll_delay", 0.2)
-                    
-                    # Initial scroll
-                    await page.evaluate(f"window.scrollTo(0, {current_position})")
-                    await asyncio.sleep(scroll_delay)
-                    
-                    # Get height after first scroll to account for any dynamic content
-                    total_height = await page.evaluate("document.documentElement.scrollHeight")
-                    
-                    while current_position < total_height:
-                        current_position = min(current_position + viewport_height, total_height)
-                        await page.evaluate(f"window.scrollTo(0, {current_position})")
-                        await asyncio.sleep(scroll_delay)
-                        
-                        # Check for dynamic content
-                        new_height = await page.evaluate("document.documentElement.scrollHeight")
-                        if new_height > total_height:
-                            total_height = new_height
-                    
-                    # Scroll back to top
-                    await page.evaluate("window.scrollTo(0, 0)")
-                    
-                except Exception as e:
-                    self.logger.warning(
-                        message="Failed to perform full page scan: {error}",
-                        tag="PAGE_SCAN", 
-                        params={"error": str(e)}
                     )
-                else:
-                    # Scroll to the bottom of the page
-                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
-
-            js_code = kwargs.get("js_code", kwargs.get("js", self.js_code))
-            if js_code:
-                if isinstance(js_code, str):
-                    await page.evaluate(js_code)
-                elif isinstance(js_code, list):
-                    for js in js_code:
+
+            # Handle full page scanning
+            if config.scan_full_page:
+                await self._handle_full_page_scan(page, config.scroll_delay)
+
+            # Execute JavaScript if provided
+            if config.js_code:
+                if isinstance(config.js_code, str):
+                    await page.evaluate(config.js_code)
+                elif isinstance(config.js_code, list):
+                    for js in config.js_code:
                         await page.evaluate(js)
                 
-                # await page.wait_for_timeout(100)
-                
-                # Check for on execution event
-                await self.execute_hook('on_execution_started', page, context = context, **kwargs)
-                
-            if kwargs.get("simulate_user", False) or kwargs.get("magic", False):
-                # Simulate user interactions
+                await self.execute_hook('on_execution_started', page, context=context)
+
+            # Handle user simulation
+            if config.simulate_user or config.magic:
                 await page.mouse.move(100, 100)
                 await page.mouse.down()
                 await page.mouse.up()
                 await page.keyboard.press('ArrowDown')
 
-            # Handle the wait_for parameter
-            wait_for = kwargs.get("wait_for")
-            if wait_for:
+            # Handle wait_for condition
+            if config.wait_for:
                 try:
-                    await self.smart_wait(page, wait_for, timeout=kwargs.get("page_timeout", 60000))
+                    await self.smart_wait(page, config.wait_for, timeout=config.page_timeout)
                 except Exception as e:
                     raise RuntimeError(f"Wait condition failed: {str(e)}")
-            
-            # if not wait_for and js_code:
-            #     await page.wait_for_load_state('networkidle', timeout=5000)
 
-            # Update image dimensions
-            if not self.text_only:
+            # Update image dimensions if needed
+            if not self.browser_config.text_only:
                 update_image_dimensions_js = load_js_script("update_image_dimensions")
-            
                 try:
                     try:
-                        await page.wait_for_load_state(
-                            # state="load",
-                            state="domcontentloaded",
-                            timeout=5
-                        )
+                        await page.wait_for_load_state("domcontentloaded", timeout=5)
                     except PlaywrightTimeoutError:
                         pass
                     await page.evaluate(update_image_dimensions_js)
                 except Exception as e:
                     self.logger.error(
-                        message="Error updating image dimensions ACS-UPDATE_IMAGE_DIMENSIONS_JS: {error}",
+                        message="Error updating image dimensions: {error}",
                         tag="ERROR",
                         params={"error": str(e)}
                     )
-                    # raise RuntimeError(f"Error updating image dimensions ACS-UPDATE_IMAGE_DIMENSIONS_JS: {str(e)}")
 
-            # Wait a bit for any onload events to complete
-            # await page.wait_for_timeout(100)
-
-            # Process iframes
-            if kwargs.get("process_iframes", False):
+            # Process iframes if needed
+            if config.process_iframes:
                 page = await self.process_iframes(page)
-            
-            await self.execute_hook('before_retrieve_html', page, context = context, **kwargs)
-            # Check if delay_before_return_html is set then wait for that time
-            delay_before_return_html = kwargs.get("delay_before_return_html", 0.1)
-            if delay_before_return_html:
-                await asyncio.sleep(delay_before_return_html)
-                
-            # Check for remove_overlay_elements parameter
-            if kwargs.get("remove_overlay_elements", False):
+
+            # Pre-content retrieval hooks and delay
+            await self.execute_hook('before_retrieve_html', page, context=context)
+            if config.delay_before_return_html:
+                await asyncio.sleep(config.delay_before_return_html)
+
+            # Handle overlay removal
+            if config.remove_overlay_elements:
                 await self.remove_overlay_elements(page)
-            
+
+            # Get final HTML content
             html = await page.content()
-            await self.execute_hook('before_return_html', page, html, context = context, **kwargs)
-            
+            await self.execute_hook('before_return_html', page, html, context=context)
+
+            # Handle PDF and screenshot generation
             start_export_time = time.perf_counter()
             pdf_data = None
-            if pdf_requested:
-                # Generate PDF once
-                pdf_data = await self.export_pdf(page)            
-            
-            # Check if kwargs has screenshot=True then take screenshot
             screenshot_data = None
-            if screenshot_requested: #kwargs.get("screenshot"):
-                # Check we have screenshot_wait_for parameter, if we have simply wait for that time
-                screenshot_wait_for = kwargs.get("screenshot_wait_for")
-                if screenshot_wait_for:
-                    await asyncio.sleep(screenshot_wait_for)
-                
-                screenshot_data = await self.take_screenshot(page, **kwargs)    
-            end_export_time = time.perf_counter()
+
+            if config.pdf:
+                pdf_data = await self.export_pdf(page)
+
+            if config.screenshot:
+                if config.screenshot_wait_for:
+                    await asyncio.sleep(config.screenshot_wait_for)
+                screenshot_data = await self.take_screenshot(
+                    page,
+                    screenshot_height_threshold=config.screenshot_height_threshold
+                )
+
             if screenshot_data or pdf_data:
                 self.logger.info(
                     message="Exporting PDF and taking screenshot took {duration:.2f}s",
                     tag="EXPORT",
-                    params={"duration": end_export_time - start_export_time}
+                    params={"duration": time.perf_counter() - start_export_time}
                 )
-           
-            if self.use_cached_html:
-                cache_file_path = os.path.join(
-                    os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home()), ".crawl4ai", "cache", hashlib.md5(url.encode()).hexdigest()
-                )
-                with open(cache_file_path, "w", encoding="utf-8") as f:
-                    f.write(html)
-                # store response headers and status code in cache
-                with open(cache_file_path + ".meta", "w", encoding="utf-8") as f:
-                    json.dump({
-                        "response_headers": response_headers,
-                        "status_code": status_code
-                    }, f)
 
+            # Define delayed content getter
             async def get_delayed_content(delay: float = 5.0) -> str:
-                if self.verbose:
-                    print(f"[LOG] Waiting for {delay} seconds before retrieving content for {url}")
+                if self.config.verbose:
+                    self.logger.info(
+                        message="Waiting for {delay} seconds before retrieving content for {url}",
+                        tag="INFO",
+                        params={"delay": delay, "url": url}
+                    )                    
                 await asyncio.sleep(delay)
                 return await page.content()
-                
-            response = AsyncCrawlResponse(
-                html=html, 
-                response_headers=response_headers, 
+
+            # Return complete response
+            return AsyncCrawlResponse(
+                html=html,
+                response_headers=response_headers,
                 status_code=status_code,
                 screenshot=screenshot_data,
                 pdf_data=pdf_data,
                 get_delayed_content=get_delayed_content,
                 downloaded_files=self._downloaded_files if self._downloaded_files else None
             )
-            return response
-        except Error as e:
-            raise Error(f"async_crawler_strategy.py:_crawleb(): {str(e)}")
-        # finally:
-        #     if not session_id:
-        #         await page.close()
-        #         await context.close()
 
+        except Exception as e:
+            raise e
+
+    async def _handle_full_page_scan(self, page: Page, scroll_delay: float):
+        """Helper method to handle full page scanning"""
+        try:
+            viewport_height = page.viewport_size.get("height", self.browser_config.viewport_height)
+            current_position = viewport_height
+            
+            await page.evaluate(f"window.scrollTo(0, {current_position})")
+            await asyncio.sleep(scroll_delay)
+            
+            total_height = await page.evaluate("document.documentElement.scrollHeight")
+            
+            while current_position < total_height:
+                current_position = min(current_position + viewport_height, total_height)
+                await page.evaluate(f"window.scrollTo(0, {current_position})")
+                await asyncio.sleep(scroll_delay)
+                
+                new_height = await page.evaluate("document.documentElement.scrollHeight")
+                if new_height > total_height:
+                    total_height = new_height
+            
+            await page.evaluate("window.scrollTo(0, 0)")
+            
+        except Exception as e:
+            self.logger.warning(
+                message="Failed to perform full page scan: {error}",
+                tag="PAGE_SCAN",
+                params={"error": str(e)}
+            )
+        else:
+            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
+    
+    
     async def _handle_download(self, download):
         """Handle file downloads."""
         try:
@@ -1170,8 +1040,6 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
                 params={"error": str(e)}
             )
             
-            # if self.verbose:
-            #     print(f"[ERROR] Failed to handle download: {str(e)}")
     
     async def crawl_many(self, urls: List[str], **kwargs) -> List[AsyncCrawlResponse]:
         semaphore_count = kwargs.get('semaphore_count', 5)  # Adjust as needed
@@ -1192,7 +1060,7 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
         Args:
             page (Page): The Playwright page instance
         """
-        remove_overlays_js = load_js_script("remove_overlays")
+        remove_overlays_js = load_js_script("remove_overlay_elements")
     
         try:
             await page.evaluate(remove_overlays_js)
@@ -1203,8 +1071,6 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
                 tag="SCRAPE",
                 params={"error": str(e)}
             )            
-            # if self.verbose:
-            #     print(f"Warning: Failed to remove overlay elements: {str(e)}")
 
     async def export_pdf(self, page: Page) -> bytes:
         """
@@ -1386,7 +1252,6 @@ class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
             return base64.b64encode(screenshot).decode('utf-8')
         except Exception as e:
             error_message = f"Failed to take screenshot: {str(e)}"
-            # print(error_message)
             self.logger.error(
                 message="Screenshot failed: {error}",
                 tag="ERROR",
diff --git a/crawl4ai/async_database.py b/crawl4ai/async_database.py
index 3c97e7d..5cdafac 100644
--- a/crawl4ai/async_database.py
+++ b/crawl4ai/async_database.py
@@ -1,4 +1,4 @@
-import os
+import os, sys
 from pathlib import Path
 import aiosqlite
 import asyncio
@@ -13,6 +13,7 @@ import aiofiles
 from .config import NEED_MIGRATION
 from .version_manager import VersionManager
 from .async_logger import AsyncLogger
+from .utils import get_error_context, create_box_message
 # Set up logging
 logging.basicConfig(level=logging.INFO)
 logger = logging.getLogger(__name__)
@@ -97,35 +98,84 @@ class AsyncDatabaseManager:
 
     @asynccontextmanager
     async def get_connection(self):
-        """Connection pool manager"""
+        """Connection pool manager with enhanced error handling"""
         if not self._initialized:
-            # Use an asyncio.Lock to ensure only one initialization occurs
             async with self.init_lock:
                 if not self._initialized:
-                    await self.initialize()
-                    self._initialized = True
+                    try:
+                        await self.initialize()
+                        self._initialized = True
+                    except Exception as e:
+                        import sys
+                        error_context = get_error_context(sys.exc_info())
+                        self.logger.error(
+                            message="Database initialization failed:\n{error}\n\nContext:\n{context}\n\nTraceback:\n{traceback}",
+                            tag="ERROR",
+                            force_verbose=True,
+                            params={
+                                "error": str(e),
+                                "context": error_context["code_context"],
+                                "traceback": error_context["full_traceback"]
+                            }
+                        )
+                        raise
 
         await self.connection_semaphore.acquire()
         task_id = id(asyncio.current_task())
+        
         try:
             async with self.pool_lock:
                 if task_id not in self.connection_pool:
-                    conn = await aiosqlite.connect(
-                        self.db_path,
-                        timeout=30.0
-                    )
-                    await conn.execute('PRAGMA journal_mode = WAL')
-                    await conn.execute('PRAGMA busy_timeout = 5000')
-                    self.connection_pool[task_id] = conn
+                    try:
+                        conn = await aiosqlite.connect(
+                            self.db_path,
+                            timeout=30.0
+                        )
+                        await conn.execute('PRAGMA journal_mode = WAL')
+                        await conn.execute('PRAGMA busy_timeout = 5000')
+                        
+                        # Verify database structure
+                        async with conn.execute("PRAGMA table_info(crawled_data)") as cursor:
+                            columns = await cursor.fetchall()
+                            column_names = [col[1] for col in columns]
+                            expected_columns = {
+                                'url', 'html', 'cleaned_html', 'markdown', 'extracted_content',
+                                'success', 'media', 'links', 'metadata', 'screenshot',
+                                'response_headers', 'downloaded_files'
+                            }
+                            missing_columns = expected_columns - set(column_names)
+                            if missing_columns:
+                                raise ValueError(f"Database missing columns: {missing_columns}")
+                        
+                        self.connection_pool[task_id] = conn
+                    except Exception as e:
+                        import sys
+                        error_context = get_error_context(sys.exc_info())
+                        error_message = (
+                            f"Unexpected error in db get_connection at line {error_context['line_no']} "
+                            f"in {error_context['function']} ({error_context['filename']}):\n"
+                            f"Error: {str(e)}\n\n"
+                            f"Code context:\n{error_context['code_context']}"
+                        )
+                        self.logger.error(
+                            message=create_box_message(error_message, type= "error"),
+                        )
+
+                        raise
 
             yield self.connection_pool[task_id]
 
         except Exception as e:
+            import sys
+            error_context = get_error_context(sys.exc_info())
+            error_message = (
+                f"Unexpected error in db get_connection at line {error_context['line_no']} "
+                f"in {error_context['function']} ({error_context['filename']}):\n"
+                f"Error: {str(e)}\n\n"
+                f"Code context:\n{error_context['code_context']}"
+            )
             self.logger.error(
-                message="Connection error: {error}",
-                tag="ERROR",
-                force_verbose=True,
-                params={"error": str(e)}
+                message=create_box_message(error_message, type= "error"),
             )
             raise
         finally:
@@ -230,7 +280,8 @@ class AsyncDatabaseManager:
                     'cleaned_html': row_dict['cleaned_html'],
                     'markdown': row_dict['markdown'],
                     'extracted_content': row_dict['extracted_content'],
-                    'screenshot': row_dict['screenshot']
+                    'screenshot': row_dict['screenshot'],
+                    'screenshots': row_dict['screenshot'],
                 }
                 
                 for field, hash_value in content_fields.items():
diff --git a/crawl4ai/async_webcrawler.py b/crawl4ai/async_webcrawler.py
index fc6fe82..72ef0bf 100644
--- a/crawl4ai/async_webcrawler.py
+++ b/crawl4ai/async_webcrawler.py
@@ -1,4 +1,4 @@
-import os
+import os, sys
 import time
 import warnings
 from enum import Enum
@@ -17,7 +17,7 @@ from .async_crawler_strategy import AsyncCrawlerStrategy, AsyncPlaywrightCrawler
 from .cache_context import CacheMode, CacheContext, _legacy_to_cache_mode
 from .content_scraping_strategy import WebScrapingStrategy
 from .async_logger import AsyncLogger
-
+from .async_configs import BrowserConfig, CrawlerRunConfig
 from .config import (
     MIN_WORD_THRESHOLD, 
     IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
@@ -40,31 +40,20 @@ class AsyncWebCrawler:
     """
     Asynchronous web crawler with flexible caching capabilities.
     
-    Migration Guide (from version X.X.X):
+    Migration Guide:
     Old way (deprecated):
-        crawler = AsyncWebCrawler(always_by_pass_cache=True)
-        result = await crawler.arun(
-            url="https://example.com",
-            bypass_cache=True,
-            no_cache_read=True,
-            no_cache_write=False
-        )
+        crawler = AsyncWebCrawler(always_by_pass_cache=True, browser_type="chromium", headless=True)
     
     New way (recommended):
-        crawler = AsyncWebCrawler(always_bypass_cache=True)
-        result = await crawler.arun(
-            url="https://example.com",
-            cache_mode=CacheMode.WRITE_ONLY
-        )
-    
-    To disable deprecation warnings:
-        Pass warning=False to suppress the warning.
+        browser_config = BrowserConfig(browser_type="chromium", headless=True)
+        crawler = AsyncWebCrawler(browser_config=browser_config)
     """
     _domain_last_hit = {}
 
     def __init__(
         self,
         crawler_strategy: Optional[AsyncCrawlerStrategy] = None,
+        config: Optional[BrowserConfig] = None,
         always_bypass_cache: bool = False,
         always_by_pass_cache: Optional[bool] = None,  # Deprecated parameter
         base_directory: str = str(os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())),
@@ -75,28 +64,48 @@ class AsyncWebCrawler:
         Initialize the AsyncWebCrawler.
 
         Args:
-            crawler_strategy: Strategy for crawling web pages
+            crawler_strategy: Strategy for crawling web pages. If None, will create AsyncPlaywrightCrawlerStrategy
+            config: Configuration object for browser settings. If None, will be created from kwargs
             always_bypass_cache: Whether to always bypass cache (new parameter)
             always_by_pass_cache: Deprecated, use always_bypass_cache instead
             base_directory: Base directory for storing cache
+            thread_safe: Whether to use thread-safe operations
+            **kwargs: Additional arguments for backwards compatibility
         """  
-        self.verbose = kwargs.get("verbose", False)
+        # Handle browser configuration
+        browser_config = config
+        if browser_config is not None:
+            if any(k in kwargs for k in ["browser_type", "headless", "viewport_width", "viewport_height"]):
+                self.logger.warning(
+                    message="Both browser_config and legacy browser parameters provided. browser_config will take precedence.",
+                    tag="WARNING"
+                )
+        else:
+            # Create browser config from kwargs for backwards compatibility
+            browser_config = BrowserConfig.from_kwargs(kwargs)
+
+        self.browser_config = browser_config
+        
+        # Initialize logger first since other components may need it
         self.logger = AsyncLogger(
             log_file=os.path.join(base_directory, ".crawl4ai", "crawler.log"),
-            verbose=self.verbose,
+            verbose=self.browser_config.verbose,    
             tag_width=10
         )
+
         
+        # Initialize crawler strategy
         self.crawler_strategy = crawler_strategy or AsyncPlaywrightCrawlerStrategy(
-            logger = self.logger,
-            **kwargs
+            browser_config=browser_config,
+            logger=self.logger,
+            **kwargs  # Pass remaining kwargs for backwards compatibility
         )
         
-        # Handle deprecated parameter
+        # Handle deprecated cache parameter
         if always_by_pass_cache is not None:
             if kwargs.get("warning", True):
                 warnings.warn(
-                    "'always_by_pass_cache' is deprecated and will be removed in version X.X.X. "
+                    "'always_by_pass_cache' is deprecated and will be removed in version 0.5.0. "
                     "Use 'always_bypass_cache' instead. "
                     "Pass warning=False to suppress this warning.",
                     DeprecationWarning,
@@ -106,13 +115,15 @@ class AsyncWebCrawler:
         else:
             self.always_bypass_cache = always_bypass_cache
 
+        # Thread safety setup
         self._lock = asyncio.Lock() if thread_safe else None
         
+        # Initialize directories
         self.crawl4ai_folder = os.path.join(base_directory, ".crawl4ai")
         os.makedirs(self.crawl4ai_folder, exist_ok=True)
         os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)
+        
         self.ready = False
-        self.verbose = kwargs.get("verbose", False)
 
     async def __aenter__(self):
         await self.crawler_strategy.__aenter__()
@@ -131,197 +142,198 @@ class AsyncWebCrawler:
         self.logger.info(f"Crawl4AI {crawl4ai_version}", tag="INIT")
         self.ready = True
 
-    async def arun(
-        self,
-        url: str,
-        word_count_threshold=MIN_WORD_THRESHOLD,
-        extraction_strategy: ExtractionStrategy = None,
-        chunking_strategy: ChunkingStrategy = RegexChunking(),
-        content_filter: RelevantContentFilter = None,
-        cache_mode: Optional[CacheMode] = None,
-        # Deprecated parameters
-        bypass_cache: bool = False,
-        disable_cache: bool = False,
-        no_cache_read: bool = False,
-        no_cache_write: bool = False,
-        # Other parameters
-        css_selector: str = None,
-        screenshot: bool = False,
-        pdf: bool = False,
-        user_agent: str = None,
-        verbose=True,
-        **kwargs,
-    ) -> CrawlResult:
-        """
-        Runs the crawler for a single source: URL (web, local file, or raw HTML).
 
-        Migration from legacy cache parameters:
+    async def arun(
+            self,
+            url: str,
+            config: Optional[CrawlerRunConfig] = None,
+            # Legacy parameters maintained for backwards compatibility
+            word_count_threshold=MIN_WORD_THRESHOLD,
+            extraction_strategy: ExtractionStrategy = None,
+            chunking_strategy: ChunkingStrategy = RegexChunking(),
+            content_filter: RelevantContentFilter = None,
+            cache_mode: Optional[CacheMode] = None,
+            # Deprecated cache parameters
+            bypass_cache: bool = False,
+            disable_cache: bool = False,
+            no_cache_read: bool = False,
+            no_cache_write: bool = False,
+            # Other legacy parameters
+            css_selector: str = None,
+            screenshot: bool = False,
+            pdf: bool = False,
+            user_agent: str = None,
+            verbose=True,
+            **kwargs,
+        ) -> CrawlResult:
+            """
+            Runs the crawler for a single source: URL (web, local file, or raw HTML).
+
+            Migration Guide:
             Old way (deprecated):
-                await crawler.arun(url, bypass_cache=True, no_cache_read=True)
+                result = await crawler.arun(
+                    url="https://example.com",
+                    word_count_threshold=200,
+                    screenshot=True,
+                    ...
+                )
             
-            New way:
-                await crawler.arun(url, cache_mode=CacheMode.BYPASS)
+            New way (recommended):
+                config = CrawlerRunConfig(
+                    word_count_threshold=200,
+                    screenshot=True,
+                    ...
+                )
+                result = await crawler.arun(url="https://example.com", crawler_config=config)
 
-        Args:
-            url: The URL to crawl (http://, https://, file://, or raw:)
-            cache_mode: Cache behavior control (recommended)
-            word_count_threshold: Minimum word count threshold
-            extraction_strategy: Strategy for content extraction
-            chunking_strategy: Strategy for content chunking
-            css_selector: CSS selector for content extraction
-            screenshot: Whether to capture screenshot
-            user_agent: Custom user agent
-            verbose: Enable verbose logging
+            Args:
+                url: The URL to crawl (http://, https://, file://, or raw:)
+                crawler_config: Configuration object controlling crawl behavior
+                [other parameters maintained for backwards compatibility]
             
-            Deprecated Args:
-                bypass_cache: Use cache_mode=CacheMode.BYPASS instead
-                disable_cache: Use cache_mode=CacheMode.DISABLED instead
-                no_cache_read: Use cache_mode=CacheMode.WRITE_ONLY instead
-                no_cache_write: Use cache_mode=CacheMode.READ_ONLY instead
-
-        Returns:
-            CrawlResult: The result of crawling and processing
-        """
-        # Check if url is not string and is not empty
-        if not isinstance(url, str) or not url:
-            raise ValueError("Invalid URL, make sure the URL is a non-empty string")
-        
-        async with self._lock or self.nullcontext(): # Lock for thread safety previously -> nullcontext():
-            try:
-                # Handle deprecated parameters
-                if any([bypass_cache, disable_cache, no_cache_read, no_cache_write]):
-                    if kwargs.get("warning", True):
-                        warnings.warn(
-                            "Cache control boolean flags are deprecated and will be removed in version X.X.X. "
-                            "Use 'cache_mode' parameter instead. Examples:\n"
-                            "- For bypass_cache=True, use cache_mode=CacheMode.BYPASS\n"
-                            "- For disable_cache=True, use cache_mode=CacheMode.DISABLED\n"
-                            "- For no_cache_read=True, use cache_mode=CacheMode.WRITE_ONLY\n"
-                            "- For no_cache_write=True, use cache_mode=CacheMode.READ_ONLY\n"
-                            "Pass warning=False to suppress this warning.",
-                            DeprecationWarning,
-                            stacklevel=2
-                        )
+            Returns:
+                CrawlResult: The result of crawling and processing
+            """
+            crawler_config = config
+            if not isinstance(url, str) or not url:
+                raise ValueError("Invalid URL, make sure the URL is a non-empty string")
+            
+            async with self._lock or self.nullcontext():
+                try:
+                    # Handle configuration
+                    if crawler_config is not None:
+                        if any(param is not None for param in [
+                            word_count_threshold, extraction_strategy, chunking_strategy,
+                            content_filter, cache_mode, css_selector, screenshot, pdf
+                        ]):
+                            self.logger.warning(
+                                message="Both crawler_config and legacy parameters provided. crawler_config will take precedence.",
+                                tag="WARNING"
+                            )
+                        config = crawler_config
+                    else:
+                        # Merge all parameters into a single kwargs dict for config creation
+                        config_kwargs = {
+                            "word_count_threshold": word_count_threshold,
+                            "extraction_strategy": extraction_strategy,
+                            "chunking_strategy": chunking_strategy,
+                            "content_filter": content_filter,
+                            "cache_mode": cache_mode,
+                            "bypass_cache": bypass_cache,
+                            "disable_cache": disable_cache,
+                            "no_cache_read": no_cache_read,
+                            "no_cache_write": no_cache_write,
+                            "css_selector": css_selector,
+                            "screenshot": screenshot,
+                            "pdf": pdf,
+                            "verbose": verbose,
+                            **kwargs
+                        }
+                        config = CrawlerRunConfig.from_kwargs(config_kwargs)
+
+                    # Handle deprecated cache parameters
+                    if any([bypass_cache, disable_cache, no_cache_read, no_cache_write]):
+                        if kwargs.get("warning", True):
+                            warnings.warn(
+                                "Cache control boolean flags are deprecated and will be removed in version 0.5.0. "
+                                "Use 'cache_mode' parameter instead.",
+                                DeprecationWarning,
+                                stacklevel=2
+                            )
+                        
+                        # Convert legacy parameters if cache_mode not provided
+                        if config.cache_mode is None:
+                            config.cache_mode = _legacy_to_cache_mode(
+                                disable_cache=disable_cache,
+                                bypass_cache=bypass_cache,
+                                no_cache_read=no_cache_read,
+                                no_cache_write=no_cache_write
+                            )
                     
-                    # Convert legacy parameters if cache_mode not provided
-                    if cache_mode is None:
-                        cache_mode = _legacy_to_cache_mode(
-                            disable_cache=disable_cache,
-                            bypass_cache=bypass_cache,
-                            no_cache_read=no_cache_read,
-                            no_cache_write=no_cache_write
-                        )
-                
-                # Default to ENABLED if no cache mode specified
-                if cache_mode is None:
-                    cache_mode = CacheMode.ENABLED
-
-                # Create cache context
-                cache_context = CacheContext(url, cache_mode, self.always_bypass_cache)
-
-                extraction_strategy = extraction_strategy or NoExtractionStrategy()
-                extraction_strategy.verbose = verbose
-                if not isinstance(extraction_strategy, ExtractionStrategy):
-                    raise ValueError("Unsupported extraction strategy")
-                if not isinstance(chunking_strategy, ChunkingStrategy):
-                    raise ValueError("Unsupported chunking strategy")
-                
-                word_count_threshold = max(word_count_threshold, MIN_WORD_THRESHOLD)
-
-                async_response: AsyncCrawlResponse = None
-                cached_result = None
-                screenshot_data = None
-                pdf_data = None
-                extracted_content = None
-                
-                start_time = time.perf_counter()
-                
-                # Try to get cached result if appropriate
-                if cache_context.should_read():
-                    cached_result = await async_db_manager.aget_cached_url(url)
-                            
-                if cached_result:
-                    html = sanitize_input_encode(cached_result.html)
-                    extracted_content = sanitize_input_encode(cached_result.extracted_content or "")
-                    if screenshot:
+                    # Default to ENABLED if no cache mode specified
+                    if config.cache_mode is None:
+                        config.cache_mode = CacheMode.ENABLED
+
+                    # Create cache context
+                    cache_context = CacheContext(url, config.cache_mode, self.always_bypass_cache)
+
+                    # Initialize processing variables
+                    async_response: AsyncCrawlResponse = None
+                    cached_result = None
+                    screenshot_data = None
+                    pdf_data = None
+                    extracted_content = None
+                    start_time = time.perf_counter()
+
+                    # Try to get cached result if appropriate
+                    if cache_context.should_read():
+                        cached_result = await async_db_manager.aget_cached_url(url)
+
+                    if cached_result:
+                        html = sanitize_input_encode(cached_result.html)
+                        extracted_content = sanitize_input_encode(cached_result.extracted_content or "")
+                        # If screenshot is requested but its not in cache, then set cache_result to None
                         screenshot_data = cached_result.screenshot
-                        if not screenshot_data:
-                            cached_result = None
-                    if pdf:
                         pdf_data = cached_result.pdf
-                        if not pdf_data:
+                        if config.screenshot and not screenshot or config.pdf and not pdf:
                             cached_result = None
-                    # if verbose:
-                    #     print(f"{Fore.BLUE}{self.tag_format('FETCH')} {self.log_icons['FETCH']} Cache hit for {cache_context.display_url} | Status: {Fore.GREEN if bool(html) else Fore.RED}{bool(html)}{Style.RESET_ALL} | Time: {time.perf_counter() - start_time:.2f}s")
-                    self.logger.url_status(
+
+                        self.logger.url_status(
                             url=cache_context.display_url,
                             success=bool(html),
                             timing=time.perf_counter() - start_time,
                             tag="FETCH"
-                        )                    
+                        )
 
+                    # Fetch fresh content if needed
+                    if not cached_result or not html:
+                        t1 = time.perf_counter()
+                        
+                        if user_agent:
+                            self.crawler_strategy.update_user_agent(user_agent)
+                        
+                        # Pass config to crawl method
+                        async_response = await self.crawler_strategy.crawl(
+                            url,
+                            config=config  # Pass the entire config object
+                        )
+                        
+                        html = sanitize_input_encode(async_response.html)
+                        screenshot_data = async_response.screenshot
+                        pdf_data = async_response.pdf_data
+                        
+                        t2 = time.perf_counter()
+                        self.logger.url_status(
+                            url=cache_context.display_url,
+                            success=bool(html),
+                            timing=t2 - t1,
+                            tag="FETCH"
+                        )
 
-                # Fetch fresh content if needed
-                if not cached_result or not html:
-                    t1 = time.perf_counter()
-                    
-                    if user_agent:
-                        self.crawler_strategy.update_user_agent(user_agent)
-                    async_response: AsyncCrawlResponse = await self.crawler_strategy.crawl(
-                        url, 
-                        screenshot=screenshot, 
-                        pdf=pdf,
-                        **kwargs
-                    )
-                    html = sanitize_input_encode(async_response.html)
-                    screenshot_data = async_response.screenshot
-                    pdf_data = async_response.pdf_data
-                    t2 = time.perf_counter()
-                    self.logger.url_status(
-                        url=cache_context.display_url,
-                        success=bool(html),
-                        timing=t2 - t1,
-                        tag="FETCH"
+                    # Process the HTML content
+                    crawl_result = await self.aprocess_html(
+                        url=url,
+                        html=html,
+                        extracted_content=extracted_content,
+                        config=config,  # Pass the config object instead of individual parameters
+                        screenshot=screenshot_data,
+                        pdf_data=pdf_data,
+                        verbose=config.verbose
                     )
-                    # if verbose:
-                    #     print(f"{Fore.BLUE}{self.tag_format('FETCH')} {self.log_icons['FETCH']} Live fetch for {cache_context.display_url}... | Status: {Fore.GREEN if bool(html) else Fore.RED}{bool(html)}{Style.RESET_ALL} | Time: {t2 - t1:.2f}s")
-
-                # Process the HTML content
-                crawl_result = await self.aprocess_html(
-                    url=url,
-                    html=html,
-                    extracted_content=extracted_content,
-                    word_count_threshold=word_count_threshold,
-                    extraction_strategy=extraction_strategy,
-                    chunking_strategy=chunking_strategy,
-                    content_filter=content_filter,
-                    css_selector=css_selector,
-                    screenshot=screenshot_data,
-                    pdf_data=pdf_data,
-                    verbose=verbose,
-                    is_cached=bool(cached_result),
-                    async_response=async_response,
-                    is_web_url=cache_context.is_web_url,
-                    is_local_file=cache_context.is_local_file,
-                    is_raw_html=cache_context.is_raw_html,
-                    **kwargs,
-                )
-                
-                # Set response data
-                if async_response:
-                    crawl_result.status_code = async_response.status_code
-                    crawl_result.response_headers = async_response.response_headers
-                    crawl_result.downloaded_files = async_response.downloaded_files
-                else:
-                    crawl_result.status_code = 200
-                    crawl_result.response_headers = cached_result.response_headers if cached_result else {}
 
-                crawl_result.success = bool(html)
-                crawl_result.session_id = kwargs.get("session_id", None)
+                    # Set response data
+                    if async_response:
+                        crawl_result.status_code = async_response.status_code
+                        crawl_result.response_headers = async_response.response_headers
+                        crawl_result.downloaded_files = async_response.downloaded_files
+                    else:
+                        crawl_result.status_code = 200
+                        crawl_result.response_headers = cached_result.response_headers if cached_result else {}
+
+                    crawl_result.success = bool(html)
+                    crawl_result.session_id = getattr(config, 'session_id', None)
 
-                # if verbose:
-                #     print(f"{Fore.GREEN}{self.tag_format('COMPLETE')} {self.log_icons['COMPLETE']} {cache_context.display_url[:URL_LOG_SHORTEN_LENGTH]}... | Status: {Fore.GREEN if crawl_result.success else Fore.RED}{crawl_result.success} | {Fore.YELLOW}Total: {time.perf_counter() - start_time:.2f}s{Style.RESET_ALL}")
-                self.logger.success(
+                    self.logger.success(
                         message="{url:.50}... | Status: {status} | Total: {timing}",
                         tag="COMPLETE",
                         params={
@@ -335,254 +347,312 @@ class AsyncWebCrawler:
                         }
                     )
 
-                # Update cache if appropriate
-                if cache_context.should_write() and not bool(cached_result):
-                    await async_db_manager.acache_url(crawl_result)
+                    # Update cache if appropriate
+                    if cache_context.should_write() and not bool(cached_result):
+                        await async_db_manager.acache_url(crawl_result)
+
+                    return crawl_result
 
-                return crawl_result
+                except Exception as e:
+                    error_context = get_error_context(sys.exc_info())
+                
+                    error_message = (
+                        f"Unexpected error in _crawl_web at line {error_context['line_no']} "
+                        f"in {error_context['function']} ({error_context['filename']}):\n"
+                        f"Error: {str(e)}\n\n"
+                        f"Code context:\n{error_context['code_context']}"
+                    )
+                    # if not hasattr(e, "msg"):
+                    #     e.msg = str(e)
+                    
+                    self.logger.error_status(
+                        url=url,
+                        error=create_box_message(error_message, type="error"),
+                        tag="ERROR"
+                    )
+                    
+                    return CrawlResult(
+                        url=url,
+                        html="",
+                        success=False,
+                        error_message=error_message
+                    )
+
+    async def aprocess_html(
+            self,
+            url: str,
+            html: str,
+            extracted_content: str,
+            config: CrawlerRunConfig,
+            screenshot: str,
+            pdf_data: str,
+            verbose: bool,
+            **kwargs,
+        ) -> CrawlResult:
+            """
+            Process HTML content using the provided configuration.
+            
+            Args:
+                url: The URL being processed
+                html: Raw HTML content
+                extracted_content: Previously extracted content (if any)
+                config: Configuration object controlling processing behavior
+                screenshot: Screenshot data (if any)
+                verbose: Whether to enable verbose logging
+                **kwargs: Additional parameters for backwards compatibility
             
+            Returns:
+                CrawlResult: Processed result containing extracted and formatted content
+            """
+            try:
+                _url = url if not kwargs.get("is_raw_html", False) else "Raw HTML"
+                t1 = time.perf_counter()
+
+                # Initialize scraping strategy
+                scrapping_strategy = WebScrapingStrategy(logger=self.logger)
+
+                # Process HTML content
+                result = scrapping_strategy.scrap(
+                    url,
+                    html,
+                    word_count_threshold=config.word_count_threshold,
+                    css_selector=config.css_selector,
+                    only_text=config.only_text,
+                    image_description_min_word_threshold=config.image_description_min_word_threshold,
+                    content_filter=config.content_filter
+                )
+
+                if result is None:
+                    raise ValueError(f"Process HTML, Failed to extract content from the website: {url}")
+
+            except InvalidCSSSelectorError as e:
+                raise ValueError(str(e))
             except Exception as e:
-                if not hasattr(e, "msg"):
-                    e.msg = str(e)
-                # print(f"{Fore.RED}{self.tag_format('ERROR')} {self.log_icons['ERROR']} Failed to crawl {cache_context.display_url[:URL_LOG_SHORTEN_LENGTH]}... | {e.msg}{Style.RESET_ALL}")
+                raise ValueError(f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}")
+
+            # Extract results
+            markdown_v2 = result.get("markdown_v2", None)
+            cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
+            markdown = sanitize_input_encode(result.get("markdown", ""))
+            fit_markdown = sanitize_input_encode(result.get("fit_markdown", ""))
+            fit_html = sanitize_input_encode(result.get("fit_html", ""))
+            media = result.get("media", [])
+            links = result.get("links", [])
+            metadata = result.get("metadata", {})
+
+            # Log processing completion
+            self.logger.info(
+                message="Processed {url:.50}... | Time: {timing}ms",
+                tag="SCRAPE",
+                params={
+                    "url": _url,
+                    "timing": int((time.perf_counter() - t1) * 1000)
+                }
+            )
+
+            # Handle content extraction if needed
+            if (extracted_content is None and 
+                config.extraction_strategy and 
+                config.chunking_strategy and 
+                not isinstance(config.extraction_strategy, NoExtractionStrategy)):
                 
-                self.logger.error_status(
-                    # url=cache_context.display_url,
-                    url=url,
-                    error=create_box_message(e.msg, type = "error"),
-                    tag="ERROR"
-                )            
-                return CrawlResult(
-                    url=url, 
-                    html="", 
-                    success=False, 
-                    error_message=e.msg
+                t1 = time.perf_counter()
+                
+                # Handle different extraction strategy types
+                if isinstance(config.extraction_strategy, (JsonCssExtractionStrategy, JsonCssExtractionStrategy)):
+                    config.extraction_strategy.verbose = verbose
+                    extracted_content = config.extraction_strategy.run(url, [html])
+                    extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)
+                else:
+                    sections = config.chunking_strategy.chunk(markdown)
+                    extracted_content = config.extraction_strategy.run(url, sections)
+                    extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)
+
+                # Log extraction completion
+                self.logger.info(
+                    message="Completed for {url:.50}... | Time: {timing}s",
+                    tag="EXTRACT",
+                    params={
+                        "url": _url,
+                        "timing": time.perf_counter() - t1
+                    }
                 )
 
-    async def arun_many(
-        self,
-        urls: List[str],
-        word_count_threshold=MIN_WORD_THRESHOLD,
-        extraction_strategy: ExtractionStrategy = None,
-        chunking_strategy: ChunkingStrategy = RegexChunking(),
-        content_filter: RelevantContentFilter = None,
-        cache_mode: Optional[CacheMode] = None,
-        # Deprecated parameters
-        bypass_cache: bool = False,
-        css_selector: str = None,
-        screenshot: bool = False,
-        pdf: bool = False,
-        user_agent: str = None,
-        verbose=True,
-        **kwargs,
-    ) -> List[CrawlResult]:
-        """
-        Runs the crawler for multiple URLs concurrently.
+            # Handle screenshot and PDF data
+            screenshot_data = None if not screenshot else screenshot
+            pdf_data = None if not pdf_data else pdf_data
+
+            # Apply HTML formatting if requested
+            if config.prettiify:
+                cleaned_html = fast_format_html(cleaned_html)
+
+            # Return complete crawl result
+            return CrawlResult(
+                url=url,
+                html=html,
+                cleaned_html=cleaned_html,
+                markdown_v2=markdown_v2,
+                markdown=markdown,
+                fit_markdown=fit_markdown,
+                fit_html=fit_html,
+                media=media,
+                links=links,
+                metadata=metadata,
+                screenshot=screenshot_data,
+                pdf=pdf_data,
+                extracted_content=extracted_content,
+                success=True,
+                error_message="",
+            )    
 
-        Migration from legacy parameters:
+    async def arun_many(
+            self,
+            urls: List[str],
+            config: Optional[CrawlerRunConfig] = None,
+            # Legacy parameters maintained for backwards compatibility
+            word_count_threshold=MIN_WORD_THRESHOLD,
+            extraction_strategy: ExtractionStrategy = None,
+            chunking_strategy: ChunkingStrategy = RegexChunking(),
+            content_filter: RelevantContentFilter = None,
+            cache_mode: Optional[CacheMode] = None,
+            bypass_cache: bool = False,
+            css_selector: str = None,
+            screenshot: bool = False,
+            pdf: bool = False,
+            user_agent: str = None,
+            verbose=True,
+            **kwargs,
+        ) -> List[CrawlResult]:
+            """
+            Runs the crawler for multiple URLs concurrently.
+
+            Migration Guide:
             Old way (deprecated):
-                results = await crawler.arun_many(urls, bypass_cache=True)
+                results = await crawler.arun_many(
+                    urls,
+                    word_count_threshold=200,
+                    screenshot=True,
+                    ...
+                )
             
-            New way:
-                results = await crawler.arun_many(urls, cache_mode=CacheMode.BYPASS)
-
-        Args:
-            urls: List of URLs to crawl
-            cache_mode: Cache behavior control (recommended)
-            [other parameters same as arun()]
-
-        Returns:
-            List[CrawlResult]: Results for each URL
-        """
-        if bypass_cache:
-            if kwargs.get("warning", True):
-                warnings.warn(
-                    "'bypass_cache' is deprecated and will be removed in version X.X.X. "
-                    "Use 'cache_mode=CacheMode.BYPASS' instead. "
-                    "Pass warning=False to suppress this warning.",
-                    DeprecationWarning,
-                    stacklevel=2
+            New way (recommended):
+                config = CrawlerRunConfig(
+                    word_count_threshold=200,
+                    screenshot=True,
+                    ...
                 )
-            if cache_mode is None:
-                cache_mode = CacheMode.BYPASS
-
-        semaphore_count = kwargs.get('semaphore_count', 10)
-        semaphore = asyncio.Semaphore(semaphore_count)
+                results = await crawler.arun_many(urls, crawler_config=config)
 
-        async def crawl_with_semaphore(url):
-            domain = urlparse(url).netloc
-            current_time = time.time()
-            
-            # print(f"{Fore.LIGHTBLACK_EX}{self.tag_format('PARALLEL')} Started task for {url[:50]}...{Style.RESET_ALL}")
-            self.logger.debug(
-                message="Started task for {url:.50}...",
-                tag="PARALLEL",
-                params={"url": url}
-            )            
-            
-            # Get delay settings from kwargs or use defaults
-            mean_delay = kwargs.get('mean_delay', 0.1)  # 0.5 seconds default mean delay
-            max_range = kwargs.get('max_range', 0.3)    # 1 seconds default max additional delay
-            
-            # Check if we need to wait
-            if domain in self._domain_last_hit:
-                time_since_last = current_time - self._domain_last_hit[domain]
-                if time_since_last < mean_delay:
-                    delay = mean_delay + random.uniform(0, max_range)
-                    await asyncio.sleep(delay)
+            Args:
+                urls: List of URLs to crawl
+                crawler_config: Configuration object controlling crawl behavior for all URLs
+                [other parameters maintained for backwards compatibility]
             
-            # Update last hit time
-            self._domain_last_hit[domain] = current_time    
-                    
-            async with semaphore:
-                return await self.arun(
-                    url,
-                    word_count_threshold=word_count_threshold,
-                    extraction_strategy=extraction_strategy,
-                    chunking_strategy=chunking_strategy,
-                    content_filter=content_filter,
-                    cache_mode=cache_mode,
-                    css_selector=css_selector,
-                    screenshot=screenshot,
-                    user_agent=user_agent,
-                    verbose=verbose,
-                    **kwargs,
-                )
+            Returns:
+                List[CrawlResult]: Results for each URL
+            """
+            crawler_config = config
+            # Handle configuration
+            if crawler_config is not None:
+                if any(param is not None for param in [
+                    word_count_threshold, extraction_strategy, chunking_strategy,
+                    content_filter, cache_mode, css_selector, screenshot, pdf
+                ]):
+                    self.logger.warning(
+                        message="Both crawler_config and legacy parameters provided. crawler_config will take precedence.",
+                        tag="WARNING"
+                    )
+                config = crawler_config
+            else:
+                # Merge all parameters into a single kwargs dict for config creation
+                config_kwargs = {
+                    "word_count_threshold": word_count_threshold,
+                    "extraction_strategy": extraction_strategy,
+                    "chunking_strategy": chunking_strategy,
+                    "content_filter": content_filter,
+                    "cache_mode": cache_mode,
+                    "bypass_cache": bypass_cache,
+                    "css_selector": css_selector,
+                    "screenshot": screenshot,
+                    "pdf": pdf,
+                    "verbose": verbose,
+                    **kwargs
+                }
+                config = CrawlerRunConfig.from_kwargs(config_kwargs)
+
+            if bypass_cache:
+                if kwargs.get("warning", True):
+                    warnings.warn(
+                        "'bypass_cache' is deprecated and will be removed in version 0.5.0. "
+                        "Use 'cache_mode=CacheMode.BYPASS' instead. "
+                        "Pass warning=False to suppress this warning.",
+                        DeprecationWarning,
+                        stacklevel=2
+                    )
+                if config.cache_mode is None:
+                    config.cache_mode = CacheMode.BYPASS
 
-        # Print start message
-        # print(f"{Fore.CYAN}{self.tag_format('INIT')} {self.log_icons['INIT']} Starting concurrent crawling for {len(urls)} URLs...{Style.RESET_ALL}")
-        self.logger.info(
-            message="Starting concurrent crawling for {count} URLs...",
-            tag="INIT",
-            params={"count": len(urls)}
-        )        
-        start_time = time.perf_counter()
-        tasks = [crawl_with_semaphore(url) for url in urls]
-        results = await asyncio.gather(*tasks, return_exceptions=True)
-        end_time = time.perf_counter()
-        # print(f"{Fore.YELLOW}{self.tag_format('COMPLETE')} {self.log_icons['COMPLETE']} Concurrent crawling completed for {len(urls)} URLs | Total time: {end_time - start_time:.2f}s{Style.RESET_ALL}")
-        self.logger.success(
-            message="Concurrent crawling completed for {count} URLs | " + Fore.YELLOW + " Total time: {timing}" + Style.RESET_ALL,
-            tag="COMPLETE",
-            params={
-                "count": len(urls),
-                "timing": f"{end_time - start_time:.2f}s"
-            },
-            colors={"timing": Fore.YELLOW}
-        )        
-        return [result if not isinstance(result, Exception) else str(result) for result in results]
+            semaphore_count = config.semaphore_count or 5
+            semaphore = asyncio.Semaphore(semaphore_count)
 
+            async def crawl_with_semaphore(url):
+                # Handle rate limiting per domain
+                domain = urlparse(url).netloc
+                current_time = time.time()
+                
+                self.logger.debug(
+                    message="Started task for {url:.50}...",
+                    tag="PARALLEL",
+                    params={"url": url}
+                )
 
-    async def aprocess_html(
-        self,
-        url: str,
-        html: str,
-        extracted_content: str,
-        word_count_threshold: int,
-        extraction_strategy: ExtractionStrategy,
-        chunking_strategy: ChunkingStrategy,
-        content_filter: RelevantContentFilter,
-        css_selector: str,
-        screenshot: str,
-        verbose: bool,
-        **kwargs,
-    ) -> CrawlResult:
-        # Extract content from HTML
-        try:
-            _url = url if not kwargs.get("is_raw_html", False) else "Raw HTML"
-            t1 = time.perf_counter()
-            scrapping_strategy = WebScrapingStrategy(
-                logger=self.logger,
-            )
-            # result = await scrapping_strategy.ascrap(
-            result = scrapping_strategy.scrap(
-                url,
-                html,
-                word_count_threshold=word_count_threshold,
-                css_selector=css_selector,
-                only_text=kwargs.pop("only_text", False),
-                image_description_min_word_threshold=kwargs.pop(
-                    "image_description_min_word_threshold", IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD
-                ),
-                content_filter = content_filter,
-                **kwargs,
-            )
+                # Get delay settings from config
+                mean_delay = config.mean_delay
+                max_range = config.max_range
+                
+                # Apply rate limiting
+                if domain in self._domain_last_hit:
+                    time_since_last = current_time - self._domain_last_hit[domain]
+                    if time_since_last < mean_delay:
+                        delay = mean_delay + random.uniform(0, max_range)
+                        await asyncio.sleep(delay)
+                
+                self._domain_last_hit[domain] = current_time
 
-            if result is None:
-                raise ValueError(f"Process HTML, Failed to extract content from the website: {url}")
-        except InvalidCSSSelectorError as e:
-            raise ValueError(str(e))
-        except Exception as e:
-            raise ValueError(f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}")
+                async with semaphore:
+                    return await self.arun(
+                        url,
+                        crawler_config=config,  # Pass the entire config object
+                        user_agent=user_agent  # Maintain user_agent override capability
+                    )
 
-        markdown_v2: MarkdownGenerationResult = result.get("markdown_v2", None)
-        
-        cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
-        markdown = sanitize_input_encode(result.get("markdown", ""))
-        fit_markdown = sanitize_input_encode(result.get("fit_markdown", ""))
-        fit_html = sanitize_input_encode(result.get("fit_html", ""))
-        media = result.get("media", [])
-        links = result.get("links", [])
-        metadata = result.get("metadata", {})
-        
-        # if verbose:
-        #     print(f"{Fore.MAGENTA}{self.tag_format('SCRAPE')} {self.log_icons['SCRAPE']} Processed {_url[:URL_LOG_SHORTEN_LENGTH]}...{Style.RESET_ALL} | Time: {int((time.perf_counter() - t1) * 1000)}ms")
-        self.logger.info(
-            message="Processed {url:.50}... | Time: {timing}ms",
-            tag="SCRAPE",
-            params={
-                "url": _url,
-                "timing": int((time.perf_counter() - t1) * 1000)
-            }
-        )
+            # Log start of concurrent crawling
+            self.logger.info(
+                message="Starting concurrent crawling for {count} URLs...",
+                tag="INIT",
+                params={"count": len(urls)}
+            )
 
+            # Execute concurrent crawls
+            start_time = time.perf_counter()
+            tasks = [crawl_with_semaphore(url) for url in urls]
+            results = await asyncio.gather(*tasks, return_exceptions=True)
+            end_time = time.perf_counter()
 
-        if extracted_content is None and extraction_strategy and chunking_strategy and not isinstance(extraction_strategy, NoExtractionStrategy):
-            t1 = time.perf_counter()
-            # Check if extraction strategy is type of JsonCssExtractionStrategy
-            if isinstance(extraction_strategy, JsonCssExtractionStrategy) or isinstance(extraction_strategy, JsonCssExtractionStrategy):
-                extraction_strategy.verbose = verbose
-                extracted_content = extraction_strategy.run(url, [html])
-                extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)
-            else:
-                sections = chunking_strategy.chunk(markdown)
-                extracted_content = extraction_strategy.run(url, sections)
-                extracted_content = json.dumps(extracted_content, indent=4, default=str, ensure_ascii=False)
-            # if verbose:
-                # print(f"{Fore.YELLOW}{self.tag_format('EXTRACT')} {self.log_icons['EXTRACT']} Completed for {_url[:URL_LOG_SHORTEN_LENGTH]}...{Style.RESET_ALL} | Time: {time.perf_counter() - t1:.2f}s{Style.RESET_ALL}")
-            self.logger.info(
-                message="Completed for {url:.50}... | Time: {timing}s",
-                tag="EXTRACT",
+            # Log completion
+            self.logger.success(
+                message="Concurrent crawling completed for {count} URLs | Total time: {timing}",
+                tag="COMPLETE",
                 params={
-                    "url": _url,
-                    "timing": time.perf_counter() - t1
+                    "count": len(urls),
+                    "timing": f"{end_time - start_time:.2f}s"
+                },
+                colors={
+                    "timing": Fore.YELLOW
                 }
             )
 
-        screenshot = None if not screenshot else screenshot
-        pdf_data = kwargs.get("pdf_data", None) 
-        
-        
-        if kwargs.get("prettiify", False):
-            cleaned_html = fast_format_html(cleaned_html)
-        
-        return CrawlResult(
-            url=url,
-            html=html,
-            cleaned_html=cleaned_html,
-            markdown_v2=markdown_v2,
-            markdown=markdown,
-            fit_markdown=fit_markdown,
-            fit_html= fit_html,
-            media=media,
-            links=links,
-            metadata=metadata,
-            screenshot=screenshot,
-            pdf=pdf_data,
-            extracted_content=extracted_content,
-            success=True,
-            error_message="",
-        )
+            return [result if not isinstance(result, Exception) else str(result) for result in results]
 
     async def aclear_cache(self):
         """Clear the cache database."""
diff --git a/crawl4ai/config.py b/crawl4ai/config.py
index e17ff34..7c8a931 100644
--- a/crawl4ai/config.py
+++ b/crawl4ai/config.py
@@ -57,4 +57,6 @@ MAX_METRICS_HISTORY = 1000
 NEED_MIGRATION = True
 URL_LOG_SHORTEN_LENGTH = 30
 SHOW_DEPRECATION_WARNINGS = True
-SCREENSHOT_HEIGHT_TRESHOLD = 10000
\ No newline at end of file
+SCREENSHOT_HEIGHT_TRESHOLD = 10000
+PAGE_TIMEOUT=60000
+DOWNLOAD_PAGE_TIMEOUT=60000
\ No newline at end of file
diff --git a/crawl4ai/utils.py b/crawl4ai/utils.py
index 8a12ff0..7ecc22d 100644
--- a/crawl4ai/utils.py
+++ b/crawl4ai/utils.py
@@ -29,7 +29,7 @@ class InvalidCSSSelectorError(Exception):
 def create_box_message(
    message: str, 
    type: str = "info", 
-   width: int = 80, 
+   width: int = 120, 
    add_newlines: bool = True,
    double_line: bool = False
 ) -> str:
@@ -1223,7 +1223,8 @@ def ensure_content_dirs(base_path: str) -> Dict[str, str]:
         'cleaned': 'cleaned_html',
         'markdown': 'markdown_content', 
         'extracted': 'extracted_content',
-        'screenshots': 'screenshots'
+        'screenshots': 'screenshots',
+        'screenshot': 'screenshots'
     }
     
     content_paths = {}
@@ -1232,4 +1233,60 @@ def ensure_content_dirs(base_path: str) -> Dict[str, str]:
         os.makedirs(path, exist_ok=True)
         content_paths[key] = path
         
-    return content_paths
\ No newline at end of file
+    return content_paths
+
+def get_error_context(exc_info, context_lines: int = 5):
+    """
+    Extract error context with more reliable line number tracking.
+    
+    Args:
+        exc_info: The exception info from sys.exc_info()
+        context_lines: Number of lines to show before and after the error
+    
+    Returns:
+        dict: Error context information
+    """
+    import traceback
+    import linecache
+    import os
+    
+    # Get the full traceback
+    tb = traceback.extract_tb(exc_info[2])
+    
+    # Get the last frame (where the error occurred)
+    last_frame = tb[-1]
+    filename = last_frame.filename
+    line_no = last_frame.lineno
+    func_name = last_frame.name
+    
+    # Get the source code context using linecache
+    # This is more reliable than inspect.getsourcelines
+    context_start = max(1, line_no - context_lines)
+    context_end = line_no + context_lines + 1
+    
+    # Build the context lines with line numbers
+    context_lines = []
+    for i in range(context_start, context_end):
+        line = linecache.getline(filename, i)
+        if line:
+            # Remove any trailing whitespace/newlines and add the pointer for error line
+            line = line.rstrip()
+            pointer = '→' if i == line_no else ' '
+            context_lines.append(f"{i:4d} {pointer} {line}")
+    
+    # Join the lines with newlines
+    code_context = '\n'.join(context_lines)
+    
+    # Get relative path for cleaner output
+    try:
+        rel_path = os.path.relpath(filename)
+    except ValueError:
+        # Fallback if relpath fails (can happen on Windows with different drives)
+        rel_path = filename
+    
+    return {
+        "filename": rel_path,
+        "line_no": line_no,
+        "function": func_name,
+        "code_context": code_context
+    }
\ No newline at end of file
diff --git a/docs/md_v2/basic/cache-modes.md b/docs/md_v2/basic/cache-modes.md
index 04a4f21..01cfe34 100644
--- a/docs/md_v2/basic/cache-modes.md
+++ b/docs/md_v2/basic/cache-modes.md
@@ -1,7 +1,7 @@
 # Crawl4AI Cache System and Migration Guide
 
 ## Overview
-Starting from version X.X.X, Crawl4AI introduces a new caching system that replaces the old boolean flags with a more intuitive `CacheMode` enum. This change simplifies cache control and makes the behavior more predictable.
+Starting from version 0.5.0, Crawl4AI introduces a new caching system that replaces the old boolean flags with a more intuitive `CacheMode` enum. This change simplifies cache control and makes the behavior more predictable.
 
 ## Old vs New Approach
 
