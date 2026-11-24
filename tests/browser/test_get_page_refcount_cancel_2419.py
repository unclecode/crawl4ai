"""
Regression tests for #2419: get_page() must not leak context refcounts on
cancellation / BaseException before the page is returned, and browser recycle
must not block forever inside get_page when the pending drain is full.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.browser_manager import BrowserManager


def _bm(**kwargs):
    cfg = BrowserConfig(**kwargs)
    bm = BrowserManager(cfg, logger=None)
    return bm


@pytest.mark.asyncio
async def test_cancel_during_new_page_releases_refcount():
    """CancelledError after the refcount bump must return the refcount to 0."""
    bm = _bm()
    sig = "sig_cancel_new_page"
    context = MagicMock()
    started = asyncio.Event()

    async def hang_new_page():
        started.set()
        await asyncio.sleep(3600)
        return MagicMock()

    context.new_page = hang_new_page
    bm.contexts_by_config[sig] = context
    bm._context_refcounts[sig] = 0
    bm._context_last_used[sig] = 0.0
    bm._make_config_signature = MagicMock(return_value=sig)

    task = asyncio.create_task(bm.get_page(CrawlerRunConfig()))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert bm._context_refcounts.get(sig, 0) == 0


@pytest.mark.asyncio
async def test_exception_after_new_page_releases_refcount_and_closes_page():
    """Exception from stealth after new_page must drop refcount and close the page."""
    bm = _bm()
    sig = "sig_stealth_boom"
    context = MagicMock()
    page = MagicMock()
    page.close = AsyncMock()

    async def ok_new_page():
        return page

    context.new_page = ok_new_page
    bm.contexts_by_config[sig] = context
    bm._context_refcounts[sig] = 0
    bm._context_last_used[sig] = 0.0
    bm._make_config_signature = MagicMock(return_value=sig)
    bm._apply_stealth_to_page = AsyncMock(side_effect=RuntimeError("stealth failed"))

    with pytest.raises(RuntimeError, match="stealth failed"):
        await bm.get_page(CrawlerRunConfig())

    assert bm._context_refcounts.get(sig, 0) == 0
    page.close.assert_awaited()
    assert page not in bm._page_to_sig


@pytest.mark.asyncio
async def test_cancel_during_bump_releases_refcount():
    """Cancel while recycle bump runs after the page was created must not leak."""
    bm = _bm()
    bm.config.max_pages_before_recycle = 1
    sig = "sig_bump_cancel"
    context = MagicMock()
    page = MagicMock()
    page.close = AsyncMock()

    async def ok_new_page():
        return page

    context.new_page = ok_new_page
    bm.contexts_by_config[sig] = context
    bm._context_refcounts[sig] = 0
    bm._context_last_used[sig] = 0.0
    bm._pages_served = 0
    bm._make_config_signature = MagicMock(return_value=sig)
    bm._apply_stealth_to_page = AsyncMock()

    entered = asyncio.Event()

    async def blocking_bump():
        entered.set()
        await asyncio.sleep(3600)

    bm._maybe_bump_browser_version = blocking_bump

    task = asyncio.create_task(bm.get_page(CrawlerRunConfig()))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert bm._context_refcounts.get(sig, 0) == 0
    page.close.assert_awaited()


@pytest.mark.asyncio
async def test_recycle_defers_when_pending_drain_full():
    """Full pending drain must defer the bump instead of waiting inside get_page."""
    bm = _bm()
    bm.config.max_pages_before_recycle = 1
    bm._pages_served = 1
    bm._max_pending_browsers = 3
    # Three active (refcount > 0) pending entries — cannot opportunistically clear.
    for i in range(3):
        sig = f"old_{i}"
        bm._pending_cleanup[sig] = {"version": 1, "done": asyncio.Event()}
        bm._context_refcounts[sig] = 1
        bm.contexts_by_config[sig] = MagicMock()

    await asyncio.wait_for(bm._maybe_bump_browser_version(), timeout=1.0)

    assert bm._browser_version == 1  # deferred, not bumped
    assert bm._pages_served == 1
    assert len(bm._pending_cleanup) == 3


@pytest.mark.asyncio
async def test_recycle_clears_drained_pending_then_bumps():
    """Refcount-0 pending entries are cleared so recycle can proceed."""
    bm = _bm()
    bm.config.max_pages_before_recycle = 1
    bm._pages_served = 1
    bm._max_pending_browsers = 3
    bm._browser_version = 5

    for i in range(3):
        sig = f"drained_{i}"
        ctx = MagicMock()
        ctx.close = AsyncMock()
        bm._pending_cleanup[sig] = {"version": 4, "done": asyncio.Event()}
        bm._context_refcounts[sig] = 0
        bm.contexts_by_config[sig] = ctx
        bm._context_last_used[sig] = 0.0

    # Also seed a live context that will be active during the bump.
    live_sig = "live"
    live_ctx = MagicMock()
    live_ctx.close = AsyncMock()
    bm.contexts_by_config[live_sig] = live_ctx
    bm._context_refcounts[live_sig] = 1
    bm._context_last_used[live_sig] = 1.0

    await asyncio.wait_for(bm._maybe_bump_browser_version(), timeout=1.0)

    assert bm._browser_version == 6
    assert bm._pages_served == 0
    # drained_* removed; live moved into pending cleanup for the old version
    assert "live" in bm._pending_cleanup
    assert all(s not in bm._pending_cleanup for s in ("drained_0", "drained_1", "drained_2"))


@pytest.mark.asyncio
async def test_successful_get_page_keeps_refcount_for_caller():
    """A successful get_page must leave refcount=1 for release_page_async."""
    bm = _bm()
    sig = "sig_ok"
    context = MagicMock()
    page = MagicMock()
    page.close = AsyncMock()

    async def ok_new_page():
        return page

    context.new_page = ok_new_page
    bm.contexts_by_config[sig] = context
    bm._context_refcounts[sig] = 0
    bm._context_last_used[sig] = 0.0
    bm._make_config_signature = MagicMock(return_value=sig)
    bm._apply_stealth_to_page = AsyncMock()

    got_page, got_ctx = await bm.get_page(CrawlerRunConfig())
    assert got_page is page
    assert got_ctx is context
    assert bm._context_refcounts[sig] == 1
    assert bm._page_to_sig[page] == sig
    page.close.assert_not_awaited()
