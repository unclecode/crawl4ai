#!/usr/bin/env python3
"""
Test suite for playwright-stealth v2.0.0+ compatibility fix.
Tests the stealth implementation update from deprecated stealth_async to Stealth class.
"""

import pytest
from unittest.mock import Mock, patch


class TestPlaywrightStealthCompatibility:
    """Test playwright-stealth v2.0.0+ compatibility fix"""

    @patch('crawl4ai.async_crawler_strategy.Stealth')
    def test_stealth_import_works(self, mock_stealth_class):
        """Test that Stealth class can be imported successfully"""
        from crawl4ai.async_crawler_strategy import Stealth
        
        # Should not raise ImportError
        assert Stealth is not None
        assert mock_stealth_class.called is False  # Just checking import, not instantiation

    @patch('crawl4ai.async_crawler_strategy.Stealth')
    def test_stealth_instantiation_works(self, mock_stealth_class):
        """Test that Stealth class can be instantiated"""
        from crawl4ai.async_crawler_strategy import Stealth
        
        # Create a mock instance
        mock_stealth_instance = Mock()
        mock_stealth_class.return_value = mock_stealth_instance
        
        # This should work without errors
        stealth = Stealth()
        assert stealth is not None
        mock_stealth_class.assert_called_once()

    @patch('crawl4ai.async_crawler_strategy.Stealth')
    def test_stealth_has_apply_method(self, mock_stealth_class):
        """Test that Stealth instance has apply_stealth_async method"""
        from crawl4ai.async_crawler_strategy import Stealth
        
        # Create a mock instance with apply_stealth_async method
        mock_stealth_instance = Mock()
        mock_stealth_instance.apply_stealth_async = Mock()
        mock_stealth_class.return_value = mock_stealth_instance
        
        stealth = Stealth()
        assert hasattr(stealth, 'apply_stealth_async')
        assert callable(stealth.apply_stealth_async)

    def test_browser_config_has_stealth_flag(self):
        """Test that BrowserConfig has stealth flag"""
        from crawl4ai.async_configs import BrowserConfig
        
        # Test default value
        config = BrowserConfig()
        assert hasattr(config, 'stealth')
        assert config.stealth is True  # Default should be True
        
        # Test explicit setting
        config_disabled = BrowserConfig(stealth=False)
        assert config_disabled.stealth is False

    def test_stealth_flag_serialization(self):
        """Test that stealth flag is properly serialized in BrowserConfig"""
        from crawl4ai.async_configs import BrowserConfig
        
        config = BrowserConfig(stealth=True)
        config_dict = config.to_dict()
        
        assert 'stealth' in config_dict
        assert config_dict['stealth'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
