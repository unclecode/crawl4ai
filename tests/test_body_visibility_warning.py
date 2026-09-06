"""The body-visibility wait must not time out silently (issue #2144).

When the wait times out and `ignore_body_visibility` is True (the default), the
result is discarded and the crawl succeeds — just `body_visibility_timeout` ms
slower, with no signal at all. That silence is what made the delay in #2129
impossible to attribute without instrumenting the pipeline, and what makes
`body_visibility_timeout` undiscoverable. A warning names the option.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


def _strategy(is_visible: bool, wait_seconds: float = 0.0):
    """A strategy whose body-visibility wait returns `is_visible` after
    `wait_seconds` of (real) waiting."""
    page = MagicMock()
    page.evaluate = AsyncMock()
    page.set_content = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.content = AsyncMock(return_value="<body>hi</body>")

    strategy = AsyncPlaywrightCrawlerStrategy.__new__(AsyncPlaywrightCrawlerStrategy)
    strategy.browser_config = SimpleNamespace(
        use_persistent_context=False, accept_downloads=False, text_mode=True, verbose=False
    )
    strategy.browser_manager = SimpleNamespace(
        get_page=AsyncMock(return_value=(page, MagicMock()))
    )
    strategy.execute_hook = AsyncMock()

    async def wait(*args, **kwargs):
        await asyncio.sleep(wait_seconds)
        return is_visible

    strategy.csp_compliant_wait = AsyncMock(side_effect=wait)
    strategy.check_visibility = AsyncMock(return_value={})
    strategy.logger = MagicMock()
    return strategy


def _visibility_warnings(strategy):
    """The body-visibility warning calls, selected by message rather than by
    position — other warnings may fire on the same crawl."""
    return [
        call
        for call in strategy.logger.warning.call_args_list
        if "never became visible" in call.kwargs.get("message", "")
    ]


@pytest.mark.asyncio
async def test_warns_when_wait_times_out_and_result_is_discarded():
    strategy = _strategy(is_visible=False, wait_seconds=0.1)
    config = CrawlerRunConfig(session_id="body-vis-warn", body_visibility_timeout=100)

    await strategy._crawl_web("raw:<body>hi</body>", config)

    calls = _visibility_warnings(strategy)
    assert len(calls) == 1, strategy.logger.warning.call_args_list
    assert "body_visibility_timeout" in calls[0].kwargs["message"]
    # The time actually spent is reported, so the number matches the delay the
    # user is trying to explain.
    assert calls[0].kwargs["params"]["elapsed"] >= 90


@pytest.mark.asyncio
async def test_warning_is_not_suppressed_by_verbose_off():
    """Servers and batch jobs run with verbose off — the case that most needs
    this warning. Without force_verbose the logger drops it (#2144)."""
    strategy = _strategy(is_visible=False, wait_seconds=0.1)
    config = CrawlerRunConfig(
        session_id="body-vis-quiet-logger", body_visibility_timeout=100, verbose=False
    )

    await strategy._crawl_web("raw:<body>hi</body>", config)

    calls = _visibility_warnings(strategy)
    assert len(calls) == 1
    assert calls[0].kwargs.get("force_verbose") is True


@pytest.mark.asyncio
async def test_no_warning_when_wait_fails_early():
    """csp_compliant_wait also returns False when the evaluation errors out
    (page closed, context destroyed) — that costs no time, so blaming
    body_visibility_timeout for it would send the user after the wrong knob."""
    strategy = _strategy(is_visible=False, wait_seconds=0.0)
    config = CrawlerRunConfig(
        session_id="body-vis-early-fail", body_visibility_timeout=30000
    )

    await strategy._crawl_web("raw:<body>hi</body>", config)

    assert _visibility_warnings(strategy) == []


@pytest.mark.asyncio
async def test_no_warning_when_body_is_visible():
    strategy = _strategy(is_visible=True)
    config = CrawlerRunConfig(session_id="body-vis-quiet")

    await strategy._crawl_web("raw:<body>hi</body>", config)

    assert _visibility_warnings(strategy) == []


@pytest.mark.asyncio
async def test_no_warning_when_hidden_body_is_treated_as_an_error():
    """With ignore_body_visibility=False the hidden body raises with details,
    so the warning would be redundant noise."""
    from playwright.async_api import Error

    strategy = _strategy(is_visible=False)
    config = CrawlerRunConfig(
        session_id="body-vis-strict", ignore_body_visibility=False
    )

    with pytest.raises(Error, match="Body element is hidden"):
        await strategy._crawl_web("raw:<body>hi</body>", config)

    assert _visibility_warnings(strategy) == []
