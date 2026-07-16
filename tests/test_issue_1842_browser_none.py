"""
Tests for issue #1842: Docker Job Queue API Error: 'NoneType' object has no attribute 'new_context'

Verifies that BrowserManager.create_browser_context() raises clear, correct
RuntimeError messages when self.browser is None, distinguishing between:
  - persistent context mode (self._launched_persistent = True)
  - browser closed/crashed/not started (self._launched_persistent = False)
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from crawl4ai.browser_manager import BrowserManager
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig


@pytest.fixture
def browser_config():
    """Default BrowserConfig for testing."""
    return BrowserConfig()


@pytest.fixture
def manager(browser_config):
    """BrowserManager with browser=None (simulating closed/crashed state)."""
    mgr = BrowserManager(browser_config)
    assert mgr.browser is None  # starts as None
    return mgr


# ── Guard raises RuntimeError (not AttributeError) ─────────────────────

class TestBrowserNoneGuard:
    """Verify that create_browser_context raises RuntimeError when browser is None."""

    @pytest.mark.asyncio
    async def test_browser_none_raises_runtime_error(self, manager):
        """Should raise RuntimeError, not AttributeError."""
        with pytest.raises(RuntimeError):
            await manager.create_browser_context()

    @pytest.mark.asyncio
    async def test_browser_none_not_attribute_error(self, manager):
        """Must never raise AttributeError ('NoneType' has no attribute 'new_context')."""
        with pytest.raises(RuntimeError):
            await manager.create_browser_context()
        # If we get here, it raised RuntimeError — not AttributeError. Good.

    @pytest.mark.asyncio
    async def test_browser_none_with_crawler_run_config(self, manager):
        """Guard should trigger even when CrawlerRunConfig is passed."""
        config = CrawlerRunConfig()
        with pytest.raises(RuntimeError):
            await manager.create_browser_context(config)


# ── Correct error message based on cause ────────────────────────────────

class TestErrorMessageAccuracy:
    """Verify error messages correctly identify why browser is None."""

    @pytest.mark.asyncio
    async def test_persistent_context_message(self, manager):
        """When _launched_persistent=True, message should mention persistent context."""
        manager._launched_persistent = True
        with pytest.raises(RuntimeError, match="use_persistent_context=True"):
            await manager.create_browser_context()

    @pytest.mark.asyncio
    async def test_persistent_context_message_mentions_single_context(self, manager):
        """Persistent context error should mention single shared context."""
        manager._launched_persistent = True
        with pytest.raises(RuntimeError, match="single shared context"):
            await manager.create_browser_context()

    @pytest.mark.asyncio
    async def test_closed_browser_message(self, manager):
        """When browser is closed (not persistent), message should mention closed/crashed."""
        manager._launched_persistent = False
        with pytest.raises(RuntimeError, match="closed.*crashed|crashed.*closed"):
            await manager.create_browser_context()

    @pytest.mark.asyncio
    async def test_closed_browser_message_no_persistent_mention(self, manager):
        """Non-persistent error should NOT mention use_persistent_context."""
        manager._launched_persistent = False
        with pytest.raises(RuntimeError) as exc_info:
            await manager.create_browser_context()
        assert "use_persistent_context" not in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_default_state_gives_closed_message(self, manager):
        """Default manager (never started) should give the closed/crashed message."""
        # _launched_persistent defaults to False
        assert manager._launched_persistent is False
        with pytest.raises(RuntimeError, match="not available"):
            await manager.create_browser_context()


# ── Browser available (no guard triggered) ──────────────────────────────

class TestBrowserAvailable:
    """Verify create_browser_context works normally when browser is available."""

    @pytest.mark.asyncio
    async def test_browser_set_does_not_raise(self, manager):
        """When browser is set, should not raise RuntimeError."""
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        manager.browser = mock_browser

        context = await manager.create_browser_context()
        assert context == mock_context
        mock_browser.new_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_set_with_config(self, manager):
        """When browser is set, should work with CrawlerRunConfig."""
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        manager.browser = mock_browser

        config = CrawlerRunConfig()
        context = await manager.create_browser_context(config)
        assert context == mock_context


# ── Simulate Docker race condition scenario ─────────────────────────────

class TestDockerRaceCondition:
    """Simulate the scenario from issue #1842: browser becomes None during use."""

    @pytest.mark.asyncio
    async def test_browser_closed_mid_use(self, manager):
        """Simulate browser being closed while another task tries to use it."""
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        manager.browser = mock_browser

        # First call works
        ctx = await manager.create_browser_context()
        assert ctx == mock_context

        # Simulate janitor closing the browser
        manager.browser = None

        # Second call should raise RuntimeError, not AttributeError
        with pytest.raises(RuntimeError, match="not available"):
            await manager.create_browser_context()

    @pytest.mark.asyncio
    async def test_concurrent_access_after_close(self, manager):
        """Multiple concurrent calls after browser close all get RuntimeError."""
        manager.browser = None
        manager._launched_persistent = False

        async def try_create():
            with pytest.raises(RuntimeError, match="not available"):
                await manager.create_browser_context()

        # Run multiple concurrent attempts
        await asyncio.gather(*[try_create() for _ in range(5)])

    @pytest.mark.asyncio
    async def test_error_type_is_not_attribute_error(self, manager):
        """Explicitly verify the original bug (AttributeError) cannot occur."""
        manager.browser = None
        try:
            await manager.create_browser_context()
            assert False, "Should have raised"
        except RuntimeError:
            pass  # Expected
        except AttributeError:
            pytest.fail(
                "Got AttributeError ('NoneType' has no attribute 'new_context') "
                "— this is the original bug from issue #1842"
            )
