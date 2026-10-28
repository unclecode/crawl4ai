"""BrowserConfig.clone() must carry over fields that to_dict() used to drop."""

import inspect

from crawl4ai import BrowserConfig


def test_clone_preserves_cdp_connection_options():
    config = BrowserConfig(
        cdp_url="http://localhost:9222",
        cdp_close_delay=0,
        cache_cdp_connection=True,
    )

    cloned = config.clone(headless=False)

    assert cloned.cdp_close_delay == 0
    assert cloned.cache_cdp_connection is True
    assert cloned.headless is False


def test_clone_can_override_cdp_connection_options():
    config = BrowserConfig(cdp_close_delay=0, cache_cdp_connection=True)

    cloned = config.clone(cdp_close_delay=2.5, cache_cdp_connection=False)

    assert cloned.cdp_close_delay == 2.5
    assert cloned.cache_cdp_connection is False


def test_to_dict_distinguishes_cdp_connection_options():
    # The Docker browser pool keys browsers by a hash of to_dict().
    assert (
        BrowserConfig(cache_cdp_connection=True).to_dict()
        != BrowserConfig().to_dict()
    )
    assert BrowserConfig(cdp_close_delay=0).to_dict() != BrowserConfig().to_dict()


def test_to_dict_covers_every_init_param():
    params = set(inspect.signature(BrowserConfig.__init__).parameters) - {"self"}
    # viewport is unpacked into viewport_width/viewport_height, which to_dict() carries.
    missing = params - set(BrowserConfig().to_dict()) - {"viewport"}

    assert not missing, f"add these to BrowserConfig.to_dict(): {sorted(missing)}"
