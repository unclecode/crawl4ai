import subprocess
import sys
import asyncio
from .async_logger import AsyncLogger, LogLevel

# Initialize logger
logger = AsyncLogger(log_level=LogLevel.DEBUG, verbose=True)


def post_install():
    """Run all post-installation tasks"""
    logger.info("Running post-installation setup...", tag="INIT")
    install_playwright()
    run_migration()
    logger.success("Post-installation setup completed!", tag="COMPLETE")


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

    return asyncio.run(run_doctor())
