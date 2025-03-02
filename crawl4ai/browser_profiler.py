"""
Browser Profiler Module

This module provides a dedicated class for managing browser profiles
that can be used for identity-based crawling with Crawl4AI.
"""

import os
import asyncio
import signal
import sys
import datetime
import uuid
import shutil
from typing import List, Dict, Optional, Any
from colorama import Fore, Style, init

from .async_configs import BrowserConfig
from .browser_manager import ManagedBrowser
from .async_logger import AsyncLogger, AsyncLoggerBase
from .utils import get_home_folder


class BrowserProfiler:
    """
    A dedicated class for managing browser profiles for Crawl4AI.
    
    The BrowserProfiler allows you to:
    - Create browser profiles interactively
    - List available profiles
    - Delete profiles when no longer needed
    - Get profile paths for use in BrowserConfig
    
    Profiles are stored by default in ~/.crawl4ai/profiles/
    """
    
    def __init__(self, logger: Optional[AsyncLoggerBase] = None):
        """
        Initialize the BrowserProfiler.
        
        Args:
            logger (AsyncLoggerBase, optional): Logger for outputting messages.
                If None, a default AsyncLogger will be created.
        """
        # Initialize colorama for colorful terminal output
        init()
        
        # Create a logger if not provided
        if logger is None:
            self.logger = AsyncLogger(verbose=True)
        elif not isinstance(logger, AsyncLoggerBase):
            self.logger = AsyncLogger(verbose=True)
        else:
            self.logger = logger
            
        # Ensure profiles directory exists
        self.profiles_dir = os.path.join(get_home_folder(), "profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)
    
    async def create_profile(self, 
                            profile_name: Optional[str] = None, 
                            browser_config: Optional[BrowserConfig] = None) -> Optional[str]:
        """
        Creates a browser profile by launching a browser for interactive user setup
        and waits until the user closes it. The profile is stored in a directory that
        can be used later with BrowserConfig.user_data_dir.
        
        Args:
            profile_name (str, optional): Name for the profile directory.
                If None, a name is generated based on timestamp.
            browser_config (BrowserConfig, optional): Configuration for the browser.
                If None, a default configuration is used with headless=False.
                
        Returns:
            str: Path to the created profile directory, or None if creation failed
            
        Example:
            ```python
            profiler = BrowserProfiler()
            
            # Create a profile interactively
            profile_path = await profiler.create_profile(
                profile_name="my-login-profile"
            )
            
            # Use the profile in a crawler
            browser_config = BrowserConfig(
                headless=True,
                use_managed_browser=True,
                user_data_dir=profile_path
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                # The crawler will now use your profile with all your cookies and login state
                result = await crawler.arun("https://example.com/dashboard")
            ```
        """
        # Create default browser config if none provided
        if browser_config is None:
            from .async_configs import BrowserConfig
            browser_config = BrowserConfig(
                browser_type="chromium",
                headless=False,  # Must be visible for user interaction
                verbose=True
            )
        else:
            # Ensure headless is False for user interaction
            browser_config.headless = False
            
        # Generate profile name if not provided
        if not profile_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            profile_name = f"profile_{timestamp}_{uuid.uuid4().hex[:6]}"
            
        # Sanitize profile name (replace spaces and special chars)
        profile_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in profile_name)
        
        # Set user data directory
        profile_path = os.path.join(self.profiles_dir, profile_name)
        os.makedirs(profile_path, exist_ok=True)
        
        # Print instructions for the user with colorama formatting
        border = f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}"
        self.logger.info(f"\n{border}", tag="PROFILE")
        self.logger.info(f"Creating browser profile: {Fore.GREEN}{profile_name}{Style.RESET_ALL}", tag="PROFILE")
        self.logger.info(f"Profile directory: {Fore.YELLOW}{profile_path}{Style.RESET_ALL}", tag="PROFILE")
        
        self.logger.info("\nInstructions:", tag="PROFILE")
        self.logger.info("1. A browser window will open for you to set up your profile.", tag="PROFILE")
        self.logger.info(f"2. {Fore.CYAN}Log in to websites{Style.RESET_ALL}, configure settings, etc. as needed.", tag="PROFILE")
        self.logger.info(f"3. When you're done, {Fore.YELLOW}press 'q' in this terminal{Style.RESET_ALL} to close the browser.", tag="PROFILE")
        self.logger.info("4. The profile will be saved and ready to use with Crawl4AI.", tag="PROFILE")
        self.logger.info(f"{border}\n", tag="PROFILE")
        
        # Create managed browser instance
        managed_browser = ManagedBrowser(
            browser_type=browser_config.browser_type,
            user_data_dir=profile_path,
            headless=False,  # Must be visible
            logger=self.logger,
            debugging_port=browser_config.debugging_port
        )
        
        # Set up signal handlers to ensure cleanup on interrupt
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        
        # Define cleanup handler for signals
        async def cleanup_handler(sig, frame):
            self.logger.warning("\nCleaning up browser process...", tag="PROFILE")
            await managed_browser.cleanup()
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            if sig == signal.SIGINT:
                self.logger.error("Profile creation interrupted. Profile may be incomplete.", tag="PROFILE")
                sys.exit(1)
                
        # Set signal handlers
        def sigint_handler(sig, frame):
            asyncio.create_task(cleanup_handler(sig, frame))
        
        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)
        
        # Event to signal when user is done with the browser
        user_done_event = asyncio.Event()
        
        # Run keyboard input loop in a separate task
        async def listen_for_quit_command():
            import termios
            import tty
            import select
            
            # First output the prompt
            self.logger.info(f"{Fore.CYAN}Press '{Fore.WHITE}q{Fore.CYAN}' when you've finished using the browser...{Style.RESET_ALL}", tag="PROFILE")
            
            # Save original terminal settings
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # Switch to non-canonical mode (no line buffering)
                tty.setcbreak(fd)
                
                while True:
                    # Check if input is available (non-blocking)
                    readable, _, _ = select.select([sys.stdin], [], [], 0.5)
                    if readable:
                        key = sys.stdin.read(1)
                        if key.lower() == 'q':
                            self.logger.info(f"{Fore.GREEN}Closing browser and saving profile...{Style.RESET_ALL}", tag="PROFILE")
                            user_done_event.set()
                            return
                    
                    # Check if the browser process has already exited
                    if managed_browser.browser_process and managed_browser.browser_process.poll() is not None:
                        self.logger.info("Browser already closed. Ending input listener.", tag="PROFILE")
                        user_done_event.set()
                        return
                        
                    await asyncio.sleep(0.1)
            
            finally:
                # Restore terminal settings 
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        try:
            # Start the browser
            await managed_browser.start()
            
            # Check if browser started successfully
            browser_process = managed_browser.browser_process
            if not browser_process:
                self.logger.error("Failed to start browser process.", tag="PROFILE")
                return None
            
            self.logger.info(f"Browser launched. {Fore.CYAN}Waiting for you to finish...{Style.RESET_ALL}", tag="PROFILE") 
            
            # Start listening for keyboard input
            listener_task = asyncio.create_task(listen_for_quit_command())
            
            # Wait for either the user to press 'q' or for the browser process to exit naturally
            while not user_done_event.is_set() and browser_process.poll() is None:
                await asyncio.sleep(0.5)
            
            # Cancel the listener task if it's still running
            if not listener_task.done():
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass
            
            # If the browser is still running and the user pressed 'q', terminate it
            if browser_process.poll() is None and user_done_event.is_set():
                self.logger.info("Terminating browser process...", tag="PROFILE")
                await managed_browser.cleanup()
            
            self.logger.success(f"Browser closed. Profile saved at: {Fore.GREEN}{profile_path}{Style.RESET_ALL}", tag="PROFILE")
                
        except Exception as e:
            self.logger.error(f"Error creating profile: {str(e)}", tag="PROFILE")
            await managed_browser.cleanup()
            return None
        finally:
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            
            # Make sure browser is fully cleaned up
            await managed_browser.cleanup()
        
        # Return the profile path
        return profile_path
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        Lists all available browser profiles in the Crawl4AI profiles directory.
        
        Returns:
            list: A list of dictionaries containing profile information:
                  [{"name": "profile_name", "path": "/path/to/profile", "created": datetime, "type": "chromium|firefox"}]
                  
        Example:
            ```python
            profiler = BrowserProfiler()
            
            # List all available profiles
            profiles = profiler.list_profiles()
            
            for profile in profiles:
                print(f"Profile: {profile['name']}")
                print(f"  Path: {profile['path']}")
                print(f"  Created: {profile['created']}")
                print(f"  Browser type: {profile['type']}")
            ```
        """
        if not os.path.exists(self.profiles_dir):
            return []
            
        profiles = []
        
        for name in os.listdir(self.profiles_dir):
            profile_path = os.path.join(self.profiles_dir, name)
            
            # Skip if not a directory
            if not os.path.isdir(profile_path):
                continue
                
            # Check if this looks like a valid browser profile
            # For Chromium: Look for Preferences file
            # For Firefox: Look for prefs.js file
            is_valid = False
            
            if os.path.exists(os.path.join(profile_path, "Preferences")) or \
               os.path.exists(os.path.join(profile_path, "Default", "Preferences")):
                is_valid = "chromium"
            elif os.path.exists(os.path.join(profile_path, "prefs.js")):
                is_valid = "firefox"
                
            if is_valid:
                # Get creation time
                created = datetime.datetime.fromtimestamp(
                    os.path.getctime(profile_path)
                )
                
                profiles.append({
                    "name": name,
                    "path": profile_path,
                    "created": created,
                    "type": is_valid
                })
                
        # Sort by creation time, newest first
        profiles.sort(key=lambda x: x["created"], reverse=True)
        
        return profiles
    
    def get_profile_path(self, profile_name: str) -> Optional[str]:
        """
        Get the full path to a profile by name.
        
        Args:
            profile_name (str): Name of the profile (not the full path)
            
        Returns:
            str: Full path to the profile directory, or None if not found
            
        Example:
            ```python
            profiler = BrowserProfiler()
            
            path = profiler.get_profile_path("my-profile")
            if path:
                print(f"Profile path: {path}")
            else:
                print("Profile not found")
            ```
        """
        profile_path = os.path.join(self.profiles_dir, profile_name)
        
        # Check if path exists and is a valid profile
        if not os.path.isdir(profile_path):
            return None
        
        # Look for profile indicators
        is_profile = (
            os.path.exists(os.path.join(profile_path, "Preferences")) or
            os.path.exists(os.path.join(profile_path, "Default", "Preferences")) or
            os.path.exists(os.path.join(profile_path, "prefs.js"))
        )
        
        if not is_profile:
            return None  # Not a valid browser profile
            
        return profile_path
    
    def delete_profile(self, profile_name_or_path: str) -> bool:
        """
        Delete a browser profile by name or path.
        
        Args:
            profile_name_or_path (str): Name of the profile or full path to profile directory
            
        Returns:
            bool: True if the profile was deleted successfully, False otherwise
            
        Example:
            ```python
            profiler = BrowserProfiler()
            
            # Delete by name
            success = profiler.delete_profile("my-profile")
            
            # Delete by path
            success = profiler.delete_profile("/path/to/.crawl4ai/profiles/my-profile")
            ```
        """
        # Determine if input is a name or a path
        if os.path.isabs(profile_name_or_path):
            # Full path provided
            profile_path = profile_name_or_path
        else:
            # Just a name provided, construct path
            profile_path = os.path.join(self.profiles_dir, profile_name_or_path)
        
        # Check if path exists and is a valid profile
        if not os.path.isdir(profile_path):
            return False
            
        # Look for profile indicators
        is_profile = (
            os.path.exists(os.path.join(profile_path, "Preferences")) or
            os.path.exists(os.path.join(profile_path, "Default", "Preferences")) or
            os.path.exists(os.path.join(profile_path, "prefs.js"))
        )
        
        if not is_profile:
            return False  # Not a valid browser profile
            
        # Delete the profile directory
        try:
            shutil.rmtree(profile_path)
            return True
        except Exception:
            return False
            
    async def interactive_manager(self, crawl_callback=None):
        """
        Launch an interactive profile management console.
        
        Args:
            crawl_callback (callable, optional): Function to call when selecting option to use 
                a profile for crawling. It will be called with (profile_path, url).
                
        Example:
            ```python
            profiler = BrowserProfiler()
            
            # Define a custom crawl function
            async def my_crawl_function(profile_path, url):
                print(f"Crawling {url} with profile {profile_path}")
                # Implement your crawling logic here
                
            # Start interactive manager
            await profiler.interactive_manager(crawl_callback=my_crawl_function)
            ```
        """
        while True:
            self.logger.info(f"\n{Fore.CYAN}Profile Management Options:{Style.RESET_ALL}", tag="MENU")
            self.logger.info(f"1. {Fore.GREEN}Create a new profile{Style.RESET_ALL}", tag="MENU")
            self.logger.info(f"2. {Fore.YELLOW}List available profiles{Style.RESET_ALL}", tag="MENU")
            self.logger.info(f"3. {Fore.RED}Delete a profile{Style.RESET_ALL}", tag="MENU")
            
            # Only show crawl option if callback provided
            if crawl_callback:
                self.logger.info(f"4. {Fore.CYAN}Use a profile to crawl a website{Style.RESET_ALL}", tag="MENU")
                self.logger.info(f"5. {Fore.MAGENTA}Exit{Style.RESET_ALL}", tag="MENU")
                exit_option = "5"
            else:
                self.logger.info(f"4. {Fore.MAGENTA}Exit{Style.RESET_ALL}", tag="MENU")
                exit_option = "4"
            
            choice = input(f"\n{Fore.CYAN}Enter your choice (1-{exit_option}): {Style.RESET_ALL}")
            
            if choice == "1":
                # Create new profile
                name = input(f"{Fore.GREEN}Enter a name for the new profile (or press Enter for auto-generated name): {Style.RESET_ALL}")
                await self.create_profile(name or None)
                
            elif choice == "2":
                # List profiles
                profiles = self.list_profiles()
                
                if not profiles:
                    self.logger.warning("  No profiles found. Create one first with option 1.", tag="PROFILES")
                    continue
                
                # Print profile information with colorama formatting
                self.logger.info("\nAvailable profiles:", tag="PROFILES")
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {Fore.CYAN}{profile['name']}{Style.RESET_ALL}", tag="PROFILES")
                    self.logger.info(f"    Path: {Fore.YELLOW}{profile['path']}{Style.RESET_ALL}", tag="PROFILES")
                    self.logger.info(f"    Created: {profile['created'].strftime('%Y-%m-%d %H:%M:%S')}", tag="PROFILES")
                    self.logger.info(f"    Browser type: {profile['type']}", tag="PROFILES")
                    self.logger.info("", tag="PROFILES")  # Empty line for spacing
                
            elif choice == "3":
                # Delete profile
                profiles = self.list_profiles()
                if not profiles:
                    self.logger.warning("No profiles found to delete", tag="PROFILES")
                    continue
                    
                # Display numbered list
                self.logger.info(f"\n{Fore.YELLOW}Available profiles:{Style.RESET_ALL}", tag="PROFILES")
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")
                    
                # Get profile to delete
                profile_idx = input(f"{Fore.RED}Enter the number of the profile to delete (or 'c' to cancel): {Style.RESET_ALL}")
                if profile_idx.lower() == 'c':
                    continue
                    
                try:
                    idx = int(profile_idx) - 1
                    if 0 <= idx < len(profiles):
                        profile_name = profiles[idx]["name"]
                        self.logger.info(f"Deleting profile: {Fore.YELLOW}{profile_name}{Style.RESET_ALL}", tag="PROFILES")
                        
                        # Confirm deletion
                        confirm = input(f"{Fore.RED}Are you sure you want to delete this profile? (y/n): {Style.RESET_ALL}")
                        if confirm.lower() == 'y':
                            success = self.delete_profile(profiles[idx]["path"])
                            
                            if success:
                                self.logger.success(f"Profile {Fore.GREEN}{profile_name}{Style.RESET_ALL} deleted successfully", tag="PROFILES")
                            else:
                                self.logger.error(f"Failed to delete profile {Fore.RED}{profile_name}{Style.RESET_ALL}", tag="PROFILES")
                    else:
                        self.logger.error("Invalid profile number", tag="PROFILES")
                except ValueError:
                    self.logger.error("Please enter a valid number", tag="PROFILES")
                    
            elif choice == "4" and crawl_callback:
                # Use profile to crawl a site
                profiles = self.list_profiles()
                if not profiles:
                    self.logger.warning("No profiles found. Create one first.", tag="PROFILES")
                    continue
                    
                # Display numbered list
                self.logger.info(f"\n{Fore.YELLOW}Available profiles:{Style.RESET_ALL}", tag="PROFILES")
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")
                    
                # Get profile to use
                profile_idx = input(f"{Fore.CYAN}Enter the number of the profile to use (or 'c' to cancel): {Style.RESET_ALL}")
                if profile_idx.lower() == 'c':
                    continue
                    
                try:
                    idx = int(profile_idx) - 1
                    if 0 <= idx < len(profiles):
                        profile_path = profiles[idx]["path"]
                        url = input(f"{Fore.CYAN}Enter the URL to crawl: {Style.RESET_ALL}")
                        if url:
                            # Call the provided crawl callback
                            await crawl_callback(profile_path, url)
                        else:
                            self.logger.error("No URL provided", tag="CRAWL")
                    else:
                        self.logger.error("Invalid profile number", tag="PROFILES")
                except ValueError:
                    self.logger.error("Please enter a valid number", tag="PROFILES")
                    
            elif choice == exit_option:
                # Exit
                self.logger.info("Exiting profile management", tag="MENU")
                break
                
            else:
                self.logger.error(f"Invalid choice. Please enter a number between 1 and {exit_option}.", tag="MENU")