"""
Identity-Based Browsing Example with Crawl4AI

This example demonstrates how to:
1. Create a persistent browser profile interactively
2. List available profiles
3. Use a saved profile for crawling authenticated sites
4. Delete profiles when no longer needed

Uses the new BrowserProfiler class for profile management.
"""

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.browser_profiler import BrowserProfiler
from crawl4ai.async_logger import AsyncLogger
from colorama import Fore, Style, init

# Initialize colorama
init()

# Create a shared logger instance
logger = AsyncLogger(verbose=True)

# Create a shared BrowserProfiler instance
profiler = BrowserProfiler(logger=logger)


async def crawl_with_profile(profile_path, url):
    """Use a profile to crawl an authenticated page"""
    logger.info(f"\nCrawling {Fore.CYAN}{url}{Style.RESET_ALL} using profile at {Fore.YELLOW}{profile_path}{Style.RESET_ALL}", tag="CRAWL")
    
    # Create browser config with the profile path
    browser_config = BrowserConfig(
        headless=False,  # Set to False if you want to see the browser window
        use_managed_browser=True,  # Required for persistent profiles
        user_data_dir=profile_path
    )
    
    start_time = asyncio.get_event_loop().time()
    
    # Initialize crawler with the browser config
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Crawl the URL - You should have access to authenticated content now
        result = await crawler.arun(url)
        
        elapsed_time = asyncio.get_event_loop().time() - start_time
        
        if result.success:
            # Use url_status method for consistent logging
            logger.url_status(url, True, elapsed_time, tag="CRAWL")
            
            # Print page title or some indication of success
            title = result.metadata.get("title", "")
            logger.success(f"Page title: {Fore.GREEN}{title}{Style.RESET_ALL}", tag="CRAWL")
            return result
        else:
            # Log error status
            logger.error_status(url, result.error_message, tag="CRAWL")
            return None


async def main():
    logger.info(f"{Fore.CYAN}Identity-Based Browsing Example with Crawl4AI{Style.RESET_ALL}", tag="DEMO")
    logger.info("This example demonstrates using profiles for authenticated browsing", tag="DEMO")
    
    # Choose between interactive mode and automatic mode
    mode = input(f"{Fore.CYAN}Run in [i]nteractive mode or [a]utomatic mode? (i/a): {Style.RESET_ALL}").lower()
    
    if mode == 'i':
        # Interactive profile management - use the interactive_manager method
        # Pass the crawl_with_profile function as the callback for the "crawl a website" option
        await profiler.interactive_manager(crawl_callback=crawl_with_profile)
    else:
        # Automatic mode - simplified example
        profiles = profiler.list_profiles()
        
        if not profiles:
            # Create a new profile if none exists
            logger.info("No profiles found. Creating a new one...", tag="DEMO")
            profile_path = await profiler.create_profile()
            if not profile_path:
                logger.error("Cannot proceed without a valid profile", tag="DEMO")
                return
        else:
            # Use the first (most recent) profile
            profile_path = profiles[0]["path"]
            logger.info(f"Using existing profile: {Fore.CYAN}{profiles[0]['name']}{Style.RESET_ALL}", tag="DEMO")
        
        # Example: Crawl an authenticated page
        urls_to_crawl = [
            "https://github.com/settings/profile",  # GitHub requires login
            # "https://twitter.com/home",  # Twitter requires login
            # "https://www.linkedin.com/feed/",  # LinkedIn requires login
        ]
        
        for url in urls_to_crawl:
            await crawl_with_profile(profile_path, url)


if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Example interrupted by user", tag="DEMO")
    except Exception as e:
        logger.error(f"Error in example: {str(e)}", tag="DEMO")