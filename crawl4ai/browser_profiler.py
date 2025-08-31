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
import json
import subprocess
import time
from typing import List, Dict, Optional, Any
from rich.console import Console

from .async_configs import BrowserConfig
from .browser_manager import ManagedBrowser
from .async_logger import AsyncLogger, AsyncLoggerBase, LogColor
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
        # Initialize rich console for colorful input prompts
        self.console = Console()
        
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
        
        # Builtin browser config file
        self.builtin_browser_dir = os.path.join(get_home_folder(), "builtin-browser")
        self.builtin_config_file = os.path.join(self.builtin_browser_dir, "browser_config.json")
        os.makedirs(self.builtin_browser_dir, exist_ok=True)
    
    def _is_windows(self) -> bool:
        """Check if running on Windows platform."""
        return sys.platform.startswith('win') or sys.platform == 'cygwin'
    
    def _is_macos(self) -> bool:
        """Check if running on macOS platform."""
        return sys.platform == 'darwin'
    
    def _is_linux(self) -> bool:
        """Check if running on Linux platform."""
        return sys.platform.startswith('linux')
    
    def _get_quit_message(self, tag: str) -> str:
        """Get appropriate quit message based on context."""
        if tag == "PROFILE":
            return "Closing browser and saving profile..."
        elif tag == "CDP":
            return "Closing browser..."
        else:
            return "Closing browser..."
    
    async def _listen_windows(self, user_done_event, check_browser_process, tag: str):
        """Windows-specific keyboard listener using msvcrt."""
        try:
            import msvcrt
        except ImportError:
            raise ImportError("msvcrt module not available on this platform")
        
        while True:
            try:
                # Check for keyboard input
                if msvcrt.kbhit():
                    raw = msvcrt.getch()
                    
                    # Handle Unicode decoding more robustly
                    key = None
                    try:
                        key = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            # Try different encodings
                            key = raw.decode("latin1")
                        except UnicodeDecodeError:
                            # Skip if we can't decode
                            continue
                    
                    # Validate key
                    if not key or len(key) != 1:
                        continue
                    
                    # Check for printable characters only
                    if not key.isprintable():
                        continue
                    
                    # Check for quit command
                    if key.lower() == "q":
                        self.logger.info(
                            self._get_quit_message(tag),
                            tag=tag,
                            base_color=LogColor.GREEN
                        )
                        user_done_event.set()
                        return
                
                # Check if browser process ended
                if await check_browser_process():
                    return
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.warning(f"Error in Windows keyboard listener: {e}", tag=tag)
                # Continue trying instead of failing completely
                await asyncio.sleep(0.1)
                continue
    
    async def _listen_unix(self, user_done_event: asyncio.Event, check_browser_process, tag: str):
        """Unix/Linux/macOS keyboard listener using termios and select."""
        try:
            import termios
            import tty
            import select
        except ImportError:
            raise ImportError("termios/tty/select modules not available on this platform")
        
        # Get stdin file descriptor
        try:
            fd = sys.stdin.fileno()
        except (AttributeError, OSError):
            raise ImportError("stdin is not a terminal")
        
        # Save original terminal settings
        old_settings = None
        try:
            old_settings = termios.tcgetattr(fd)
        except termios.error as e:
            raise ImportError(f"Cannot get terminal attributes: {e}")
        
        try:
            # Switch to non-canonical mode (cbreak mode)
            tty.setcbreak(fd)
            
            while True:
                try:
                    # Use select to check if input is available (non-blocking)
                    # Timeout of 0.5 seconds to periodically check browser process
                    readable, _, _ = select.select([sys.stdin], [], [], 0.5)
                    
                    if readable:
                        # Read one character
                        key = sys.stdin.read(1)
                        
                        if key and key.lower() == "q":
                            self.logger.info(
                                self._get_quit_message(tag),
                                tag=tag,
                                base_color=LogColor.GREEN
                            )
                            user_done_event.set()
                            return
                    
                    # Check if browser process ended
                    if await check_browser_process():
                        return
                    
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.1)
                    
                except (KeyboardInterrupt, EOFError):
                    # Handle Ctrl+C or EOF gracefully
                    self.logger.info("Keyboard interrupt received", tag=tag)
                    user_done_event.set()
                    return
                except Exception as e:
                    self.logger.warning(f"Error in Unix keyboard listener: {e}", tag=tag)
                    await asyncio.sleep(0.1)
                    continue
                    
        finally:
            # Always restore terminal settings
            if old_settings is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except Exception as e:
                    self.logger.error(f"Failed to restore terminal settings: {e}", tag=tag)
    
    async def _listen_fallback(self, user_done_event: asyncio.Event, check_browser_process, tag: str):
        """Fallback keyboard listener using simple input() method."""
        self.logger.info("Using fallback input mode. Type 'q' and press Enter to quit.", tag=tag)
        
        # Run input in a separate thread to avoid blocking
        import threading
        import queue
        
        input_queue = queue.Queue()
        
        def input_thread():
            """Thread function to handle input."""
            try:
                while not user_done_event.is_set():
                    try:
                        # Use input() with a prompt
                        user_input = input("Press 'q' + Enter to quit: ").strip().lower()
                        input_queue.put(user_input)
                        if user_input == 'q':
                            break
                    except (EOFError, KeyboardInterrupt):
                        input_queue.put('q')
                        break
                    except Exception as e:
                        self.logger.warning(f"Error in input thread: {e}", tag=tag)
                        break
            except Exception as e:
                self.logger.error(f"Input thread failed: {e}", tag=tag)
        
        # Start input thread
        thread = threading.Thread(target=input_thread, daemon=True)
        thread.start()
        
        try:
            while not user_done_event.is_set():
                # Check for user input
                try:
                    user_input = input_queue.get_nowait()
                    if user_input == 'q':
                        self.logger.info(
                            self._get_quit_message(tag),
                            tag=tag,
                            base_color=LogColor.GREEN
                        )
                        user_done_event.set()
                        return
                except queue.Empty:
                    pass
                
                # Check if browser process ended
                if await check_browser_process():
                    return
                
                # Small delay
                await asyncio.sleep(0.5)
                
        except Exception as e:
            self.logger.error(f"Fallback listener failed: {e}", tag=tag)
            user_done_event.set()
    
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
        
        # Print instructions for the user with rich formatting
        border = f"{'='*80}"
        self.logger.info("{border}", tag="PROFILE", params={"border": f"\n{border}"}, colors={"border": LogColor.CYAN})
        self.logger.info("Creating browser profile: {profile_name}", tag="PROFILE", params={"profile_name": profile_name}, colors={"profile_name": LogColor.GREEN})
        self.logger.info("Profile directory: {profile_path}", tag="PROFILE", params={"profile_path": profile_path}, colors={"profile_path": LogColor.YELLOW})
        
        self.logger.info("\nInstructions:", tag="PROFILE")
        self.logger.info("1. A browser window will open for you to set up your profile.", tag="PROFILE")
        self.logger.info("{segment}, configure settings, etc. as needed.", tag="PROFILE", params={"segment": "2. Log in to websites"}, colors={"segment": LogColor.CYAN})
        self.logger.info("3. When you're done, {segment} to close the browser.", tag="PROFILE", params={"segment": "press 'q' in this terminal"}, colors={"segment": LogColor.YELLOW})
        self.logger.info("4. The profile will be saved and ready to use with Crawl4AI.", tag="PROFILE")
        self.logger.info("{border}", tag="PROFILE", params={"border": f"{border}\n"}, colors={"border": LogColor.CYAN})
        
        browser_config.headless = False
        browser_config.user_data_dir = profile_path
        
        
        # Create managed browser instance
        managed_browser = ManagedBrowser(
            browser_config=browser_config,
            # user_data_dir=profile_path,
            # headless=False,  # Must be visible
            logger=self.logger,
            # debugging_port=browser_config.debugging_port
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
            """Cross-platform keyboard listener that waits for 'q' key press."""
            # First output the prompt
            self.logger.info(
                "Press {segment} when you've finished using the browser...",
                tag="PROFILE",
                params={"segment": "'q'"}, colors={"segment": LogColor.YELLOW},
                base_color=LogColor.CYAN
            )

            async def check_browser_process():
                """Check if browser process is still running."""
                if (
                    managed_browser.browser_process
                    and managed_browser.browser_process.poll() is not None
                ):
                    self.logger.info(
                        "Browser already closed. Ending input listener.", tag="PROFILE"
                    )
                    user_done_event.set()
                    return True
                return False

            # Try platform-specific implementations with fallback
            try:
                if self._is_windows():
                    await self._listen_windows(user_done_event, check_browser_process, "PROFILE")
                else:
                    await self._listen_unix(user_done_event, check_browser_process, "PROFILE")
            except Exception as e:
                self.logger.warning(f"Platform-specific keyboard listener failed: {e}", tag="PROFILE")
                self.logger.info("Falling back to simple input mode...", tag="PROFILE")
                await self._listen_fallback(user_done_event, check_browser_process, "PROFILE")
        
        try:
            from playwright.async_api import async_playwright

            # Start the browser
            # await managed_browser.start()
            # 1. ── Start the browser ─────────────────────────────────────────
            cdp_url = await managed_browser.start()

            # 2. ── Attach Playwright to that running Chrome ──────────────────
            pw       = await async_playwright().start()
            browser  = await pw.chromium.connect_over_cdp(cdp_url)
            # Grab the existing default context (there is always one)
            context  = browser.contexts[0]
            
            # Check if browser started successfully
            browser_process = managed_browser.browser_process
            if not browser_process:
                self.logger.error("Failed to start browser process.", tag="PROFILE")
                return None
            
            self.logger.info("Browser launched. Waiting for you to finish...", tag="PROFILE") 
            
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
            
            # 3. ── Persist storage state *before* we kill Chrome ─────────────
            state_file = os.path.join(profile_path, "storage_state.json")
            try:
                await context.storage_state(path=state_file)
                self.logger.info(f"[PROFILE].i  storage_state saved → {state_file}", tag="PROFILE")
            except Exception as e:
                self.logger.warning(f"[PROFILE].w  failed to save storage_state: {e}", tag="PROFILE")

            # 4. ── Close everything cleanly ──────────────────────────────────
            await browser.close()
            await pw.stop()

            # If the browser is still running and the user pressed 'q', terminate it
            if browser_process.poll() is None and user_done_event.is_set():
                self.logger.info("Terminating browser process...", tag="PROFILE")
                await managed_browser.cleanup()
            
            self.logger.success(f"Browser closed. Profile saved at: {profile_path}", tag="PROFILE")
                
        except Exception as e:
            self.logger.error(f"Error creating profile: {e!s}", tag="PROFILE")
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
            # Chrck if profile_name itself is full path
            if os.path.isabs(profile_name):
                profile_path = profile_name
            else:
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
            self.logger.info("\nProfile Management Options:", tag="MENU")
            self.logger.info("1. Create a new profile", tag="MENU", base_color=LogColor.GREEN)
            self.logger.info("2. List available profiles", tag="MENU", base_color=LogColor.YELLOW)
            self.logger.info("3. Delete a profile", tag="MENU", base_color=LogColor.RED)
            
            # Only show crawl option if callback provided
            if crawl_callback:
                self.logger.info("4. Use a profile to crawl a website", tag="MENU", base_color=LogColor.CYAN)
                self.logger.info("5. Exit", tag="MENU", base_color=LogColor.MAGENTA)
                exit_option = "5"
            else:
                self.logger.info("4. Exit", tag="MENU", base_color=LogColor.MAGENTA)
                exit_option = "4"
            
            self.logger.info(f"\n[cyan]Enter your choice (1-{exit_option}): [/cyan]", end="")
            choice = input()
            
            if choice == "1":
                # Create new profile
                self.console.print("[green]Enter a name for the new profile (or press Enter for auto-generated name): [/green]", end="")
                name = input()
                await self.create_profile(name or None)
                
            elif choice == "2":
                # List profiles
                profiles = self.list_profiles()
                
                if not profiles:
                    self.logger.warning("  No profiles found. Create one first with option 1.", tag="PROFILES")
                    continue
                
                # Print profile information 
                self.logger.info("\nAvailable profiles:", tag="PROFILES")
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")
                    self.logger.info(f"    Path: {profile['path']}", tag="PROFILES", base_color=LogColor.YELLOW)
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
                self.logger.info("\nAvailable profiles:", tag="PROFILES", base_color=LogColor.YELLOW)
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")
                    
                # Get profile to delete
                self.console.print("[red]Enter the number of the profile to delete (or 'c' to cancel): [/red]", end="")
                profile_idx = input()
                if profile_idx.lower() == 'c':
                    continue
                    
                try:
                    idx = int(profile_idx) - 1
                    if 0 <= idx < len(profiles):
                        profile_name = profiles[idx]["name"]
                        self.logger.info(f"Deleting profile: [yellow]{profile_name}[/yellow]", tag="PROFILES")
                        
                        # Confirm deletion
                        self.console.print("[red]Are you sure you want to delete this profile? (y/n): [/red]", end="")
                        confirm = input()
                        if confirm.lower() == 'y':
                            success = self.delete_profile(profiles[idx]["path"])
                            
                            if success:
                                self.logger.success(f"Profile {profile_name} deleted successfully", tag="PROFILES")
                            else:
                                self.logger.error(f"Failed to delete profile {profile_name}", tag="PROFILES")
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
                self.logger.info("\nAvailable profiles:", tag="PROFILES", base_color=LogColor.YELLOW)
                for i, profile in enumerate(profiles):
                    self.logger.info(f"[{i+1}] {profile['name']}", tag="PROFILES")
                    
                # Get profile to use
                self.console.print("[cyan]Enter the number of the profile to use (or 'c' to cancel): [/cyan]", end="")
                profile_idx = input()
                if profile_idx.lower() == 'c':
                    continue
                    
                try:
                    idx = int(profile_idx) - 1
                    if 0 <= idx < len(profiles):
                        profile_path = profiles[idx]["path"]
                        self.console.print("[cyan]Enter the URL to crawl: [/cyan]", end="")
                        url = input()
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

    async def launch_standalone_browser(self, 
                                  browser_type: str = "chromium",
                                  user_data_dir: Optional[str] = None,
                                  debugging_port: int = 9222,
                                  headless: bool = False,
                                  save_as_builtin: bool = False) -> Optional[str]:
        """
        Launch a standalone browser with CDP debugging enabled and keep it running
        until the user presses 'q'. Returns and displays the CDP URL.
        
        Args:
            browser_type (str): Type of browser to launch ('chromium' or 'firefox')
            user_data_dir (str, optional): Path to user profile directory
            debugging_port (int): Port to use for CDP debugging
            headless (bool): Whether to run in headless mode
            
        Returns:
            str: CDP URL for the browser, or None if launch failed
            
        Example:
            ```python
            profiler = BrowserProfiler()
            cdp_url = await profiler.launch_standalone_browser(
                user_data_dir="/path/to/profile",
                debugging_port=9222
            )
            # Use cdp_url to connect to the browser
            ```
        """
        # Use the provided directory if specified, otherwise create a temporary directory
        if user_data_dir:
            # Directory is provided directly, ensure it exists
            profile_path = user_data_dir
            os.makedirs(profile_path, exist_ok=True)
        else:
            # Create a temporary profile directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            profile_name = f"temp_{timestamp}_{uuid.uuid4().hex[:6]}"
            profile_path = os.path.join(self.profiles_dir, profile_name)
            os.makedirs(profile_path, exist_ok=True)
        
        # Print initial information
        border = f"{'='*80}"
        self.logger.info("{border}", tag="CDP", params={"border": border}, colors={"border": LogColor.CYAN})
        self.logger.info("Launching standalone browser with CDP debugging", tag="CDP")
        self.logger.info("Browser type: {browser_type}", tag="CDP", params={"browser_type": browser_type}, colors={"browser_type": LogColor.CYAN})
        self.logger.info("Profile path: {profile_path}", tag="CDP", params={"profile_path": profile_path}, colors={"profile_path": LogColor.YELLOW})
        self.logger.info(f"Debugging port: {debugging_port}", tag="CDP")
        self.logger.info(f"Headless mode: {headless}", tag="CDP")
        
        # create browser config
        browser_config = BrowserConfig(
            browser_type=browser_type,
            headless=headless,
            user_data_dir=profile_path,
            debugging_port=debugging_port,
            verbose=True
        )
        
        # Create managed browser instance
        managed_browser = ManagedBrowser(
            browser_config=browser_config,
            user_data_dir=profile_path,
            headless=headless,
            logger=self.logger,
            debugging_port=debugging_port
        )
        
        # Set up signal handlers to ensure cleanup on interrupt
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        
        # Define cleanup handler for signals
        async def cleanup_handler(sig, frame):
            self.logger.warning("\nCleaning up browser process...", tag="CDP")
            await managed_browser.cleanup()
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            if sig == signal.SIGINT:
                self.logger.error("Browser terminated by user.", tag="CDP")
                sys.exit(1)
                    
        # Set signal handlers
        def sigint_handler(sig, frame):
            asyncio.create_task(cleanup_handler(sig, frame))
        
        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)
        
        # Event to signal when user wants to exit
        user_done_event = asyncio.Event()
        
        # Run keyboard input loop in a separate task
        async def listen_for_quit_command():
            """Cross-platform keyboard listener that waits for 'q' key press."""
            # First output the prompt
            self.logger.info(
                "Press {segment} to stop the browser and exit...",
                tag="CDP",
                params={"segment": "'q'"}, colors={"segment": LogColor.YELLOW},
                base_color=LogColor.CYAN
            )

            async def check_browser_process():
                """Check if browser process is still running."""
                if managed_browser.browser_process and managed_browser.browser_process.poll() is not None:
                    self.logger.info("Browser already closed. Ending input listener.", tag="CDP")
                    user_done_event.set()
                    return True
                return False

            # Try platform-specific implementations with fallback
            try:
                if self._is_windows():
                    await self._listen_windows(user_done_event, check_browser_process, "CDP")
                else:
                    await self._listen_unix(user_done_event, check_browser_process, "CDP")
            except Exception as e:
                self.logger.warning(f"Platform-specific keyboard listener failed: {e}", tag="CDP")
                self.logger.info("Falling back to simple input mode...", tag="CDP")
                await self._listen_fallback(user_done_event, check_browser_process, "CDP")
                
        # Function to retrieve and display CDP JSON config
        async def get_cdp_json(port):
            import aiohttp
            cdp_url = f"http://localhost:{port}"
            json_url = f"{cdp_url}/json/version"
            
            try:
                async with aiohttp.ClientSession() as session:
                    # Try multiple times in case the browser is still starting up
                    for _ in range(10):
                        try:
                            async with session.get(json_url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    return cdp_url, data
                        except Exception:
                            pass
                        
                        await asyncio.sleep(0.5)
                    
                    return cdp_url, None
            except Exception as e:
                self.logger.error(f"Error fetching CDP JSON: {str(e)}", tag="CDP")
                return cdp_url, None
        
        cdp_url = None
        config_json = None
        
        try:
            # Start the browser
            await managed_browser.start()
            
            # Check if browser started successfully
            browser_process = managed_browser.browser_process
            if not browser_process:
                self.logger.error("Failed to start browser process.", tag="CDP")
                return None
            
            self.logger.info("Browser launched successfully. Retrieving CDP information...", tag="CDP") 
            
            # Get CDP URL and JSON config
            cdp_url, config_json = await get_cdp_json(debugging_port)
            
            if cdp_url:
                self.logger.success(f"CDP URL: {cdp_url}", tag="CDP")
                
                if config_json:
                    # Display relevant CDP information
                    self.logger.info(f"Browser: {config_json.get('Browser', 'Unknown')}", tag="CDP", colors={"Browser": LogColor.CYAN})
                    self.logger.info(f"Protocol Version: {config_json.get('Protocol-Version', 'Unknown')}", tag="CDP", colors={"Protocol-Version": LogColor.CYAN})
                    if 'webSocketDebuggerUrl' in config_json:
                        self.logger.info("WebSocket URL: {webSocketDebuggerUrl}", tag="CDP", params={"webSocketDebuggerUrl": config_json['webSocketDebuggerUrl']}, colors={"webSocketDebuggerUrl": LogColor.GREEN})
                else:
                    self.logger.warning("Could not retrieve CDP configuration JSON", tag="CDP")
            else:
                self.logger.error(f"Failed to get CDP URL on port {debugging_port}", tag="CDP")
                await managed_browser.cleanup()
                return None
            
            # Start listening for keyboard input
            listener_task = asyncio.create_task(listen_for_quit_command())
            
            # Wait for the user to press 'q' or for the browser process to exit naturally
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
                self.logger.info("Terminating browser process...", tag="CDP")
                await managed_browser.cleanup()
            
            self.logger.success("Browser closed.", tag="CDP")
                
        except Exception as e:
            self.logger.error(f"Error launching standalone browser: {str(e)}", tag="CDP")
            await managed_browser.cleanup()
            return None
        finally:
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            
            # Make sure browser is fully cleaned up
            await managed_browser.cleanup()
        
        # Return the CDP URL
        return cdp_url
    
    async def launch_builtin_browser(self, 
                                 browser_type: str = "chromium",
                                 debugging_port: int = 9222,
                                 headless: bool = True) -> Optional[str]:
        """
        Launch a browser in the background for use as the builtin browser.
        
        Args:
            browser_type (str): Type of browser to launch ('chromium' or 'firefox')
            debugging_port (int): Port to use for CDP debugging
            headless (bool): Whether to run in headless mode
            
        Returns:
            str: CDP URL for the browser, or None if launch failed
        """
        # Check if there's an existing browser still running
        browser_info = self.get_builtin_browser_info()
        if browser_info and self._is_browser_running(browser_info.get('pid')):
            self.logger.info("Builtin browser is already running", tag="BUILTIN")
            return browser_info.get('cdp_url')
        
        # Create a user data directory for the builtin browser
        user_data_dir = os.path.join(self.builtin_browser_dir, "user_data")
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Create managed browser instance
        managed_browser = ManagedBrowser(
            browser_type=browser_type,
            user_data_dir=user_data_dir,
            headless=headless,
            logger=self.logger,
            debugging_port=debugging_port
        )
        
        try:
            # Start the browser
            await managed_browser.start()
            
            # Check if browser started successfully
            browser_process = managed_browser.browser_process
            if not browser_process:
                self.logger.error("Failed to start browser process.", tag="BUILTIN")
                return None
            
            # Get CDP URL
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
                self.logger.warning(f"Could not verify browser: {str(e)}", tag="BUILTIN")
            
            # Save browser info
            browser_info = {
                'pid': browser_process.pid,
                'cdp_url': cdp_url,
                'user_data_dir': user_data_dir,
                'browser_type': browser_type,
                'debugging_port': debugging_port,
                'start_time': time.time(),
                'config': config_json
            }
            
            with open(self.builtin_config_file, 'w') as f:
                json.dump(browser_info, f, indent=2)
                
            # Detach from the browser process - don't keep any references
            # This is important to allow the Python script to exit while the browser continues running
            # We'll just record the PID and other info, and the browser will run independently
            managed_browser.browser_process = None
                
            self.logger.success(f"Builtin browser launched at CDP URL: {cdp_url}", tag="BUILTIN")
            return cdp_url
            
        except Exception as e:
            self.logger.error(f"Error launching builtin browser: {str(e)}", tag="BUILTIN")
            if managed_browser:
                await managed_browser.cleanup()
            return None
    
    def get_builtin_browser_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the builtin browser.
        
        Returns:
            dict: Browser information or None if no builtin browser is configured
        """
        if not os.path.exists(self.builtin_config_file):
            return None
            
        try:
            with open(self.builtin_config_file, 'r') as f:
                browser_info = json.load(f)
                
            # Check if the browser is still running
            if not self._is_browser_running(browser_info.get('pid')):
                self.logger.warning("Builtin browser is not running", tag="BUILTIN")
                return None
                
            return browser_info
        except Exception as e:
            self.logger.error(f"Error reading builtin browser config: {str(e)}", tag="BUILTIN")
            return None
            
    def _is_browser_running(self, pid: Optional[int]) -> bool:
        """Check if a process with the given PID is running"""
        if not pid:
            return False
            
        try:
            # Check if the process exists
            if sys.platform == "win32":
                process = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], 
                                         capture_output=True, text=True)
                return str(pid) in process.stdout
            else:
                # Unix-like systems
                os.kill(pid, 0)  # This doesn't actually kill the process, just checks if it exists
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False
            
    async def kill_builtin_browser(self) -> bool:
        """
        Kill the builtin browser if it's running.
        
        Returns:
            bool: True if the browser was killed, False otherwise
        """
        browser_info = self.get_builtin_browser_info()
        if not browser_info:
            self.logger.warning("No builtin browser found", tag="BUILTIN")
            return False
            
        pid = browser_info.get('pid')
        if not pid:
            return False
            
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
            else:
                os.kill(pid, signal.SIGTERM)
                # Wait for termination
                for _ in range(5):
                    if not self._is_browser_running(pid):
                        break
                    await asyncio.sleep(0.5)
                else:
                    # Force kill if still running
                    os.kill(pid, signal.SIGKILL)
                    
            # Remove config file
            if os.path.exists(self.builtin_config_file):
                os.unlink(self.builtin_config_file)
                
            self.logger.success("Builtin browser terminated", tag="BUILTIN")
            return True
        except Exception as e:
            self.logger.error(f"Error killing builtin browser: {str(e)}", tag="BUILTIN")
            return False
    
    async def get_builtin_browser_status(self) -> Dict[str, Any]:
        """
        Get status information about the builtin browser.
        
        Returns:
            dict: Status information with running, cdp_url, and info fields
        """
        browser_info = self.get_builtin_browser_info()
        
        if not browser_info:
            return {
                'running': False,
                'cdp_url': None,
                'info': None
            }
            
        return {
            'running': True,
            'cdp_url': browser_info.get('cdp_url'),
            'info': browser_info
        }


if __name__ == "__main__":
    # Example usage
    profiler = BrowserProfiler()
    
    # Create a new profile
    import os
    from pathlib import Path
    home_dir = Path.home()
    profile_path = asyncio.run(profiler.create_profile( str(home_dir / ".crawl4ai/profiles/test-profile")))

        
            
    # Launch a standalone browser
    asyncio.run(profiler.launch_standalone_browser())
    
    # List profiles
    profiles = profiler.list_profiles()
    for profile in profiles:
        print(f"Profile: {profile['name']}, Path: {profile['path']}")
    
    # Delete a profile
    success = profiler.delete_profile("my-profile")
    if success:
        print("Profile deleted successfully")
    else:
        print("Failed to delete profile")