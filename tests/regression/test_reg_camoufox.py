import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger
from crawl4ai.browser_manager import BrowserManager


def _skip_if_camoufox_unavailable():
    pytest.importorskip("camoufox.async_api")


def _skip_if_camoufox_runtime_missing(exc: Exception) -> None:
    message = str(exc).lower()
    environment_hints = (
        "camoufox fetch",
        "browser executable",
        "no such file or directory",
        "cannot open display",
        "xvfb",
        "shared object file",
        "libgtk",
    )
    if isinstance(exc, (FileNotFoundError, OSError)) or any(
        hint in message for hint in environment_hints
    ):
        pytest.skip(f"Camoufox runtime is not ready on this machine: {exc}")
    raise exc


@pytest.mark.asyncio
async def test_camoufox_static_crawl(local_server):
    _skip_if_camoufox_unavailable()
    browser_config = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        headless=True,
    )

    try:
        async with AsyncWebCrawler(
            config=browser_config,
            logger=AsyncLogger(verbose=False),
        ) as crawler:
            result = await crawler.arun(
                f"{local_server}/products",
                config=CrawlerRunConfig(screenshot=True),
            )
    except Exception as exc:
        _skip_if_camoufox_runtime_missing(exc)

    assert result.success is True
    assert "Product" in result.html
    assert result.screenshot is not None


@pytest.mark.asyncio
async def test_camoufox_js_dynamic_crawl(local_server):
    _skip_if_camoufox_unavailable()
    browser_config = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        headless=True,
    )

    try:
        async with AsyncWebCrawler(
            config=browser_config,
            logger=AsyncLogger(verbose=False),
        ) as crawler:
            result = await crawler.arun(
                f"{local_server}/js-dynamic",
                config=CrawlerRunConfig(wait_for="css:.js-loaded"),
            )
    except Exception as exc:
        _skip_if_camoufox_runtime_missing(exc)

    assert result.success is True
    assert "Dynamic content successfully loaded via JavaScript" in result.html


@pytest.mark.asyncio
async def test_camoufox_persistent_context_reuses_local_storage(local_server, tmp_path):
    _skip_if_camoufox_unavailable()
    profile_dir = tmp_path / "camoufox-profile"
    browser_config = BrowserConfig(
        browser_runtime="camoufox",
        browser_type="firefox",
        headless=True,
        use_persistent_context=True,
        user_data_dir=str(profile_dir),
    )

    manager = None
    manager_2 = None
    try:
        manager = BrowserManager(
            browser_config=browser_config,
            logger=AsyncLogger(verbose=False),
        )
        await manager.start()
        page, _ = await manager.get_page(CrawlerRunConfig(url=f"{local_server}/"))
        await page.goto(f"{local_server}/", wait_until="domcontentloaded")
        await page.evaluate(
            "localStorage.setItem('camoufox-persistent-key', 'camoufox-value')"
        )
        await manager.close()

        manager_2 = BrowserManager(
            browser_config=browser_config,
            logger=AsyncLogger(verbose=False),
        )
        await manager_2.start()
        page_2, _ = await manager_2.get_page(CrawlerRunConfig(url=f"{local_server}/"))
        await page_2.goto(f"{local_server}/", wait_until="domcontentloaded")
        persisted_value = await page_2.evaluate(
            "localStorage.getItem('camoufox-persistent-key')"
        )
    except Exception as exc:
        _skip_if_camoufox_runtime_missing(exc)
    finally:
        if manager is not None:
            await manager.close()
        if manager_2 is not None:
            await manager_2.close()

    assert persisted_value == "camoufox-value"
