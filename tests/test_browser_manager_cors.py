import os
import sys
import pytest

# Add the parent directory to the Python path
parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(parent_dir)

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


@pytest.mark.asyncio
async def test_normal_browser_launch():
    """Test that the browser manager launches normally without --disable-web-security"""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", bypass_cache=True)
        assert result.success
        assert result.html
        assert result.markdown


@pytest.mark.asyncio
async def test_cors_bypass_with_disable_web_security():
    """Test that --disable-web-security allows XMLHttpRequest to bypass CORS"""
    browser_config = BrowserConfig(
        extra_args=['--disable-web-security'],
        headless=True  # Run headless for test
    )

    # JS code that attempts XMLHttpRequest to a cross-origin URL that normally blocks CORS
    js_code = """
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'https://raw.githubusercontent.com/tatsu-lab/alpaca_eval/main/docs/data_AlpacaEval_2/weighted_alpaca_eval_gpt4_turbo_leaderboard.csv', false);
    xhr.send();
    if (xhr.status == 200) {
        return {success: true, length: xhr.responseText.length};
    } else {
        return {success: false, status: xhr.status, error: xhr.statusText};
    }
    """

    crawler_config = CrawlerRunConfig(js_code=js_code)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=crawler_config, bypass_cache=True)
        assert result.success, f"Crawl failed: {result.error_message}"
        js_result = result.js_execution_result
        assert js_result is not None, "JS execution result is None"
        assert js_result.get('success') == True, f"XMLHttpRequest failed: {js_result}"
        # The result is wrapped in 'results' list
        results = js_result.get('results', [])
        assert len(results) > 0, "No results in JS execution"
        xhr_result = results[0]
        assert xhr_result.get('success') == True, f"XMLHttpRequest failed: {xhr_result}"
        assert xhr_result.get('length', 0) > 0, f"No data received from XMLHttpRequest: {xhr_result}"


@pytest.mark.asyncio
async def test_browser_manager_without_cors_flag():
    """Ensure that without --disable-web-security, normal functionality still works"""
    browser_config = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", bypass_cache=True)
        assert result.success
        assert result.html


# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])