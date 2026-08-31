from crawl4ai.browser_profiler import BrowserProfiler
import asyncio


if __name__ == "__main__":
    # Test launching a standalone browser
    async def test_standalone_browser():
        profiler = BrowserProfiler()
        cdp_url = await profiler.launch_standalone_browser(
            browser_type="chromium",
            user_data_dir="~/.crawl4ai/browser_profile/test-browser-data",
            debugging_port=9222,
            headless=False
        )
        print(f"CDP URL: {cdp_url}")

    asyncio.run(test_standalone_browser())