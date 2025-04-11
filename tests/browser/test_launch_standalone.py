import os
import sys
import pytest
from crawl4ai.browser_profiler import BrowserProfiler

@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires user interaction to stop the browser, more work needed")
async def test_standalone_browser():
    profiler = BrowserProfiler()
    cdp_url = await profiler.launch_standalone_browser(
        browser_type="chromium",
        user_data_dir=os.path.expanduser("~/.crawl4ai/browser_profile/test-browser-data"),
        debugging_port=9222,
        headless=False
    )
    assert cdp_url is not None, "Failed to launch standalone browser"

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))