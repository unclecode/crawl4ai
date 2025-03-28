import sys
from pathlib import Path

import pytest

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Assuming that the changes made allow different configurations
# for managed browser, persistent context, and so forth.


@pytest.mark.asyncio
async def test_default_headless():
    async with AsyncWebCrawler(
        headless=True,
        verbose=True,
        user_agent_mode="random",
        user_agent_generator_config={"platforms": ["mobile"], "os": "android"},
        use_managed_browser=False,
        use_persistent_context=False,
        ignore_https_errors=True,
        # Testing normal ephemeral context
    ) as crawler:
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/technology",
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("[test_default_headless] success:", result.success)
        print("HTML length:", len(result.html if result.html else ""))


@pytest.mark.asyncio
async def test_managed_browser_persistent(tmp_path: Path):
    # Treating use_persistent_context=True as managed_browser scenario.
    user_data_dir: Path = tmp_path / "user_data_dir"
    async with AsyncWebCrawler(
        headless=False,
        verbose=True,
        user_agent_mode="random",
        user_agent_generator_config={"platforms": ["desktop"], "os": "mac"},
        use_managed_browser=True,
        use_persistent_context=True,  # now should behave same as managed browser
        user_data_dir=user_data_dir.as_posix(),
        # This should store and reuse profile data across runs
    ) as crawler:
        result = await crawler.arun(
            url="https://www.google.com",
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("[test_managed_browser_persistent] success:", result.success)
        print("HTML length:", len(result.html if result.html else ""))


@pytest.mark.asyncio
async def test_session_reuse():
    # Test creating a session, using it for multiple calls
    session_id = "my_session"
    async with AsyncWebCrawler(
        headless=False,
        verbose=True,
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        # Fixed user-agent for consistency
        use_managed_browser=False,
        use_persistent_context=False,
    ) as crawler:
        # First call: create session
        result1 = await crawler.arun(
            url="https://www.example.com",
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("[test_session_reuse first call] success:", result1.success)

        # Second call: same session, possibly cookie retained
        result2 = await crawler.arun(
            url="https://www.example.com/about",
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("[test_session_reuse second call] success:", result2.success)


@pytest.mark.asyncio
async def test_magic_mode():
    # Test magic mode with override_navigator and simulate_user
    async with AsyncWebCrawler(
        headless=False,
        verbose=True,
        user_agent_mode="random",
        user_agent_generator_config={"platforms": ["desktop"], "os": "windows"},
        use_managed_browser=False,
        use_persistent_context=False,
        magic=True,
        override_navigator=True,
        simulate_user=True,
    ) as crawler:
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/business",
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("[test_magic_mode] success:", result.success)
        print("HTML length:", len(result.html if result.html else ""))


@pytest.mark.asyncio
async def test_proxy_settings():
    # Test with a proxy (if available) to ensure code runs with proxy
    async with AsyncWebCrawler(
        headless=True,
        verbose=False,
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        proxy="http://127.0.0.1:8080",  # Assuming local proxy server for test
        use_managed_browser=False,
        use_persistent_context=False,
    ) as crawler:
        result = await crawler.arun(
            url="https://httpbin.org/ip",
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("[test_proxy_settings] success:", result.success)
        if result.success:
            print("HTML preview:", result.html[:200] if result.html else "")


@pytest.mark.asyncio
async def test_ignore_https_errors():
    # Test ignore HTTPS errors with a self-signed or invalid cert domain
    # This is just conceptual, the domain should be one that triggers SSL error.
    # Using a hypothetical URL that fails SSL:
    async with AsyncWebCrawler(
        headless=True,
        verbose=True,
        user_agent="Mozilla/5.0",
        ignore_https_errors=True,
        use_managed_browser=False,
        use_persistent_context=False,
    ) as crawler:
        result = await crawler.arun(
            url="https://self-signed.badssl.com/",
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("[test_ignore_https_errors] success:", result.success)


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", "-v", str(__file__)]))
