import asyncio
import os
import time
import json
import subprocess
import shutil
import signal
from typing import Optional, Dict, Any, Tuple


from ...async_logger import AsyncLogger
from ...async_configs import CrawlerRunConfig
from playwright.async_api import Page, BrowserContext
from ...async_logger import AsyncLogger
from ...async_configs import BrowserConfig
from ...utils import get_home_folder
from ..utils import get_browser_executable, is_windows, is_browser_running, find_process_by_port, terminate_process


from .cdp import CDPBrowserStrategy
from .base import BaseBrowserStrategy

class BuiltinBrowserStrategy(CDPBrowserStrategy):
    """Built-in browser strategy.
    
    This strategy extends the CDP strategy to use the built-in browser.
    """
    
    def __init__(self, config: BrowserConfig, logger: Optional[AsyncLogger] = None):
        """Initialize the built-in browser strategy.
        
        Args:
            config: Browser configuration
            logger: Logger for recording events and errors
        """
        super().__init__(config, logger)
        self.builtin_browser_dir = os.path.join(get_home_folder(), "builtin-browser") if not self.config.user_data_dir else self.config.user_data_dir
        self.builtin_config_file = os.path.join(self.builtin_browser_dir, "browser_config.json")

        # Raise error if user data dir is already engaged
        if self._check_user_dir_is_engaged(self.builtin_browser_dir):
            raise Exception(f"User data directory {self.builtin_browser_dir} is already engaged by another browser instance.")

        os.makedirs(self.builtin_browser_dir, exist_ok=True)
    
    def _check_user_dir_is_engaged(self, user_data_dir: str) -> bool:
        """Check if the user data directory is already in use.
        
        Returns:
            bool: True if the directory is engaged, False otherwise
        """
        # Load browser config file, then iterate in port_map values, check "user_data_dir" key if it matches
        # the current user data directory
        if os.path.exists(self.builtin_config_file):
            try:
                with open(self.builtin_config_file, 'r') as f:
                    browser_info_dict = json.load(f)
                
                # Check if user data dir is already engaged
                for port_str, browser_info in browser_info_dict.get("port_map", {}).items():
                    if browser_info.get("user_data_dir") == user_data_dir:
                        return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error reading built-in browser config: {str(e)}", tag="BUILTIN")
        return False

    async def start(self):
        """Start or connect to the built-in browser.
        
        Returns:
            self: For method chaining
        """
        # Initialize Playwright instance via base class method
        await BaseBrowserStrategy.start(self)
        
        try:
            # Check for existing built-in browser (get_browser_info already checks if running)
            browser_info = self.get_browser_info()
            if browser_info:
                if self.logger:
                    self.logger.info(f"Using existing built-in browser at {browser_info.get('cdp_url')}", tag="BROWSER")
                self.config.cdp_url = browser_info.get('cdp_url')
            else:
                if self.logger:
                    self.logger.info("Built-in browser not found, launching new instance...", tag="BROWSER")
                cdp_url = await self.launch_builtin_browser(
                    browser_type=self.config.browser_type,
                    debugging_port=self.config.debugging_port,
                    headless=self.config.headless,
                )
                if not cdp_url:
                    if self.logger:
                        self.logger.warning("Failed to launch built-in browser, falling back to regular CDP strategy", tag="BROWSER")
                    # Call CDP's start but skip BaseBrowserStrategy.start() since we already called it
                    return await CDPBrowserStrategy.start(self)
                self.config.cdp_url = cdp_url
            
            # Connect to the browser using CDP protocol
            self.browser = await self.playwright.chromium.connect_over_cdp(self.config.cdp_url)
            
            # Get or create default context
            contexts = self.browser.contexts
            if contexts:
                self.default_context = contexts[0]
            else:
                self.default_context = await self.create_browser_context()
            
            await self.setup_context(self.default_context)
            
            if self.logger:
                self.logger.debug(f"Connected to built-in browser at {self.config.cdp_url}", tag="BUILTIN")
                
            return self
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start built-in browser: {str(e)}", tag="BUILTIN")
            raise

    async def get_page(self, crawlerRunConfig: CrawlerRunConfig) -> Tuple[Page, BrowserContext]:
        """Get a page for the given configuration.
        
        Inherits behavior from CDPBrowserStrategy for page management.
        
        Args:
            crawlerRunConfig: Configuration object for the crawler run
            
        Returns:
            Tuple of (Page, BrowserContext)
        """
        # For built-in browsers, we use the same page management as CDP strategy
        return await super().get_page(crawlerRunConfig)

    @classmethod
    def get_builtin_browser_info(cls, debugging_port: int, config_file: str, logger: Optional[AsyncLogger] = None) -> Optional[Dict[str, Any]]:
        """Get information about the built-in browser for a specific debugging port.
        
        Args:
            debugging_port: The debugging port to look for
            config_file: Path to the config file
            logger: Optional logger for recording events
            
        Returns:
            dict: Browser information or None if no running browser is configured for this port
        """
        if not os.path.exists(config_file):
            return None
            
        try:
            with open(config_file, 'r') as f:
                browser_info_dict = json.load(f)
            
            # Get browser info from port map
            if isinstance(browser_info_dict, dict) and "port_map" in browser_info_dict:
                port_str = str(debugging_port)
                if port_str in browser_info_dict["port_map"]:
                    browser_info = browser_info_dict["port_map"][port_str]
                    
                    # Check if the browser is still running
                    pids = browser_info.get('pid')
                    if type(pids) == str and len(pids.split("\n")) > 1:
                        pids = [int(pid) for pid in pids.split("\n") if pid.isdigit()]
                    elif type(pids) == str and pids.isdigit():
                        pids = [int(pids)]
                    elif type(pids) == int:
                        pids = [pids]
                    else:
                        pids = []
                    # Check if any of the PIDs are running
                    if not pids:
                        if logger:
                            logger.warning(f"Built-in browser on port {debugging_port} has no valid PID", tag="BUILTIN")
                        # Remove this port from the dictionary
                        del browser_info_dict["port_map"][port_str]
                        with open(config_file, 'w') as f:
                            json.dump(browser_info_dict, f, indent=2)
                        return None
                    # Check if any of the PIDs are running
                    for pid in pids:
                        if is_browser_running(pid):
                            browser_info['pid'] = pid
                            break
                    else:
                        # If none of the PIDs are running, remove this port from the dictionary
                        if logger:
                            logger.warning(f"Built-in browser on port {debugging_port} is not running", tag="BUILTIN")
                        # Remove this port from the dictionary
                        del browser_info_dict["port_map"][port_str]
                        with open(config_file, 'w') as f:
                            json.dump(browser_info_dict, f, indent=2)
                        return None
                    
                    return browser_info
            
            return None
                
        except Exception as e:
            if logger:
                logger.error(f"Error reading built-in browser config: {str(e)}", tag="BUILTIN")
            return None
            
    def get_browser_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current built-in browser instance.
        
        Returns:
            dict: Browser information or None if no running browser is configured
        """
        return self.get_builtin_browser_info(
            debugging_port=self.config.debugging_port,
            config_file=self.builtin_config_file,
            logger=self.logger
        )
    
    async def launch_builtin_browser(self, 
                               browser_type: str = "chromium",
                               debugging_port: int = 9222,
                               headless: bool = True) -> Optional[str]:
        """Launch a browser in the background for use as the built-in browser.
        
        Args:
            browser_type: Type of browser to launch ('chromium' or 'firefox')
            debugging_port: Port to use for CDP debugging
            headless: Whether to run in headless mode
            
        Returns:
            str: CDP URL for the browser, or None if launch failed
        """
        # Check if there's an existing browser still running
        browser_info = self.get_builtin_browser_info(
            debugging_port=debugging_port,
            config_file=self.builtin_config_file,
            logger=self.logger
        )
        if browser_info:
            if self.logger:
                self.logger.info(f"Built-in browser is already running on port {debugging_port}", tag="BUILTIN")
            return browser_info.get('cdp_url')
        
        # Create a user data directory for the built-in browser
        user_data_dir = os.path.join(self.builtin_browser_dir, "user_data")
        # Raise error if user data dir is already engaged
        if self._check_user_dir_is_engaged(user_data_dir):
            raise Exception(f"User data directory {user_data_dir} is already engaged by another browser instance.")
            
        # Create the user data directory if it doesn't exist
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Prepare browser launch arguments
        browser_path = await get_browser_executable(browser_type)
        if browser_type == "chromium":
            args = [
                browser_path,
                f"--remote-debugging-port={debugging_port}",
                f"--user-data-dir={user_data_dir}",
            ]
            if headless:
                args.append("--headless=new")
        elif browser_type == "firefox":
            args = [
                browser_path,
                "--remote-debugging-port",
                str(debugging_port),
                "--profile",
                user_data_dir,
            ]
            if headless:
                args.append("--headless")
        else:
            if self.logger:
                self.logger.error(f"Browser type {browser_type} not supported for built-in browser", tag="BUILTIN")
            return None
        
        try:

            # Check if the port is already in use
            PID = ""
            cdp_url = f"http://localhost:{debugging_port}"
            config_json = await self._check_port_in_use(cdp_url)
            if config_json:
                if self.logger:
                    self.logger.info(f"Port {debugging_port} is already in use.", tag="BUILTIN")
                PID = find_process_by_port(debugging_port)
            else:
                # Start the browser process detached
                process = None
                if is_windows():
                    process = subprocess.Popen(
                        args, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    process = subprocess.Popen(
                        args, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setpgrp  # Start in a new process group
                    )
                
                # Wait briefly to ensure the process starts successfully
                await asyncio.sleep(2.0)
                
                # Check if the process is still running
                if process and process.poll() is not None:
                    if self.logger:
                        self.logger.error(f"Browser process exited immediately with code {process.returncode}", tag="BUILTIN")
                    return None
            
                PID = process.pid
                # Construct CDP URL
                config_json = await self._check_port_in_use(cdp_url)

            
            # Create browser info
            browser_info = {
                'pid': PID,
                'cdp_url': cdp_url,
                'user_data_dir': user_data_dir,
                'browser_type': browser_type,
                'debugging_port': debugging_port,
                'start_time': time.time(),
                'config': config_json
            }
            
            # Read existing config file if it exists
            port_map = {}
            if os.path.exists(self.builtin_config_file):
                try:
                    with open(self.builtin_config_file, 'r') as f:
                        existing_data = json.load(f)
                    
                    # Check if it already uses port mapping
                    if isinstance(existing_data, dict) and "port_map" in existing_data:
                        port_map = existing_data["port_map"]
                    # Convert legacy format to port mapping
                    elif isinstance(existing_data, dict) and "debugging_port" in existing_data:
                        old_port = str(existing_data.get("debugging_port"))
                        if self._is_browser_running(existing_data.get("pid")):
                            port_map[old_port] = existing_data
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Could not read existing config: {str(e)}", tag="BUILTIN")
            
            # Add/update this browser in the port map
            port_map[str(debugging_port)] = browser_info
            
            # Write updated config
            with open(self.builtin_config_file, 'w') as f:
                json.dump({"port_map": port_map}, f, indent=2)
                
            # Detach from the browser process - don't keep any references
            # This is important to allow the Python script to exit while the browser continues running
            process = None
                
            if self.logger:
                self.logger.success(f"Built-in browser launched at CDP URL: {cdp_url}", tag="BUILTIN")
            return cdp_url
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error launching built-in browser: {str(e)}", tag="BUILTIN")
            return None

    async def _check_port_in_use(self, cdp_url: str) -> dict:
        """Check if a port is already in use by a Chrome DevTools instance.
        
        Args:
            cdp_url: The CDP URL to check
            
        Returns:
            dict: Chrome DevTools protocol version information or None if not found
        """
        import aiohttp
        json_url = f"{cdp_url}/json/version"
        json_config = None
        
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(json_url, timeout=2.0) as response:
                        if response.status == 200:
                            json_config = await response.json()
                            if self.logger:
                                self.logger.debug(f"Found CDP server running at {cdp_url}", tag="BUILTIN")
                            return json_config
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass
            return None
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error checking CDP port: {str(e)}", tag="BUILTIN")
            return None

    async def kill_builtin_browser(self) -> bool:
        """Kill the built-in browser if it's running.
        
        Returns:
            bool: True if the browser was killed, False otherwise
        """
        browser_info = self.get_browser_info()
        if not browser_info:
            if self.logger:
                self.logger.warning(f"No built-in browser found on port {self.config.debugging_port}", tag="BUILTIN")
            return False
            
        pid = browser_info.get('pid')
        if not pid:
            return False
            
        success, error_msg = terminate_process(pid, logger=self.logger)
        if success:
            # Update config file to remove this browser
            with open(self.builtin_config_file, 'r') as f:
                browser_info_dict = json.load(f)
            # Remove this port from the dictionary
            port_str = str(self.config.debugging_port)
            if port_str in browser_info_dict.get("port_map", {}):
                del browser_info_dict["port_map"][port_str]
            with open(self.builtin_config_file, 'w') as f:
                json.dump(browser_info_dict, f, indent=2)
            # Remove user data directory if it exists
            if os.path.exists(self.builtin_browser_dir):
                shutil.rmtree(self.builtin_browser_dir)
            # Clear the browser info cache
            self.browser = None
            self.temp_dir = None
            self.shutting_down = True
                
            if self.logger:
                self.logger.success("Built-in browser terminated", tag="BUILTIN")
            return True
        else:
            if self.logger:
                self.logger.error(f"Error killing built-in browser: {error_msg}", tag="BUILTIN")
            return False
    
    async def get_builtin_browser_status(self) -> Dict[str, Any]:
        """Get status information about the built-in browser.
        
        Returns:
            dict: Status information with running, cdp_url, and info fields
        """
        browser_info = self.get_browser_info()
        
        if not browser_info:
            return {
                'running': False,
                'cdp_url': None,
                'info': None,
                'port': self.config.debugging_port
            }
            
        return {
            'running': True,
            'cdp_url': browser_info.get('cdp_url'),
            'info': browser_info,
            'port': self.config.debugging_port
        }

    async def close(self):
        """Close the built-in browser and clean up resources."""
        # Store the shutting_down state
        was_shutting_down = getattr(self, 'shutting_down', False)
        
        # Call parent class close method
        await super().close()
        
        # Clean up built-in browser if we created it and were in shutdown mode
        if was_shutting_down:
            await self.kill_builtin_browser()
            if self.logger:
                self.logger.debug("Killed built-in browser during shutdown", tag="BUILTIN")