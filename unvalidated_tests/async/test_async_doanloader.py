import os
import sys
import asyncio
import shutil
from typing import List
import tempfile

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler


class TestDownloads:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="crawl4ai_test_")
        self.download_dir = os.path.join(self.temp_dir, "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
        self.results: List[str] = []

    def cleanup(self):
        shutil.rmtree(self.temp_dir)

    def log_result(self, test_name: str, success: bool, message: str = ""):
        result = f"{'✅' if success else '❌'} {test_name}: {message}"
        self.results.append(result)
        print(result)

    async def test_basic_download(self):
        """Test basic file download functionality"""
        try:
            async with AsyncWebCrawler(
                accept_downloads=True, downloads_path=self.download_dir, verbose=True
            ) as crawler:
                # Python.org downloads page typically has stable download links
                result = await crawler.arun(
                    url="https://www.python.org/downloads/",
                    js_code="""
                    // Click first download link
                    const downloadLink = document.querySelector('a[href$=".exe"]');
                    if (downloadLink) downloadLink.click();
                    """,
                )

                success = (
                    result.downloaded_files is not None
                    and len(result.downloaded_files) > 0
                )
                self.log_result(
                    "Basic Download",
                    success,
                    f"Downloaded {len(result.downloaded_files or [])} files"
                    if success
                    else "No files downloaded",
                )
        except Exception as e:
            self.log_result("Basic Download", False, str(e))

    async def test_persistent_context_download(self):
        """Test downloads with persistent context"""
        try:
            user_data_dir = os.path.join(self.temp_dir, "user_data")
            os.makedirs(user_data_dir, exist_ok=True)

            async with AsyncWebCrawler(
                accept_downloads=True,
                downloads_path=self.download_dir,
                use_persistent_context=True,
                user_data_dir=user_data_dir,
                verbose=True,
            ) as crawler:
                result = await crawler.arun(
                    url="https://www.python.org/downloads/",
                    js_code="""
                    const downloadLink = document.querySelector('a[href$=".exe"]');
                    if (downloadLink) downloadLink.click();
                    """,
                )

                success = (
                    result.downloaded_files is not None
                    and len(result.downloaded_files) > 0
                )
                self.log_result(
                    "Persistent Context Download",
                    success,
                    f"Downloaded {len(result.downloaded_files or [])} files"
                    if success
                    else "No files downloaded",
                )
        except Exception as e:
            self.log_result("Persistent Context Download", False, str(e))

    async def test_multiple_downloads(self):
        """Test multiple simultaneous downloads"""
        try:
            async with AsyncWebCrawler(
                accept_downloads=True, downloads_path=self.download_dir, verbose=True
            ) as crawler:
                result = await crawler.arun(
                    url="https://www.python.org/downloads/",
                    js_code="""
                    // Click multiple download links
                    const downloadLinks = document.querySelectorAll('a[href$=".exe"]');
                    downloadLinks.forEach(link => link.click());
                    """,
                )

                success = (
                    result.downloaded_files is not None
                    and len(result.downloaded_files) > 1
                )
                self.log_result(
                    "Multiple Downloads",
                    success,
                    f"Downloaded {len(result.downloaded_files or [])} files"
                    if success
                    else "Not enough files downloaded",
                )
        except Exception as e:
            self.log_result("Multiple Downloads", False, str(e))

    async def test_different_browsers(self):
        """Test downloads across different browser types"""
        browsers = ["chromium", "firefox", "webkit"]

        for browser_type in browsers:
            try:
                async with AsyncWebCrawler(
                    accept_downloads=True,
                    downloads_path=self.download_dir,
                    browser_type=browser_type,
                    verbose=True,
                ) as crawler:
                    result = await crawler.arun(
                        url="https://www.python.org/downloads/",
                        js_code="""
                        const downloadLink = document.querySelector('a[href$=".exe"]');
                        if (downloadLink) downloadLink.click();
                        """,
                    )

                    success = (
                        result.downloaded_files is not None
                        and len(result.downloaded_files) > 0
                    )
                    self.log_result(
                        f"{browser_type.title()} Download",
                        success,
                        f"Downloaded {len(result.downloaded_files or [])} files"
                        if success
                        else "No files downloaded",
                    )
            except Exception as e:
                self.log_result(f"{browser_type.title()} Download", False, str(e))

    async def test_edge_cases(self):
        """Test various edge cases"""

        # Test 1: Downloads without specifying download path
        try:
            async with AsyncWebCrawler(accept_downloads=True, verbose=True) as crawler:
                result = await crawler.arun(
                    url="https://www.python.org/downloads/",
                    js_code="document.querySelector('a[href$=\".exe\"]').click()",
                )
                self.log_result(
                    "Default Download Path",
                    True,
                    f"Downloaded to default path: {result.downloaded_files[0] if result.downloaded_files else 'None'}",
                )
        except Exception as e:
            self.log_result("Default Download Path", False, str(e))

        # Test 2: Downloads with invalid path
        try:
            async with AsyncWebCrawler(
                accept_downloads=True,
                downloads_path="/invalid/path/that/doesnt/exist",
                verbose=True,
            ) as crawler:
                result = await crawler.arun(
                    url="https://www.python.org/downloads/",
                    js_code="document.querySelector('a[href$=\".exe\"]').click()",
                )
                self.log_result(
                    "Invalid Download Path", False, "Should have raised an error"
                )
        except Exception:
            self.log_result(
                "Invalid Download Path", True, "Correctly handled invalid path"
            )

        # Test 3: Download with accept_downloads=False
        try:
            async with AsyncWebCrawler(accept_downloads=False, verbose=True) as crawler:
                result = await crawler.arun(
                    url="https://www.python.org/downloads/",
                    js_code="document.querySelector('a[href$=\".exe\"]').click()",
                )
                success = result.downloaded_files is None
                self.log_result(
                    "Disabled Downloads",
                    success,
                    "Correctly ignored downloads"
                    if success
                    else "Unexpectedly downloaded files",
                )
        except Exception as e:
            self.log_result("Disabled Downloads", False, str(e))

    async def run_all_tests(self):
        """Run all test cases"""
        print("\n🧪 Running Download Tests...\n")

        test_methods = [
            self.test_basic_download,
            self.test_persistent_context_download,
            self.test_multiple_downloads,
            self.test_different_browsers,
            self.test_edge_cases,
        ]

        for test in test_methods:
            print(f"\n📝 Running {test.__doc__}...")
            await test()
            await asyncio.sleep(2)  # Brief pause between tests

        print("\n📊 Test Results Summary:")
        for result in self.results:
            print(result)

        successes = len([r for r in self.results if "✅" in r])
        total = len(self.results)
        print(f"\nTotal: {successes}/{total} tests passed")

        self.cleanup()


async def main():
    tester = TestDownloads()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
