"""Browser strategies module for Crawl4AI.

This module implements the browser strategy pattern for different
browser implementations, including Playwright, CDP, and builtin browsers.
"""

import asyncio
import os
import time
import json
import subprocess
import shutil
from typing import Optional, Tuple, List

from playwright.async_api import BrowserContext, Page

from ...async_logger import AsyncLogger
from ...async_configs import BrowserConfig, CrawlerRunConfig
from ..utils import get_playwright, get_browser_executable, create_temp_directory, is_windows

from .base import BaseBrowserStrategy

class CDPBrowserStrategy(BaseBrowserStrategy):
    """CDP-based browser strategy.
    
    This strategy connects to an existing browser using CDP protocol or
    launches and connects to a browser using CDP.
    """
    
    def __init__(self, config: BrowserConfig, logger: Optional[AsyncLogger] = None):
        """Initialize the CDP browser strategy.
        
        Args:
            config: Browser configuration
            logger: Logger for recording events and errors
        """
        super().__init__(config, logger)
        self.sessions = {}
        self.session_ttl = 1800  # 30 minutes
        self.browser_process = None
        self.temp_dir = None
        self.shutting_down = False
        
    async def start(self):
        """Start or connect to the browser using CDP.
        
        Returns:
            self: For method chaining
        """
        self.playwright = await get_playwright()
        
        # Get or create CDP URL
        cdp_url = await self._get_or_create_cdp_url()
        
        # Connect to the browser using CDP
        self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
        
        # Get or create default context
        contexts = self.browser.contexts
        if contexts:
            self.default_context = contexts[0]
        else:
            self.default_context = await self.create_browser_context()
        
        await self.setup_context(self.default_context)
        return self
    
    async def _get_or_create_cdp_url(self) -> str:
        """Get existing CDP URL or launch a browser and return its CDP URL.
        
        Returns:
            str: CDP URL for connecting to the browser
        """
        # If CDP URL is provided, just return it
        if self.config.cdp_url:
            return self.config.cdp_url

        # Create temp dir if needed
        if not self.config.user_data_dir:
            self.temp_dir = create_temp_directory()
            user_data_dir = self.temp_dir
        else:
            user_data_dir = self.config.user_data_dir

        # Get browser args based on OS and browser type
        args = await self._get_browser_args(user_data_dir)

        # Start browser process
        try:
            # Use DETACHED_PROCESS flag on Windows to fully detach the process
            # On Unix, we'll use preexec_fn=os.setpgrp to start the process in a new process group
            if is_windows():
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setpgrp  # Start in a new process group
                )
                
            # Monitor for a short time to make sure it starts properly
            await asyncio.sleep(0.5)  # Give browser time to start
            await self._initial_startup_check()
            await asyncio.sleep(2)  # Give browser more time to start
            return f"http://localhost:{self.config.debugging_port}"
        except Exception as e:
            await self._cleanup_process()
            raise Exception(f"Failed to start browser: {e}")
    
    async def _initial_startup_check(self):
        """Perform a quick check to make sure the browser started successfully."""
        if not self.browser_process:
            return
            
        # Check that process started without immediate termination
        await asyncio.sleep(0.5)
        if self.browser_process.poll() is not None:
            # Process already terminated
            stdout, stderr = b"", b""
            try:
                stdout, stderr = self.browser_process.communicate(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
                
            if self.logger:
                self.logger.error(
                    message="Browser process terminated during startup | Code: {code} | STDOUT: {stdout} | STDERR: {stderr}",
                    tag="ERROR",
                    params={
                        "code": self.browser_process.returncode,
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else "",
                    },
                )
    
    async def _get_browser_args(self, user_data_dir: str) -> List[str]:
        """Returns browser-specific command line arguments.
        
        Args:
            user_data_dir: Path to user data directory
            
        Returns:
            List of command-line arguments for the browser
        """
        browser_path = await get_browser_executable(self.config.browser_type)
        base_args = [browser_path]

        if self.config.browser_type == "chromium":
            args = [
                f"--remote-debugging-port={self.config.debugging_port}",
                f"--user-data-dir={user_data_dir}",
            ]
            if self.config.headless:
                args.append("--headless=new")
        elif self.config.browser_type == "firefox":
            args = [
                "--remote-debugging-port",
                str(self.config.debugging_port),
                "--profile",
                user_data_dir,
            ]
            if self.config.headless:
                args.append("--headless")
        else:
            raise NotImplementedError(f"Browser type {self.config.browser_type} not supported")

        return base_args + args

    async def _cleanup_process(self):
        """Cleanup browser process and temporary directory."""
        # Set shutting_down flag BEFORE any termination actions
        self.shutting_down = True

        if self.browser_process:
            try:
                # Only terminate if we have proper control over the process
                if not self.browser_process.poll():
                    # Process is still running
                    self.browser_process.terminate()
                    # Wait for process to end gracefully
                    for _ in range(10):  # 10 attempts, 100ms each
                        if self.browser_process.poll() is not None:
                            break
                        await asyncio.sleep(0.1)

                    # Force kill if still running
                    if self.browser_process.poll() is None:
                        if is_windows():
                            # On Windows we might need taskkill for detached processes
                            try:
                                subprocess.run(["taskkill", "/F", "/PID", str(self.browser_process.pid)])
                            except Exception:
                                self.browser_process.kill()
                        else:
                            self.browser_process.kill()
                        await asyncio.sleep(0.1)  # Brief wait for kill to take effect

            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error terminating browser: {error}",
                        tag="ERROR", 
                        params={"error": str(e)},
                    )

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error removing temporary directory: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )
    
    async def create_browser_context(self, crawlerRunConfig: Optional[CrawlerRunConfig] = None) -> BrowserContext:
        """Create a new browser context.
        
        Uses the base class implementation which handles all configurations.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            BrowserContext: Browser context object
        """
        # Handle user_data_dir for CDP browsers
        if self.config.user_data_dir:
            # For CDP-based browsers, storage persistence is typically handled by the user_data_dir
            # at the browser level, but we'll create a storage_state location for Playwright as well
            storage_path = os.path.join(self.config.user_data_dir, "storage_state.json")
            if not os.path.exists(storage_path):
                # Create parent directory if it doesn't exist
                os.makedirs(os.path.dirname(storage_path), exist_ok=True)
                with open(storage_path, "w") as f:
                    json.dump({}, f)
            self.config.storage_state = storage_path
            
        # Use the base class implementation
        return await super().create_browser_context(crawlerRunConfig)
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions based on TTL."""
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, (_, _, last_used) in self.sessions.items()
            if current_time - last_used > self.session_ttl
        ]
        for sid in expired_sessions:
            asyncio.create_task(self._kill_session(sid))
    
    async def _kill_session(self, session_id: str):
        """Kill a browser session and clean up resources.
        
        Args:
            session_id: The session ID to kill
        """
        if session_id in self.sessions:
            context, page, _ = self.sessions[session_id]
            await page.close()
            del self.sessions[session_id]
    
    async def get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        """Get a page for the given configuration.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            Tuple of (Page, BrowserContext)
        """
        self._cleanup_expired_sessions()
        
        # If a session_id is provided and we already have it, reuse that page + context
        if crawlerRunConfig.session_id and crawlerRunConfig.session_id in self.sessions:
            context, page, _ = self.sessions[crawlerRunConfig.session_id]
            # Update last-used timestamp
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
            return page, context
        
        # For CDP, we typically use the shared default_context
        context = self.default_context
        pages = context.pages
        page = next((p for p in pages if p.url == crawlerRunConfig.url), None)
        if not page:
            page = await context.new_page()
        
        # If a session_id is specified, store this session so we can reuse later
        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
        
        return page, context
    
    async def close(self):
        """Close the browser and clean up resources."""
        # Skip cleanup if using external CDP URL and not launched by us
        if self.config.cdp_url and not self.browser_process:
            return
        
        if self.config.sleep_on_close:
            await asyncio.sleep(0.5)
        
        # If we have a user_data_dir configured, ensure persistence of storage state
        if self.config.user_data_dir and self.browser and self.default_context:
            for context in self.browser.contexts:
                try:
                    await context.storage_state(path=os.path.join(self.config.user_data_dir, "Default", "storage_state.json"))
                    if self.logger:
                        self.logger.debug("Ensuring storage state is persisted before closing browser", tag="BROWSER")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(
                            message="Failed to ensure storage persistence: {error}",
                            tag="BROWSER", 
                            params={"error": str(e)}
                        )
        
        # Close all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self._kill_session(session_id)

        # Close browser
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        # Clean up managed browser if we created it
        if self.browser_process:
            await asyncio.sleep(0.5)
            await self._cleanup_process()
            self.browser_process = None
        
        # Close temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error removing temporary directory: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )
        
        # Stop playwright
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

