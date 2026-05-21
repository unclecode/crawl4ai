import pytest

from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


class FakeFrame:
    def __init__(self, html, url):
        self._html = html
        self.url = url

    async def content(self):
        return self._html


class FakePage:
    def __init__(self, html, frames):
        self._html = html
        self.frames = frames

    async def content(self):
        return self._html


@pytest.mark.asyncio
async def test_try_follow_frameset_returns_single_full_viewport_child():
    child = FakeFrame("<html><body>Frame content</body></html>", "https://example.com/frame")
    page = FakePage(
        """
        <html>
          <frameset rows="100%">
            <frame src="https://example.com/frame">
          </frameset>
        </html>
        """,
        [FakeFrame("", "https://example.com"), child],
    )

    html, url = await AsyncPlaywrightCrawlerStrategy._try_follow_frameset(object(), page)

    assert html == "<html><body>Frame content</body></html>"
    assert url == "https://example.com/frame"


@pytest.mark.asyncio
async def test_try_follow_frameset_ignores_multi_frame_layout():
    page = FakePage(
        """
        <html>
          <frameset cols="25%,75%">
            <frame src="/nav"><frame src="/content">
          </frameset>
        </html>
        """,
        [
            FakeFrame("", "https://example.com"),
            FakeFrame("nav", "https://example.com/nav"),
            FakeFrame("content", "https://example.com/content"),
        ],
    )

    assert await AsyncPlaywrightCrawlerStrategy._try_follow_frameset(object(), page) == (None, None)


def test_crawler_run_config_follow_frames_round_trips():
    default_config = CrawlerRunConfig()
    disabled_config = CrawlerRunConfig(follow_frames=False)

    assert default_config.follow_frames is True
    assert default_config.to_dict()["follow_frames"] is True
    assert CrawlerRunConfig.from_kwargs({"follow_frames": False}).follow_frames is False
    assert disabled_config.to_dict()["follow_frames"] is False
