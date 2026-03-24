"""Tests for PR #1463: configurable device_scale_factor in BrowserConfig."""

import pytest
import pytest_asyncio
import base64
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


class TestDeviceScaleFactorConfig:
    """Test that device_scale_factor flows correctly through BrowserConfig."""

    def test_default_value(self):
        config = BrowserConfig()
        assert config.device_scale_factor == 1.0

    def test_custom_value(self):
        config = BrowserConfig(device_scale_factor=2.0)
        assert config.device_scale_factor == 2.0

    def test_to_dict_includes_field(self):
        config = BrowserConfig(device_scale_factor=3.0)
        d = config.to_dict()
        assert d["device_scale_factor"] == 3.0

    def test_clone_preserves(self):
        config = BrowserConfig(device_scale_factor=2.5)
        cloned = config.clone()
        assert cloned.device_scale_factor == 2.5

    def test_from_kwargs(self):
        config = BrowserConfig.from_kwargs({"device_scale_factor": 1.5})
        assert config.device_scale_factor == 1.5

    def test_from_kwargs_default(self):
        config = BrowserConfig.from_kwargs({})
        assert config.device_scale_factor == 1.0


@pytest.mark.asyncio
async def test_device_scale_factor_produces_larger_screenshot():
    """Integration test: higher device_scale_factor should produce a larger screenshot."""
    html = "<html><body><h1>Scale Test</h1></body></html>"
    raw_url = f"raw:{html}"
    run_config = CrawlerRunConfig(screenshot=True)

    # Take screenshot at scale 1.0
    browser_1x = BrowserConfig(headless=True, device_scale_factor=1.0, viewport_width=800, viewport_height=600)
    async with AsyncWebCrawler(config=browser_1x) as crawler:
        result_1x = await crawler.arun(raw_url, config=run_config)

    # Take screenshot at scale 2.0
    browser_2x = BrowserConfig(headless=True, device_scale_factor=2.0, viewport_width=800, viewport_height=600)
    async with AsyncWebCrawler(config=browser_2x) as crawler:
        result_2x = await crawler.arun(raw_url, config=run_config)

    assert result_1x.screenshot is not None
    assert result_2x.screenshot is not None

    # 2x scale should produce more pixel data (larger base64 string)
    size_1x = len(base64.b64decode(result_1x.screenshot))
    size_2x = len(base64.b64decode(result_2x.screenshot))
    assert size_2x > size_1x, f"2x screenshot ({size_2x} bytes) should be larger than 1x ({size_1x} bytes)"
