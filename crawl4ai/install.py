import subprocess
import sys
import asyncio
from .async_logger import AsyncLogger, LogLevel
from pathlib import Path
import os
import shutil

# Initialize logger
logger = AsyncLogger(log_level=LogLevel.DEBUG, verbose=True)

def setup_home_directory():
    """Set up the .crawl4ai folder structure in the user's home directory."""
    base_dir = os.getenv("CRAWL4_AI_BASE_DIRECTORY")
    crawl4ai_folder = Path(base_dir) if base_dir else Path.home()
    crawl4ai_config = crawl4ai_folder / "global.yml"
    crawl4ai_folder = crawl4ai_folder / ".crawl4ai"
    cache_folder = crawl4ai_folder / "cache"
    content_folders = [
        "html_content",
        "cleaned_html",
        "markdown_content",
        "extracted_content",
        "screenshots",
    ]

    # Clean up old cache if exists
    if cache_folder.exists():
        shutil.rmtree(cache_folder)

    # Create new folder structure
    crawl4ai_folder.mkdir(exist_ok=True)
    cache_folder.mkdir(exist_ok=True)
    for folder in content_folders:
        (crawl4ai_folder / folder).mkdir(exist_ok=True)
    
    # If config file does not exist, create it
    if not crawl4ai_config.exists():
        with open(crawl4ai_config, "w") as f:
            f.write("")

def post_install():
    """
    Run all post-installation tasks.
    Checks CRAWL4AI_MODE environment variable. If set to 'api',
    skips Playwright browser installation.
    Exits with code 1 when the browser could not be installed.
    """
    logger.info("Running post-installation setup...", tag="INIT")
    setup_home_directory()

    # Check environment variable to conditionally skip Playwright install
    run_mode = os.getenv('CRAWL4AI_MODE')
    browser_installed = True
    if run_mode == 'api':
        logger.warning(
            "CRAWL4AI_MODE=api detected. Skipping Playwright browser installation.",
            tag="SETUP"
        )
    else:
        # Proceed with installation only if mode is not 'api'
        browser_installed = install_playwright()

    run_migration()
    # TODO: Will be added in the future
    # setup_builtin_browser()
    if not browser_installed:
        logger.error(
            "Setup did not finish: the browser is not installed. "
            "Run the command above, then 'crawl4ai-doctor' to check.",
            tag="SETUP",
        )
        sys.exit(1)
    logger.success("Post-installation setup completed!", tag="COMPLETE")
    try:
        from .cloud_notice import show_at_install

        show_at_install(logger)
    except Exception:
        pass

def setup_builtin_browser():
    """Set up a builtin browser for use with Crawl4AI"""
    try:
        logger.info("Setting up builtin browser...", tag="INIT")
        asyncio.run(_setup_builtin_browser())
        logger.success("Builtin browser setup completed!", tag="COMPLETE")
    except Exception as e:
        logger.warning(f"Failed to set up builtin browser: {e}")
        logger.warning("You can manually set up a builtin browser using 'crawl4ai-doctor builtin-browser-start'")
    
async def _setup_builtin_browser():
    try:
        # Import BrowserProfiler here to avoid circular imports
        from .browser_profiler import BrowserProfiler
        profiler = BrowserProfiler(logger=logger)
        
        # Launch the builtin browser
        cdp_url = await profiler.launch_builtin_browser(headless=True)
        if cdp_url:
            logger.success(f"Builtin browser launched at {cdp_url}", tag="BROWSER")
        else:
            logger.warning("Failed to launch builtin browser", tag="BROWSER")
    except Exception as e:
        logger.warning(f"Error setting up builtin browser: {e}", tag="BROWSER")
        raise


def _run_install(command: list) -> str:
    """Run one install command. Returns "" when it worked, otherwise the reason it failed."""
    try:
        subprocess.check_call(command)
        return ""
    except subprocess.CalledProcessError as e:
        return f"exit code {e.returncode}"
    except Exception as e:
        return str(e)


def _install_chromium(tool: str) -> bool:
    """Install Chromium with ``tool`` ("playwright" or "patchright"). Returns True when the browser is installed.

    1. Try with ``--with-deps``, which also installs the system libraries. On Linux that needs root.
    2. If that fails, install the browser alone, and print the command for the system libraries.
    3. If that fails too, print the command to run by hand.
    """
    install = [sys.executable, "-m", tool, "install"]
    reason = _run_install(install + ["--with-deps", "--force", "chromium"])
    if not reason:
        logger.success(f"{tool} Chromium installed.", tag="COMPLETE")
        return True
    logger.warning(
        f"'{tool} install --with-deps chromium' failed ({reason}); the error is printed above. "
        "Trying the browser alone, without the system libraries...",
        tag="SETUP",
    )

    # ---- 2. The browser alone needs no root; only the system libraries do
    reason = _run_install(install + ["--force", "chromium"])
    if not reason:
        logger.warning(f"{tool} Chromium installed, but its system libraries may be missing.", tag="SETUP")
        if sys.platform.startswith("linux"):
            logger.warning(
                f"If the browser does not start, run: sudo {sys.executable} -m {tool} install-deps chromium",
                tag="SETUP",
            )
        return True

    # ---- 3. Nothing worked: the user runs it by hand
    logger.error(f"'{tool} install chromium' failed ({reason}); the error is printed above.", tag="SETUP")
    logger.error(f"Install it by hand: {sys.executable} -m {tool} install --with-deps chromium", tag="SETUP")
    if sys.platform.startswith("linux"):
        logger.error("Installing the system libraries needs root: run the command with sudo.", tag="SETUP")
    return False


def install_playwright() -> bool:
    """Install the Playwright and Patchright browsers. Returns True when the Playwright browser is installed.
    Patchright only serves the undetected mode, so its failure is a warning."""
    logger.info("Installing Playwright browsers...", tag="INIT")
    playwright_installed = _install_chromium("playwright")

    # Install Patchright browsers for undetected browser support
    logger.info("Installing Patchright browsers for undetected mode...", tag="INIT")
    if not _install_chromium("patchright"):
        logger.warning("Only the undetected browser mode needs Patchright; everything else works without it.", tag="SETUP")
    return playwright_installed


def run_migration():
    """Initialize database during installation"""
    try:
        logger.info("Starting database initialization...", tag="INIT")
        from crawl4ai.async_database import async_db_manager

        asyncio.run(async_db_manager.initialize())
        logger.success(
            "Database initialization completed successfully.", tag="COMPLETE"
        )
    except ImportError:
        logger.warning("Database module not found. Will initialize on first use.")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Database will be initialized on first use")


async def run_doctor():
    """Test if Crawl4AI is working properly"""
    logger.info("Running Crawl4AI health check...", tag="INIT")
    try:
        from .async_webcrawler import (
            AsyncWebCrawler,
            BrowserConfig,
            CrawlerRunConfig,
            CacheMode,
        )

        browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            ignore_https_errors=True,
            light_mode=True,
            viewport_width=1280,
            viewport_height=720,
        )

        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            screenshot=True,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            logger.info("Testing crawling capabilities...", tag="TEST")
            result = await crawler.arun(url="https://crawl4ai.com", config=run_config)

            if result and result.success and result.markdown:
                logger.success("✅ Crawling test passed!", tag="COMPLETE")
                return True
            else:
                raise Exception(f"Failed to get content: {getattr(result, 'error_message', None) or 'empty page'}")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", tag="ERROR")
        return False


def doctor():
    """Entry point for the doctor command. Exits with code 1 when the test crawl fails."""
    import asyncio

    # The doctor checks the installation; a cloud banner here would read as "the library is broken, go hosted"
    from .cloud_notice import _ENV_OFF

    os.environ[_ENV_OFF] = "1"
    passed = asyncio.run(run_doctor())
    sys.exit(0 if passed else 1)
