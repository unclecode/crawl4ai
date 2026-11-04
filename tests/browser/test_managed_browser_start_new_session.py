"""Regression test for issue #2238.

ManagedBrowser.start() used preexec_fn=os.setpgrp to put the launched
Chromium in its own process group. preexec_fn runs arbitrary Python code
between fork() and exec() in the child process; in a multi-threaded parent
(e.g. a gunicorn/uvicorn worker) the child only inherits the calling
thread, so a lock held by another thread at fork time (allocator, import
lock, ...) can leave the child deadlocked or crashing before exec ever
runs. start_new_session=True achieves the same "own process group" result
via setsid() without executing Python in the forked child.
"""
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from crawl4ai.browser_manager import ManagedBrowser
from crawl4ai.async_configs import BrowserConfig


@pytest.mark.asyncio
async def test_start_uses_start_new_session_not_preexec_fn():
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        debugging_port=9222,
        host="localhost",
    )
    manager = ManagedBrowser(browser_config=browser_config, logger=MagicMock())
    manager._get_browser_args = AsyncMock(return_value=["/fake/chrome"])
    manager._initial_startup_check = AsyncMock(return_value=None)

    fake_process = MagicMock()
    fake_process.poll.return_value = None

    with patch("crawl4ai.browser_manager.sys.platform", "linux"), \
         patch("crawl4ai.browser_manager.subprocess.Popen", return_value=fake_process) as mock_popen, \
         patch("crawl4ai.browser_manager.subprocess.check_output", side_effect=FileNotFoundError), \
         patch("asyncio.sleep", new=AsyncMock(return_value=None)):
        await manager.start()

    assert mock_popen.called
    _, kwargs = mock_popen.call_args
    assert kwargs.get("start_new_session") is True
    assert "preexec_fn" not in kwargs
