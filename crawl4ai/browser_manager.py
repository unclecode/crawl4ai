import asyncio
import time
from typing import Dict, List, Optional, Tuple
import os
import sys
import shutil
import tempfile
import psutil  
import signal
import subprocess
import shlex
from playwright.async_api import BrowserContext
import hashlib
from .js_snippet import load_js_script
from .config import DOWNLOAD_PAGE_TIMEOUT
from .async_configs import BrowserConfig, CrawlerRunConfig
from .utils import get_chromium_path
import warnings


BROWSER_DISABLE_OPTIONS = [
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-extensions-with-background-pages",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-features=TranslateUI",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-sync",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--no-first-run",
    "--password-store=basic",
    "--use-mock-keychain",
]


class ManagedBrowser:
    """
    Manages the browser process and context. This class allows to connect to the browser using CDP protocol.

    Attributes:
        browser_type (str): The type of browser to launch. Supported values: "chromium", "firefox", "webkit".
                            Default: "chromium".
        user_data_dir (str or None): Path to a user data directory for persistent sessions. If None, a
                                     temporary directory may be used. Default: None.
        headless (bool): Whether to run the browser in headless mode (no visible GUI).
                         Default: True.
        browser_process (subprocess.Popen): The process object for the browser.
        temp_dir (str): Temporary directory for user data if not provided.
        debugging_port (int): Port for debugging the browser.
        host (str): Host for debugging the browser.

        Methods:
            start(): Starts the browser process and returns the CDP endpoint URL.
            _get_browser_path(): Returns the browser executable path based on OS and browser type.
            _get_browser_args(): Returns browser-specific command line arguments.
            _get_user_data_dir(): Returns the user data directory path.
            _cleanup(): Terminates the browser process and removes the temporary directory.
            create_profile(): Static method to create a user profile by launching a browser for user interaction.
    """
    
    @staticmethod
    def build_browser_flags(config: BrowserConfig) -> List[str]:
        """Common CLI flags for launching Chromium"""
        flags = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--disable-blink-features=AutomationControlled",
            "--window-position=400,0",
            "--disable-renderer-backgrounding",
            "--disable-ipc-flooding-protection",
            "--force-color-profile=srgb",
            "--mute-audio",
            "--disable-background-timer-throttling",
            # Memory-saving flags: disable unused Chrome features
            "--disable-features=OptimizationHints,MediaRouter,DialMediaRouteProvider",
            "--disable-component-update",
            "--disable-domain-reliability",
        ]
        # GPU flags disable WebGL which anti-bot sensors detect as headless.
        # Keep WebGL working (via SwiftShader) when stealth mode is active.
        if not config.enable_stealth:
            flags.extend([
                "--disable-gpu",
                "--disable-gpu-compositing",
                "--disable-software-rasterizer",
            ])
        if config.memory_saving_mode:
            flags.extend([
                "--aggressive-cache-discard",
                '--js-flags=--max-old-space-size=512',
            ])
        if config.light_mode:
            flags.extend(BROWSER_DISABLE_OPTIONS)
        if config.text_mode:
            flags.extend([
                "--blink-settings=imagesEnabled=false",
                "--disable-remote-fonts",
                "--disable-images",
                "--disable-javascript",
                "--disable-software-rasterizer",
                "--disable-dev-shm-usage",
            ])
        # proxy support — only pass server URL, never credentials.
        # Chromium's --proxy-server flag silently ignores inline user:pass@.
        # Auth credentials are handled at the Playwright context level instead.
        if config.proxy:
            flags.append(f"--proxy-server={config.proxy}")
        elif config.proxy_config:
            flags.append(f"--proxy-server={config.proxy_config.server}")
        # dedupe
        return list(dict.fromkeys(flags))

    browser_type: str
    user_data_dir: str
    headless: bool
    browser_process: subprocess.Popen
    temp_dir: str
    debugging_port: int
    host: str

    def __init__(
        self,
        browser_type: str = "chromium",
        user_data_dir: Optional[str] = None,
        headless: bool = False,
        logger=None,
        host: str = "localhost",
        debugging_port: int = 9222,
        cdp_url: Optional[str] = None, 
        browser_config: Optional[BrowserConfig] = None,
    ):
        """
        Initialize the ManagedBrowser instance.

        Args:
            browser_type (str): The type of browser to launch. Supported values: "chromium", "firefox", "webkit".
                                Default: "chromium".
            user_data_dir (str or None): Path to a user data directory for persistent sessions. If None, a
                                         temporary directory may be used. Default: None.
            headless (bool): Whether to run the browser in headless mode (no visible GUI).
                             Default: True.
            logger (logging.Logger): Logger instance for logging messages. Default: None.
            host (str): Host for debugging the browser. Default: "localhost".
            debugging_port (int): Port for debugging the browser. Default: 9222.
            cdp_url (str or None): CDP URL to connect to the browser. Default: None.
            browser_config (BrowserConfig): Configuration object containing all browser settings. Default: None.
        """
        self.browser_type = browser_config.browser_type
        self.user_data_dir = browser_config.user_data_dir
        self.headless = browser_config.headless
        self.browser_process = None
        self.temp_dir = None
        self.debugging_port = browser_config.debugging_port
        self.host = browser_config.host
        self.logger = logger
        self.shutting_down = False
        self.cdp_url = browser_config.cdp_url
        self.browser_config = browser_config

    async def start(self) -> str:
        """
        Starts the browser process or returns CDP endpoint URL.
        If cdp_url is provided, returns it directly.
        If user_data_dir is not provided for local browser, creates a temporary directory.
        
        Returns:
            str: CDP endpoint URL
        """
        # If CDP URL provided, just return it
        if self.cdp_url:
            return self.cdp_url

        # Create temp dir if needed
        if not self.user_data_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="browser-profile-")
            self.user_data_dir = self.temp_dir

        # Get browser path and args based on OS and browser type
        # browser_path = self._get_browser_path()
        args = await self._get_browser_args()
        
        if self.browser_config.extra_args:
            args.extend(self.browser_config.extra_args)
            

        # ── make sure no old Chromium instance is owning the same port/profile ──
        try:
            if sys.platform == "win32":
                if psutil is None:
                    raise RuntimeError("psutil not available, cannot clean old browser")
                for p in psutil.process_iter(["pid", "name", "cmdline"]):
                    cl = " ".join(p.info.get("cmdline") or [])
                    if (
                        f"--remote-debugging-port={self.debugging_port}" in cl
                        and f"--user-data-dir={self.user_data_dir}" in cl
                    ):
                        p.kill()
                        p.wait(timeout=5)
            else:  # macOS / Linux
                # kill any process listening on the same debugging port
                try:
                    pids = (
                        subprocess.check_output(
                            shlex.split(f"lsof -t -i:{self.debugging_port}"),
                            stderr=subprocess.DEVNULL,
                        )
                        .decode()
                        .strip()
                        .splitlines()
                    )
                except (FileNotFoundError, subprocess.CalledProcessError):
                    pids = []
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except ProcessLookupError:
                        pass

                # remove Chromium singleton locks, or new launch exits with
                # “Opening in existing browser session.”
                for f in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
                    fp = os.path.join(self.user_data_dir, f)
                    if os.path.exists(fp):
                        os.remove(fp)
        except Exception as _e:
            # non-fatal — we'll try to start anyway, but log what happened
            self.logger.warning(f"pre-launch cleanup failed: {_e}", tag="BROWSER")            
            

        # Start browser process
        try:
            # Use DETACHED_PROCESS flag on Windows to fully detach the process
            # On Unix, we'll use preexec_fn=os.setpgrp to start the process in a new process group
            if sys.platform == "win32":
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setpgrp  # Start in a new process group
                )
                
            # If verbose is True print args used to run the process
            if self.logger and self.browser_config.verbose:
                self.logger.debug(
                    f"Starting browser with args: {' '.join(args)}",
                    tag="BROWSER"
                )    
                
            # We'll monitor for a short time to make sure it starts properly, but won't keep monitoring
            await asyncio.sleep(0.5)  # Give browser time to start
            await self._initial_startup_check()
            await asyncio.sleep(2)  # Give browser time to start
            return f"http://{self.host}:{self.debugging_port}"
        except Exception as e:
            await self.cleanup()
            raise Exception(f"Failed to start browser: {e}")

    async def _initial_startup_check(self):
        """
        Perform a quick check to make sure the browser started successfully.
        This only runs once at startup rather than continuously monitoring.
        """
        if not self.browser_process:
            return
            
        # Check that process started without immediate termination
        await asyncio.sleep(0.5)
        if self.browser_process.poll() is not None:
            # Process already terminated
            stdout, stderr = b"", b""
            try:
                stdout, stderr = self.browser_process.communicate(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
                
            self.logger.error(
                message="Browser process terminated during startup | Code: {code} | STDOUT: {stdout} | STDERR: {stderr}",
                tag="ERROR",
                params={
                    "code": self.browser_process.returncode,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                },
            )
    
    async def _monitor_browser_process(self):
        """
        Monitor the browser process for unexpected termination.

        How it works:
        1. Read stdout and stderr from the browser process.
        2. If the process has terminated, log the error message and terminate the browser.
        3. If the shutting_down flag is set, log the normal termination message.
        4. If any other error occurs, log the error message.

        Note: This method should be called in a separate task to avoid blocking the main event loop.
        This is DEPRECATED and should not be used for builtin browsers that need to outlive the Python process.
        """
        if self.browser_process:
            try:
                stdout, stderr = await asyncio.gather(
                    asyncio.to_thread(self.browser_process.stdout.read),
                    asyncio.to_thread(self.browser_process.stderr.read),
                )

                # Check shutting_down flag BEFORE logging anything
                if self.browser_process.poll() is not None:
                    if not self.shutting_down:
                        self.logger.error(
                            message="Browser process terminated unexpectedly | Code: {code} | STDOUT: {stdout} | STDERR: {stderr}",
                            tag="ERROR",
                            params={
                                "code": self.browser_process.returncode,
                                "stdout": stdout.decode(),
                                "stderr": stderr.decode(),
                            },
                        )
                        await self.cleanup()
                    else:
                        self.logger.info(
                            message="Browser process terminated normally | Code: {code}",
                            tag="INFO",
                            params={"code": self.browser_process.returncode},
                        )
            except Exception as e:
                if not self.shutting_down:
                    self.logger.error(
                        message="Error monitoring browser process: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )

    def _get_browser_path_WIP(self) -> str:
        """Returns the browser executable path based on OS and browser type"""
        if sys.platform == "darwin":  # macOS
            paths = {
                "chromium": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
                "webkit": "/Applications/Safari.app/Contents/MacOS/Safari",
            }
        elif sys.platform == "win32":  # Windows
            paths = {
                "chromium": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "webkit": None,  # WebKit not supported on Windows
            }
        else:  # Linux
            paths = {
                "chromium": "google-chrome",
                "firefox": "firefox",
                "webkit": None,  # WebKit not supported on Linux
            }

        return paths.get(self.browser_type)

    async def _get_browser_path(self) -> str:
        browser_path = await get_chromium_path(self.browser_type)
        return browser_path

    async def _get_browser_args(self) -> List[str]:
        """Returns full CLI args for launching the browser"""
        base = [await self._get_browser_path()]
        if self.browser_type == "chromium":
            flags = [
                f"--remote-debugging-port={self.debugging_port}",
                f"--user-data-dir={self.user_data_dir}",
            ]
            if self.headless:
                flags.append("--headless=new")
            # Add viewport flag if specified in config
            if self.browser_config.viewport_height and self.browser_config.viewport_width:
                flags.append(f"--window-size={self.browser_config.viewport_width},{self.browser_config.viewport_height}")
            # merge common launch flags
            flags.extend(self.build_browser_flags(self.browser_config))
        elif self.browser_type == "firefox":
            flags = [
                "--remote-debugging-port",
                str(self.debugging_port),
                "--profile",
                self.user_data_dir,
            ]
            if self.headless:
                flags.append("--headless")
        else:
            raise NotImplementedError(f"Browser type {self.browser_type} not supported")
        return base + flags

    async def cleanup(self):
        """Cleanup browser process and temporary directory"""
        # Set shutting_down flag BEFORE any termination actions
        self.shutting_down = True

        if self.browser_process:
            try:
                # For builtin browsers that should persist, we should check if it's a detached process
                # Only terminate if we have proper control over the process
                if not self.browser_process.poll():
                    # Process is still running
                    self.browser_process.terminate()
                    # Wait for process to end gracefully
                    for _ in range(10):  # 10 attempts, 100ms each
                        if self.browser_process.poll() is not None:
                            break
                        await asyncio.sleep(0.1)

                    # Force kill if still running
                    if self.browser_process.poll() is None:
                        if sys.platform == "win32":
                            # On Windows, use taskkill /T to kill the entire process tree
                            try:
                                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.browser_process.pid)])
                            except Exception:
                                self.browser_process.kill()
                        else:
                            # On Unix, kill entire process group to reap child processes
                            try:
                                os.killpg(os.getpgid(self.browser_process.pid), signal.SIGKILL)
                            except (ProcessLookupError, OSError):
                                pass
                        await asyncio.sleep(0.1)  # Brief wait for kill to take effect

            except Exception as e:
                self.logger.error(
                    message="Error terminating browser: {error}",
                    tag="ERROR", 
                    params={"error": str(e)},
                )

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.logger.error(
                    message="Error removing temporary directory: {error}",
                    tag="ERROR",
                    params={"error": str(e)},
                )
                
    # These methods have been moved to BrowserProfiler class
    @staticmethod
    async def create_profile(browser_config=None, profile_name=None, logger=None):
        """
        This method has been moved to the BrowserProfiler class.
        
        Creates a browser profile by launching a browser for interactive user setup
        and waits until the user closes it. The profile is stored in a directory that
        can be used later with BrowserConfig.user_data_dir.
        
        Please use BrowserProfiler.create_profile() instead.
        
        Example:
            ```python
            from crawl4ai.browser_profiler import BrowserProfiler
            
            profiler = BrowserProfiler()
            profile_path = await profiler.create_profile(profile_name="my-login-profile")
            ```
        """
        from .browser_profiler import BrowserProfiler
        
        # Create a BrowserProfiler instance and delegate to it
        profiler = BrowserProfiler(logger=logger)
        return await profiler.create_profile(profile_name=profile_name, browser_config=browser_config)
    
    @staticmethod
    def list_profiles():
        """
        This method has been moved to the BrowserProfiler class.
        
        Lists all available browser profiles in the Crawl4AI profiles directory.
        
        Please use BrowserProfiler.list_profiles() instead.
        
        Example:
            ```python
            from crawl4ai.browser_profiler import BrowserProfiler
            
            profiler = BrowserProfiler()
            profiles = profiler.list_profiles()
            ```
        """
        from .browser_profiler import BrowserProfiler
        
        # Create a BrowserProfiler instance and delegate to it
        profiler = BrowserProfiler()
        return profiler.list_profiles()
        
    @staticmethod
    def delete_profile(profile_name_or_path):
        """
        This method has been moved to the BrowserProfiler class.
        
        Delete a browser profile by name or path.
        
        Please use BrowserProfiler.delete_profile() instead.
        
        Example:
            ```python
            from crawl4ai.browser_profiler import BrowserProfiler
            
            profiler = BrowserProfiler()
            success = profiler.delete_profile("my-profile")
            ```
        """
        from .browser_profiler import BrowserProfiler
        
        # Create a BrowserProfiler instance and delegate to it
        profiler = BrowserProfiler()
        return profiler.delete_profile(profile_name_or_path)


async def clone_runtime_state(
    src: BrowserContext,
    dst: BrowserContext,
    crawlerRunConfig: CrawlerRunConfig | None = None,
    browserConfig: BrowserConfig | None = None,
) -> None:
    """
    Bring everything that *can* be changed at runtime from `src` → `dst`.

    1. Cookies
    2. localStorage (and sessionStorage, same API)
    3. Extra headers, permissions, geolocation if supplied in configs
    """

    # ── 1. cookies ────────────────────────────────────────────────────────────
    cookies = await src.cookies()
    if cookies:
        await dst.add_cookies(cookies)

    # ── 2. localStorage / sessionStorage ──────────────────────────────────────
    state = await src.storage_state()
    for origin in state.get("origins", []):
        url = origin["origin"]
        kvs = origin.get("localStorage", [])
        if not kvs:
            continue

        page = dst.pages[0] if dst.pages else await dst.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        for k, v in kvs:
            await page.evaluate("(k,v)=>localStorage.setItem(k,v)", k, v)

    # ── 3. runtime-mutable extras from configs ────────────────────────────────
    # headers
    if browserConfig and browserConfig.headers:
        await dst.set_extra_http_headers(browserConfig.headers)

    # geolocation
    if crawlerRunConfig and crawlerRunConfig.geolocation:
        await dst.grant_permissions(["geolocation"])
        await dst.set_geolocation(
            {
                "latitude": crawlerRunConfig.geolocation.latitude,
                "longitude": crawlerRunConfig.geolocation.longitude,
                "accuracy": crawlerRunConfig.geolocation.accuracy,
            }
        )
        
    return dst



class _CDPConnectionCache:
    """
    Class-level cache for Playwright + CDP browser connections.

    When enabled via BrowserConfig(cache_cdp_connection=True), multiple
    BrowserManager instances connecting to the same cdp_url will share
    a single Playwright subprocess and CDP WebSocket. Reference-counted;
    the connection is closed when the last user releases it.
    """

    _cache: Dict[str, Tuple] = {}  # cdp_url -> (playwright, browser, ref_count)
    _lock: Optional[asyncio.Lock] = None  # lazy-init to avoid event loop issues
    _lock_loop: Optional[asyncio.AbstractEventLoop] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        if cls._lock is None or cls._lock_loop is not loop:
            cls._lock = asyncio.Lock()
            cls._lock_loop = loop
        return cls._lock

    @classmethod
    async def acquire(cls, cdp_url: str, use_undetected: bool = False):
        """Get or create a cached (playwright, browser) for this cdp_url."""
        async with cls._get_lock():
            if cdp_url in cls._cache:
                pw, browser, count = cls._cache[cdp_url]
                if browser.is_connected():
                    cls._cache[cdp_url] = (pw, browser, count + 1)
                    return pw, browser
                # Stale connection — clean up and fall through to create new
                try:
                    await pw.stop()
                except Exception:
                    pass
                del cls._cache[cdp_url]

            # Create new connection
            if use_undetected:
                from patchright.async_api import async_playwright
            else:
                from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            browser = await pw.chromium.connect_over_cdp(cdp_url)
            cls._cache[cdp_url] = (pw, browser, 1)
            return pw, browser

    @classmethod
    async def release(cls, cdp_url: str):
        """Decrement ref count; close connection when last user releases."""
        async with cls._get_lock():
            if cdp_url not in cls._cache:
                return
            pw, browser, count = cls._cache[cdp_url]
            if count <= 1:
                try:
                    await browser.close()
                except Exception:
                    pass
                try:
                    await pw.stop()
                except Exception:
                    pass
                del cls._cache[cdp_url]
            else:
                cls._cache[cdp_url] = (pw, browser, count - 1)

    @classmethod
    async def close_all(cls):
        """Force-close all cached connections. Call on application shutdown."""
        async with cls._get_lock():
            for cdp_url in list(cls._cache.keys()):
                pw, browser, _ = cls._cache[cdp_url]
                try:
                    await browser.close()
                except Exception:
                    pass
                try:
                    await pw.stop()
                except Exception:
                    pass
            cls._cache.clear()


class BrowserManager:
    """
    Manages the browser instance and context.

    Attributes:
        config (BrowserConfig): Configuration object containing all browser settings
        logger: Logger instance for recording events and errors
        browser (Browser): The browser instance
        default_context (BrowserContext): The default browser context
        managed_browser (ManagedBrowser): The managed browser instance
        playwright (Playwright): The Playwright instance
        sessions (dict): Dictionary to store session information
        session_ttl (int): Session timeout in seconds
    """

    _playwright_instance = None

    # Class-level tracking of pages in use, keyed by browser endpoint (CDP URL or instance id)
    # This ensures multiple BrowserManager instances connecting to the same browser
    # share the same page tracking, preventing race conditions.
    _global_pages_in_use: dict = {}  # endpoint_key -> set of pages
    _global_pages_lock: asyncio.Lock = None  # Initialized lazily

    @classmethod
    def _get_global_lock(cls) -> asyncio.Lock:
        """Get or create the global pages lock (lazy initialization for async context)."""
        if cls._global_pages_lock is None:
            cls._global_pages_lock = asyncio.Lock()
        return cls._global_pages_lock

    @classmethod
    async def get_playwright(cls, use_undetected: bool = False):
        if use_undetected:
            from patchright.async_api import async_playwright
        else:
            from playwright.async_api import async_playwright
        cls._playwright_instance = await async_playwright().start()
        return cls._playwright_instance    

    def __init__(self, browser_config: BrowserConfig, logger=None, use_undetected: bool = False):
        """
        Initialize the BrowserManager with a browser configuration.

        Args:
            browser_config (BrowserConfig): Configuration object containing all browser settings
            logger: Logger instance for recording events and errors
            use_undetected (bool): Whether to use undetected browser (Patchright)
        """
        self.config: BrowserConfig = browser_config
        self.logger = logger
        self.use_undetected = use_undetected

        # Browser state
        self.browser = None
        self.default_context = None
        self.managed_browser = None
        self.playwright = None
        self._using_cached_cdp = False
        self._launched_persistent = False  # True when using launch_persistent_context

        # Session management
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes

        # Keep track of contexts by a "config signature," so each unique config reuses a single context
        self.contexts_by_config = {}
        self._contexts_lock = asyncio.Lock()

        # Context lifecycle tracking for LRU eviction
        self._context_refcounts = {}    # sig -> int  (active crawls using this context)
        self._context_last_used = {}    # sig -> float (monotonic timestamp for LRU)
        self._page_to_sig = {}          # page -> sig  (for decrement lookup on release)
        self._max_contexts = 20         # LRU eviction threshold

        # Serialize context.new_page() across concurrent tasks to avoid races
        # when using a shared persistent context (context.pages may be empty
        # for all racers). Prevents 'Target page/context closed' errors.
        self._page_lock = asyncio.Lock()

        # Browser endpoint key for global page tracking (set after browser starts)
        self._browser_endpoint_key: Optional[str] = None

        # Browser recycling state (version-based approach)
        self._pages_served = 0
        self._browser_version = 1  # included in signature, bump to create new browser
        self._pending_cleanup = {}  # old_sig -> {"browser": browser, "contexts": [...], "done": Event}
        self._pending_cleanup_lock = asyncio.Lock()
        self._max_pending_browsers = 3  # safety cap — block if too many draining
        self._cleanup_slot_available = asyncio.Event()
        self._cleanup_slot_available.set()  # starts open

        # Stealth adapter for stealth mode
        self._stealth_adapter = None
        if self.config.enable_stealth and not self.use_undetected:
            from .browser_adapter import StealthAdapter
            self._stealth_adapter = StealthAdapter()

        # Initialize ManagedBrowser if needed
        if self.config.use_managed_browser:
            self.managed_browser = ManagedBrowser(
                browser_type=self.config.browser_type,
                user_data_dir=self.config.user_data_dir,
                headless=self.config.headless,
                logger=self.logger,
                debugging_port=self.config.debugging_port,
                cdp_url=self.config.cdp_url,
                browser_config=self.config,
            )

    async def start(self):
        """
        Start the browser instance and set up the default context.

        How it works:
        1. Check if Playwright is already initialized.
        2. If not, initialize Playwright.
        3. If managed browser is used, start it and connect to the CDP endpoint.
        4. If managed browser is not used, launch the browser and set up the default context.

        Note: This method should be called in a separate task to avoid blocking the main event loop.
        """
        if self.playwright is not None:
            await self.close()

        # Use cached CDP connection if enabled and cdp_url is set
        if self.config.cache_cdp_connection and self.config.cdp_url:
            self._using_cached_cdp = True
            self.config.use_managed_browser = True
            self.playwright, self.browser = await _CDPConnectionCache.acquire(
                self.config.cdp_url, self.use_undetected
            )
        else:
            self._using_cached_cdp = False
            if self.use_undetected:
                from patchright.async_api import async_playwright
            else:
                from playwright.async_api import async_playwright

            # Initialize playwright
            self.playwright = await async_playwright().start()

        # ── Persistent context via Playwright's native API ──────────────
        # When use_persistent_context is set and we're not connecting to an
        # external CDP endpoint, use launch_persistent_context() instead of
        # subprocess + CDP.  This properly supports proxy authentication
        # (server + username + password) which the --proxy-server CLI flag
        # cannot handle.
        if (
            self.config.use_persistent_context
            and not self.config.cdp_url
            and not self._using_cached_cdp
        ):
            # Collect stealth / optimization CLI flags, excluding ones that
            # launch_persistent_context handles via keyword arguments.
            _skip_prefixes = (
                "--proxy-server",
                "--remote-debugging-port",
                "--user-data-dir",
                "--headless",
                "--window-size",
            )
            cli_args = [
                flag
                for flag in ManagedBrowser.build_browser_flags(self.config)
                if not flag.startswith(_skip_prefixes)
            ]
            if self.config.extra_args:
                cli_args.extend(self.config.extra_args)

            launch_kwargs = {
                "headless": self.config.headless,
                "args": list(dict.fromkeys(cli_args)),  # dedupe
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
                "user_agent": self.config.user_agent or None,
                "ignore_https_errors": self.config.ignore_https_errors,
                "accept_downloads": self.config.accept_downloads,
            }

            if self.config.proxy_config:
                launch_kwargs["proxy"] = {
                    "server": self.config.proxy_config.server,
                    "username": self.config.proxy_config.username,
                    "password": self.config.proxy_config.password,
                }

            if self.config.storage_state:
                launch_kwargs["storage_state"] = self.config.storage_state

            user_data_dir = self.config.user_data_dir or tempfile.mkdtemp(
                prefix="crawl4ai-persistent-"
            )

            self.default_context = (
                await self.playwright.chromium.launch_persistent_context(
                    user_data_dir, **launch_kwargs
                )
            )
            self.browser = None  # persistent context has no separate Browser
            self._launched_persistent = True

            await self.setup_context(self.default_context)

            # Set the browser endpoint key for global page tracking
            self._browser_endpoint_key = self._compute_browser_endpoint_key()
            if self._browser_endpoint_key not in BrowserManager._global_pages_in_use:
                BrowserManager._global_pages_in_use[self._browser_endpoint_key] = set()
            return

        if self.config.cdp_url or self.config.use_managed_browser:
            self.config.use_managed_browser = True

            if not self._using_cached_cdp:
                cdp_url = await self.managed_browser.start() if not self.config.cdp_url else self.config.cdp_url

                # Add CDP endpoint verification before connecting
                if not await self._verify_cdp_ready(cdp_url):
                    raise Exception(f"CDP endpoint at {cdp_url} is not ready after startup")

                self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)

            contexts = self.browser.contexts

            # If browser_context_id is provided, we're using a pre-created context
            if self.config.browser_context_id:
                if self.logger:
                    self.logger.debug(
                        f"Using pre-existing browser context: {self.config.browser_context_id}",
                        tag="BROWSER"
                    )
                # When connecting to a pre-created context, it should be in contexts
                if contexts:
                    self.default_context = contexts[0]
                    if self.logger:
                        self.logger.debug(
                            f"Found {len(contexts)} existing context(s), using first one",
                            tag="BROWSER"
                        )
                else:
                    # Context was created but not yet visible - wait a bit
                    await asyncio.sleep(0.2)
                    contexts = self.browser.contexts
                    if contexts:
                        self.default_context = contexts[0]
                    else:
                        # Still no contexts - this shouldn't happen with pre-created context
                        if self.logger:
                            self.logger.warning(
                                "Pre-created context not found, creating new one",
                                tag="BROWSER"
                            )
                        self.default_context = await self.create_browser_context()
            elif contexts:
                self.default_context = contexts[0]
            else:
                self.default_context = await self.create_browser_context()
            await self.setup_context(self.default_context)
        else:
            browser_args = self._build_browser_args()

            # Launch appropriate browser type
            if self.config.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_args)
            elif self.config.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(**browser_args)
            else:
                self.browser = await self.playwright.chromium.launch(**browser_args)

            self.default_context = self.browser

        # Set the browser endpoint key for global page tracking
        self._browser_endpoint_key = self._compute_browser_endpoint_key()
        # Initialize global tracking set for this endpoint if needed
        if self._browser_endpoint_key not in BrowserManager._global_pages_in_use:
            BrowserManager._global_pages_in_use[self._browser_endpoint_key] = set()

    def _compute_browser_endpoint_key(self) -> str:
        """
        Compute a unique key identifying this browser connection.

        For CDP connections, uses the normalized CDP URL so all BrowserManager
        instances connecting to the same browser share page tracking.
        For standalone browsers, uses instance id since each is independent.

        Returns:
            str: Unique identifier for this browser connection
        """
        # For CDP connections, use the CDP URL as the key (normalized)
        if self.config.cdp_url:
            return self._normalize_cdp_url(self.config.cdp_url)

        # For managed browsers, use the CDP URL/port that was assigned
        if self.managed_browser:
            # Use debugging port as the key since it uniquely identifies the browser
            port = getattr(self.managed_browser, 'debugging_port', None)
            host = getattr(self.managed_browser, 'host', 'localhost')
            if port:
                return f"cdp:http://{host}:{port}"

        # For standalone browsers, use instance id (no sharing needed)
        return f"instance:{id(self)}"

    def _normalize_cdp_url(self, cdp_url: str) -> str:
        """
        Normalize a CDP URL to a canonical form for consistent tracking.

        Handles various formats:
        - http://localhost:9222
        - ws://localhost:9222/devtools/browser/xxx
        - http://localhost:9222?browser_id=xxx

        Returns:
            str: Normalized CDP key in format "cdp:http://host:port"
        """
        from urllib.parse import urlparse

        parsed = urlparse(cdp_url)
        host = parsed.hostname or 'localhost'
        port = parsed.port or 9222

        return f"cdp:http://{host}:{port}"

    def _get_pages_in_use(self) -> set:
        """Get the set of pages currently in use for this browser."""
        if self._browser_endpoint_key and self._browser_endpoint_key in BrowserManager._global_pages_in_use:
            return BrowserManager._global_pages_in_use[self._browser_endpoint_key]
        # Fallback: shouldn't happen, but return empty set
        return set()

    def _mark_page_in_use(self, page) -> None:
        """Mark a page as in use."""
        if self._browser_endpoint_key:
            if self._browser_endpoint_key not in BrowserManager._global_pages_in_use:
                BrowserManager._global_pages_in_use[self._browser_endpoint_key] = set()
            BrowserManager._global_pages_in_use[self._browser_endpoint_key].add(page)

    def _release_page_from_use(self, page) -> None:
        """Release a page from the in-use tracking."""
        if self._browser_endpoint_key and self._browser_endpoint_key in BrowserManager._global_pages_in_use:
            BrowserManager._global_pages_in_use[self._browser_endpoint_key].discard(page)

    async def _verify_cdp_ready(self, cdp_url: str) -> bool:
        """Verify CDP endpoint is ready with exponential backoff.

        Supports multiple URL formats:
        - HTTP URLs: http://localhost:9222
        - HTTP URLs with query params: http://localhost:9222?browser_id=XXX
        - WebSocket URLs: ws://localhost:9222/devtools/browser/XXX
        """
        import aiohttp
        from urllib.parse import urlparse, urlunparse

        # If WebSocket URL, Playwright handles connection directly - skip HTTP verification
        if cdp_url.startswith(('ws://', 'wss://')):
            self.logger.debug(f"WebSocket CDP URL provided, skipping HTTP verification", tag="BROWSER")
            return True

        # Parse HTTP URL and properly construct /json/version endpoint
        parsed = urlparse(cdp_url)
        # Build URL with /json/version path, preserving query params
        verify_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            '/json/version',  # Always use this path for verification
            '',  # params
            parsed.query,  # preserve query string
            ''   # fragment
        ))

        self.logger.debug(f"Starting CDP verification for {verify_url}", tag="BROWSER")
        for attempt in range(5):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(verify_url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                        if response.status == 200:
                            self.logger.debug(f"CDP endpoint ready after {attempt + 1} attempts", tag="BROWSER")
                            return True
            except Exception as e:
                self.logger.debug(f"CDP check attempt {attempt + 1} failed: {e}", tag="BROWSER")
            delay = 0.5 * (1.4 ** attempt)
            self.logger.debug(f"Waiting {delay:.2f}s before next CDP check...", tag="BROWSER")
            await asyncio.sleep(delay)
        self.logger.debug(f"CDP verification failed after 5 attempts", tag="BROWSER")
        return False

    def _build_browser_args(self) -> dict:
        """Build browser launch arguments from config."""
        args = [
            "--disable-gpu",
            "--disable-gpu-compositing",
            "--disable-software-rasterizer",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certificate-errors",
            "--ignore-certificate-errors-spki-list",
            "--disable-blink-features=AutomationControlled",
            "--window-position=400,0",
            "--disable-renderer-backgrounding",
            "--disable-ipc-flooding-protection",
            "--force-color-profile=srgb",
            "--mute-audio",
            "--disable-background-timer-throttling",
            # Memory-saving flags: disable unused Chrome features
            "--disable-features=OptimizationHints,MediaRouter,DialMediaRouteProvider",
            "--disable-component-update",
            "--disable-domain-reliability",
            # "--single-process",
            f"--window-size={self.config.viewport_width},{self.config.viewport_height}",
        ]

        if self.config.memory_saving_mode:
            args.extend([
                "--aggressive-cache-discard",
                '--js-flags=--max-old-space-size=512',
            ])

        if self.config.light_mode:
            args.extend(BROWSER_DISABLE_OPTIONS)

        if self.config.text_mode:
            args.extend(
                [
                    "--blink-settings=imagesEnabled=false",
                    "--disable-remote-fonts",
                    "--disable-images",
                    "--disable-javascript",
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                ]
            )

        if self.config.extra_args:
            args.extend(self.config.extra_args)

        # Deduplicate args
        args = list(dict.fromkeys(args))
        
        browser_args = {"headless": self.config.headless, "args": args}

        if self.config.chrome_channel:
            browser_args["channel"] = self.config.chrome_channel

        if self.config.accept_downloads:
            browser_args["downloads_path"] = self.config.downloads_path or os.path.join(
                os.getcwd(), "downloads"
            )
            os.makedirs(browser_args["downloads_path"], exist_ok=True)

        if self.config.proxy:
            warnings.warn(
                "BrowserConfig.proxy is deprecated and ignored. Use proxy_config instead.",
                DeprecationWarning,
            )
        if self.config.proxy_config:
            from playwright.async_api import ProxySettings

            proxy_settings = ProxySettings(
                server=self.config.proxy_config.server,
                username=self.config.proxy_config.username,
                password=self.config.proxy_config.password,
            )
            browser_args["proxy"] = proxy_settings

        return browser_args

    async def setup_context(
        self,
        context: BrowserContext,
        crawlerRunConfig: CrawlerRunConfig = None,
        is_default=False,
    ):
        """
        Set up a browser context with the configured options.

        How it works:
        1. Set extra HTTP headers if provided.
        2. Add cookies if provided.
        3. Load storage state if provided.
        4. Accept downloads if enabled.
        5. Set default timeouts for navigation and download.
        6. Set user agent if provided.
        7. Set browser hints if provided.
        8. Set proxy if provided.
        9. Set downloads path if provided.
        10. Set storage state if provided.
        11. Set cache if provided.
        12. Set extra HTTP headers if provided.
        13. Add cookies if provided.
        14. Set default timeouts for navigation and download if enabled.
        15. Set user agent if provided.
        16. Set browser hints if provided.

        Args:
            context (BrowserContext): The browser context to set up
            crawlerRunConfig (CrawlerRunConfig): Configuration object containing all browser settings
            is_default (bool): Flag indicating if this is the default context
        Returns:
            None
        """
        if self.config.headers:
            await context.set_extra_http_headers(self.config.headers)

        if self.config.cookies:
            await context.add_cookies(self.config.cookies)

        if self.config.storage_state:
            await context.storage_state(path=None)

        if self.config.accept_downloads:
            context.set_default_timeout(DOWNLOAD_PAGE_TIMEOUT)
            context.set_default_navigation_timeout(DOWNLOAD_PAGE_TIMEOUT)
            if self.config.downloads_path:
                context._impl_obj._options["accept_downloads"] = True
                context._impl_obj._options[
                    "downloads_path"
                ] = self.config.downloads_path

        # Handle user agent and browser hints
        if self.config.user_agent:
            combined_headers = {
                "User-Agent": self.config.user_agent,
                "sec-ch-ua": self.config.browser_hint,
            }
            combined_headers.update(self.config.headers)
            await context.set_extra_http_headers(combined_headers)

        # Add default cookie (skip for raw:/file:// URLs which are not valid cookie URLs)
        cookie_url = None
        if crawlerRunConfig and crawlerRunConfig.url:
            url = crawlerRunConfig.url
            # Only set cookie for http/https URLs
            if url.startswith(("http://", "https://")):
                cookie_url = url
            elif crawlerRunConfig.base_url and crawlerRunConfig.base_url.startswith(("http://", "https://")):
                # Use base_url as fallback for raw:/file:// URLs
                cookie_url = crawlerRunConfig.base_url

        if cookie_url:
            await context.add_cookies(
                [
                    {
                        "name": "cookiesEnabled",
                        "value": "true",
                        "url": cookie_url,
                    }
                ]
            )

        # Handle navigator overrides
        if crawlerRunConfig:
            if (
                crawlerRunConfig.override_navigator
                or crawlerRunConfig.simulate_user
                or crawlerRunConfig.magic
            ):
                await context.add_init_script(load_js_script("navigator_overrider"))
                context._crawl4ai_nav_overrider_injected = True

        # Force-open closed shadow roots when flatten_shadow_dom is enabled
        if crawlerRunConfig and crawlerRunConfig.flatten_shadow_dom:
            await context.add_init_script("""
                const _origAttachShadow = Element.prototype.attachShadow;
                Element.prototype.attachShadow = function(init) {
                    return _origAttachShadow.call(this, {...init, mode: 'open'});
                };
            """)
            context._crawl4ai_shadow_dom_injected = True

        # Apply custom init_scripts from BrowserConfig (for stealth evasions, etc.)
        if self.config.init_scripts:
            for script in self.config.init_scripts:
                await context.add_init_script(script)

    async def create_browser_context(self, crawlerRunConfig: CrawlerRunConfig = None):
        """
        Creates and returns a new browser context with configured settings.
        Applies text-only mode settings if text_mode is enabled in config.

        Returns:
            Context: Browser context object with the specified configurations
        """
        if self.browser is None:
            if self._launched_persistent:
                raise RuntimeError(
                    "Cannot create new browser contexts when using "
                    "use_persistent_context=True. Persistent context uses a "
                    "single shared context."
                )
            raise RuntimeError(
                "Browser is not available. It may have been closed, crashed, "
                "or not yet started. Ensure the browser is running before "
                "creating new contexts."
            )
        # Base settings
        user_agent = self.config.headers.get("User-Agent", self.config.user_agent) 
        viewport_settings = {
            "width": self.config.viewport_width,
            "height": self.config.viewport_height,
        }
        proxy_settings = {"server": self.config.proxy} if self.config.proxy else None

        # CSS extensions (blocked separately via avoid_css flag)
        css_extensions = ["css", "less", "scss", "sass"]

        # Static resource extensions (blocked when text_mode is enabled)
        static_extensions = [
            # Images
            "jpg", "jpeg", "png", "gif", "webp", "svg", "ico", "bmp", "tiff", "psd",
            # Fonts
            "woff", "woff2", "ttf", "otf", "eot",
            # Media
            "mp4", "webm", "ogg", "avi", "mov", "wmv", "flv", "m4v",
            "mp3", "wav", "aac", "m4a", "opus", "flac",
            # Documents
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
            # Archives
            "zip", "rar", "7z", "tar", "gz",
            # Scripts and data
            "xml", "swf", "wasm",
        ]

        # Ad and tracker domain patterns (curated from uBlock/EasyList sources)
        ad_tracker_patterns = [
            "**/google-analytics.com/**",
            "**/googletagmanager.com/**",
            "**/googlesyndication.com/**",
            "**/doubleclick.net/**",
            "**/adservice.google.com/**",
            "**/adsystem.com/**",
            "**/adzerk.net/**",
            "**/adnxs.com/**",
            "**/ads.linkedin.com/**",
            "**/facebook.net/**",
            "**/analytics.twitter.com/**",
            "**/ads-twitter.com/**",
            "**/hotjar.com/**",
            "**/clarity.ms/**",
            "**/scorecardresearch.com/**",
            "**/pixel.wp.com/**",
            "**/amazon-adsystem.com/**",
            "**/mixpanel.com/**",
            "**/segment.com/**",
        ]

        # Common context settings
        context_settings = {
            "user_agent": user_agent,
            "viewport": viewport_settings,
            "proxy": proxy_settings,
            "accept_downloads": self.config.accept_downloads,
            "storage_state": self.config.storage_state,
            "ignore_https_errors": self.config.ignore_https_errors,
            "device_scale_factor": self.config.device_scale_factor,
            "java_script_enabled": self.config.java_script_enabled,
        }
        
        if crawlerRunConfig:
            # Check if there is value for crawlerRunConfig.proxy_config set add that to context
            if crawlerRunConfig.proxy_config:
                from playwright.async_api import ProxySettings
                proxy_settings = ProxySettings(
                    server=crawlerRunConfig.proxy_config.server,
                    username=crawlerRunConfig.proxy_config.username,
                    password=crawlerRunConfig.proxy_config.password,
                )
                context_settings["proxy"] = proxy_settings

        if self.config.text_mode:
            text_mode_settings = {
                "has_touch": False,
                "is_mobile": False,
            }
            # Update context settings with text mode settings
            context_settings.update(text_mode_settings)

        # inject locale / tz / geo if user provided them
        if crawlerRunConfig:
            if crawlerRunConfig.locale:
                context_settings["locale"] = crawlerRunConfig.locale
            if crawlerRunConfig.timezone_id:
                context_settings["timezone_id"] = crawlerRunConfig.timezone_id
            if crawlerRunConfig.geolocation:
                context_settings["geolocation"] = {
                    "latitude": crawlerRunConfig.geolocation.latitude,
                    "longitude": crawlerRunConfig.geolocation.longitude,
                    "accuracy": crawlerRunConfig.geolocation.accuracy,
                }
                # ensure geolocation permission
                perms = context_settings.get("permissions", [])
                perms.append("geolocation")
                context_settings["permissions"] = perms

        # Create and return the context with all settings
        context = await self.browser.new_context(**context_settings)

        # Build dynamic blocking list based on config flags
        to_block = []
        if self.config.avoid_css:
            to_block.extend(css_extensions)
        if self.config.text_mode:
            to_block.extend(static_extensions)

        if to_block:
            for ext in to_block:
                await context.route(f"**/*.{ext}", lambda route: route.abort())

        if self.config.avoid_ads:
            for pattern in ad_tracker_patterns:
                await context.route(pattern, lambda route: route.abort())

        return context

    def _make_config_signature(self, crawlerRunConfig: CrawlerRunConfig) -> str:
        """
        Hash ONLY the CrawlerRunConfig fields that affect browser context
        creation (create_browser_context) or context setup (setup_context).

        Whitelist approach: fields like css_selector, word_count_threshold,
        screenshot, verbose, etc. do NOT cause a new context to be created.
        """
        import json

        sig_dict = {}

        # Fields that flow into create_browser_context()
        pc = crawlerRunConfig.proxy_config
        if pc is not None:
            sig_dict["proxy_config"] = {
                "server": getattr(pc, "server", None),
                "username": getattr(pc, "username", None),
                "password": getattr(pc, "password", None),
            }
        else:
            sig_dict["proxy_config"] = None

        sig_dict["locale"] = crawlerRunConfig.locale
        sig_dict["timezone_id"] = crawlerRunConfig.timezone_id

        geo = crawlerRunConfig.geolocation
        if geo is not None:
            sig_dict["geolocation"] = {
                "latitude": geo.latitude,
                "longitude": geo.longitude,
                "accuracy": geo.accuracy,
            }
        else:
            sig_dict["geolocation"] = None

        # Fields that flow into setup_context() as init scripts
        sig_dict["override_navigator"] = crawlerRunConfig.override_navigator
        sig_dict["simulate_user"] = crawlerRunConfig.simulate_user
        sig_dict["magic"] = crawlerRunConfig.magic

        # Browser version — bumped on recycle to force new browser instance
        sig_dict["_browser_version"] = self._browser_version

        signature_json = json.dumps(sig_dict, sort_keys=True, default=str)
        return hashlib.sha256(signature_json.encode("utf-8")).hexdigest()

    def _evict_lru_context_locked(self):
        """
        If contexts exceed the limit, find the least-recently-used context
        with zero active crawls and remove it from all tracking dicts.

        MUST be called while holding self._contexts_lock.

        Returns the BrowserContext to close (caller closes it OUTSIDE the
        lock), or None if no eviction is needed or possible.
        """
        if len(self.contexts_by_config) <= self._max_contexts:
            return None

        # Sort candidates by last-used timestamp (oldest first)
        candidates = sorted(
            self._context_last_used.items(),
            key=lambda item: item[1],
        )
        for evict_sig, _ in candidates:
            if self._context_refcounts.get(evict_sig, 0) == 0:
                ctx = self.contexts_by_config.pop(evict_sig, None)
                self._context_refcounts.pop(evict_sig, None)
                self._context_last_used.pop(evict_sig, None)
                # Clean up stale page->sig mappings for evicted context
                stale_pages = [
                    p for p, s in self._page_to_sig.items() if s == evict_sig
                ]
                for p in stale_pages:
                    del self._page_to_sig[p]
                return ctx

        # All contexts are in active use — cannot evict
        return None

    async def _apply_stealth_to_page(self, page):
        """Apply stealth to a page if stealth mode is enabled"""
        if self._stealth_adapter:
            try:
                await self._stealth_adapter.apply_stealth(page)
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        message="Failed to apply stealth to page: {error}",
                        tag="STEALTH",
                        params={"error": str(e)}
                    )

    async def _get_page_by_target_id(self, context: BrowserContext, target_id: str):
        """
        Get an existing page by its CDP target ID.

        This is used when connecting to a pre-created browser context with an existing page.
        Playwright may not immediately see targets created via raw CDP commands, so we
        use CDP to get all targets and find the matching one.

        Args:
            context: The browser context to search in
            target_id: The CDP target ID to find

        Returns:
            Page object if found, None otherwise
        """
        try:
            # First check if Playwright already sees the page
            for page in context.pages:
                # Playwright's internal target ID might match
                if hasattr(page, '_impl_obj') and hasattr(page._impl_obj, '_target_id'):
                    if page._impl_obj._target_id == target_id:
                        return page

            # If not found, try using CDP to get targets
            if hasattr(self.browser, '_impl_obj') and hasattr(self.browser._impl_obj, '_connection'):
                cdp_session = await context.new_cdp_session(context.pages[0] if context.pages else None)
                if cdp_session:
                    try:
                        result = await cdp_session.send("Target.getTargets")
                        targets = result.get("targetInfos", [])
                        for target in targets:
                            if target.get("targetId") == target_id:
                                # Found the target - if it's a page type, we can use it
                                if target.get("type") == "page":
                                    # The page exists, let Playwright discover it
                                    await asyncio.sleep(0.1)
                                    # Refresh pages list
                                    if context.pages:
                                        return context.pages[0]
                    finally:
                        await cdp_session.detach()

            # Fallback: if there are any pages now, return the first one
            if context.pages:
                return context.pages[0]

            return None
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    message="Failed to get page by target ID: {error}",
                    tag="BROWSER",
                    params={"error": str(e)}
                )
            return None

    async def get_page(self, crawlerRunConfig: CrawlerRunConfig):
        """
        Get a page for the given session ID, creating a new one if needed.

        Args:
            crawlerRunConfig (CrawlerRunConfig): Configuration object containing all browser settings

        Returns:
            (page, context): The Page and its BrowserContext
        """
        self._cleanup_expired_sessions()

        # If a session_id is provided and we already have it, reuse that page + context
        if crawlerRunConfig.session_id and crawlerRunConfig.session_id in self.sessions:
            context, page, _ = self.sessions[crawlerRunConfig.session_id]
            # Update last-used timestamp
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            return page, context

        # If using a managed browser, just grab the shared default_context
        if self.config.use_managed_browser:
            # If create_isolated_context is True, create isolated contexts for concurrent crawls
            # Uses the same caching mechanism as non-CDP mode: cache context by config signature,
            # but always create a new page. This prevents navigation conflicts while allowing
            # context reuse for multiple URLs with the same config (e.g., batch/deep crawls).
            if self.config.create_isolated_context:
                config_signature = self._make_config_signature(crawlerRunConfig)
                to_close = None

                async with self._contexts_lock:
                    if config_signature in self.contexts_by_config:
                        context = self.contexts_by_config[config_signature]
                    else:
                        context = await self.create_browser_context(crawlerRunConfig)
                        await self.setup_context(context, crawlerRunConfig)
                        self.contexts_by_config[config_signature] = context
                        self._context_refcounts[config_signature] = 0
                        to_close = self._evict_lru_context_locked()

                    # Increment refcount INSIDE lock before releasing
                    self._context_refcounts[config_signature] = (
                        self._context_refcounts.get(config_signature, 0) + 1
                    )
                    self._context_last_used[config_signature] = time.monotonic()

                # Close evicted context OUTSIDE lock
                if to_close is not None:
                    try:
                        await to_close.close()
                    except Exception:
                        pass

                # Always create a new page for each crawl (isolation for navigation)
                try:
                    page = await context.new_page()
                except Exception:
                    async with self._contexts_lock:
                        if config_signature in self._context_refcounts:
                            self._context_refcounts[config_signature] = max(
                                0, self._context_refcounts[config_signature] - 1
                            )
                    raise
                await self._apply_stealth_to_page(page)
                self._page_to_sig[page] = config_signature
            elif self.config.storage_state:
                tmp_context = await self.create_browser_context(crawlerRunConfig)
                ctx = self.default_context        # default context, one window only
                ctx = await clone_runtime_state(tmp_context, ctx, crawlerRunConfig, self.config)
                # Close the temporary context — only needed as a clone source
                try:
                    await tmp_context.close()
                except Exception:
                    pass
                context = ctx  # so (page, context) return value is correct
                # Avoid concurrent new_page on shared persistent context
                # See GH-1198: context.pages can be empty under races
                async with self._page_lock:
                    page = await ctx.new_page()
                await self._apply_stealth_to_page(page)
            else:
                context = self.default_context

                # Handle pre-existing target case (for reconnecting to specific CDP targets)
                if self.config.browser_context_id and self.config.target_id:
                    page = await self._get_page_by_target_id(context, self.config.target_id)
                    if not page:
                        async with self._page_lock:
                            page = await context.new_page()
                            self._mark_page_in_use(page)
                        await self._apply_stealth_to_page(page)
                    else:
                        # Mark pre-existing target as in use
                        self._mark_page_in_use(page)
                else:
                    # For CDP connections (external browser), multiple Playwright connections
                    # create separate browser/context objects. Page reuse across connections
                    # isn't reliable because each connection sees different page objects.
                    # Always create new pages for CDP to avoid cross-connection race conditions.
                    if self.config.cdp_url and not self.config.use_managed_browser:
                        async with self._page_lock:
                            page = await context.new_page()
                            self._mark_page_in_use(page)
                        await self._apply_stealth_to_page(page)
                    else:
                        # For managed browsers (single process), page reuse is safe.
                        # Use lock to safely check for available pages and track usage.
                        # This prevents race conditions when multiple crawls run concurrently.
                        async with BrowserManager._get_global_lock():
                            pages = context.pages
                            pages_in_use = self._get_pages_in_use()
                            # Find first available page (exists and not currently in use)
                            available_page = next(
                                (p for p in pages if p not in pages_in_use),
                                None
                            )
                            if available_page:
                                page = available_page
                            else:
                                # No available pages - create a new one
                                page = await context.new_page()
                                await self._apply_stealth_to_page(page)
                            # Mark page as in use (global tracking)
                            self._mark_page_in_use(page)
        else:
            # Otherwise, check if we have an existing context for this config
            config_signature = self._make_config_signature(crawlerRunConfig)
            to_close = None

            async with self._contexts_lock:
                if config_signature in self.contexts_by_config:
                    context = self.contexts_by_config[config_signature]
                else:
                    # Create and setup a new context
                    context = await self.create_browser_context(crawlerRunConfig)
                    await self.setup_context(context, crawlerRunConfig)
                    self.contexts_by_config[config_signature] = context
                    self._context_refcounts[config_signature] = 0
                    to_close = self._evict_lru_context_locked()

                # Increment refcount INSIDE lock before releasing
                self._context_refcounts[config_signature] = (
                    self._context_refcounts.get(config_signature, 0) + 1
                )
                self._context_last_used[config_signature] = time.monotonic()

            # Close evicted context OUTSIDE lock
            if to_close is not None:
                try:
                    await to_close.close()
                except Exception:
                    pass

            # Create a new page from the chosen context
            try:
                page = await context.new_page()
            except Exception:
                async with self._contexts_lock:
                    if config_signature in self._context_refcounts:
                        self._context_refcounts[config_signature] = max(
                            0, self._context_refcounts[config_signature] - 1
                        )
                raise
            await self._apply_stealth_to_page(page)
            self._page_to_sig[page] = config_signature

        # If a session_id is specified, store this session so we can reuse later
        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())

        self._pages_served += 1

        # Check if browser recycle threshold is hit — bump version for next requests
        # This happens AFTER incrementing counter so concurrent requests see correct count
        await self._maybe_bump_browser_version()

        return page, context

    async def kill_session(self, session_id: str):
        """
        Kill a browser session and clean up resources.

        Args:
            session_id (str): The session ID to kill.
        """
        if session_id in self.sessions:
            context, page, _ = self.sessions[session_id]
            self._release_page_from_use(page)
            # Decrement context refcount for the session's page
            should_close_context = False
            async with self._contexts_lock:
                sig = self._page_to_sig.pop(page, None)
                if sig is not None and sig in self._context_refcounts:
                    self._context_refcounts[sig] = max(
                        0, self._context_refcounts[sig] - 1
                    )
                    # Only close the context if no other pages are using it
                    # (refcount dropped to 0) AND we own the context (not managed)
                    if not self.config.use_managed_browser:
                        if self._context_refcounts.get(sig, 0) == 0:
                            self.contexts_by_config.pop(sig, None)
                            self._context_refcounts.pop(sig, None)
                            self._context_last_used.pop(sig, None)
                            should_close_context = True
            await page.close()
            if should_close_context:
                await context.close()
            del self.sessions[session_id]

    def release_page(self, page):
        """
        Release a page from the in-use tracking set (global tracking).
        Sync variant — does NOT decrement context refcount.
        """
        self._release_page_from_use(page)

    async def release_page_with_context(self, page):
        """
        Release a page and decrement its context's refcount under the lock.

        Should be called from the async crawl finally block instead of
        release_page() so the context lifecycle is properly tracked.
        """
        self._release_page_from_use(page)
        sig = None
        refcount = -1
        async with self._contexts_lock:
            sig = self._page_to_sig.pop(page, None)
            if sig is not None and sig in self._context_refcounts:
                self._context_refcounts[sig] = max(
                    0, self._context_refcounts[sig] - 1
                )
                refcount = self._context_refcounts[sig]

        # Check if this signature belongs to an old browser waiting to be cleaned up
        if sig is not None and refcount == 0:
            await self._maybe_cleanup_old_browser(sig)

    def _should_recycle(self) -> bool:
        """Check if page threshold reached for browser recycling."""
        limit = self.config.max_pages_before_recycle
        if limit <= 0:
            return False
        return self._pages_served >= limit

    async def _maybe_bump_browser_version(self):
        """Bump browser version if threshold reached, moving old browser to pending cleanup.

        New requests automatically get a new browser (via new signature).
        Old browser drains naturally and gets cleaned up when refcount hits 0.
        """
        if not self._should_recycle():
            return

        # Safety cap: wait if too many old browsers are draining
        while True:
            async with self._pending_cleanup_lock:
                # Re-check threshold under lock (another request may have bumped already)
                if not self._should_recycle():
                    return

                # Check safety cap
                if len(self._pending_cleanup) >= self._max_pending_browsers:
                    if self.logger:
                        self.logger.debug(
                            message="Waiting for old browser to drain (pending: {count})",
                            tag="BROWSER",
                            params={"count": len(self._pending_cleanup)},
                        )
                    self._cleanup_slot_available.clear()
                    # Release lock and wait
                else:
                    # We have a slot — do the bump inside this lock hold
                    old_version = self._browser_version
                    active_sigs = []
                    idle_sigs = []
                    async with self._contexts_lock:
                        for sig in list(self._context_refcounts.keys()):
                            if self._context_refcounts.get(sig, 0) > 0:
                                active_sigs.append(sig)
                            else:
                                idle_sigs.append(sig)

                    if self.logger:
                        self.logger.info(
                            message="Bumping browser version {old} -> {new} after {count} pages ({active} active, {idle} idle sigs)",
                            tag="BROWSER",
                            params={
                                "old": old_version,
                                "new": old_version + 1,
                                "count": self._pages_served,
                                "active": len(active_sigs),
                                "idle": len(idle_sigs),
                            },
                        )

                    # Only add sigs with active crawls to pending cleanup.
                    # Sigs with refcount 0 are cleaned up immediately below
                    # to avoid them being stuck in _pending_cleanup forever
                    # (no future release would trigger their cleanup).
                    done_event = asyncio.Event()
                    for sig in active_sigs:
                        self._pending_cleanup[sig] = {
                            "version": old_version,
                            "done": done_event,
                        }

                    # Bump version — new get_page() calls will create new contexts
                    self._browser_version += 1
                    self._pages_served = 0

                    # Clean up idle sigs immediately (outside pending_cleanup_lock below)
                    break  # exit while loop to do cleanup outside locks

            # Safety cap path: wait for a cleanup slot, then retry.
            # Timeout prevents permanent deadlock if stuck entries never drain.
            try:
                await asyncio.wait_for(
                    self._cleanup_slot_available.wait(), timeout=30.0
                )
            except asyncio.TimeoutError:
                # Force-clean any pending entries that have refcount 0
                # (they're stuck and will never drain naturally)
                async with self._pending_cleanup_lock:
                    stuck_sigs = [
                        s for s in list(self._pending_cleanup.keys())
                        if self._context_refcounts.get(s, 0) == 0
                    ]
                    for sig in stuck_sigs:
                        self._pending_cleanup.pop(sig, None)
                    if stuck_sigs:
                        if self.logger:
                            self.logger.warning(
                                message="Force-cleaned {count} stuck pending entries after timeout",
                                tag="BROWSER",
                                params={"count": len(stuck_sigs)},
                            )
                        # Clean up the stuck contexts
                        for sig in stuck_sigs:
                            async with self._contexts_lock:
                                context = self.contexts_by_config.pop(sig, None)
                                self._context_refcounts.pop(sig, None)
                                self._context_last_used.pop(sig, None)
                            if context is not None:
                                try:
                                    await context.close()
                                except Exception:
                                    pass
                        if len(self._pending_cleanup) < self._max_pending_browsers:
                            self._cleanup_slot_available.set()

        # Reached via break — clean up idle sigs immediately (outside locks)
        for sig in idle_sigs:
            async with self._contexts_lock:
                context = self.contexts_by_config.pop(sig, None)
                self._context_refcounts.pop(sig, None)
                self._context_last_used.pop(sig, None)
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
        if idle_sigs and self.logger:
            self.logger.debug(
                message="Immediately cleaned up {count} idle contexts from version {version}",
                tag="BROWSER",
                params={"count": len(idle_sigs), "version": old_version},
            )

    async def _maybe_cleanup_old_browser(self, sig: str):
        """Clean up an old browser's context if its refcount hit 0 and it's pending cleanup."""
        async with self._pending_cleanup_lock:
            if sig not in self._pending_cleanup:
                return  # Not an old browser signature

            cleanup_info = self._pending_cleanup.pop(sig)
            old_version = cleanup_info["version"]

            if self.logger:
                self.logger.debug(
                    message="Cleaning up context from browser version {version} (sig: {sig})",
                    tag="BROWSER",
                    params={"version": old_version, "sig": sig[:12]},
                )

            # Remove context from tracking
            async with self._contexts_lock:
                context = self.contexts_by_config.pop(sig, None)
                self._context_refcounts.pop(sig, None)
                self._context_last_used.pop(sig, None)

            # Close context outside locks
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass

            # Check if any signatures from this old version remain
            remaining_old = [
                s for s, info in self._pending_cleanup.items()
                if info["version"] == old_version
            ]

            if not remaining_old:
                if self.logger:
                    self.logger.info(
                        message="All contexts from browser version {version} cleaned up",
                        tag="BROWSER",
                        params={"version": old_version},
                    )

            # Open a cleanup slot if we're below the cap
            if len(self._pending_cleanup) < self._max_pending_browsers:
                self._cleanup_slot_available.set()

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions based on TTL."""
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, (_, _, last_used) in self.sessions.items()
            if current_time - last_used > self.session_ttl
        ]
        for sid in expired_sessions:
            asyncio.create_task(self.kill_session(sid))

    async def close(self):
        """Close all browser resources and clean up."""
        # Cached CDP path: only clean up this instance's sessions/contexts,
        # then release the shared connection reference.
        if self._using_cached_cdp:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.kill_session(session_id)
            for ctx in self.contexts_by_config.values():
                try:
                    await ctx.close()
                except Exception:
                    pass
            self.contexts_by_config.clear()
            self._context_refcounts.clear()
            self._context_last_used.clear()
            self._page_to_sig.clear()
            await _CDPConnectionCache.release(self.config.cdp_url)
            self.browser = None
            self.playwright = None
            self._using_cached_cdp = False
            return

        if self.config.cdp_url:
            # When using external CDP, we don't own the browser process.
            # If cdp_cleanup_on_close is True, properly disconnect from the browser
            # and clean up Playwright resources. This frees the browser for other clients.
            if self.config.cdp_cleanup_on_close:
                # First close all sessions (pages)
                session_ids = list(self.sessions.keys())
                for session_id in session_ids:
                    await self.kill_session(session_id)

                # Close all contexts we created
                for ctx in self.contexts_by_config.values():
                    try:
                        await ctx.close()
                    except Exception:
                        pass
                self.contexts_by_config.clear()
                self._context_refcounts.clear()
                self._context_last_used.clear()
                self._page_to_sig.clear()

                # Disconnect from browser (doesn't terminate it, just releases connection)
                if self.browser:
                    try:
                        await self.browser.close()
                    except Exception as e:
                        if self.logger:
                            self.logger.debug(
                                message="Error disconnecting from CDP browser: {error}",
                                tag="BROWSER",
                                params={"error": str(e)}
                            )
                    self.browser = None
                    # Allow time for CDP connection to fully release before another client connects
                    if self.config.cdp_close_delay > 0:
                        await asyncio.sleep(self.config.cdp_close_delay)

                # Stop Playwright instance to prevent memory leaks
                if self.playwright:
                    await self.playwright.stop()
                    self.playwright = None
            return

        # ── Persistent context launched via launch_persistent_context ──
        if self._launched_persistent:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.kill_session(session_id)
            for ctx in self.contexts_by_config.values():
                try:
                    await ctx.close()
                except Exception:
                    pass
            self.contexts_by_config.clear()
            self._context_refcounts.clear()
            self._context_last_used.clear()
            self._page_to_sig.clear()

            # Closing the persistent context also terminates the browser
            if self.default_context:
                try:
                    await self.default_context.close()
                except Exception:
                    pass
                self.default_context = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            self._launched_persistent = False
            return

        if self.config.sleep_on_close:
            await asyncio.sleep(0.5)

        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.kill_session(session_id)

        # Now close all contexts we created. This reclaims memory from ephemeral contexts.
        for ctx in self.contexts_by_config.values():
            try:
                await ctx.close()
            except Exception as e:
                self.logger.error(
                    message="Error closing context: {error}",
                    tag="ERROR",
                    params={"error": str(e)}
                )
        self.contexts_by_config.clear()
        self._context_refcounts.clear()
        self._context_last_used.clear()
        self._page_to_sig.clear()

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.managed_browser:
            await asyncio.sleep(0.5)
            await self.managed_browser.cleanup()
            self.managed_browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
