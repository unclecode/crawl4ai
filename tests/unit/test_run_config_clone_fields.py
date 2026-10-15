"""CrawlerRunConfig.clone() must carry over fields that to_dict() used to drop."""

from crawl4ai import CrawlerRunConfig
from crawl4ai.async_configs import VirtualScrollConfig


async def _fallback(url: str) -> str:
    return "<html><body>fallback</body></html>"


def test_clone_preserves_fallback_fetch_function():
    config = CrawlerRunConfig(fallback_fetch_function=_fallback)

    cloned = config.clone(deep_crawl_strategy=None, stream=True)

    assert cloned.fallback_fetch_function is _fallback
    assert cloned.stream is True


def test_clone_can_override_fallback_fetch_function():
    config = CrawlerRunConfig(fallback_fetch_function=_fallback)

    assert config.clone(fallback_fetch_function=None).fallback_fetch_function is None


def test_clone_preserves_cache_validation_and_virtual_scroll():
    scroll = VirtualScrollConfig(container_selector="#feed")
    config = CrawlerRunConfig(
        check_cache_freshness=True,
        cache_validation_timeout=3.5,
        virtual_scroll_config=scroll,
    )

    cloned = config.clone(stream=True)

    assert cloned.check_cache_freshness is True
    assert cloned.cache_validation_timeout == 3.5
    assert cloned.virtual_scroll_config is scroll
