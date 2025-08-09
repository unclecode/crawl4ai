"""
Test config selection logic in dispatchers
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawl4ai.async_configs import CrawlerRunConfig, MatchMode
from crawl4ai.async_dispatcher import BaseDispatcher, MemoryAdaptiveDispatcher

class TestDispatcher(BaseDispatcher):
    """Simple test dispatcher to verify config selection"""
    
    async def crawl_url(self, url, config, task_id, **kwargs):
        # Just return which config was selected
        selected = self.select_config(url, config)
        return {"url": url, "config_id": id(selected)}
    
    async def run_urls(self, urls, crawler, config):
        results = []
        for url in urls:
            result = await self.crawl_url(url, config, "test")
            results.append(result)
        return results

async def test_dispatcher_config_selection():
    print("Testing dispatcher config selection")
    print("=" * 50)
    
    # Create test configs with different matchers
    pdf_config = CrawlerRunConfig(url_matcher="*.pdf")
    api_config = CrawlerRunConfig(url_matcher=lambda url: 'api' in url)
    default_config = CrawlerRunConfig()  # No matcher
    
    configs = [pdf_config, api_config, default_config]
    
    # Create test dispatcher
    dispatcher = TestDispatcher()
    
    # Test single config
    print("\nTest 1: Single config")
    result = await dispatcher.crawl_url("https://example.com/file.pdf", pdf_config, "test1")
    assert result["config_id"] == id(pdf_config)
    print("✓ Single config works")
    
    # Test config list selection
    print("\nTest 2: Config list selection")
    test_cases = [
        ("https://example.com/file.pdf", id(pdf_config)),
        ("https://api.example.com/data", id(api_config)),
        ("https://example.com/page", id(configs[0])),  # No match, uses first
    ]
    
    for url, expected_id in test_cases:
        result = await dispatcher.crawl_url(url, configs, "test")
        assert result["config_id"] == expected_id, f"URL {url} got wrong config"
        print(f"✓ {url} -> correct config selected")
    
    # Test with MemoryAdaptiveDispatcher
    print("\nTest 3: MemoryAdaptiveDispatcher config selection")
    mem_dispatcher = MemoryAdaptiveDispatcher()
    
    # Test select_config method directly
    selected = mem_dispatcher.select_config("https://example.com/doc.pdf", configs)
    assert selected == pdf_config
    print("✓ MemoryAdaptiveDispatcher.select_config works")
    
    # Test empty config list
    print("\nTest 4: Edge cases")
    selected = mem_dispatcher.select_config("https://example.com", [])
    assert isinstance(selected, CrawlerRunConfig)  # Should return default
    print("✓ Empty config list returns default config")
    
    # Test None config
    selected = mem_dispatcher.select_config("https://example.com", None)
    assert isinstance(selected, CrawlerRunConfig)  # Should return default
    print("✓ None config returns default config")
    
    print("\n" + "=" * 50)
    print("All dispatcher tests passed! ✓")

if __name__ == "__main__":
    asyncio.run(test_dispatcher_config_selection())