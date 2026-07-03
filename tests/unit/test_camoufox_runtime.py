import types

import pytest

from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.browser_adapter import UndetectedAdapter
import crawl4ai.browser_manager as browser_manager_module
from crawl4ai.browser_manager import BrowserManager


class FakeContext:
    def __init__(self):
        self._impl_obj = types.SimpleNamespace(_options={})
        self.headers = []
        self.cookies = []
        self.init_scripts = []
        self.closed = False
        self.pages = []

    async def set_extra_http_headers(self, headers):
        self.headers.append(dict(headers))

    async def add_cookies(self, cookies):
        self.cookies.extend(cookies)

    async def storage_state(self, path=None):
        return {"cookies": [], "origins": []}

    def set_default_timeout(self, value):
        self.default_timeout = value

    def set_default_navigation_timeout(self, value):
        self.default_navigation_timeout = value

    async def add_init_script(self, script):
        self.init_scripts.append(script)

    async def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self):
        self.created_contexts = []
        self.closed = False

    async def new_context(self, **kwargs):
        context = FakeContext()
        context.context_kwargs = kwargs
        self.created_contexts.append(context)
        return context

    async def close(self):
        self.closed = True


class FakeAsyncCamoufox:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.entered = False
        self.exited = False
        self.result = None
        type(self).instances.append(self)

    async def __aenter__(self):
        self.entered = True
        if self.kwargs.get("persistent_context"):
            self.result = FakeContext()
        else:
            self.result = FakeBrowser()
        return self.result

    async def __aexit__(self, exc_type, exc, tb):
        self.exited = True


@pytest.fixture(autouse=True)
def reset_fake_instances():
    FakeAsyncCamoufox.instances.clear()
    yield
    FakeAsyncCamoufox.instances.clear()


def install_fake_camoufox(monkeypatch):
    real_import_module = browser_manager_module.importlib.import_module

    def fake_import_module(name, *args, **kwargs):
        if name == "camoufox.async_api":
            return types.SimpleNamespace(AsyncCamoufox=FakeAsyncCamoufox)
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(
        browser_manager_module.importlib, "import_module", fake_import_module
    )


def test_firefox_defaults_do_not_inherit_chrome_identity():
    cfg = BrowserConfig(browser_type="firefox")

    assert "Firefox/" in cfg.user_agent
    assert "Chrome/" not in cfg.user_agent
    assert "sec-ch-ua" not in cfg.headers
    assert cfg.browser_hint == ""


def test_chromium_defaults_stay_unchanged():
    cfg = BrowserConfig()

    assert "Chrome/" in cfg.user_agent
    assert cfg.headers["sec-ch-ua"]


@pytest.mark.parametrize("browser_type", ["chromium", "webkit"])
def test_camoufox_requires_firefox(browser_type):
    with pytest.raises(ValueError, match="requires browser_type='firefox'"):
        BrowserConfig(browser_runtime="camoufox", browser_type=browser_type)


@pytest.mark.parametrize("browser_mode", ["builtin", "custom", "docker", "cdp"])
def test_camoufox_requires_dedicated_browser_mode(browser_mode):
    with pytest.raises(ValueError, match="supports only browser_mode='dedicated'"):
        BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            browser_mode=browser_mode,
            cdp_url="ws://localhost:9222/devtools/browser/example"
            if browser_mode in {"custom", "cdp"}
            else None,
        )


def test_camoufox_rejects_cdp_url_even_in_dedicated_mode():
    with pytest.raises(ValueError, match="does not support cdp_url"):
        BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            cdp_url="ws://localhost:9222/devtools/browser/example",
        )


def test_camoufox_persistent_context_rejects_storage_state():
    with pytest.raises(ValueError, match="does not support storage_state"):
        BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            use_persistent_context=True,
            user_data_dir="/tmp/camoufox-profile",
            storage_state={"cookies": [], "origins": []},
        )


def test_camoufox_rejects_conflicting_proxy_sources():
    with pytest.raises(ValueError, match="Set only one proxy source"):
        BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            proxy_config={"server": "http://proxy.example:8080"},
            camoufox_options={"proxy": {"server": "http://other.example:8080"}},
        )


def test_camoufox_rejects_identity_headers():
    with pytest.raises(ValueError, match="identity-bearing BrowserConfig.headers"):
        BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            headers={"Accept-Language": "en-US,en;q=0.9"},
        )


def test_camoufox_rejects_enable_stealth():
    with pytest.raises(ValueError, match="cannot be combined with enable_stealth"):
        BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            enable_stealth=True,
        )


def test_camoufox_roundtrip_preserves_runtime_config():
    cfg = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        camoufox_options={"geoip": True, "humanize": True},
    )

    restored = BrowserConfig.from_kwargs(cfg.to_dict())
    cloned = cfg.clone()

    assert restored.browser_runtime == "camoufox"
    assert restored.camoufox_options == {"geoip": True, "humanize": True}
    assert cloned.browser_runtime == "camoufox"


@pytest.mark.parametrize(
    "field_name, field_value",
    [
        ("proxy_config", {"server": "http://proxy.example:8080"}),
        ("user_agent", "Mozilla/5.0 Custom"),
        ("user_agent_mode", "random"),
        ("locale", "en-US"),
        ("timezone_id", "UTC"),
        ("geolocation", {"latitude": 1.0, "longitude": 2.0, "accuracy": 3.0}),
        ("override_navigator", True),
        ("magic", True),
    ],
)
def test_camoufox_rejects_run_level_identity_overrides(field_name, field_value):
    cfg = BrowserConfig(browser_runtime="camoufox", browser_type="firefox")
    run_cfg = CrawlerRunConfig(**{field_name: field_value})

    with pytest.raises(ValueError, match="Remove these CrawlerRunConfig overrides"):
        cfg.validate_crawler_run_config(run_cfg)


def test_camoufox_rejects_undetected_adapter():
    with pytest.raises(ValueError, match="cannot be combined with UndetectedAdapter"):
        AsyncPlaywrightCrawlerStrategy(
            browser_config=BrowserConfig(
                browser_runtime="camoufox",
                browser_type="firefox",
            ),
            logger=AsyncLogger(verbose=False),
            browser_adapter=UndetectedAdapter(),
        )


def test_playwright_firefox_launch_args_skip_chromium_flags():
    manager = BrowserManager(
        browser_config=BrowserConfig(browser_type="firefox"),
        logger=AsyncLogger(verbose=False),
    )

    browser_args = manager._build_browser_args()

    assert browser_args["headless"] is True
    assert browser_args.get("args", []) == []
    assert "channel" not in browser_args


def test_camoufox_launch_args_include_camoufox_options_and_proxy():
    manager = BrowserManager(
        browser_config=BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            proxy_config={"server": "http://proxy.example:8080"},
            camoufox_options={"geoip": True, "humanize": True},
        ),
        logger=AsyncLogger(verbose=False),
    )

    browser_args = manager._build_browser_args()

    assert browser_args["headless"] is True
    assert browser_args["geoip"] is True
    assert browser_args["humanize"] is True
    assert browser_args["proxy"]["server"] == "http://proxy.example:8080"


@pytest.mark.asyncio
async def test_camoufox_browser_manager_dedicated_launch_and_cleanup(monkeypatch):
    install_fake_camoufox(monkeypatch)
    manager = BrowserManager(
        browser_config=BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            proxy_config={"server": "http://proxy.example:8080"},
            camoufox_options={"geoip": True},
        ),
        logger=AsyncLogger(verbose=False),
    )

    await manager.start()

    instance = FakeAsyncCamoufox.instances[-1]
    assert instance.entered is True
    assert instance.kwargs["geoip"] is True
    assert instance.kwargs["proxy"]["server"] == "http://proxy.example:8080"
    assert manager.browser is instance.result
    assert manager.default_context is manager.browser

    await manager.close()

    assert instance.exited is True


@pytest.mark.asyncio
async def test_camoufox_browser_manager_persistent_launch_and_cleanup(
    monkeypatch, tmp_path
):
    install_fake_camoufox(monkeypatch)
    profile_dir = tmp_path / "camoufox-profile"
    manager = BrowserManager(
        browser_config=BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            use_persistent_context=True,
            user_data_dir=str(profile_dir),
            camoufox_options={"geoip": True, "humanize": True},
        ),
        logger=AsyncLogger(verbose=False),
    )

    await manager.start()

    instance = FakeAsyncCamoufox.instances[-1]
    assert instance.entered is True
    assert instance.kwargs["persistent_context"] is True
    assert instance.kwargs["user_data_dir"] == str(profile_dir)
    assert instance.kwargs["geoip"] is True
    assert instance.kwargs["humanize"] is True
    assert manager.browser is None
    assert manager.default_context is instance.result

    await manager.close()

    assert instance.exited is True
