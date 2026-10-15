"""
Block detection must judge the FINAL hop of a redirect chain.

`CrawlResult.status_code` deliberately carries the first hop of a redirect
chain (issue #660, documented in docs/md_v2/api/crawl-result.md §1.3), while
the HTML always comes from the last hop, kept separately as
`redirected_status_code` (PR #1435, §1.4).  `async_webcrawler` used to hand the
first hop to `antibot_detector.is_blocked()`, so a 301 was judged instead of
the 403 it led to — and no status rule in `is_blocked` can fire on a 3xx.

Effect: any site that redirects (apex -> www, http -> https) and then serves a
4xx/5xx block page was returned as `success: True` with the block page as its
content.  Note `AsyncHTTPCrawlerStrategy` already sets `status_code` to the
post-redirect status, so the same URL produced different verdicts depending on
which crawler strategy ran.

No browser or network needed.

    pytest tests/proxy/test_antibot_redirect_status.py -q
"""

import asyncio

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.antibot_detector import effective_status, is_blocked
from crawl4ai.models import AsyncCrawlResponse

BLOCK_PAGE = (
    "<!DOCTYPE html><html><head><title>403 Forbidden</title></head><body>"
    "<h1>Error 403 Forbidden</h1><p>Forbidden</p><h3>Error 54113</h3>"
    "<p>Details: cache-ams-eham8680049-AMS</p><hr><p>Varnish cache server</p>"
    "</body></html>"
)

REAL_PAGE = (
    "<!DOCTYPE html><html><head><title>Example Co</title></head><body>"
    "<h1>Example Co</h1><p>Contact: info@example.com</p>"
    "<p>Phone +1 555 0100. Address: 1 Example Street, Springfield.</p>"
    "<ul><li>Services</li><li>References</li><li>Contact</li></ul>"
    "<p>Example Co is a company that does example things for example people.</p>"
    "</body></html>"
)


class _FakeStrategy:
    """Returns a canned AsyncCrawlResponse; counts page loads."""

    def __init__(self, response):
        self.response = response
        self.calls = 0

    def update_user_agent(self, ua):
        pass

    async def crawl(self, url, config=None, **kwargs):
        self.calls += 1
        return self.response


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


def _response(html, status_code, redirected_status_code=None, redirected_url=None):
    return AsyncCrawlResponse(
        html=html,
        response_headers={},
        status_code=status_code,
        redirected_status_code=redirected_status_code,
        redirected_url=redirected_url,
    )


async def _crawl(response, url="https://example.com", max_retries=1):
    strategy = _FakeStrategy(response)
    crawler = AsyncWebCrawler(crawler_strategy=strategy)
    crawler.ready = True  # skip start(): no browser is launched
    result = await crawler.arun(url, config=CrawlerRunConfig(max_retries=max_retries))
    return result, strategy


def test_effective_status_prefers_the_final_hop():
    assert effective_status(301, 403) == 403
    assert effective_status(302, 200) == 200


def test_effective_status_falls_back_without_a_redirect():
    # raw:, file:// and js_only paths leave redirected_status_code as None.
    assert effective_status(200, None) == 200
    assert effective_status(None, None) is None
    assert effective_status(403, 403) == 403


def test_block_page_behind_a_redirect_is_detected():
    async def main():
        result, _ = await _crawl(
            _response(BLOCK_PAGE, 301, 403, "https://www.example.com/")
        )
        assert result.success is False
        assert result.error_message.startswith("Blocked by anti-bot protection:")
        assert "403" in result.error_message
        # status_code semantics are unchanged: still the first hop.
        assert result.status_code == 301
        assert result.redirected_status_code == 403

    _run(main())


def test_block_page_without_a_redirect_still_detected():
    async def main():
        result, _ = await _crawl(_response(BLOCK_PAGE, 403, 403))
        assert result.success is False
        assert "Blocked by anti-bot protection:" in result.error_message

    _run(main())


def test_benign_redirect_is_not_a_false_positive():
    async def main():
        result, strategy = await _crawl(
            _response(REAL_PAGE, 301, 200, "https://www.example.com/"),
            url="http://example.com",
        )
        assert result.success is True
        assert not result.error_message
        assert strategy.calls == 1  # no retry burned on a good page

    _run(main())


def test_no_redirect_is_a_no_op():
    async def main():
        result, strategy = await _crawl(_response(REAL_PAGE, 200, 200))
        assert result.success is True
        assert strategy.calls == 1

    _run(main())


def test_raw_url_still_skips_block_detection():
    async def main():
        result, _ = await _crawl(
            _response(BLOCK_PAGE, 200, None), url="raw:" + BLOCK_PAGE
        )
        assert result.success is True

    _run(main())


def test_detector_itself_is_unchanged():
    # Only the argument changed; is_blocked's own rules are untouched.
    assert is_blocked(301, BLOCK_PAGE)[0] is False
    assert is_blocked(403, BLOCK_PAGE)[0] is True
