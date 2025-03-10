# Cleanup Chrome process on module unload
import atexit
import asyncio
import logging
import functions_framework
from flask import jsonify, Request
import os
import sys
import time
import subprocess
import signal
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Python version: {sys.version}")
logger.info(f"Python path: {sys.path}")

# Try to find where crawl4ai is coming from
try:
    import crawl4ai
    logger.info(f"Crawl4AI module location: {crawl4ai.__file__}")
    logger.info(f"Contents of crawl4ai: {dir(crawl4ai)}")
except ImportError:
    logger.error("Crawl4AI module not found")

# Now attempt the import
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, CrawlResult

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Paths and constants
FUNCTION_DIR = os.path.dirname(os.path.realpath(__file__))
CHROME_BINARY = os.path.join(FUNCTION_DIR, "resources/chrome/headless_shell")
CDP_PORT = 9222

def start_chrome():
    """Start Chrome process synchronously with exponential backoff."""
    logger.debug("Starting Chrome process...")
    chrome_args = [
        CHROME_BINARY,
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-debugging-address=0.0.0.0",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--headless=new",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-zygote",
        "--single-process",
        "--disable-features=site-per-process",
        "--no-first-run",
        "--disable-extensions"
    ]
    
    process = subprocess.Popen(
        chrome_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    logger.debug(f"Chrome process started with PID: {process.pid}")
    
    # Wait for CDP endpoint with exponential backoff
    wait_time = 1  # Start with 1 second
    max_wait_time = 16  # Cap at 16 seconds per retry
    max_attempts = 10  # Total attempts
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=2)
            if response.status_code == 200:
                # Get ws URL from response
                ws_url = response.json()['webSocketDebuggerUrl']
                logger.debug("Chrome CDP is ready")
                logger.debug(f"CDP URL: {ws_url}")
                return process
        except requests.exceptions.ConnectionError:
            logger.debug(f"Waiting for CDP endpoint (attempt {attempt + 1}/{max_attempts}), retrying in {wait_time} seconds")
            time.sleep(wait_time)
            wait_time = min(wait_time * 2, max_wait_time)  # Double wait time, up to max
    
    # If we get here, all retries failed
    stdout, stderr = process.communicate()  # Get output for debugging
    logger.error(f"Chrome stdout: {stdout.decode()}")
    logger.error(f"Chrome stderr: {stderr.decode()}")
    raise Exception("Chrome CDP endpoint failed to start after retries")

async def fetch_with_crawl4ai(url: str) -> dict:
    """Fetch page content using Crawl4ai and return the result object"""
    # Get CDP URL from the running Chrome instance
    version_response = requests.get(f'http://localhost:{CDP_PORT}/json/version')
    cdp_url = version_response.json()['webSocketDebuggerUrl']
    
    # Configure and run Crawl4ai
    browser_config = BrowserConfig(cdp_url=cdp_url, use_managed_browser=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
        )
        result : CrawlResult = await crawler.arun(
            url=url, config=crawler_config
        )
        return result.model_dump()  # Convert Pydantic model to dict for JSON response

# Start Chrome when the module loads
logger.info("Starting Chrome process on module load")
chrome_process = start_chrome()

@functions_framework.http
def crawl(request: Request):
    """HTTP Cloud Function to fetch web content using Crawl4ai"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is required', 'status': 400}), 400
        
        # Create and run an asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                asyncio.wait_for(fetch_with_crawl4ai(url), timeout=10.0)
            )
            return jsonify({
                'status': 200,
                'data': result
            })
        finally:
            loop.close()
            
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'error': error_msg,
            'status': 500,
            'details': {
                'error_type': type(e).__name__,
                'stack_trace': str(e),
                'chrome_running': chrome_process.poll() is None if chrome_process else False
            }
        }), 500


@atexit.register
def cleanup():
    """Cleanup Chrome process on shutdown"""
    if chrome_process and chrome_process.poll() is None:
        try:
            os.killpg(os.getpgid(chrome_process.pid), signal.SIGTERM)
            logger.info("Chrome process terminated")
        except Exception as e:
            logger.error(f"Failed to terminate Chrome process: {e}")