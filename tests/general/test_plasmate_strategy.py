"""Tests for AsyncPlasmateCrawlerStrategy."""

import asyncio
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from crawl4ai.async_plasmate_strategy import AsyncPlasmateCrawlerStrategy
from crawl4ai.models import AsyncCrawlResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _completed_process(stdout: str = "extracted content", returncode: int = 0) -> MagicMock:
    m = MagicMock()
    m.stdout = stdout
    m.returncode = returncode
    m.stderr = ""
    return m


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_init_defaults():
    strategy = AsyncPlasmateCrawlerStrategy()
    assert strategy.output_format == "text"
    assert strategy.timeout == 30
    assert strategy.selector is None
    assert strategy.extra_headers == {}
    assert strategy.fallback_to_playwright is False


def test_init_custom():
    strategy = AsyncPlasmateCrawlerStrategy(
        output_format="markdown",
        timeout=60,
        selector="main",
        extra_headers={"X-Custom": "val"},
        fallback_to_playwright=True,
    )
    assert strategy.output_format == "markdown"
    assert strategy.timeout == 60
    assert strategy.selector == "main"
    assert strategy.extra_headers == {"X-Custom": "val"}
    assert strategy.fallback_to_playwright is True


def test_init_invalid_format():
    with pytest.raises(ValueError, match="output_format"):
        AsyncPlasmateCrawlerStrategy(output_format="html")


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------

def test_build_cmd_defaults():
    strategy = AsyncPlasmateCrawlerStrategy()
    strategy._plasmate_bin = "/usr/local/bin/plasmate"
    cmd = strategy._build_cmd("https://example.com")
    assert cmd[0] == "/usr/local/bin/plasmate"
    assert "fetch" in cmd
    assert "https://example.com" in cmd
    assert "--format" in cmd
    assert "text" in cmd
    assert "--timeout" in cmd
    assert "30000" in cmd


def test_build_cmd_with_selector():
    strategy = AsyncPlasmateCrawlerStrategy(selector="main")
    strategy._plasmate_bin = "/usr/local/bin/plasmate"
    cmd = strategy._build_cmd("https://example.com")
    assert "--selector" in cmd
    assert cmd[cmd.index("--selector") + 1] == "main"


def test_build_cmd_with_headers():
    strategy = AsyncPlasmateCrawlerStrategy(extra_headers={"Authorization": "Bearer tok"})
    strategy._plasmate_bin = "/usr/local/bin/plasmate"
    cmd = strategy._build_cmd("https://example.com")
    assert "--header" in cmd
    assert "Authorization: Bearer tok" in cmd[cmd.index("--header") + 1]


def test_build_cmd_timeout_converted_to_ms():
    strategy = AsyncPlasmateCrawlerStrategy(timeout=45)
    strategy._plasmate_bin = "/usr/local/bin/plasmate"
    cmd = strategy._build_cmd("https://example.com")
    assert "45000" in cmd


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_aenter_sets_binary():
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"):
        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)
        async with strategy:
            assert strategy._plasmate_bin == "/usr/local/bin/plasmate"


@pytest.mark.asyncio
async def test_aenter_raises_if_binary_missing():
    with patch("shutil.which", return_value=None), \
         patch("builtins.__import__", side_effect=ImportError):
        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)
        with pytest.raises(ImportError, match="plasmate is required"):
            await strategy.__aenter__()


@pytest.mark.asyncio
async def test_aexit_does_not_raise():
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"):
        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)
        async with strategy:
            pass  # __aexit__ should complete cleanly


# ---------------------------------------------------------------------------
# crawl() — success paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_returns_async_crawl_response():
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", return_value=_completed_process("Page text content")):
        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)
        async with strategy:
            response = await strategy.crawl("https://example.com")

    assert isinstance(response, AsyncCrawlResponse)
    assert response.status_code == 200
    assert "Page text content" in response.html


@pytest.mark.asyncio
async def test_crawl_markdown_format():
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", return_value=_completed_process("# Heading\n\nBody")):
        strategy = AsyncPlasmateCrawlerStrategy(output_format="markdown", verbose=False)
        async with strategy:
            response = await strategy.crawl("https://example.com")

    assert "# Heading" in response.html
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_crawl_som_format():
    som = '{"role":"document","children":[{"role":"heading","name":"Title"}]}'
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", return_value=_completed_process(som)):
        strategy = AsyncPlasmateCrawlerStrategy(output_format="som", verbose=False)
        async with strategy:
            response = await strategy.crawl("https://example.com")

    assert "heading" in response.html
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# crawl() — error paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_nonzero_returncode_returns_500():
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", return_value=_completed_process("", returncode=1)):
        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)
        async with strategy:
            response = await strategy.crawl("https://example.com")

    assert response.status_code == 500
    assert response.html == ""


@pytest.mark.asyncio
async def test_crawl_timeout_returns_504():
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="plasmate", timeout=30)):
        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)
        async with strategy:
            response = await strategy.crawl("https://example.com")

    assert response.status_code == 504
    assert response.html == ""


# ---------------------------------------------------------------------------
# Playwright fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_triggered_on_empty_response():
    fallback_html = "<html><body>Playwright fallback</body></html>"

    mock_fallback_response = AsyncCrawlResponse(
        html=fallback_html,
        response_headers={},
        status_code=200,
    )
    mock_strategy = MagicMock()
    mock_strategy.crawl = asyncio.coroutine(lambda url: mock_fallback_response) \
        if hasattr(asyncio, "coroutine") else None

    async def fake_crawl(url):
        return mock_fallback_response

    mock_strategy.crawl = fake_crawl
    mock_strategy.__aenter__ = asyncio.coroutine(lambda s: s) \
        if hasattr(asyncio, "coroutine") else None
    mock_strategy.__aexit__ = asyncio.coroutine(lambda s, *a: None) \
        if hasattr(asyncio, "coroutine") else None

    async def fake_aenter(self):
        return self

    async def fake_aexit(self, *args):
        pass

    mock_strategy.__aenter__ = lambda: fake_aenter(mock_strategy)
    mock_strategy.__aexit__ = lambda *a: fake_aexit(mock_strategy, *a)

    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", return_value=_completed_process("")), \
         patch(
             "crawl4ai.async_plasmate_strategy.AsyncPlaywrightCrawlerStrategy",
             return_value=mock_strategy,
         ):
        strategy = AsyncPlasmateCrawlerStrategy(fallback_to_playwright=True, verbose=False)
        async with strategy:
            response = await strategy.crawl("https://spa-example.com")

    assert "Playwright fallback" in response.html


@pytest.mark.asyncio
async def test_no_fallback_when_content_present():
    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", return_value=_completed_process("Real content")), \
         patch("crawl4ai.async_plasmate_strategy.AsyncPlaywrightCrawlerStrategy") as mock_pw:
        strategy = AsyncPlasmateCrawlerStrategy(fallback_to_playwright=True, verbose=False)
        async with strategy:
            response = await strategy.crawl("https://example.com")

    mock_pw.assert_not_called()
    assert "Real content" in response.html


# ---------------------------------------------------------------------------
# Async concurrency
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_multiple_urls_concurrently():
    """Ensure multiple crawl() calls can run concurrently (each is a short-lived subprocess)."""
    import time

    call_count = {"n": 0}

    def slow_run(*args, **kwargs):
        call_count["n"] += 1
        return _completed_process(f"content {call_count['n']}")

    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", side_effect=slow_run):
        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)
        async with strategy:
            urls = [f"https://example.com/{i}" for i in range(5)]
            responses = await asyncio.gather(*[strategy.crawl(u) for u in urls])

    assert len(responses) == 5
    assert all(r.status_code == 200 for r in responses)


# ---------------------------------------------------------------------------
# Integration with AsyncWebCrawler (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_drop_in_with_async_web_crawler():
    """Verify strategy is accepted by AsyncWebCrawler without errors."""
    from crawl4ai import AsyncWebCrawler

    with patch("shutil.which", return_value="/usr/local/bin/plasmate"), \
         patch("subprocess.run", return_value=_completed_process("crawled content")):

        strategy = AsyncPlasmateCrawlerStrategy(verbose=False)

        # Patch the webcrawler's __aenter__ to avoid browser initialisation
        with patch.object(AsyncWebCrawler, "__aenter__", return_value=MagicMock()), \
             patch.object(AsyncWebCrawler, "__aexit__", return_value=None):
            crawler = AsyncWebCrawler(crawler_strategy=strategy)
            assert crawler.crawler_strategy is strategy
