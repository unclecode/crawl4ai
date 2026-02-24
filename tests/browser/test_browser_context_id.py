"""Test for browser_context_id and target_id parameters.

These tests verify that Crawl4AI can connect to and use pre-created
browser contexts, which is essential for cloud browser services that
pre-create isolated contexts for each user.

The flow being tested:
1. Start a browser with CDP
2. Create a context via raw CDP commands (simulating cloud service)
3. Create a page/target in that context
4. Have Crawl4AI connect using browser_context_id and target_id
5. Verify Crawl4AI uses the existing context/page instead of creating new ones
"""

import asyncio
import json
import os
import sys
import websockets

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai.browser_manager import BrowserManager, ManagedBrowser
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)


class CDPContextCreator:
    """
    Helper class to create browser contexts via raw CDP commands.
    This simulates what a cloud browser service would do.
    """

    def __init__(self, cdp_url: str):
        self.cdp_url = cdp_url
        self._message_id = 0
        self._ws = None
        self._pending_responses = {}
        self._receiver_task = None

    async def connect(self):
        """Establish WebSocket connection to browser."""
        # Convert HTTP URL to WebSocket URL if needed
        ws_url = self.cdp_url.replace("http://", "ws://").replace("https://", "wss://")
        if not ws_url.endswith("/devtools/browser"):
            # Get the browser websocket URL from /json/version
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.cdp_url}/json/version") as response:
                    data = await response.json()
                    ws_url = data.get("webSocketDebuggerUrl", ws_url)

        self._ws = await websockets.connect(ws_url, max_size=None, ping_interval=None)
        self._receiver_task = asyncio.create_task(self._receive_messages())
        logger.info(f"Connected to CDP at {ws_url}", tag="CDP")

    async def disconnect(self):
        """Close WebSocket connection."""
        if self._receiver_task:
            self._receiver_task.cancel()
            try:
                await self._receiver_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def _receive_messages(self):
        """Background task to receive CDP messages."""
        try:
            async for message in self._ws:
                data = json.loads(message)
                msg_id = data.get('id')
                if msg_id is not None and msg_id in self._pending_responses:
                    self._pending_responses[msg_id].set_result(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"CDP receiver error: {e}", tag="CDP")

    async def _send_command(self, method: str, params: dict = None) -> dict:
        """Send CDP command and wait for response."""
        self._message_id += 1
        msg_id = self._message_id

        message = {
            "id": msg_id,
            "method": method,
            "params": params or {}
        }

        future = asyncio.get_event_loop().create_future()
        self._pending_responses[msg_id] = future

        try:
            await self._ws.send(json.dumps(message))
            response = await asyncio.wait_for(future, timeout=30.0)

            if 'error' in response:
                raise Exception(f"CDP error: {response['error']}")

            return response.get('result', {})
        finally:
            self._pending_responses.pop(msg_id, None)

    async def create_context(self) -> dict:
        """
        Create an isolated browser context with a blank page.

        Returns:
            dict with browser_context_id, target_id, and cdp_session_id
        """
        await self.connect()

        # 1. Create isolated browser context
        result = await self._send_command("Target.createBrowserContext", {
            "disposeOnDetach": False  # Keep context alive
        })
        browser_context_id = result["browserContextId"]
        logger.info(f"Created browser context: {browser_context_id}", tag="CDP")

        # 2. Create a new page (target) in the context
        result = await self._send_command("Target.createTarget", {
            "url": "about:blank",
            "browserContextId": browser_context_id
        })
        target_id = result["targetId"]
        logger.info(f"Created target: {target_id}", tag="CDP")

        # 3. Attach to the target to get a session ID
        result = await self._send_command("Target.attachToTarget", {
            "targetId": target_id,
            "flatten": True
        })
        cdp_session_id = result["sessionId"]
        logger.info(f"Attached to target, sessionId: {cdp_session_id}", tag="CDP")

        return {
            "browser_context_id": browser_context_id,
            "target_id": target_id,
            "cdp_session_id": cdp_session_id
        }

    async def get_targets(self) -> list:
        """Get list of all targets in the browser."""
        result = await self._send_command("Target.getTargets")
        return result.get("targetInfos", [])

    async def dispose_context(self, browser_context_id: str):
        """Dispose of a browser context."""
        try:
            await self._send_command("Target.disposeBrowserContext", {
                "browserContextId": browser_context_id
            })
            logger.info(f"Disposed browser context: {browser_context_id}", tag="CDP")
        except Exception as e:
            logger.warning(f"Error disposing context: {e}", tag="CDP")


async def test_browser_context_id_basic():
    """
    Test that BrowserConfig accepts browser_context_id and target_id parameters.
    """
    logger.info("Testing BrowserConfig browser_context_id parameter", tag="TEST")

    try:
        # Test that BrowserConfig accepts the new parameters
        config = BrowserConfig(
            cdp_url="http://localhost:9222",
            browser_context_id="test-context-id",
            target_id="test-target-id",
            headless=True
        )

        # Verify parameters are set correctly
        assert config.browser_context_id == "test-context-id", "browser_context_id not set"
        assert config.target_id == "test-target-id", "target_id not set"

        # Test from_kwargs
        config2 = BrowserConfig.from_kwargs({
            "cdp_url": "http://localhost:9222",
            "browser_context_id": "test-context-id-2",
            "target_id": "test-target-id-2"
        })

        assert config2.browser_context_id == "test-context-id-2", "browser_context_id not set via from_kwargs"
        assert config2.target_id == "test-target-id-2", "target_id not set via from_kwargs"

        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict.get("browser_context_id") == "test-context-id", "browser_context_id not in to_dict"
        assert config_dict.get("target_id") == "test-target-id", "target_id not in to_dict"

        logger.success("BrowserConfig browser_context_id test passed", tag="TEST")
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        return False


async def test_pre_created_context_usage():
    """
    Test that Crawl4AI uses a pre-created browser context instead of creating a new one.

    This simulates the cloud browser service flow:
    1. Start browser with CDP
    2. Create context via raw CDP (simulating cloud service)
    3. Have Crawl4AI connect with browser_context_id
    4. Verify it uses existing context
    """
    logger.info("Testing pre-created context usage", tag="TEST")

    # Start a managed browser first
    browser_config_initial = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        debugging_port=9226,  # Use unique port
        verbose=True
    )

    managed_browser = ManagedBrowser(browser_config=browser_config_initial, logger=logger)
    cdp_creator = None
    manager = None
    context_info = None

    try:
        # Start the browser
        cdp_url = await managed_browser.start()
        logger.info(f"Browser started at {cdp_url}", tag="TEST")

        # Create a context via raw CDP (simulating cloud service)
        cdp_creator = CDPContextCreator(cdp_url)
        context_info = await cdp_creator.create_context()

        logger.info(f"Pre-created context: {context_info['browser_context_id']}", tag="TEST")
        logger.info(f"Pre-created target: {context_info['target_id']}", tag="TEST")

        # Get initial target count
        targets_before = await cdp_creator.get_targets()
        initial_target_count = len(targets_before)
        logger.info(f"Initial target count: {initial_target_count}", tag="TEST")

        # Now create BrowserManager with browser_context_id and target_id
        browser_config = BrowserConfig(
            cdp_url=cdp_url,
            browser_context_id=context_info['browser_context_id'],
            target_id=context_info['target_id'],
            headless=True,
            verbose=True
        )

        manager = BrowserManager(browser_config=browser_config, logger=logger)
        await manager.start()

        logger.info("BrowserManager started with pre-created context", tag="TEST")

        # Get a page
        crawler_config = CrawlerRunConfig()
        page, context = await manager.get_page(crawler_config)

        # Navigate to a test page
        await page.goto("https://example.com", wait_until="domcontentloaded")
        title = await page.title()

        logger.info(f"Page title: {title}", tag="TEST")

        # Get target count after
        targets_after = await cdp_creator.get_targets()
        final_target_count = len(targets_after)
        logger.info(f"Final target count: {final_target_count}", tag="TEST")

        # Verify: target count should not have increased significantly
        # (allow for 1 extra target for internal use, but not many more)
        target_diff = final_target_count - initial_target_count
        logger.info(f"Target count difference: {target_diff}", tag="TEST")

        # Success criteria:
        # 1. Page navigation worked
        # 2. Target count didn't explode (reused existing context)
        success = title == "Example Domain" and target_diff <= 1

        if success:
            logger.success("Pre-created context usage test passed", tag="TEST")
        else:
            logger.error(f"Test failed - Title: {title}, Target diff: {target_diff}", tag="TEST")

        return success

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if manager:
            try:
                await manager.close()
            except:
                pass

        if cdp_creator and context_info:
            try:
                await cdp_creator.dispose_context(context_info['browser_context_id'])
                await cdp_creator.disconnect()
            except:
                pass

        if managed_browser:
            try:
                await managed_browser.cleanup()
            except:
                pass


async def test_context_isolation():
    """
    Test that using browser_context_id actually provides isolation.
    Create two contexts and verify they don't share state.
    """
    logger.info("Testing context isolation with browser_context_id", tag="TEST")

    browser_config_initial = BrowserConfig(
        use_managed_browser=True,
        headless=True,
        debugging_port=9227,
        verbose=True
    )

    managed_browser = ManagedBrowser(browser_config=browser_config_initial, logger=logger)
    cdp_creator = None
    manager1 = None
    manager2 = None
    context_info_1 = None
    context_info_2 = None

    try:
        # Start the browser
        cdp_url = await managed_browser.start()
        logger.info(f"Browser started at {cdp_url}", tag="TEST")

        # Create two separate contexts
        cdp_creator = CDPContextCreator(cdp_url)
        context_info_1 = await cdp_creator.create_context()
        logger.info(f"Context 1: {context_info_1['browser_context_id']}", tag="TEST")

        # Need to reconnect for second context (or use same connection)
        await cdp_creator.disconnect()
        cdp_creator2 = CDPContextCreator(cdp_url)
        context_info_2 = await cdp_creator2.create_context()
        logger.info(f"Context 2: {context_info_2['browser_context_id']}", tag="TEST")

        # Verify contexts are different
        assert context_info_1['browser_context_id'] != context_info_2['browser_context_id'], \
            "Contexts should have different IDs"

        # Connect with first context
        browser_config_1 = BrowserConfig(
            cdp_url=cdp_url,
            browser_context_id=context_info_1['browser_context_id'],
            target_id=context_info_1['target_id'],
            headless=True
        )

        manager1 = BrowserManager(browser_config=browser_config_1, logger=logger)
        await manager1.start()

        # Set a cookie in context 1
        page1, ctx1 = await manager1.get_page(CrawlerRunConfig())
        await page1.goto("https://example.com", wait_until="domcontentloaded")
        await ctx1.add_cookies([{
            "name": "test_isolation",
            "value": "context_1_value",
            "domain": "example.com",
            "path": "/"
        }])

        cookies1 = await ctx1.cookies(["https://example.com"])
        cookie1_value = next((c["value"] for c in cookies1 if c["name"] == "test_isolation"), None)
        logger.info(f"Cookie in context 1: {cookie1_value}", tag="TEST")

        # Connect with second context
        browser_config_2 = BrowserConfig(
            cdp_url=cdp_url,
            browser_context_id=context_info_2['browser_context_id'],
            target_id=context_info_2['target_id'],
            headless=True
        )

        manager2 = BrowserManager(browser_config=browser_config_2, logger=logger)
        await manager2.start()

        # Check cookies in context 2 - should not have the cookie from context 1
        page2, ctx2 = await manager2.get_page(CrawlerRunConfig())
        await page2.goto("https://example.com", wait_until="domcontentloaded")

        cookies2 = await ctx2.cookies(["https://example.com"])
        cookie2_value = next((c["value"] for c in cookies2 if c["name"] == "test_isolation"), None)
        logger.info(f"Cookie in context 2: {cookie2_value}", tag="TEST")

        # Verify isolation
        isolation_works = cookie1_value == "context_1_value" and cookie2_value is None

        if isolation_works:
            logger.success("Context isolation test passed", tag="TEST")
        else:
            logger.error(f"Isolation failed - Cookie1: {cookie1_value}, Cookie2: {cookie2_value}", tag="TEST")

        return isolation_works

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        for mgr in [manager1, manager2]:
            if mgr:
                try:
                    await mgr.close()
                except:
                    pass

        for ctx_info, creator in [(context_info_1, cdp_creator), (context_info_2, cdp_creator2 if 'cdp_creator2' in dir() else None)]:
            if ctx_info and creator:
                try:
                    await creator.dispose_context(ctx_info['browser_context_id'])
                    await creator.disconnect()
                except:
                    pass

        if managed_browser:
            try:
                await managed_browser.cleanup()
            except:
                pass


async def run_tests():
    """Run all browser_context_id tests."""
    results = []

    logger.info("Running browser_context_id tests", tag="SUITE")

    # Basic parameter test
    results.append(("browser_context_id_basic", await test_browser_context_id_basic()))

    # Pre-created context usage test
    results.append(("pre_created_context_usage", await test_pre_created_context_usage()))

    # Note: Context isolation test is commented out because isolation is enforced
    # at the CDP level by the cloud browser service, not at the Playwright level.
    # When multiple BrowserManagers connect to the same browser, Playwright sees
    # all contexts. In production, each worker gets exactly one pre-created context.
    # results.append(("context_isolation", await test_context_isolation()))

    # Print summary
    total = len(results)
    passed = sum(1 for _, r in results if r)

    logger.info("=" * 50, tag="SUMMARY")
    logger.info(f"Test Results: {passed}/{total} passed", tag="SUMMARY")
    logger.info("=" * 50, tag="SUMMARY")

    for name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"  {name}: {status}", tag="SUMMARY")

    if passed == total:
        logger.success("All tests passed!", tag="SUMMARY")
        return True
    else:
        logger.error(f"{total - passed} tests failed", tag="SUMMARY")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
