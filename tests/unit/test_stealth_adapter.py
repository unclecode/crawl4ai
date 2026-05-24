import importlib.util
import sys
import types
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "crawl4ai" / "browser_adapter.py"


def load_browser_adapter():
    spec = importlib.util.spec_from_file_location("browser_adapter_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyPage:
    pass


def test_stealth_adapter_uses_playwright_stealth_v2(monkeypatch):
    calls = []

    class Stealth:
        async def apply_stealth_async(self, page):
            calls.append(page)

    monkeypatch.setitem(sys.modules, "playwright_stealth", types.SimpleNamespace(Stealth=Stealth))
    StealthAdapter = load_browser_adapter().StealthAdapter

    adapter = StealthAdapter()
    page = DummyPage()

    assert adapter._stealth_available is True

    import asyncio

    asyncio.run(adapter.apply_stealth(page))

    assert calls == [page]


def test_stealth_adapter_keeps_legacy_function_support(monkeypatch):
    calls = []

    async def stealth_async(page):
        calls.append(page)

    module = types.ModuleType("playwright_stealth")
    module.stealth_async = stealth_async
    monkeypatch.setitem(sys.modules, "playwright_stealth", module)
    StealthAdapter = load_browser_adapter().StealthAdapter

    adapter = StealthAdapter()
    page = DummyPage()

    assert adapter._stealth_available is True

    import asyncio

    asyncio.run(adapter.apply_stealth(page))

    assert calls == [page]
