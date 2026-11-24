"""Issue #2239: OptimizationHints must not appear in built --disable-features.

Chrome-for-Testing 151+ SEGV_ACCERRs under --headless=new on macOS arm64 when
OptimizationHints is disabled. MediaRouter and DialMediaRouteProvider stay.

These are flag-construction checks only — no browser or network required.

#2219 merges repeated --disable-features switches and currently expects
OptimizationHints to survive that merge. After this change the surviving
defaults are MediaRouter and DialMediaRouteProvider only.
"""

from crawl4ai import BrowserConfig
from crawl4ai.browser_manager import BrowserManager, ManagedBrowser


def _disable_feature_names(args):
    """Every name listed in any --disable-features switch (not last-wins)."""
    names = []
    for arg in args:
        if arg.startswith("--disable-features="):
            names.extend(
                name.strip()
                for name in arg.split("=", 1)[1].split(",")
                if name.strip()
            )
    return names


def test_build_browser_flags_omits_optimization_hints():
    config = BrowserConfig(headless=True)
    names = _disable_feature_names(ManagedBrowser.build_browser_flags(config))
    assert "OptimizationHints" not in names
    assert "MediaRouter" in names
    assert "DialMediaRouteProvider" in names


def test_build_browser_args_omits_optimization_hints():
    config = BrowserConfig(headless=True)
    args = BrowserManager(browser_config=config)._build_browser_args()["args"]
    names = _disable_feature_names(args)
    assert "OptimizationHints" not in names
    assert "MediaRouter" in names
    assert "DialMediaRouteProvider" in names


def test_light_mode_still_omits_optimization_hints():
    """light_mode appends BROWSER_DISABLE_OPTIONS; OptimizationHints must
    not reappear there either. Aligns with #2219's merge expectations:
    MediaRouter / DialMediaRouteProvider remain the crawl4ai defaults."""
    config = BrowserConfig(headless=True, light_mode=True)
    for flags in (
        ManagedBrowser.build_browser_flags(config),
        BrowserManager(browser_config=config)._build_browser_args()["args"],
    ):
        names = _disable_feature_names(flags)
        assert "OptimizationHints" not in names
        assert "MediaRouter" in names
        assert "DialMediaRouteProvider" in names
