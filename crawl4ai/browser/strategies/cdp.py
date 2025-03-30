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
from ..utils import get_playwright, get_browser_executable, create_temp_directory, is_windows, check_process_is_running, terminate_process

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
        # Call the base class start to initialize Playwright
        await super().start()
        
        try:
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
            
            if self.logger:
                self.logger.debug(f"Connected to CDP browser at {cdp_url}", tag="CDP")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to connect to CDP browser: {str(e)}", tag="CDP")

            # Clean up any resources before re-raising
            await self._cleanup_process()
            raise
            
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
        # args = await self._get_browser_args(user_data_dir)
        browser_args = super()._build_browser_args()
        browser_path = await get_browser_executable(self.config.browser_type)
        base_args = [browser_path]

        if self.config.browser_type == "chromium":
            args = [
                f"--remote-debugging-port={self.config.debugging_port}",
                f"--user-data-dir={user_data_dir}",
            ]
            # if self.config.headless:
            #     args.append("--headless=new")

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

        args = base_args + browser_args + args        

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
            is_running, return_code, stdout, stderr = await check_process_is_running(self.browser_process, delay=2)
            if not is_running:
                if self.logger:
                    self.logger.error(
                        message="Browser process terminated unexpectedly | Code: {code} | STDOUT: {stdout} | STDERR: {stderr}",
                        tag="ERROR",
                        params={
                            "code": return_code,
                            "stdout": stdout.decode() if stdout else "",
                            "stderr": stderr.decode() if stderr else "",
                        },
                    )
                await self._cleanup_process()
                raise Exception("Browser process terminated unexpectedly")

            return f"http://localhost:{self.config.debugging_port}"
        except Exception as e:
            await self._cleanup_process()
            raise Exception(f"Failed to start browser: {e}")    

    async def _cleanup_process(self):
        """Cleanup browser process and temporary directory."""
        # Set shutting_down flag BEFORE any termination actions
        self.shutting_down = True

        if self.browser_process:
            try:
                # Only attempt termination if the process is still running
                if self.browser_process.poll() is None:
                    # Use our robust cross-platform termination utility
                    success = terminate_process(
                        pid=self.browser_process.pid,
                        timeout=1.0,  # Equivalent to the previous 10*0.1s wait
                        logger=self.logger
                    )
                    
                    if not success and self.logger:
                        self.logger.warning(
                            message="Failed to terminate browser process cleanly",
                            tag="PROCESS"
                        )
                        
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error during browser process cleanup: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                if self.logger:
                    self.logger.debug("Removed temporary directory", tag="CDP")
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        message="Error removing temporary directory: {error}",
                        tag="CDP",
                        params={"error": str(e)}
                    )

        self.browser_process = None
    
    async def _generate_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        # For CDP, we typically use the shared default_context
        context = self.default_context
        pages = context.pages
        
        # Otherwise, check if we have an existing context for this config
        config_signature = self._make_config_signature(crawlerRunConfig)
        self.contexts_by_config[config_signature] = context

        await self.setup_context(context, crawlerRunConfig)

        # Check if there's already a page with the target URL
        page = next((p for p in pages if p.url == crawlerRunConfig.url), None)
        
        # If not found, create a new page
        if not page:
            page = await context.new_page()
        
        return page, context

    async def _get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        """Get a page for the given configuration.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            Tuple of (Page, BrowserContext)
        """
        # Call parent method to ensure browser is started
        await super().get_page(crawlerRunConfig)
        
        # For CDP, we typically use the shared default_context
        context = self.default_context
        pages = context.pages
        
        # Otherwise, check if we have an existing context for this config
        config_signature = self._make_config_signature(crawlerRunConfig)
        self.contexts_by_config[config_signature] = context

        await self.setup_context(context, crawlerRunConfig)

        # Check if there's already a page with the target URL
        page = next((p for p in pages if p.url == crawlerRunConfig.url), None)
        
        # If not found, create a new page
        if not page:
            page = await context.new_page()
        
        # If a session_id is specified, store this session for reuse
        if crawlerRunConfig.session_id:
            self.sessions[crawlerRunConfig.session_id] = (context, page, time.time())
        
        return page, context

    async def close(self):
        """Close the CDP browser and clean up resources."""
        # Skip cleanup if using external CDP URL and not launched by us
        if self.config.cdp_url and not self.browser_process:
            if self.logger:
                self.logger.debug("Skipping cleanup for external CDP browser", tag="CDP")
            return
        
        # Call parent implementation for common cleanup
        await super().close()
        
        # Additional CDP-specific cleanup
        await asyncio.sleep(0.5)
        await self._cleanup_process()
