### browser_manager.py

| Function | What it does |
|---|---|
| `ManagedBrowser.build_browser_flags` | Returns baseline Chromium CLI flags, disables GPU and sandbox, plugs locale, timezone, stealth tweaks, and any extras from `BrowserConfig`. |
| `ManagedBrowser.__init__` | Stores config and logger, creates temp dir, preps internal state. |
| `ManagedBrowser.start` | Spawns or connects to the Chromium process, returns its CDP endpoint plus the `subprocess.Popen` handle. |
| `ManagedBrowser._initial_startup_check` | Pings the CDP endpoint once to be sure the browser is alive, raises if not. |
| `ManagedBrowser._monitor_browser_process` | Async-loops on the subprocess, logs exits or crashes, restarts if policy allows. |
| `ManagedBrowser._get_browser_path_WIP` | Old helper that maps OS + browser type to an executable path. |
| `ManagedBrowser._get_browser_path` | Current helper, checks env vars, Playwright cache, and OS defaults for the real executable. |
| `ManagedBrowser._get_browser_args` | Builds the final CLI arg list by merging user flags, stealth flags, and defaults. |
| `ManagedBrowser.cleanup` | Terminates the browser, stops monitors, deletes the temp dir. |
| `ManagedBrowser.create_profile` | Opens a visible browser so a human can log in, then zips the resulting user-data-dir to `~/.crawl4ai/profiles/<name>`. |
| `ManagedBrowser.list_profiles` | Thin wrapper, now forwarded to `BrowserProfiler.list_profiles()`. |
| `ManagedBrowser.delete_profile` | Thin wrapper, now forwarded to `BrowserProfiler.delete_profile()`. |
| `BrowserManager.__init__` | Holds the global Playwright instance, browser handle, config signature cache, session map, and logger. |
| `BrowserManager.start` | Boots the underlying `ManagedBrowser`, then spins up the default Playwright browser context with stealth patches. |
| `BrowserManager._build_browser_args` | Translates `CrawlerRunConfig` (proxy, UA, timezone, headless flag, etc.) into Playwright `launch_args`. |
| `BrowserManager.setup_context` | Applies locale, geolocation, permissions, cookies, and UA overrides on a fresh context. |
| `BrowserManager.create_browser_context` | Internal helper that actually calls `browser.new_context(**options)` after running `setup_context`. |
| `BrowserManager._make_config_signature` | Hashes the non-ephemeral parts of `CrawlerRunConfig` so contexts can be reused safely. |
| `BrowserManager.get_page` | Returns a ready `Page` for a given session id, reusing an existing one or creating a new context/page, injects helper scripts, updates `last_used`. |
| `BrowserManager.kill_session` | Force-closes a context/page for a session and removes it from the session map. |
| `BrowserManager._cleanup_expired_sessions` | Periodic sweep that drops sessions idle longer than `ttl_seconds`. |
| `BrowserManager.close` | Gracefully shuts down all contexts, the browser, Playwright, and background tasks. |

---

### browser_profiler.py

| Function | What it does |
|---|---|
| `BrowserProfiler.__init__` | Sets up profile folder paths, async logger, and signal handlers. |
| `BrowserProfiler.create_profile` | Launches a visible browser with a new user-data-dir for manual login, on exit compresses and stores it as a named profile. |
| `BrowserProfiler.cleanup_handler` | General SIGTERM/SIGINT cleanup wrapper that kills child processes. |
| `BrowserProfiler.sigint_handler` | Handles Ctrl-C during an interactive session, makes sure the browser shuts down cleanly. |
| `BrowserProfiler.listen_for_quit_command` | Async REPL that exits when the user types `q`. |
| `BrowserProfiler.list_profiles` | Enumerates `~/.crawl4ai/profiles`, prints profile name, browser type, size, and last modified. |
| `BrowserProfiler.get_profile_path` | Returns the absolute path of a profile given its name, or `None` if missing. |
| `BrowserProfiler.delete_profile` | Removes a profile folder or a direct path from disk, with optional confirmation prompt. |
| `BrowserProfiler.interactive_manager` | Text UI loop for listing, creating, deleting, or launching profiles. |
| `BrowserProfiler.launch_standalone_browser` | Starts a non-headless Chromium with remote debugging enabled and keeps it alive for manual tests. |
| `BrowserProfiler.get_cdp_json` | Pulls `/json/version` from a CDP endpoint and returns the parsed JSON. |
| `BrowserProfiler.launch_builtin_browser` | Spawns a headless Chromium in the background, saves `{wsEndpoint, pid, started_at}` to `~/.crawl4ai/builtin_browser.json`. |
| `BrowserProfiler.get_builtin_browser_info` | Reads that JSON file, verifies the PID, and returns browser status info. |
| `BrowserProfiler._is_browser_running` | Cross-platform helper that checks if a PID is still alive. |
| `BrowserProfiler.kill_builtin_browser` | Terminates the background builtin browser and removes its status file. |
| `BrowserProfiler.get_builtin_browser_status` | Returns `{running: bool, wsEndpoint, pid, started_at}` for quick health checks. |

Let me know what you want to tweak or dive into next.