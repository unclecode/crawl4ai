"""
Tests for ConfigHealthMonitor class.

This test suite validates the health monitoring functionality for crawler configurations.
"""

import pytest
import asyncio
from crawl4ai.config_health_monitor import ConfigHealthMonitor, ResolutionResult, ConfigHealthState
from crawl4ai import BrowserConfig, CrawlerRunConfig


class TestConfigHealthMonitorBasic:
    """Basic functionality tests for ConfigHealthMonitor."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test monitor initialization with default settings."""
        monitor = ConfigHealthMonitor()
        
        assert monitor.check_interval >= 10.0  # Minimum enforced
        assert monitor.failure_threshold >= 1
        assert monitor.resolution_retry_limit >= 0
        assert monitor.registered_count == 0
        assert not monitor.is_running
        assert monitor.uptime is None
    
    @pytest.mark.asyncio
    async def test_initialization_with_config(self):
        """Test monitor initialization with custom configuration."""
        browser_config = BrowserConfig(headless=True, verbose=False)
        
        monitor = ConfigHealthMonitor(
            browser_config=browser_config,
            check_interval=30.0,
            failure_threshold=2,
            resolution_retry_limit=3,
            enable_metrics=True
        )
        
        assert monitor.check_interval == 30.0
        assert monitor.failure_threshold == 2
        assert monitor.resolution_retry_limit == 3
        assert monitor.enable_metrics is True
    
    @pytest.mark.asyncio
    async def test_register_config(self):
        """Test registering a configuration."""
        monitor = ConfigHealthMonitor()
        
        config = CrawlerRunConfig(page_timeout=30000)
        config_id = monitor.register_config(
            config=config,
            test_url="https://example.com",
            config_id="test_config"
        )
        
        assert config_id == "test_config"
        assert monitor.registered_count == 1
    
    @pytest.mark.asyncio
    async def test_register_config_auto_id(self):
        """Test registering a configuration with auto-generated ID."""
        monitor = ConfigHealthMonitor()
        
        config = CrawlerRunConfig(page_timeout=30000)
        config_id = monitor.register_config(
            config=config,
            test_url="https://example.com"
        )
        
        assert config_id.startswith("config_")
        assert monitor.registered_count == 1
    
    @pytest.mark.asyncio
    async def test_register_duplicate_config_id(self):
        """Test that duplicate config IDs raise an error."""
        monitor = ConfigHealthMonitor()
        
        config = CrawlerRunConfig(page_timeout=30000)
        monitor.register_config(
            config=config,
            test_url="https://example.com",
            config_id="duplicate"
        )
        
        with pytest.raises(ValueError, match="already registered"):
            monitor.register_config(
                config=config,
                test_url="https://example.com",
                config_id="duplicate"
            )
    
    @pytest.mark.asyncio
    async def test_register_empty_url(self):
        """Test that empty test URLs raise an error."""
        monitor = ConfigHealthMonitor()
        config = CrawlerRunConfig()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            monitor.register_config(
                config=config,
                test_url=""
            )
    
    @pytest.mark.asyncio
    async def test_unregister_config(self):
        """Test unregistering a configuration."""
        monitor = ConfigHealthMonitor()
        
        config = CrawlerRunConfig()
        config_id = monitor.register_config(
            config=config,
            test_url="https://example.com",
            config_id="to_remove"
        )
        
        assert monitor.registered_count == 1
        
        result = monitor.unregister_config(config_id)
        assert result is True
        assert monitor.registered_count == 0
    
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_config(self):
        """Test unregistering a non-existent configuration."""
        monitor = ConfigHealthMonitor()
        
        result = monitor.unregister_config("nonexistent")
        assert result is False


class TestConfigHealthMonitorLifecycle:
    """Lifecycle management tests."""
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test monitor start and stop."""
        monitor = ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        )
        
        assert not monitor.is_running
        
        await monitor.start()
        assert monitor.is_running
        assert monitor.uptime is not None
        
        await monitor.stop()
        assert not monitor.is_running
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test monitor as async context manager."""
        async with ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        ) as monitor:
            assert monitor.is_running
            
            # Register a config
            config_id = monitor.register_config(
                config=CrawlerRunConfig(),
                test_url="https://example.com"
            )
            assert monitor.registered_count == 1
        
        # After context exit, should be stopped
        assert not monitor.is_running
    
    @pytest.mark.asyncio
    async def test_double_start(self):
        """Test that double start is handled gracefully."""
        monitor = ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        )
        
        await monitor.start()
        await monitor.start()  # Should log warning but not fail
        
        assert monitor.is_running
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        """Test that stop without start is handled gracefully."""
        monitor = ConfigHealthMonitor()
        await monitor.stop()  # Should log warning but not fail


class TestConfigHealthMonitorHealthChecks:
    """Health checking tests."""
    
    @pytest.mark.asyncio
    async def test_manual_health_check_success(self):
        """Test manual health check on a working URL."""
        async with ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        ) as monitor:
            config_id = monitor.register_config(
                config=CrawlerRunConfig(page_timeout=30000),
                test_url="https://example.com",
                config_id="example_test"
            )
            
            # Perform health check
            is_healthy = await monitor.check_health(config_id)
            
            assert is_healthy is True
            
            # Check state
            status = monitor.get_health_status(config_id)
            assert status.status == "healthy"
            assert status.consecutive_failures == 0
            assert status.consecutive_successes == 1
            assert status.last_check_time is not None
            assert status.last_success_time is not None
    
    @pytest.mark.asyncio
    async def test_manual_health_check_failure(self):
        """Test manual health check on a non-existent URL."""
        async with ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        ) as monitor:
            config_id = monitor.register_config(
                config=CrawlerRunConfig(page_timeout=10000),
                test_url="https://this-domain-definitely-does-not-exist-12345.com",
                config_id="failing_test"
            )
            
            # Perform health check
            is_healthy = await monitor.check_health(config_id)
            
            assert is_healthy is False
            
            # Check state
            status = monitor.get_health_status(config_id)
            assert status.consecutive_failures == 1
            assert status.last_error is not None
    
    @pytest.mark.asyncio
    async def test_health_check_nonexistent_config(self):
        """Test health check on non-existent config raises error."""
        async with ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        ) as monitor:
            with pytest.raises(ValueError, match="not registered"):
                await monitor.check_health("nonexistent")


class TestConfigHealthMonitorResolution:
    """Resolution strategy tests."""
    
    @pytest.mark.asyncio
    async def test_set_default_resolution_strategy(self):
        """Test setting a default resolution strategy."""
        monitor = ConfigHealthMonitor()
        
        async def dummy_strategy(state, monitor):
            return ResolutionResult(success=True, action="dummy")
        
        monitor.set_resolution_strategy(dummy_strategy)
        assert monitor._default_resolution_strategy == dummy_strategy
    
    @pytest.mark.asyncio
    async def test_set_config_specific_resolution_strategy(self):
        """Test setting a config-specific resolution strategy."""
        monitor = ConfigHealthMonitor()
        
        config_id = monitor.register_config(
            config=CrawlerRunConfig(),
            test_url="https://example.com",
            config_id="with_strategy"
        )
        
        async def custom_strategy(state, monitor):
            return ResolutionResult(success=True, action="custom")
        
        monitor.set_resolution_strategy(custom_strategy, config_id)
        assert monitor._resolution_strategies[config_id] == custom_strategy
    
    @pytest.mark.asyncio
    async def test_set_strategy_for_nonexistent_config(self):
        """Test setting strategy for non-existent config raises error."""
        monitor = ConfigHealthMonitor()
        
        async def dummy_strategy(state, monitor):
            return ResolutionResult(success=True, action="dummy")
        
        with pytest.raises(ValueError, match="not registered"):
            monitor.set_resolution_strategy(dummy_strategy, "nonexistent")
    
    @pytest.mark.asyncio
    async def test_register_with_resolution_strategy(self):
        """Test registering a config with a resolution strategy."""
        monitor = ConfigHealthMonitor()
        
        async def custom_strategy(state, monitor):
            return ResolutionResult(success=True, action="custom")
        
        config_id = monitor.register_config(
            config=CrawlerRunConfig(),
            test_url="https://example.com",
            resolution_strategy=custom_strategy
        )
        
        assert monitor._resolution_strategies[config_id] == custom_strategy


class TestConfigHealthMonitorMetrics:
    """Metrics and status query tests."""
    
    @pytest.mark.asyncio
    async def test_get_health_status_single(self):
        """Test getting status for a single config."""
        monitor = ConfigHealthMonitor()
        
        config_id = monitor.register_config(
            config=CrawlerRunConfig(),
            test_url="https://example.com",
            config_id="status_test"
        )
        
        status = monitor.get_health_status(config_id)
        
        assert isinstance(status, ConfigHealthState)
        assert status.config_id == config_id
        assert status.status == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_health_status_all(self):
        """Test getting status for all configs."""
        monitor = ConfigHealthMonitor()
        
        # Register multiple configs
        for i in range(3):
            monitor.register_config(
                config=CrawlerRunConfig(),
                test_url="https://example.com",
                config_id=f"config_{i}"
            )
        
        all_statuses = monitor.get_health_status()
        
        assert isinstance(all_statuses, dict)
        assert len(all_statuses) == 3
        assert all(isinstance(s, ConfigHealthState) for s in all_statuses.values())
    
    @pytest.mark.asyncio
    async def test_get_health_status_nonexistent(self):
        """Test getting status for non-existent config raises error."""
        monitor = ConfigHealthMonitor()
        
        with pytest.raises(ValueError, match="not registered"):
            monitor.get_health_status("nonexistent")
    
    @pytest.mark.asyncio
    async def test_get_metrics_empty(self):
        """Test getting metrics with no configs."""
        monitor = ConfigHealthMonitor()
        
        metrics = monitor.get_metrics()
        
        assert metrics["total_checks"] == 0
        assert metrics["successful_checks"] == 0
        assert metrics["failed_checks"] == 0
        assert metrics["success_rate"] == 0.0
        assert metrics["configs"] == {}
    
    @pytest.mark.asyncio
    async def test_get_metrics_with_checks(self):
        """Test metrics after performing health checks."""
        async with ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False),
            enable_metrics=True
        ) as monitor:
            config_id = monitor.register_config(
                config=CrawlerRunConfig(),
                test_url="https://example.com",
                config_id="metrics_test"
            )
            
            # Perform a health check
            await monitor.check_health(config_id)
            
            metrics = monitor.get_metrics()
            
            assert metrics["total_checks"] >= 0
            assert "configs" in metrics
            assert config_id in metrics["configs"]
            
            config_metrics = metrics["configs"][config_id]
            assert config_metrics["status"] == "healthy"
            assert config_metrics["total_checks"] >= 1
            assert "avg_response_time" in config_metrics


class TestConfigHealthMonitorProperties:
    """Property tests."""
    
    @pytest.mark.asyncio
    async def test_is_running_property(self):
        """Test is_running property."""
        monitor = ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        )
        
        assert monitor.is_running is False
        
        await monitor.start()
        assert monitor.is_running is True
        
        await monitor.stop()
        assert monitor.is_running is False
    
    @pytest.mark.asyncio
    async def test_registered_count_property(self):
        """Test registered_count property."""
        monitor = ConfigHealthMonitor()
        
        assert monitor.registered_count == 0
        
        for i in range(5):
            monitor.register_config(
                config=CrawlerRunConfig(),
                test_url="https://httpbin.org/html",
                config_id=f"count_test_{i}"
            )
        
        assert monitor.registered_count == 5
        
        monitor.unregister_config("count_test_0")
        assert monitor.registered_count == 4
    
    @pytest.mark.asyncio
    async def test_uptime_property(self):
        """Test uptime property."""
        monitor = ConfigHealthMonitor(
            browser_config=BrowserConfig(headless=True, verbose=False)
        )
        
        assert monitor.uptime is None
        
        await monitor.start()
        await asyncio.sleep(0.1)
        
        uptime = monitor.uptime
        assert uptime is not None
        assert uptime >= 0.1
        
        await monitor.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

