"""
AsyncPlasmateCrawlerStrategy — lightweight alternative to AsyncPlaywrightCrawlerStrategy.

Uses Plasmate (https://github.com/plasmate-labs/plasmate) instead of Chrome/Playwright.
Plasmate is an open-source Rust browser engine that outputs Structured Object Model (SOM)
instead of raw HTML, using ~64MB RAM per session vs ~300MB and delivering
10-100x fewer tokens per page — significantly reducing LLM costs.

Install: pip install plasmate
Docs:    https://plasmate.app
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from typing import Dict, List, Optional

from .async_crawler_strategy import AsyncCrawlerStrategy
from .async_logger import AsyncLogger
from .models import AsyncCrawlResponse

_INSTALL_MSG = (
    "plasmate is required for AsyncPlasmateCrawlerStrategy. "
    "Install it with: pip install plasmate\n"
    "Docs: https://plasmate.app"
)

_VALID_FORMATS = ("text", "markdown", "som", "links")


def _find_plasmate() -> Optional[str]:
    """Return the resolved path to the plasmate binary, or None."""
    path = shutil.which("plasmate")
    if path:
        return path
    try:
        import plasmate as _p  # noqa: F401
        return shutil.which("plasmate")
    except ImportError:
        return None


class AsyncPlasmateCrawlerStrategy(AsyncCrawlerStrategy):
    """Lightweight crawler strategy using Plasmate instead of Chrome/Playwright.

    Plasmate fetches pages and returns them as Structured Object Model (SOM)
    or plain text / markdown — no browser process, no GPU, no 300 MB Chrome.

    This strategy is a drop-in replacement for ``AsyncPlaywrightCrawlerStrategy``
    for static and server-rendered pages. For JavaScript-heavy SPAs that require
    a real browser, set ``fallback_to_playwright=True``.

    Attributes:
        output_format: Page output format — ``"text"`` (default), ``"markdown"``,
            ``"som"`` (full JSON), or ``"links"``.
        timeout: Per-request timeout in seconds. Defaults to 30.
        selector: Optional ARIA role or CSS id selector to scope extraction
            (e.g. ``"main"`` or ``"#article"``).
        extra_headers: Optional HTTP headers forwarded with each request.
        fallback_to_playwright: If True, retry with Playwright when Plasmate
            returns an empty response (handles SPAs automatically).
        verbose: Whether to emit log messages. Defaults to True.

    Example — drop-in replacement::

        import asyncio
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_plasmate_strategy import AsyncPlasmateCrawlerStrategy

        async def main():
            strategy = AsyncPlasmateCrawlerStrategy(
                output_format="markdown",
                timeout=30,
                fallback_to_playwright=True,
            )
            async with AsyncWebCrawler(crawler_strategy=strategy) as crawler:
                result = await crawler.arun("https://docs.python.org/3/")
                print(result.markdown[:500])

        asyncio.run(main())

    Example — direct use::

        strategy = AsyncPlasmateCrawlerStrategy(output_format="text")
        async with strategy:
            response = await strategy.crawl("https://example.com")
            print(response.html)  # clean text output, no HTML boilerplate
    """

    def __init__(
        self,
        output_format: str = "text",
        timeout: int = 30,
        selector: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        fallback_to_playwright: bool = False,
        verbose: bool = True,
        logger: Optional[AsyncLogger] = None,
        **kwargs,
    ):
        if output_format not in _VALID_FORMATS:
            raise ValueError(
                f"output_format must be one of {_VALID_FORMATS}; got {output_format!r}"
            )
        self.output_format = output_format
        self.timeout = timeout
        self.selector = selector
        self.extra_headers = extra_headers or {}
        self.fallback_to_playwright = fallback_to_playwright
        self.verbose = verbose
        self.logger = logger or AsyncLogger(verbose=verbose)
        self._plasmate_bin: Optional[str] = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "AsyncPlasmateCrawlerStrategy":
        self._plasmate_bin = _find_plasmate()
        if self._plasmate_bin is None:
            raise ImportError(_INSTALL_MSG)
        if self.verbose:
            self.logger.info(
                f"AsyncPlasmateCrawlerStrategy ready (format={self.output_format}, "
                f"timeout={self.timeout}s, fallback={self.fallback_to_playwright})",
                tag="INIT",
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # No persistent process to clean up — each fetch is a short-lived subprocess.
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_cmd(self, url: str) -> List[str]:
        """Build the plasmate CLI command for a URL."""
        cmd = [
            self._plasmate_bin,
            "fetch",
            url,
            "--format", self.output_format,
            "--timeout", str(self.timeout * 1000),  # plasmate uses ms
        ]
        if self.selector:
            cmd += ["--selector", self.selector]
        for key, value in self.extra_headers.items():
            cmd += ["--header", f"{key}: {value}"]
        return cmd

    async def _fetch(self, url: str) -> tuple[str, int]:
        """Run plasmate in a thread-pool executor; returns (content, status_code)."""
        loop = asyncio.get_event_loop()

        def _run() -> tuple[str, int]:
            try:
                result = subprocess.run(
                    self._build_cmd(url),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout + 5,
                )
                if result.returncode != 0:
                    if self.verbose:
                        self.logger.warning(
                            f"plasmate exited {result.returncode} for {url}: "
                            f"{result.stderr[:200]}",
                            tag="FETCH",
                        )
                    return "", 500
                return result.stdout.strip(), 200
            except subprocess.TimeoutExpired:
                if self.verbose:
                    self.logger.warning(f"Timeout fetching {url}", tag="FETCH")
                return "", 504
            except FileNotFoundError:
                raise ImportError(_INSTALL_MSG)

        return await loop.run_in_executor(None, _run)

    async def _playwright_fallback(self, url: str) -> tuple[str, int]:
        """Delegate to AsyncPlaywrightCrawlerStrategy and return its raw HTML."""
        if self.verbose:
            self.logger.info(
                f"Plasmate returned empty — falling back to Playwright for {url}",
                tag="FALLBACK",
            )
        from .async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

        strategy = AsyncPlaywrightCrawlerStrategy()
        async with strategy:
            response = await strategy.crawl(url)
        return response.html, response.status_code

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse:
        """Fetch *url* with Plasmate and return an :class:`AsyncCrawlResponse`.

        The ``html`` field of the response contains the Plasmate output in the
        requested format (text / markdown / SOM JSON / links) rather than raw HTML.
        Downstream Crawl4AI extraction strategies receive this pre-processed content,
        reducing token consumption before any LLM call.

        Args:
            url: The URL to fetch.
            **kwargs: Ignored (accepted for interface compatibility).

        Returns:
            :class:`AsyncCrawlResponse` with ``html`` set to Plasmate output.
        """
        if self.verbose:
            self.logger.info(f"Fetching: {url}", tag="FETCH")

        content, status_code = await self._fetch(url)

        if not content.strip() and self.fallback_to_playwright:
            content, status_code = await self._playwright_fallback(url)

        if self.verbose and content:
            self.logger.success(
                f"Got {len(content):,} chars from {url} "
                f"(format={self.output_format})",
                tag="FETCH",
            )

        return AsyncCrawlResponse(
            html=content,
            response_headers={},
            status_code=status_code,
        )
