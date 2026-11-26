"""Regression tests for #2628: direct file navigation downloads and API artifact delivery.

Covers:
1. Direct navigation to a file URL triggering ``Page.goto: Download is starting``
   when ``accept_downloads=True`` does not raise a fatal navigation error.
2. In-flight download tasks are tracked and awaited before page/context teardown
   so ``download.save_as`` is not cancelled and ``downloaded_files`` is populated.
3. ``accept_downloads=True`` without an explicit ``downloads_path`` resolves to a
   writable directory (never ``$CWD/downloads``) and falls back cleanly if home is
   not writable.
4. Concurrent crawls sharing a strategy keep downloads isolated and remove
   ``download`` listeners on page reuse.
5. End-to-end Playwright Chromium crawl against a local HTTP server serving both
   ``Content-Disposition: attachment`` PDFs and direct binary downloads (including
   slow streaming responses) succeeds without ``downloads_path``.
"""

import asyncio
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import AsyncMock, MagicMock

import pytest
from playwright.async_api import Error as PlaywrightError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig  # noqa: E402
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy  # noqa: E402
from crawl4ai.browser_manager import BrowserManager  # noqa: E402


class _FakeDownload:
    def __init__(self, filename: str, content: bytes = b"%PDF-1.4\ntest", delay: float = 0.0):
        self.suggested_filename = filename
        self._content = content
        self._delay = delay

    async def save_as(self, path: str) -> None:
        if self._delay:
            await asyncio.sleep(self._delay)
        with open(path, "wb") as f:
            f.write(self._content)


class _FakePage:
    def __init__(self, goto_exc=None, download_obj=None, fire_delay: float = 0.0):
        self.url = "about:blank"
        self._listeners = {}
        self._goto_exc = goto_exc
        self._download_obj = download_obj
        self._fire_delay = fire_delay
        self.closed = False

    def on(self, event, fn):
        self._listeners.setdefault(event, []).append(fn)

    def remove_listener(self, event, fn):
        if event in self._listeners and fn in self._listeners[event]:
            self._listeners[event].remove(fn)

    async def goto(self, url, **kwargs):
        if self._download_obj is not None:
            async def _emit():
                if self._fire_delay:
                    await asyncio.sleep(self._fire_delay)
                for fn in list(self._listeners.get("download", [])):
                    fn(self._download_obj)

            asyncio.create_task(_emit())
        if self._goto_exc is not None:
            raise self._goto_exc
        return None

    async def wait_for_selector(self, *args, **kwargs):
        return None

    async def evaluate(self, *args, **kwargs):
        return True

    async def content(self):
        return "<html><head></head><body></body></html>"

    async def close(self):
        self.closed = True


class _FakeBrowser:
    def __init__(self):
        self.contexts = []


class _FakeContext:
    def __init__(self):
        self.browser = _FakeBrowser()
        self.pages = []


class TestUnitDirectDownload2628:
    @pytest.mark.asyncio
    async def test_download_is_starting_error_handled_and_awaited(self, tmp_path):
        """Page.goto raising 'Download is starting' must succeed and await save_as."""
        dl_dir = str(tmp_path / "dl")
        os.makedirs(dl_dir, exist_ok=True)
        cfg = BrowserConfig(accept_downloads=True, downloads_path=dl_dir, verbose=False)
        strategy = AsyncPlaywrightCrawlerStrategy(browser_config=cfg)

        dl = _FakeDownload("datasheet.pdf", content=b"%PDF-1.4\nhello", delay=0.15)
        page = _FakePage(
            goto_exc=PlaywrightError("Page.goto: Download is starting"),
            download_obj=dl,
            fire_delay=0.02,
        )
        ctx = _FakeContext()
        ctx.pages.append(page)
        ctx.browser.contexts.append(ctx)

        strategy.browser_manager = MagicMock()
        strategy.browser_manager.get_page = AsyncMock(return_value=(page, ctx))
        strategy.browser_manager.release_page_with_context = AsyncMock()

        run_cfg = CrawlerRunConfig(delay_before_return_html=0.0, verbose=False)
        resp = await strategy._crawl_web("https://example.com/datasheet.pdf", run_cfg)

        assert resp.downloaded_files is not None
        assert len(resp.downloaded_files) == 1
        saved = resp.downloaded_files[0]
        assert saved.endswith("datasheet.pdf")
        with open(saved, "rb") as f:
            assert f.read() == b"%PDF-1.4\nhello"
        # Listener must be cleaned up on exit so reused pages don't accumulate handlers.
        assert page._listeners.get("download", []) == []

    @pytest.mark.asyncio
    async def test_accept_downloads_without_downloads_path_uses_writable_default(
        self, tmp_path, monkeypatch
    ):
        """accept_downloads=True with downloads_path=None must never fail with NoneType or write to read-only CWD."""
        ro_cwd = tmp_path / "readonly_app"
        ro_cwd.mkdir()
        os.chmod(ro_cwd, 0o555)
        monkeypatch.chdir(ro_cwd)
        monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(tmp_path / "home"))
        monkeypatch.delenv("CRAWL4AI_DOWNLOADS_DIR", raising=False)

        try:
            cfg = BrowserConfig(accept_downloads=True, downloads_path=None, verbose=False)
            bm = BrowserManager(browser_config=cfg)
            browser_args = bm._build_browser_args()
            assert browser_args["downloads_path"] is not None
            assert os.path.isdir(browser_args["downloads_path"])
            assert not browser_args["downloads_path"].startswith(str(ro_cwd))

            strategy = AsyncPlaywrightCrawlerStrategy(browser_config=cfg)
            dl = _FakeDownload("auto.bin", content=b"BINARYDATA")
            page = _FakePage(
                goto_exc=PlaywrightError("Page.goto: Download is starting"),
                download_obj=dl,
            )
            ctx = _FakeContext()
            ctx.pages.append(page)
            ctx.browser.contexts.append(ctx)

            strategy.browser_manager = MagicMock()
            strategy.browser_manager.get_page = AsyncMock(return_value=(page, ctx))
            strategy.browser_manager.release_page_with_context = AsyncMock()

            run_cfg = CrawlerRunConfig(delay_before_return_html=0.0, verbose=False)
            resp = await strategy._crawl_web("https://example.com/auto.bin", run_cfg)
            assert resp.downloaded_files and len(resp.downloaded_files) == 1
            assert os.path.isfile(resp.downloaded_files[0])
        finally:
            os.chmod(ro_cwd, 0o755)

    @pytest.mark.asyncio
    async def test_concurrent_crawls_isolate_downloads(self, tmp_path):
        """Concurrent _crawl_web invocations on one strategy do not cross-contaminate downloaded_files."""
        dl_dir = str(tmp_path / "dl")
        os.makedirs(dl_dir, exist_ok=True)
        cfg = BrowserConfig(accept_downloads=True, downloads_path=dl_dir, verbose=False)
        strategy = AsyncPlaywrightCrawlerStrategy(browser_config=cfg)

        page_a = _FakePage(
            goto_exc=PlaywrightError("Page.goto: Download is starting"),
            download_obj=_FakeDownload("a.pdf", content=b"AAA", delay=0.12),
        )
        page_b = _FakePage(
            goto_exc=PlaywrightError("Page.goto: Download is starting"),
            download_obj=_FakeDownload("b.pdf", content=b"BBB", delay=0.02),
        )
        ctx = _FakeContext()
        ctx.pages.extend([page_a, page_b])
        ctx.browser.contexts.append(ctx)

        pages = iter([(page_a, ctx), (page_b, ctx)])
        strategy.browser_manager = MagicMock()
        strategy.browser_manager.get_page = AsyncMock(side_effect=lambda **kw: next(pages))
        strategy.browser_manager.release_page_with_context = AsyncMock()

        resp_a, resp_b = await asyncio.gather(
            strategy._crawl_web("https://example.com/a.pdf", CrawlerRunConfig(delay_before_return_html=0.0, verbose=False)),
            strategy._crawl_web("https://example.com/b.pdf", CrawlerRunConfig(delay_before_return_html=0.0, verbose=False)),
        )

        assert resp_a.downloaded_files and len(resp_a.downloaded_files) == 1
        assert resp_a.downloaded_files[0].endswith("a.pdf")
        assert resp_b.downloaded_files and len(resp_b.downloaded_files) == 1
        assert resp_b.downloaded_files[0].endswith("b.pdf")

    @pytest.mark.asyncio
    async def test_download_is_starting_still_fails_when_accept_downloads_false(self):
        """Negative control: accept_downloads=False must still treat Download is starting as an error."""
        cfg = BrowserConfig(accept_downloads=False, verbose=False)
        strategy = AsyncPlaywrightCrawlerStrategy(browser_config=cfg)
        page = _FakePage(goto_exc=PlaywrightError("Page.goto: Download is starting"))
        ctx = _FakeContext()
        ctx.pages.append(page)
        ctx.browser.contexts.append(ctx)

        strategy.browser_manager = MagicMock()
        strategy.browser_manager.get_page = AsyncMock(return_value=(page, ctx))
        strategy.browser_manager.release_page_with_context = AsyncMock()

        with pytest.raises(RuntimeError, match="Download is starting"):
            await strategy._crawl_web(
                "https://example.com/file.pdf",
                CrawlerRunConfig(delay_before_return_html=0.0, verbose=False),
            )

    def test_resolve_downloads_path_falls_back_to_tempdir_when_home_readonly(
        self, tmp_path, monkeypatch
    ):
        """When home is read-only, resolve_downloads_path(None) falls back to tempdir."""
        from crawl4ai.utils import resolve_downloads_path

        ro_home = tmp_path / "ro_home"
        ro_home.mkdir()
        os.chmod(ro_home, 0o555)
        monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(ro_home))
        monkeypatch.delenv("CRAWL4AI_DOWNLOADS_DIR", raising=False)

        try:
            resolved = resolve_downloads_path(None)
            assert os.path.isdir(resolved)
            assert not resolved.startswith(str(ro_home))
        finally:
            os.chmod(ro_home, 0o755)


class _DownloadHandler(BaseHTTPRequestHandler):
    PDF_BYTES = b"%PDF-1.4\n%fake-pdf-payload-for-2628\n" + b"0" * 1024
    BIN_BYTES = b"\x00\x01\x02\x03CRAWL4AI_BIN" * 128

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/slow.pdf":
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", 'attachment; filename="slow_doc.pdf"')
            self.send_header("Content-Length", str(len(self.PDF_BYTES)))
            self.end_headers()
            mid = len(self.PDF_BYTES) // 2
            self.wfile.write(self.PDF_BYTES[:mid])
            self.wfile.flush()
            time.sleep(0.25)
            self.wfile.write(self.PDF_BYTES[mid:])
            self.wfile.flush()
        elif self.path == "/direct.bin":
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(self.BIN_BYTES)))
            self.end_headers()
            self.wfile.write(self.BIN_BYTES)
        elif self.path == "/page.html":
            body = b'<html><body><a id="dl" href="/slow.pdf">Download</a></body></html>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture(scope="module")
def local_download_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DownloadHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


class TestPlaywrightDirectDownloadE2E:
    @pytest.mark.asyncio
    async def test_direct_pdf_and_bin_download_without_downloads_path(
        self, local_download_server, tmp_path, monkeypatch
    ):
        """Real headless Chromium navigates to direct download URLs with no downloads_path."""
        monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(tmp_path / "home"))
        monkeypatch.delenv("CRAWL4AI_DOWNLOADS_DIR", raising=False)

        browser_cfg = BrowserConfig(headless=True, accept_downloads=True, verbose=False)
        run_cfg = CrawlerRunConfig(delay_before_return_html=0.0, verbose=False)

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            res_pdf = await crawler.arun(f"{local_download_server}/slow.pdf", config=run_cfg)
            assert res_pdf.success is True, res_pdf.error_message
            assert res_pdf.downloaded_files and len(res_pdf.downloaded_files) == 1
            with open(res_pdf.downloaded_files[0], "rb") as f:
                assert f.read() == _DownloadHandler.PDF_BYTES

            res_bin = await crawler.arun(f"{local_download_server}/direct.bin", config=run_cfg)
            assert res_bin.success is True, res_bin.error_message
            assert res_bin.downloaded_files and len(res_bin.downloaded_files) == 1
            with open(res_bin.downloaded_files[0], "rb") as f:
                assert f.read() == _DownloadHandler.BIN_BYTES

            res_click = await crawler.arun(
                f"{local_download_server}/page.html",
                config=CrawlerRunConfig(
                    delay_before_return_html=0.0,
                    js_code="document.getElementById('dl').click();",
                    verbose=False,
                ),
            )
            assert res_click.success is True, res_click.error_message
            assert res_click.downloaded_files and len(res_click.downloaded_files) == 1
            with open(res_click.downloaded_files[0], "rb") as f:
                assert f.read() == _DownloadHandler.PDF_BYTES
