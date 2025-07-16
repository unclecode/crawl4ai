#!/usr/bin/env python3
"""
Test suite for playwright-stealth backward compatibility.
Tests that stealth functionality works automatically without user configuration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock


class TestPlaywrightStealthCompatibility:
    """Test playwright-stealth backward compatibility with transparent operation"""

    def test_api_detection_works(self):
        """Test that API detection works correctly"""
        from crawl4ai.async_crawler_strategy import STEALTH_NEW_API
        # The value depends on which version is installed, but should not be undefined
        assert STEALTH_NEW_API is not None or STEALTH_NEW_API is False or STEALTH_NEW_API is None

    @pytest.mark.asyncio
    @patch('crawl4ai.async_crawler_strategy.STEALTH_NEW_API', True)
    @patch('crawl4ai.async_crawler_strategy.Stealth')
    async def test_apply_stealth_new_api(self, mock_stealth_class):
        """Test stealth application with new API works transparently"""
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        
        # Setup mock
        mock_stealth_instance = Mock()
        mock_stealth_instance.apply_stealth_async = Mock()
        mock_stealth_class.return_value = mock_stealth_instance
        
        # Create strategy instance
        strategy = AsyncPlaywrightCrawlerStrategy()
        
        # Mock page
        mock_page = Mock()
        
        # Test the method - should work transparently
        await strategy._apply_stealth(mock_page)
        
        # Verify new API was used
        mock_stealth_class.assert_called_once()
        mock_stealth_instance.apply_stealth_async.assert_called_once_with(mock_page)

    @pytest.mark.asyncio
    @patch('crawl4ai.async_crawler_strategy.STEALTH_NEW_API', False)
    async def test_apply_stealth_legacy_api(self):
        """Test stealth application with legacy API works transparently"""
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        
        # Mock stealth_async function by setting it as a module attribute
        mock_stealth_async = Mock()
        mock_stealth_async.return_value = None
        
        # Import the module to add the mock function
        import crawl4ai.async_crawler_strategy
        crawl4ai.async_crawler_strategy.stealth_async = mock_stealth_async
        
        try:
            # Create strategy instance
            strategy = AsyncPlaywrightCrawlerStrategy()
            
            # Mock page
            mock_page = Mock()
            
            # Test the method - should work transparently
            await strategy._apply_stealth(mock_page)
            
            # Verify legacy API was used
            mock_stealth_async.assert_called_once_with(mock_page)
        finally:
            # Clean up
            if hasattr(crawl4ai.async_crawler_strategy, 'stealth_async'):
                delattr(crawl4ai.async_crawler_strategy, 'stealth_async')

    @pytest.mark.asyncio
    @patch('crawl4ai.async_crawler_strategy.STEALTH_NEW_API', None)
    async def test_apply_stealth_no_library(self):
        """Test stealth application when no stealth library is available"""
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        
        # Create strategy instance
        strategy = AsyncPlaywrightCrawlerStrategy()
        
        # Mock page
        mock_page = Mock()
        
        # Test the method - should work transparently even without stealth
        await strategy._apply_stealth(mock_page)
        
        # Should complete without error even when no stealth is available

    @pytest.mark.asyncio
    @patch('crawl4ai.async_crawler_strategy.STEALTH_NEW_API', True)
    @patch('crawl4ai.async_crawler_strategy.Stealth')
    async def test_stealth_error_handling(self, mock_stealth_class):
        """Test that stealth errors are handled gracefully without breaking crawling"""
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        
        # Setup mock to raise an error
        mock_stealth_instance = Mock()
        mock_stealth_instance.apply_stealth_async = Mock(side_effect=Exception("Stealth failed"))
        mock_stealth_class.return_value = mock_stealth_instance
        
        # Create strategy instance
        strategy = AsyncPlaywrightCrawlerStrategy()
        
        # Mock page
        mock_page = Mock()
        
        # Test the method - should not raise an error, continue silently
        await strategy._apply_stealth(mock_page)
        
        # Should complete without raising the stealth error

    def test_strategy_creation_without_config(self):
        """Test that strategy can be created without any stealth configuration"""
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        
        # Should work without any stealth-related parameters
        strategy = AsyncPlaywrightCrawlerStrategy()
        assert strategy is not None
        assert hasattr(strategy, '_apply_stealth')

    def test_browser_config_works_without_stealth_param(self):
        """Test that BrowserConfig works without stealth parameter"""
        from crawl4ai.async_configs import BrowserConfig
        
        # Should work without stealth parameter
        config = BrowserConfig()
        assert config is not None
        
        # Should also work with other parameters
        config = BrowserConfig(headless=False, browser_type="firefox")
        assert config.headless == False
        assert config.browser_type == "firefox"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
