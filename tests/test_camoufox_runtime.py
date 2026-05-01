import sys
import types

import pytest

from crawl4ai.async_configs import BrowserConfig
from crawl4ai.browser_manager import BrowserManager


class FakeCamoufoxPage:
    async def close(self):
        return None


class FakeCamoufoxContext:
    def __init__(self):
        self.pages = []
        self.closed = False
        self.headers = None
        self.cookies = []
        self.init_scripts = []

    async def new_page(self):
        page = FakeCamoufoxPage()
        self.pages.append(page)
        return page

    async def close(self):
        self.closed = True

    async def set_extra_http_headers(self, headers):
        self.headers = headers

    async def add_cookies(self, cookies):
        self.cookies.extend(cookies)

    async def add_init_script(self, script):
        self.init_scripts.append(script)


class FakeCamoufoxBrowser:
    def __init__(self):
        self.contexts = []
        self.closed = False

    async def new_context(self, **kwargs):
        context = FakeCamoufoxContext()
        context.kwargs = kwargs
        self.contexts.append(context)
        return context

    async def close(self):
        self.closed = True


class FakeAsyncCamoufox:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.exited = False
        self.payload = FakeCamoufoxContext() if kwargs.get("persistent_context") else FakeCamoufoxBrowser()
        FakeAsyncCamoufox.instances.append(self)

    async def __aenter__(self):
        return self.payload

    async def __aexit__(self, exc_type, exc, tb):
        self.exited = True


@pytest.fixture(autouse=True)
def fake_camoufox_module(monkeypatch):
    FakeAsyncCamoufox.instances.clear()
    module = types.SimpleNamespace(AsyncCamoufox=FakeAsyncCamoufox)
    monkeypatch.setitem(sys.modules, "camoufox", types.SimpleNamespace(async_api=module))
    monkeypatch.setitem(sys.modules, "camoufox.async_api", module)


def test_camoufox_browser_config_validates_runtime():
    cfg = BrowserConfig(browser_runtime="camoufox", browser_type="firefox")

    assert cfg.browser_runtime == "camoufox"
    assert cfg.browser_type == "firefox"


def test_camoufox_browser_config_rejects_chromium():
    with pytest.raises(ValueError, match="requires browser_type='firefox'"):
        BrowserConfig(browser_runtime="camoufox", browser_type="chromium")


def test_camoufox_browser_config_rejects_proxy_conflict():
    with pytest.raises(ValueError, match="cannot use both proxy_config"):
        BrowserConfig(
            browser_runtime="camoufox",
            browser_type="firefox",
            proxy_config={"server": "http://proxy.example:8080"},
            camoufox_options={"proxy": {"server": "http://other.example:8080"}},
        )


@pytest.mark.asyncio
async def test_browser_manager_launches_camoufox_with_options():
    cfg = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        camoufox_options={"geoip": True, "humanize": True, "headless": "virtual"},
        proxy_config={"server": "http://proxy.example:8080", "username": "u", "password": "p"},
    )
    manager = BrowserManager(cfg)

    await manager.start()
    await manager.close()

    assert len(FakeAsyncCamoufox.instances) == 1
    instance = FakeAsyncCamoufox.instances[0]
    assert instance.kwargs["geoip"] is True
    assert instance.kwargs["humanize"] is True
    assert instance.kwargs["headless"] == "virtual"
    assert instance.kwargs["proxy"] == {
        "server": "http://proxy.example:8080",
        "username": "u",
        "password": "p",
    }
    assert instance.exited is True


@pytest.mark.asyncio
async def test_browser_manager_supports_camoufox_context_creation():
    cfg = BrowserConfig(browser_runtime="camoufox", browser_type="firefox")
    manager = BrowserManager(cfg)

    await manager.start()
    context = await manager.create_browser_context()
    await manager.close()

    assert context.kwargs["viewport"] == {"width": 1080, "height": 600}
    assert context.kwargs["java_script_enabled"] is True


@pytest.mark.asyncio
async def test_camoufox_persistent_context_requires_user_data_dir():
    cfg = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        use_persistent_context=True,
    )
    manager = BrowserManager(cfg)

    with pytest.raises(ValueError, match="requires user_data_dir"):
        await manager.start()
