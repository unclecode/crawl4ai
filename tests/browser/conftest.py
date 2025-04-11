# import logging
# import pytest


# from crawl4ai.async_configs import BrowserConfig
# from crawl4ai.browser import BrowserManager
# from crawl4ai.browser.strategies import BuiltinBrowserStrategy


# _LOGGER = logging.getLogger(__name__)

# async def cleanup_browsers():
#     """Clean up any remaining builtin browsers"""
#     browser_config = BrowserConfig(browser_mode="builtin", headless=True)
#     manager = BrowserManager(browser_config=browser_config)
#     strategy = manager._strategy
#     assert isinstance(strategy, BuiltinBrowserStrategy)

#     try:
#         # No need to start, just access the strategy directly
#         result = await strategy.kill_builtin_browser()
#         if result:
#             _LOGGER.info("Successfully killed all builtin browsers")
#         else:
#             _LOGGER.warning("No builtin browsers found to kill")
#     finally:
#         await manager.close()

# @pytest.mark.asyncio
# @pytest.hookimpl
# async def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
#     asyncio.run(cleanup_browsers())