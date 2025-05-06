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
    """
    logger.info("Running post-installation setup...", tag="INIT")
    setup_home_directory()

    # Check environment variable to conditionally skip Playwright install
    run_mode = os.getenv('CRAWL4AI_MODE')
    if run_mode == 'api':
        logger.warning(
            "CRAWL4AI_MODE=api detected. Skipping Playwright browser installation.",
            tag="SETUP"
        )
    else:
        # Proceed with installation only if mode is not 'api'
        install_playwright()

    run_migration()
    # TODO: Will be added in the future
    # setup_builtin_browser()
    logger.success("Post-installation setup completed!", tag="COMPLETE")
    
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


def install_playwright():
    logger.info("Installing Playwright browsers...", tag="INIT")
    try:
        # subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps", "--force", "chrome"])
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "playwright",
                "install",
                "--with-deps",
                "--force",
                "chromium",
            ]
        )
        logger.success(
            "Playwright installation completed successfully.", tag="COMPLETE"
        )
    except subprocess.CalledProcessError:
        # logger.error(f"Error during Playwright installation: {e}", tag="ERROR")
        logger.warning(
            f"Please run '{sys.executable} -m playwright install --with-deps' manually after the installation."
        )
    except Exception:
        # logger.error(f"Unexpected error during Playwright installation: {e}", tag="ERROR")
        logger.warning(
            f"Please run '{sys.executable} -m playwright install --with-deps' manually after the installation."
        )


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

            if result and result.markdown:
                logger.success("✅ Crawling test passed!", tag="COMPLETE")
                return True
            else:
                raise Exception("Failed to get content")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", tag="ERROR")
        return False


def doctor():
    """Entry point for the doctor command"""
    import asyncio

    asyncio.run(run_doctor())
    sys.exit(0)
