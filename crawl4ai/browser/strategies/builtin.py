import asyncio
import os
import time
import json
import subprocess
import shutil
import signal
from typing import Optional, Dict, Any


from ...async_logger import AsyncLogger
from ...async_configs import BrowserConfig
from ...utils import get_home_folder
from ..utils import get_browser_executable, is_windows, is_browser_running


from .cdp import CDPBrowserStrategy

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
                return await super().start()
            self.config.cdp_url = cdp_url
        
        # Call parent class implementation with updated CDP URL
        return await super().start()
    
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
                    if not is_browser_running(browser_info.get('pid')):
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
            # Start the browser process detached
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
            if process.poll() is not None:
                if self.logger:
                    self.logger.error(f"Browser process exited immediately with code {process.returncode}", tag="BUILTIN")
                return None
            
            # Construct CDP URL
            cdp_url = f"http://localhost:{debugging_port}"
            
            # Try to verify browser is responsive by fetching version info
            import aiohttp
            json_url = f"{cdp_url}/json/version"
            config_json = None
            
            try:
                async with aiohttp.ClientSession() as session:
                    for _ in range(10):  # Try multiple times
                        try:
                            async with session.get(json_url) as response:
                                if response.status == 200:
                                    config_json = await response.json()
                                    break
                        except Exception:
                            pass
                        await asyncio.sleep(0.5)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not verify browser: {str(e)}", tag="BUILTIN")
            
            # Create browser info
            browser_info = {
                'pid': process.pid,
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
            
        try:
            if is_windows():
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
            else:
                os.kill(pid, signal.SIGTERM)
                # Wait for termination
                for _ in range(5):
                    if not is_browser_running(pid):
                        break
                    await asyncio.sleep(0.5)
                else:
                    # Force kill if still running
                    os.kill(pid, signal.SIGKILL)
                    
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
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error killing built-in browser: {str(e)}", tag="BUILTIN")
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

    # Override the close method to handle built-in browser cleanup
    async def close(self):
        """Close the built-in browser and clean up resources."""
        # Call parent class close method
        await super().close()
        
        # Clean up built-in browser if we created it
        if self.shutting_down:
            await self.kill_builtin_browser()
