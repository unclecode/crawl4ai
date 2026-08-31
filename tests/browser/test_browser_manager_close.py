from types import SimpleNamespace

import pytest

from crawl4ai.browser_manager import BrowserManager


class _Context:
    def __init__(self, manager=None):
        self.manager = manager
        self.closed = False

    async def close(self):
        self.closed = True
        if self.manager:
            self.manager.contexts_by_config.pop("second", None)


@pytest.mark.asyncio
async def test_close_iterates_over_context_snapshot():
    manager = BrowserManager.__new__(BrowserManager)
    manager.config = SimpleNamespace(cdp_url=None, sleep_on_close=False)
    manager.sessions = {}
    manager.browser = manager.managed_browser = manager.playwright = None
    manager.logger = SimpleNamespace(error=lambda **_: None)
    manager._using_cached_cdp = manager._launched_persistent = False
    manager._context_refcounts = manager._context_last_used = manager._page_to_sig = {}
    first, second = _Context(manager), _Context()
    manager.contexts_by_config = {"first": first, "second": second}

    await manager.close()

    assert first.closed
    assert second.closed
    assert manager.contexts_by_config == {}
