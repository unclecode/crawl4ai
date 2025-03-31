import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import threading

import pytest
import requests

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
        assert result.success
        assert result.html
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
        assert result.success
        assert result.html


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
        assert result1.success

        # Second call: same session, possibly cookie retained
        result2 = await crawler.arun(
            url="https://www.example.com/about",
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        assert result2.success


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
        assert result.success
        assert result.html


class ProxyHandler(BaseHTTPRequestHandler):
    """Simple HTTP proxy handler for testing purposes."""
    def do_GET(self):
        resp = requests.get(self.path)
        self.send_response(resp.status_code)
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(resp.content)

@pytest.fixture
def proxy_server():
    """Fixture to create a simple HTTP proxy server for testing."""
    server = HTTPServer(('localhost', 0), ProxyHandler)
    port = server.server_address[1]

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield f"http://localhost:{port}"

    server.shutdown()
    thread.join()

@pytest.mark.asyncio
async def test_proxy_settings(proxy_server: str):
    # Test with a proxy (if available) to ensure code runs with proxy
    async with AsyncWebCrawler(
        headless=True,
        verbose=False,
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        proxy=proxy_server,
        use_managed_browser=False,
        use_persistent_context=False,
    ) as crawler:
        result = await crawler.arun(
            url="http://httpbin.org/ip",
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        assert result.success


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
        assert result.success


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
