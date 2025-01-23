import pytest
import pytest_asyncio
import asyncio
from typing import Dict, Any
from pathlib import Path
from unittest.mock import MagicMock, patch
import os
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.models import AsyncCrawlResponse
from crawl4ai.async_logger import AsyncLogger, LogLevel

CRAWL4AI_HOME_DIR = Path(os.path.expanduser("~")).joinpath(".crawl4ai")

if not CRAWL4AI_HOME_DIR.joinpath("profiles", "test_profile").exists():
    CRAWL4AI_HOME_DIR.joinpath("profiles", "test_profile").mkdir(parents=True)

# Test Config Files
@pytest.fixture
def basic_browser_config():
    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True
    )

@pytest.fixture
def advanced_browser_config():
    return BrowserConfig(
        browser_type="chromium", 
        headless=True,
        use_managed_browser=True,
        user_data_dir=CRAWL4AI_HOME_DIR.joinpath("profiles", "test_profile"),
        # proxy="http://localhost:8080",
        viewport_width=1920,
        viewport_height=1080,
        user_agent_mode="random"
    )

@pytest.fixture
def basic_crawler_config():
    return CrawlerRunConfig(
        word_count_threshold=100,
        wait_until="domcontentloaded",
        page_timeout=30000
    )

@pytest.fixture
def logger():
    return AsyncLogger(verbose=True, log_level=LogLevel.DEBUG)

@pytest_asyncio.fixture
async def crawler_strategy(basic_browser_config, logger):
    strategy = AsyncPlaywrightCrawlerStrategy(browser_config=basic_browser_config, logger=logger)
    await strategy.start()
    yield strategy
    await strategy.close()

# Browser Configuration Tests
@pytest.mark.asyncio
async def test_browser_config_initialization():
    config = BrowserConfig(
        browser_type="chromium",
        user_agent_mode="random"
    )
    assert config.browser_type == "chromium"
    assert config.user_agent is not None
    assert config.headless is True

@pytest.mark.asyncio 
async def test_persistent_browser_config():
    config = BrowserConfig(
        use_persistent_context=True,
        user_data_dir="/tmp/test_dir"
    )
    assert config.use_managed_browser is True
    assert config.user_data_dir == "/tmp/test_dir"

# Crawler Strategy Tests
@pytest.mark.asyncio
async def test_basic_page_load(crawler_strategy):
    response = await crawler_strategy.crawl(
        "https://example.com",
        CrawlerRunConfig()
    )
    assert response.status_code == 200
    assert len(response.html) > 0
    assert "Example Domain" in response.html

@pytest.mark.asyncio
async def test_screenshot_capture(crawler_strategy):
    config = CrawlerRunConfig(screenshot=True)
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.screenshot is not None
    assert len(response.screenshot) > 0

@pytest.mark.asyncio
async def test_pdf_generation(crawler_strategy):
    config = CrawlerRunConfig(pdf=True)
    response = await crawler_strategy.crawl(
        "https://example.com", 
        config
    )
    assert response.pdf_data is not None
    assert len(response.pdf_data) > 0

@pytest.mark.asyncio
async def test_handle_js_execution(crawler_strategy):
    config = CrawlerRunConfig(
        js_code="document.body.style.backgroundColor = 'red';"
    )
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.status_code == 200
    assert 'background-color: red' in response.html.lower()

@pytest.mark.asyncio
async def test_multiple_js_commands(crawler_strategy):
    js_commands = [
        "document.body.style.backgroundColor = 'blue';",
        "document.title = 'Modified Title';",
        "const div = document.createElement('div'); div.id = 'test'; div.textContent = 'Test Content'; document.body.appendChild(div);"
    ]
    config = CrawlerRunConfig(js_code=js_commands)
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.status_code == 200
    assert 'background-color: blue' in response.html.lower()
    assert 'id="test"' in response.html
    assert '>Test Content<' in response.html
    assert '<title>Modified Title</title>' in response.html

@pytest.mark.asyncio
async def test_complex_dom_manipulation(crawler_strategy):
    js_code = """
    // Create a complex structure
    const container = document.createElement('div');
    container.className = 'test-container';
    
    const list = document.createElement('ul');
    list.className = 'test-list';
    
    for (let i = 1; i <= 3; i++) {
        const item = document.createElement('li');
        item.textContent = `Item ${i}`;
        item.className = `item-${i}`;
        list.appendChild(item);
    }
    
    container.appendChild(list);
    document.body.appendChild(container);
    """
    config = CrawlerRunConfig(js_code=js_code)
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.status_code == 200
    assert 'class="test-container"' in response.html
    assert 'class="test-list"' in response.html
    assert 'class="item-1"' in response.html
    assert '>Item 1<' in response.html
    assert '>Item 2<' in response.html
    assert '>Item 3<' in response.html

@pytest.mark.asyncio
async def test_style_modifications(crawler_strategy):
    js_code = """
    const testDiv = document.createElement('div');
    testDiv.id = 'style-test';
    testDiv.style.cssText = 'color: green; font-size: 20px; margin: 10px;';
    testDiv.textContent = 'Styled Content';
    document.body.appendChild(testDiv);
    """
    config = CrawlerRunConfig(js_code=js_code)
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.status_code == 200
    assert 'id="style-test"' in response.html
    assert 'color: green' in response.html.lower()
    assert 'font-size: 20px' in response.html.lower()
    assert 'margin: 10px' in response.html.lower()
    assert '>Styled Content<' in response.html

@pytest.mark.asyncio
async def test_dynamic_content_loading(crawler_strategy):
    js_code = """
    // Simulate dynamic content loading
    setTimeout(() => {
        const dynamic = document.createElement('div');
        dynamic.id = 'dynamic-content';
        dynamic.textContent = 'Dynamically Loaded';
        document.body.appendChild(dynamic);
    }, 1000);
    
    // Add a loading indicator immediately
    const loading = document.createElement('div');
    loading.id = 'loading';
    loading.textContent = 'Loading...';
    document.body.appendChild(loading);
    """
    config = CrawlerRunConfig(js_code=js_code, delay_before_return_html=2.0)
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.status_code == 200
    assert 'id="loading"' in response.html
    assert '>Loading...</' in response.html
    assert 'dynamic-content' in response.html
    assert '>Dynamically Loaded<' in response.html

# @pytest.mark.asyncio
# async def test_js_return_values(crawler_strategy):
#     js_code = """
#     return {
#         title: document.title,
#         metaCount: document.getElementsByTagName('meta').length,
#         bodyClass: document.body.className
#     };
#     """
#     config = CrawlerRunConfig(js_code=js_code)
#     response = await crawler_strategy.crawl(
#         "https://example.com",
#         config
#     )
#     assert response.status_code == 200
#     assert 'Example Domain' in response.html
#     assert 'meta name="viewport"' in response.html
#     assert 'class="main"' in response.html

@pytest.mark.asyncio
async def test_async_js_execution(crawler_strategy):
    js_code = """
    await new Promise(resolve => setTimeout(resolve, 1000));
    document.body.style.color = 'green';
    const computedStyle = window.getComputedStyle(document.body);
    return computedStyle.color;
    """
    config = CrawlerRunConfig(js_code=js_code)
    response = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response.status_code == 200
    assert 'color: green' in response.html.lower()

# @pytest.mark.asyncio
# async def test_js_error_handling(crawler_strategy):
#     js_code = """
#     // Intentionally cause different types of errors
#     const results = [];
#     try {
#         nonExistentFunction();
#     } catch (e) {
#         results.push(e.name);
#     }
#     try {
#         JSON.parse('{invalid}');
#     } catch (e) {
#         results.push(e.name);
#     }
#     return results;
#     """
#     config = CrawlerRunConfig(js_code=js_code)
#     response = await crawler_strategy.crawl(
#         "https://example.com",
#         config
#     )
#     assert response.status_code == 200
#     assert 'ReferenceError' in response.html
#     assert 'SyntaxError' in response.html

@pytest.mark.asyncio
async def test_handle_navigation_timeout():
    config = CrawlerRunConfig(page_timeout=1)  # 1ms timeout
    with pytest.raises(Exception):
        async with AsyncPlaywrightCrawlerStrategy() as strategy:
            await strategy.crawl("https://example.com", config)

@pytest.mark.asyncio
async def test_session_management(crawler_strategy):
    config = CrawlerRunConfig(session_id="test_session")
    response1 = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    response2 = await crawler_strategy.crawl(
        "https://example.com",
        config
    )
    assert response1.status_code == 200
    assert response2.status_code == 200

@pytest.mark.asyncio
async def test_process_iframes(crawler_strategy):
    config = CrawlerRunConfig(
        process_iframes=True,
        wait_for_images=True
    )
    response = await crawler_strategy.crawl(
        "https://example.com",
        config  
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_stealth_mode(crawler_strategy):
    config = CrawlerRunConfig(
        simulate_user=True,
        override_navigator=True
    )
    response = await crawler_strategy.crawl(
        "https://bot.sannysoft.com",
        config
    )
    assert response.status_code == 200

# Error Handling Tests  
@pytest.mark.asyncio
async def test_invalid_url():
    with pytest.raises(ValueError):
        async with AsyncPlaywrightCrawlerStrategy() as strategy:
            await strategy.crawl("not_a_url", CrawlerRunConfig())

@pytest.mark.asyncio 
async def test_network_error_handling():
    config = CrawlerRunConfig()
    with pytest.raises(Exception):
        async with AsyncPlaywrightCrawlerStrategy() as strategy:
            await strategy.crawl("https://invalid.example.com", config)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])