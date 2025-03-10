import modal
from typing import Optional, Dict, Any

# Create a custom image with Crawl4ai and its dependencies
# "pip install crawl4ai",
image = modal.Image.debian_slim(python_version="3.10").pip_install(["fastapi[standard]"]).run_commands(
    "apt-get update",
    "apt-get install -y software-properties-common",
    "apt-get install -y git",
    "apt-add-repository non-free",
    "apt-add-repository contrib",
    "pip install -U git+https://github.com/unclecode/crawl4ai.git@next",
    "pip install -U fastapi[standard]",
    "pip install -U pydantic",
    "crawl4ai-setup",  # This installs playwright and downloads chromium
    # Print fastpi version
    "python -m fastapi --version",
)

# Define the app
app = modal.App("crawl4ai", image=image)

# Define default configurations
DEFAULT_BROWSER_CONFIG = {
    "headless": True,
    "verbose": False,
}

DEFAULT_CRAWLER_CONFIG = {
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "markdown_generator": {
                "type": "DefaultMarkdownGenerator",
                "params": {
                    "content_filter": {
                        "type": "PruningContentFilter",
                        "params": {
                            "threshold": 0.48,
                            "threshold_type": "fixed"
                        }
                    }
                }
            }
        }
    }
}

@app.function(timeout=300)  # 5 minute timeout
async def crawl(
    url: str,
    browser_config: Optional[Dict[str, Any]] = None,
    crawler_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Crawl a given URL using Crawl4ai.
    
    Args:
        url: The URL to crawl
        browser_config: Optional browser configuration to override defaults
        crawler_config: Optional crawler configuration to override defaults
        
    Returns:
        A dictionary containing the crawl results
    """
    from crawl4ai import (
        AsyncWebCrawler,
        BrowserConfig,
        CrawlerRunConfig,
        CrawlResult
    )


    # Prepare browser config using the loader method
    if browser_config is None:
        browser_config = DEFAULT_BROWSER_CONFIG
    browser_config_obj = BrowserConfig.load(browser_config)
    
    # Prepare crawler config using the loader method
    if crawler_config is None:
        crawler_config = DEFAULT_CRAWLER_CONFIG
    crawler_config_obj = CrawlerRunConfig.load(crawler_config)    
    
    
    # Perform the crawl
    async with AsyncWebCrawler(config=browser_config_obj) as crawler:
        result: CrawlResult = await crawler.arun(url=url, config=crawler_config_obj)
        
        # Return serializable results
        try:
            # Try newer Pydantic v2 method
            return result.model_dump()
        except AttributeError:
            try:
                # Try older Pydantic v1 method
                return result.__dict__
            except AttributeError:
                # Fallback to returning the raw result
                return result

@app.function()
@modal.web_endpoint(method="POST")
def crawl_endpoint(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Web endpoint that accepts POST requests with JSON data containing:
    - url: The URL to crawl
    - browser_config: Optional browser configuration
    - crawler_config: Optional crawler configuration
    
    Returns the crawl results.
    """
    url = data.get("url")
    if not url:
        return {"error": "URL is required"}
    
    browser_config = data.get("browser_config")
    crawler_config = data.get("crawler_config")
    
    return crawl.remote(url, browser_config, crawler_config)

@app.local_entrypoint()
def main(url: str = "https://www.modal.com"):
    """
    Command line entrypoint for local testing.
    """
    result = crawl.remote(url)
    print(result)
