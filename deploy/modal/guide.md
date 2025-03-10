# Deploying Crawl4ai with Modal: A Comprehensive Tutorial

Hey there! UncleCode here. I'm excited to show you how to deploy Crawl4ai using Modal - a fantastic serverless platform that makes deployment super simple and scalable.

In this tutorial, I'll walk you through deploying your own Crawl4ai instance on Modal's infrastructure. This will give you a powerful, scalable web crawling solution without having to worry about infrastructure management.

## What is Modal?

Modal is a serverless platform that allows you to run Python functions in the cloud without managing servers. It's perfect for deploying Crawl4ai because:

1. It handles all the infrastructure for you
2. It scales automatically based on demand
3. It makes deployment incredibly simple

## Prerequisites

Before we get started, you'll need:

- A Modal account (sign up at [modal.com](https://modal.com))
- Python 3.10 or later installed on your local machine
- Basic familiarity with Python and command-line operations

## Step 1: Setting Up Your Modal Account

First, sign up for a Modal account at [modal.com](https://modal.com) if you haven't already. Modal offers a generous free tier that's perfect for getting started.

After signing up, install the Modal CLI and authenticate:

```bash
pip install modal
modal token new
```

This will open a browser window where you can authenticate and generate a token for the CLI.

## Step 2: Creating Your Crawl4ai Deployment

Now, let's create a Python file called `crawl4ai_modal.py` with our deployment code:

```python
import modal
from typing import Optional, Dict, Any

# Create a custom image with Crawl4ai and its dependencies
image = modal.Image.debian_slim(python_version="3.10").pip_install(
    ["fastapi[standard]"]
).run_commands(
    "apt-get update",
    "apt-get install -y software-properties-common",
    "apt-get install -y git",
    "apt-add-repository non-free",
    "apt-add-repository contrib",
    "pip install -U crawl4ai",
    "pip install -U fastapi[standard]",
    "pip install -U pydantic",
    "crawl4ai-setup",  # This installs playwright and downloads chromium
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
                return result.dict()
            except AttributeError:
                # Fallback to manual conversion
                return {
                    "url": result.url,
                    "title": result.title,
                    "status": result.status,
                    "content": str(result.content) if hasattr(result, "content") else None,
                    "links": [{"url": link.url, "text": link.text} for link in result.links] if hasattr(result, "links") else [],
                    "markdown_v2": {
                        "raw_markdown": result.markdown_v2.raw_markdown if hasattr(result, "markdown_v2") else None
                    }
                }

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
```

## Step 3: Understanding the Code Components

Let's break down what's happening in this code:

### 1. Image Definition

```python
image = modal.Image.debian_slim(python_version="3.10").pip_install(
    ["fastapi[standard]"]
).run_commands(
    "apt-get update",
    "apt-get install -y software-properties-common",
    "apt-get install -y git",
    "apt-add-repository non-free",
    "apt-add-repository contrib",
    "pip install -U git+https://github.com/unclecode/crawl4ai.git@next",
    "pip install -U fastapi[standard]",
    "pip install -U pydantic",
    "crawl4ai-setup",  # This installs playwright and downloads chromium
)
```

This section defines the container image that Modal will use to run your code. It:
- Starts with a Debian Slim base image with Python 3.10
- Installs FastAPI
- Updates the system packages
- Installs Git and other dependencies
- Installs Crawl4ai from the GitHub repository
- Runs the Crawl4ai setup to install Playwright and download Chromium

### 2. Modal App Definition

```python
app = modal.App("crawl4ai", image=image)
```

This creates a Modal application named "crawl4ai" that uses the image we defined above.

### 3. Default Configurations

```python
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
```

These define the default configurations for the browser and crawler. You can customize these settings based on your specific needs.

### 4. The Crawl Function

```python
@app.function(timeout=300)
async def crawl(url, browser_config, crawler_config):
    # Function implementation
```

This is the main function that performs the crawling. It:
- Takes a URL and optional configurations
- Sets up the browser and crawler with those configurations
- Performs the crawl
- Returns the results in a serializable format

The `@app.function(timeout=300)` decorator tells Modal to run this function in the cloud with a 5-minute timeout.

### 5. The Web Endpoint

```python
@app.function()
@modal.web_endpoint(method="POST")
def crawl_endpoint(data: Dict[str, Any]) -> Dict[str, Any]:
    # Function implementation
```

This creates a web endpoint that accepts POST requests. It:
- Extracts the URL and configurations from the request
- Calls the crawl function with those parameters
- Returns the results

### 6. Local Entrypoint

```python
@app.local_entrypoint()
def main(url: str = "https://www.modal.com"):
    # Function implementation
```

This provides a way to test the application from the command line.

## Step 4: Testing Locally

Before deploying, let's test our application locally:

```bash
modal run crawl4ai_modal.py --url "https://example.com"
```

This command will:
1. Upload your code to Modal
2. Create the necessary containers
3. Run the `main` function with the specified URL
4. Return the results

Modal will handle all the infrastructure setup for you. You should see the crawling results printed to your console.

## Step 5: Deploying Your Application

Once you're satisfied with the local testing, it's time to deploy:

```bash
modal deploy crawl4ai_modal.py
```

This will deploy your application to Modal's cloud. The deployment process will output URLs for your web endpoints.

You should see output similar to:

```
✓ Deployed crawl4ai.
  URLs:
    crawl_endpoint => https://your-username--crawl-endpoint.modal.run
```

Save this URL - you'll need it to make requests to your deployment.

## Step 6: Using Your Deployment

Now that your application is deployed, you can use it by sending POST requests to the endpoint URL:

```bash
curl -X POST https://your-username--crawl-endpoint.modal.run \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Or in Python:

```python
import requests

response = requests.post(
    "https://your-username--crawl-endpoint.modal.run",
    json={"url": "https://example.com"}
)

result = response.json()
print(result)
```

You can also customize the browser and crawler configurations:

```python
requests.post(
    "https://your-username--crawl-endpoint.modal.run",
    json={
        "url": "https://example.com",
        "browser_config": {
            "headless": False,
            "verbose": True
        },
        "crawler_config": {
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "markdown_generator": {
                        "type": "DefaultMarkdownGenerator",
                        "params": {
                            "content_filter": {
                                "type": "PruningContentFilter",
                                "params": {
                                    "threshold": 0.6,  # Adjusted threshold
                                    "threshold_type": "fixed"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
```

## Step 7: Calling Your Deployment from Another Python Script

You can also call your deployed function directly from another Python script:

```python
import modal

# Get a reference to the deployed function
crawl_function = modal.Function.from_name("crawl4ai", "crawl")

# Call the function
result = crawl_function.remote("https://example.com")
print(result)
```

## Understanding Modal's Execution Flow

To understand how Modal works, it's important to know:

1. **Local vs. Remote Execution**: When you call a function with `.remote()`, it runs in Modal's cloud, not on your local machine.

2. **Container Lifecycle**: Modal creates containers on-demand and destroys them when they're not needed.

3. **Caching**: Modal caches your container images to speed up subsequent runs.

4. **Serverless Scaling**: Modal automatically scales your application based on demand.

## Customizing Your Deployment

You can customize your deployment in several ways:

### Changing the Crawl4ai Version

To use a different version of Crawl4ai, update the installation command in the image definition:

```python
"pip install -U git+https://github.com/unclecode/crawl4ai.git@main",  # Use main branch
```

### Adjusting Resource Limits

You can change the resources allocated to your functions:

```python
@app.function(timeout=600, cpu=2, memory=4096)  # 10 minute timeout, 2 CPUs, 4GB RAM
async def crawl(...):
    # Function implementation
```

### Keeping Containers Warm

To reduce cold start times, you can keep containers warm:

```python
@app.function(keep_warm=1)  # Keep 1 container warm
async def crawl(...):
    # Function implementation
```

## Conclusion

That's it! You've successfully deployed Crawl4ai on Modal. You now have a scalable web crawling solution that can handle as many requests as you need without requiring any infrastructure management.

The beauty of this setup is its simplicity - Modal handles all the hard parts, letting you focus on using Crawl4ai to extract the data you need.

Feel free to reach out if you have any questions or need help with your deployment!

Happy crawling!
- UncleCode

## Additional Resources

- [Modal Documentation](https://modal.com/docs)
- [Crawl4ai GitHub Repository](https://github.com/unclecode/crawl4ai)
- [Crawl4ai Documentation](https://docs.crawl4ai.com)
