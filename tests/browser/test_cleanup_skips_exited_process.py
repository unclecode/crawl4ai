"""ManagedBrowser.cleanup() must only signal a browser process that is still running.

``Popen.poll()`` returns ``None`` while the child runs and its exit code afterwards.
``cleanup()`` used the truthiness of that value, so a browser that had already exited
cleanly (code ``0``) was treated as running: it was terminated again, the 1 s wait loop
was entered, and on Windows a stale PID was handed to ``taskkill /F /T``.
"""

from types import SimpleNamespace

import pytest

from crawl4ai.browser_manager import ManagedBrowser


class _FakeProcess:
    """Minimal stand-in for ``subprocess.Popen``."""

    def __init__(self, exit_code):
        self._exit_code = exit_code
        self.pid = 4242
        self.terminated = False
        self.killed = False

    def poll(self):
        return self._exit_code

    def terminate(self):
        self.terminated = True
        # Exit as soon as the signal lands, so cleanup() never reaches the force-kill path.
        self._exit_code = 0

    def kill(self):
        self.killed = True
        self._exit_code = -9


def _managed_browser(process, temp_dir=None):
    browser = ManagedBrowser.__new__(ManagedBrowser)
    browser.browser_process = process
    browser.temp_dir = temp_dir
    browser.shutting_down = False
    browser.logger = SimpleNamespace(error=lambda **_: None)
    return browser


@pytest.mark.asyncio
@pytest.mark.parametrize("exit_code", [0, 1])
async def test_cleanup_leaves_an_exited_process_alone(exit_code):
    process = _FakeProcess(exit_code)
    browser = _managed_browser(process)

    await browser.cleanup()

    assert not process.terminated
    assert not process.killed
    assert browser.shutting_down


@pytest.mark.asyncio
async def test_cleanup_terminates_a_running_process():
    process = _FakeProcess(None)
    browser = _managed_browser(process)

    await browser.cleanup()

    assert process.terminated
