import pytest
from crawl4ai.async_configs import BrowserConfig

def test_browser_config_filtering_flags():
    """Test that BrowserConfig correctly stores the new filtering flags."""
    # Default values
    config = BrowserConfig()
    assert config.avoid_ads is False
    assert config.avoid_css is False
    
    # Custom values
    config = BrowserConfig(avoid_ads=True, avoid_css=True)
    assert config.avoid_ads is True
    assert config.avoid_css is True
    
    # Check to_dict / from_kwargs parity
    config_dict = config.to_dict()
    assert config_dict["avoid_ads"] is True
    assert config_dict["avoid_css"] is True
    
    new_config = BrowserConfig.from_kwargs(config_dict)
    assert new_config.avoid_ads is True
    assert new_config.avoid_css is True

def test_browser_config_clone():
    """Test that cloning BrowserConfig preserves the new flags."""
    config = BrowserConfig(avoid_ads=True, avoid_css=False)
    cloned = config.clone(avoid_css=True)
    
    assert cloned.avoid_ads is True
    assert cloned.avoid_css is True
    assert config.avoid_css is False # Original remains unchanged

