import json
import asyncio
import os

# Ensure environment variables and directories are set
os.environ['CRAWL4_AI_BASE_DIRECTORY'] = '/tmp/.crawl4ai'
os.environ['HOME'] = '/tmp'

# Create directory if it doesn't exist
os.makedirs('/tmp/.crawl4ai', exist_ok=True)

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)


def handler(event, context):
    # Parse the incoming event (API Gateway request)
    try:
        body = json.loads(event.get('body', '{}'))
        
        url = body.get('url')
        if not url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'URL is required'})
            }
        
        # Get optional configurations or use defaults
        browser_config_dict = body.get('browser_config', {})
        crawler_config_dict = body.get('crawler_config', {})
        
        # Run the crawler
        result = asyncio.run(crawl(url, browser_config_dict, crawler_config_dict))
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }
    
    except Exception as e:
        # Handle errors
        import traceback
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        }

async def crawl(url, browser_config_dict, crawler_config_dict):
    """
    Run the crawler with the provided configurations, with Lambda-specific settings
    """
    # Start with user-provided config but override with Lambda-required settings
    base_browser_config = BrowserConfig.load(browser_config_dict) if browser_config_dict else BrowserConfig()
    
    # Apply Lambda-specific browser configurations
    browser_config = BrowserConfig(
        verbose=True,
        browser_type="chromium",
        headless=True,
        user_agent_mode="random",
        light_mode=True,
        use_managed_browser=False,
        extra_args=[
            "--headless=new",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--remote-allow-origins=*",
            "--autoplay-policy=user-gesture-required",
            "--single-process",            
        ],
        # # Carry over any other settings from user config that aren't overridden
        # **{k: v for k, v in base_browser_config.model_dump().items() 
        #    if k not in ['verbose', 'browser_type', 'headless', 'user_agent_mode', 
        #                'light_mode', 'use_managed_browser', 'extra_args']}
    )
    
    # Start with user-provided crawler config but ensure cache is bypassed
    base_crawler_config = CrawlerRunConfig.load(crawler_config_dict) if crawler_config_dict else CrawlerRunConfig()
    
    # Apply Lambda-specific crawler configurations
    crawler_config = CrawlerRunConfig(
        exclude_external_links=base_crawler_config.exclude_external_links,
        remove_overlay_elements=True,
        magic=True,
        cache_mode=CacheMode.BYPASS,
        # Carry over markdown generator and other settings
        markdown_generator=base_crawler_config.markdown_generator
    )
    
    # Perform the crawl with Lambda-optimized settings
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)
        
        # Return serializable results
        return result.model_dump()