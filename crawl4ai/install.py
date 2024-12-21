import subprocess
import sys
import asyncio
from .async_logger import AsyncLogger, LogLevel
from .docs_manager import DocsManager

# Initialize logger
logger = AsyncLogger(log_level=LogLevel.DEBUG, verbose=True)

def post_install():
    """Run all post-installation tasks"""
    logger.info("Running post-installation setup...", tag="INIT")
    install_playwright()
    run_migration()
    asyncio.run(setup_docs())
    logger.success("Post-installation setup completed!", tag="COMPLETE")
    
def install_playwright():
    logger.info("Installing Playwright browsers...", tag="INIT")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        logger.success("Playwright installation completed successfully.", tag="COMPLETE")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during Playwright installation: {e}", tag="ERROR")
        logger.warning(
            "Please run 'python -m playwright install' manually after the installation."
        )
    except Exception as e:
        logger.error(f"Unexpected error during Playwright installation: {e}", tag="ERROR")
        logger.warning(
            "Please run 'python -m playwright install' manually after the installation."
        )

def run_migration():
    """Initialize database during installation"""
    try:
        logger.info("Starting database initialization...", tag="INIT")
        from crawl4ai.async_database import async_db_manager

        asyncio.run(async_db_manager.initialize())
        logger.success("Database initialization completed successfully.", tag="COMPLETE")
    except ImportError:
        logger.warning("Database module not found. Will initialize on first use.")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Database will be initialized on first use")

async def setup_docs():
    """Download documentation files"""
    docs_manager = DocsManager(logger)
    await docs_manager.update_docs()