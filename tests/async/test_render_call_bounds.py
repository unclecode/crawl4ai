"""
Playwright calls that carry no protocol timeout must still be bounded.

`page.content()` and `page.evaluate()` are sent to the driver with **no**
`timeout` field, so no timer is armed server-side and they can only end when
they get a reply or the target closes.  What they wait on is the frame's
execution-context promise, which every navigation replaces with a fresh,
unresolved one.  A page that keeps committing navigations therefore wedges them
forever: `page_timeout` does not cover it (that reaches only `page.goto` and the
`wait_*` family), and because the call sites wrap them in swallow-all
`try/except`, nothing is logged either.

Three bounds are pinned here, outermost last:
  1. `bounded_evaluate`  — every adapter-mediated `page.evaluate`
  2. `_capture_html`     — `page.content()`, with settle-and-retry
  3. `total_timeout`     — one budget shared by every attempt in `arun()`

No browser and no network needed.

    pytest tests/async/test_render_call_bounds.py -q
"""

import asyncio
import time

import pytest
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import async_crawler_strategy as acs
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.browser_adapter import (
    EVALUATE_TIMEOUT_S,
    PlaywrightAdapter,
    bounded_evaluate,
)
from crawl4ai.models import AsyncCrawlResponse

# The exact message Playwright raises when the context dies mid-capture.
NAVIGATING = (
    "Page.content: Unable to retrieve content because the page is navigating "
    "and changing the content."
)

PAGE_HTML = (
    "<!DOCTYPE html><html><head><title>Example Co</title></head><body>"
    "<h1>Example Co</h1><p>Contact: info@example.com</p>"
    "<p>Phone +1 555 0100. Address: 1 Example Street, Springfield.</p>"
    "<ul><li>Services</li><li>References</li><li>Contact</li></ul>"
    "<p>Example Co is a company that does example things for example people.</p>"
    "</body></html>"
)


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


async def _never():
    """Models an untimed protocol call issued against a wedged page."""
    await asyncio.Event().wait()


class _Logger:
    def debug(self, *a, **kw):
        pass

    def warning(self, *a, **kw):
        pass

    def error(self, *a, **kw):
        pass


class _FakePage:
    def __init__(self, content_behaviour, settle_ok=True):
        # each entry is "hang", "navigating", or the HTML to return
        self.behaviour = list(content_behaviour)
        self.settle_ok = settle_ok
        self.content_calls = 0
        self.settle_calls = 0

    async def content(self):
        self.content_calls += 1
        step = self.behaviour.pop(0) if self.behaviour else PAGE_HTML
        if step == "hang":
            await _never()
        if step == "navigating":
            raise PlaywrightError(NAVIGATING)
        return step

    async def wait_for_load_state(self, state, timeout=None):
        self.settle_calls += 1
        if not self.settle_ok:
            raise PlaywrightTimeoutError(f"Timeout {timeout}ms exceeded")


def _strategy():
    """_capture_html needs only .logger — build without __init__ so the test
    never touches BrowserManager or Playwright."""
    s = AsyncPlaywrightCrawlerStrategy.__new__(AsyncPlaywrightCrawlerStrategy)
    s.logger = _Logger()
    return s


# --- 1. bounded_evaluate ---------------------------------------------------


def test_bounded_evaluate_returns_the_value():
    async def main():
        async def ok():
            return {"width": 100}

        assert await bounded_evaluate(ok(), 5) == {"width": 100}

    _run(main())


def test_bounded_evaluate_raises_instead_of_hanging():
    async def main():
        t0 = time.perf_counter()
        with pytest.raises(PlaywrightTimeoutError) as exc:
            await bounded_evaluate(_never(), 0.2)
        assert time.perf_counter() - t0 < 3
        assert "navigating" in str(exc.value)

    _run(main())


def test_bounded_evaluate_error_is_catchable_by_existing_handlers():
    """Call sites wrap evaluate in `except Exception` / `except Error`. The
    bound must not escape either, or a cosmetic skip becomes a hard failure."""

    async def main():
        try:
            await bounded_evaluate(_never(), 0.1)
        except Exception as e:
            assert isinstance(e, PlaywrightError)
            return
        raise AssertionError("no exception raised")

    _run(main())


def test_adapter_evaluate_honours_an_explicit_timeout():
    class HangingPage:
        async def evaluate(self, expression, *a, **kw):
            await _never()

    async def main():
        t0 = time.perf_counter()
        with pytest.raises(PlaywrightTimeoutError):
            await PlaywrightAdapter().evaluate(HangingPage(), "1+1", timeout=0.2)
        assert time.perf_counter() - t0 < 3

    _run(main())


def test_adapter_default_timeout_is_finite():
    assert 0 < EVALUATE_TIMEOUT_S < 120
    assert 0 < acs.OPTIONAL_DOM_STEP_TIMEOUT_S <= EVALUATE_TIMEOUT_S


# --- 2. _capture_html ------------------------------------------------------


def test_capture_succeeds_first_try():
    async def main():
        page = _FakePage([PAGE_HTML])
        assert await _strategy()._capture_html(page) == PAGE_HTML
        assert page.content_calls == 1
        assert page.settle_calls == 0

    _run(main())


def test_capture_retries_after_the_navigation_race_and_succeeds():
    """The documented remedy for "the page is navigating and changing the
    content" is to capture again once the navigation settles, not to throw the
    whole crawl away."""

    async def main():
        page = _FakePage(["navigating", PAGE_HTML])
        assert await _strategy()._capture_html(page) == PAGE_HTML
        assert page.content_calls == 2
        assert page.settle_calls == 1

    _run(main())


def test_capture_gives_up_after_the_configured_attempts():
    async def main():
        page = _FakePage(["navigating"] * 10)
        with pytest.raises(PlaywrightError):
            await _strategy()._capture_html(page)
        assert page.content_calls == acs.HTML_CAPTURE_ATTEMPTS

    _run(main())


def test_capture_bails_out_when_the_page_cannot_settle():
    """A page that cannot even reach domcontentloaded is stuck, not between
    documents — another attempt would only buy another full timeout."""

    async def main():
        page = _FakePage(["navigating"] * 10, settle_ok=False)
        with pytest.raises(PlaywrightError):
            await _strategy()._capture_html(page)
        assert page.content_calls == 1

    _run(main())


def test_capture_bounds_a_hanging_content_call(monkeypatch):
    monkeypatch.setattr(acs, "HTML_CAPTURE_TIMEOUT_S", 0.2)
    monkeypatch.setattr(acs, "HTML_CAPTURE_TOTAL_TIMEOUT_S", 0.5)
    monkeypatch.setattr(acs, "HTML_CAPTURE_SETTLE_TIMEOUT_S", 0.1)

    async def main():
        page = _FakePage(["hang"] * 10)
        t0 = time.perf_counter()
        with pytest.raises(PlaywrightTimeoutError):
            await _strategy()._capture_html(page)
        # Bounded by the GROUP budget, not attempts x per-call timeout.
        assert time.perf_counter() - t0 < 2.0

    _run(main())


# --- 3. total_timeout ------------------------------------------------------


class _SlowStrategy:
    def __init__(self, delay):
        self.delay = delay
        self.calls = 0

    def update_user_agent(self, ua):
        pass

    async def crawl(self, url, config=None, **kwargs):
        self.calls += 1
        await asyncio.sleep(self.delay)
        return AsyncCrawlResponse(
            html=PAGE_HTML,
            response_headers={},
            status_code=200,
            redirected_status_code=200,
        )


async def _arun(strategy, **cfg):
    crawler = AsyncWebCrawler(crawler_strategy=strategy)
    crawler.ready = True
    return await crawler.arun("https://example.com", config=CrawlerRunConfig(**cfg))


def test_total_timeout_bounds_a_slow_attempt():
    async def main():
        strategy = _SlowStrategy(delay=5)
        t0 = time.perf_counter()
        result = await _arun(strategy, max_retries=1, total_timeout=400)
        assert time.perf_counter() - t0 < 3
        assert result.success is False
        # Attributable: the message names the budget, not just "failed".
        assert "400 ms" in result.error_message

    _run(main())


def test_total_timeout_is_shared_across_attempts_not_per_attempt():
    """Otherwise max_retries silently multiplies the caller's deadline."""

    async def main():
        strategy = _SlowStrategy(delay=5)
        t0 = time.perf_counter()
        await _arun(strategy, max_retries=3, total_timeout=400)
        assert time.perf_counter() - t0 < 3
        assert strategy.calls <= 2

    _run(main())


def test_total_timeout_defaults_to_off():
    async def main():
        assert CrawlerRunConfig().total_timeout is None
        strategy = _SlowStrategy(delay=0.2)
        result = await _arun(strategy, max_retries=0)
        assert result.success is True
        assert strategy.calls == 1

    _run(main())


def test_total_timeout_survives_clone_and_to_dict():
    cfg = CrawlerRunConfig(total_timeout=100000)
    assert cfg.to_dict()["total_timeout"] == 100000
    assert cfg.clone().total_timeout == 100000
    assert CrawlerRunConfig.from_kwargs({"total_timeout": 123}).total_timeout == 123
