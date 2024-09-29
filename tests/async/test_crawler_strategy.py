import os
import sys
import pytest
import asyncio

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

@pytest.mark.asyncio
async def test_custom_user_agent():
    async with AsyncWebCrawler(verbose=True) as crawler:
        custom_user_agent = "MyCustomUserAgent/1.0"
        crawler.crawler_strategy.update_user_agent(custom_user_agent)
        url = "https://httpbin.org/user-agent"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert custom_user_agent in result.html

@pytest.mark.asyncio
async def test_custom_headers():
    async with AsyncWebCrawler(verbose=True) as crawler:
        custom_headers = {"X-Test-Header": "TestValue"}
        crawler.crawler_strategy.set_custom_headers(custom_headers)
        url = "https://httpbin.org/headers"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert "X-Test-Header" in result.html
        assert "TestValue" in result.html

@pytest.mark.asyncio
async def test_javascript_execution():
    async with AsyncWebCrawler(verbose=True) as crawler:
        js_code = "document.body.innerHTML = '<h1>Modified by JS</h1>';"
        url = "https://www.example.com"
        result = await crawler.arun(url=url, bypass_cache=True, js_code=js_code)
        assert result.success
        assert "<h1>Modified by JS</h1>" in result.html

@pytest.mark.asyncio
async def test_hook_execution():
    async with AsyncWebCrawler(verbose=True) as crawler:
        async def test_hook(page):
            await page.evaluate("document.body.style.backgroundColor = 'red';")
            return page

        crawler.crawler_strategy.set_hook('after_goto', test_hook)
        url = "https://www.example.com"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert "background-color: red" in result.html

@pytest.mark.asyncio
async def test_response_inspection():
    responses = []

    async def log_response(response):
        responses.append({
            'url': response.url,
            'status': response.status,
            'headers': response.headers
        })

    async def on_page_created(page):
        page.on("response", log_response)
        return page

    crawler_strategy = AsyncPlaywrightCrawlerStrategy(verbose=True)
    crawler_strategy.set_hook("on_page_created", on_page_created)
    
    async with AsyncWebCrawler(verbose=True, crawler_strategy=crawler_strategy) as crawler:
        url = "https://httpbin.org/get"
        result = await crawler.arun(url=url, bypass_cache=True)
        
        assert result.success
        assert len(responses) > 0
        
        main_response = next((r for r in responses if r['url'] == url), None)
        assert main_response is not None
        assert main_response['status'] == 200
        assert 'content-type' in main_response['headers']
        assert main_response['headers']['content-type'] == 'application/json'

@pytest.mark.asyncio
async def test_screenshot():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.example.com"
        result = await crawler.arun(url=url, bypass_cache=True, screenshot=True)
        assert result.success
        assert result.screenshot
        assert isinstance(result.screenshot, str)
        assert len(result.screenshot) > 0

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])