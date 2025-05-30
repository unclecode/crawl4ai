# Preserve Your Identity with Crawl4AI

Crawl4AI empowers you to navigate and interact with the web using your **authentic digital identity**, ensuring you’re recognized as a human and not mistaken for a bot. This tutorial covers:

1. **Managed Browsers** – The recommended approach for persistent profiles and identity-based crawling.  
2. **Magic Mode** – A simplified fallback solution for quick automation without persistent identity.

---

## 1. Managed Browsers: Your Digital Identity Solution

**Managed Browsers** let developers create and use **persistent browser profiles**. These profiles store local storage, cookies, and other session data, letting you browse as your **real self**—complete with logins, preferences, and cookies.

### Key Benefits

- **Authentic Browsing Experience**: Retain session data and browser fingerprints as though you’re a normal user.  
- **Effortless Configuration**: Once you log in or solve CAPTCHAs in your chosen data directory, you can re-run crawls without repeating those steps.  
- **Empowered Data Access**: If you can see the data in your own browser, you can automate its retrieval with your genuine identity.

---

Below is a **partial update** to your **Managed Browsers** tutorial, specifically the section about **creating a user-data directory** using **Playwright’s Chromium** binary rather than a system-wide Chrome/Edge. We’ll show how to **locate** that binary and launch it with a `--user-data-dir` argument to set up your profile. You can then point `BrowserConfig.user_data_dir` to that folder for subsequent crawls.

---

### Creating a User Data Directory (Command-Line Approach via Playwright)

If you installed Crawl4AI (which installs Playwright under the hood), you already have a Playwright-managed Chromium on your system. Follow these steps to launch that **Chromium** from your command line, specifying a **custom** data directory:

1. **Find** the Playwright Chromium binary:
   - On most systems, installed browsers go under a `~/.cache/ms-playwright/` folder or similar path.  
   - To see an overview of installed browsers, run:
     ```bash
     python -m playwright install --dry-run
     ```
     or
     ```bash
     playwright install --dry-run
     ```
     (depending on your environment). This shows where Playwright keeps Chromium.

   - For instance, you might see a path like:
     ```
     ~/.cache/ms-playwright/chromium-1234/chrome-linux/chrome
     ```
     on Linux, or a corresponding folder on macOS/Windows.

2. **Launch** the Playwright Chromium binary with a **custom** user-data directory:
   ```bash
   # Linux example
   ~/.cache/ms-playwright/chromium-1234/chrome-linux/chrome \
       --user-data-dir=/home/<you>/my_chrome_profile
   ```
   ```bash
   # macOS example (Playwright’s internal binary)
   ~/Library/Caches/ms-playwright/chromium-1234/chrome-mac/Chromium.app/Contents/MacOS/Chromium \
       --user-data-dir=/Users/<you>/my_chrome_profile
   ```
   ```powershell
   # Windows example (PowerShell/cmd)
   "C:\Users\<you>\AppData\Local\ms-playwright\chromium-1234\chrome-win\chrome.exe" ^
       --user-data-dir="C:\Users\<you>\my_chrome_profile"
   ```
   
   **Replace** the path with the actual subfolder indicated in your `ms-playwright` cache structure.  
   - This **opens** a fresh Chromium with your new or existing data folder.  
   - **Log into** any sites or configure your browser the way you want.  
   - **Close** when done—your profile data is saved in that folder.

3. **Use** that folder in **`BrowserConfig.user_data_dir`**:
   ```python
   from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

   browser_config = BrowserConfig(
       headless=True,
       use_managed_browser=True,
       user_data_dir="/home/<you>/my_chrome_profile",
       browser_type="chromium"
   )
   ```
   - Next time you run your code, it reuses that folder—**preserving** your session data, cookies, local storage, etc.

---

## 3. Using Managed Browsers in Crawl4AI

Once you have a data directory with your session data, pass it to **`BrowserConfig`**:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    # 1) Reference your persistent data directory
    browser_config = BrowserConfig(
        headless=True,             # 'True' for automated runs
        verbose=True,
        use_managed_browser=True,  # Enables persistent browser strategy
        browser_type="chromium",
        user_data_dir="/path/to/my-chrome-profile"
    )

    # 2) Standard crawl config
    crawl_config = CrawlerRunConfig(
        wait_for="css:.logged-in-content"
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com/private", config=crawl_config)
        if result.success:
            print("Successfully accessed private data with your identity!")
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

### Workflow

1. **Login** externally (via CLI or your normal Chrome with `--user-data-dir=...`).  
2. **Close** that browser.  
3. **Use** the same folder in `user_data_dir=` in Crawl4AI.  
4. **Crawl** – The site sees your identity as if you’re the same user who just logged in.

---

## 4. Magic Mode: Simplified Automation

If you **don’t** need a persistent profile or identity-based approach, **Magic Mode** offers a quick way to simulate human-like browsing without storing long-term data.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        config=CrawlerRunConfig(
            magic=True,  # Simplifies a lot of interaction
            remove_overlay_elements=True,
            page_timeout=60000
        )
    )
```

**Magic Mode**:

- Simulates a user-like experience  
- Randomizes user agent & navigator
- Randomizes interactions & timings  
- Masks automation signals  
- Attempts pop-up handling  

**But** it’s no substitute for **true** user-based sessions if you want a fully legitimate identity-based solution.

---

## 5. Comparing Managed Browsers vs. Magic Mode

| Feature                    | **Managed Browsers**                                           | **Magic Mode**                                     |
|----------------------------|---------------------------------------------------------------|-----------------------------------------------------|
| **Session Persistence**    | Full localStorage/cookies retained in user_data_dir           | No persistent data (fresh each run)                |
| **Genuine Identity**       | Real user profile with full rights & preferences              | Emulated user-like patterns, but no actual identity |
| **Complex Sites**          | Best for login-gated sites or heavy config                    | Simple tasks, minimal login or config needed        |
| **Setup**                  | External creation of user_data_dir, then use in Crawl4AI       | Single-line approach (`magic=True`)                 |
| **Reliability**            | Extremely consistent (same data across runs)                  | Good for smaller tasks, can be less stable          |

---

## 6. Using the BrowserProfiler Class

Crawl4AI provides a dedicated `BrowserProfiler` class for managing browser profiles, making it easy to create, list, and delete profiles for identity-based browsing.

### Creating and Managing Profiles with BrowserProfiler

The `BrowserProfiler` class offers a comprehensive API for browser profile management:

```python
import asyncio
from crawl4ai import BrowserProfiler

async def manage_profiles():
    # Create a profiler instance
    profiler = BrowserProfiler()
    
    # Create a profile interactively - opens a browser window
    profile_path = await profiler.create_profile(
        profile_name="my-login-profile"  # Optional: name your profile
    )
    
    print(f"Profile saved at: {profile_path}")
    
    # List all available profiles
    profiles = profiler.list_profiles()
    
    for profile in profiles:
        print(f"Profile: {profile['name']}")
        print(f"  Path: {profile['path']}")
        print(f"  Created: {profile['created']}")
        print(f"  Browser type: {profile['type']}")
    
    # Get a specific profile path by name
    specific_profile = profiler.get_profile_path("my-login-profile")
    
    # Delete a profile when no longer needed
    success = profiler.delete_profile("old-profile-name")
    
asyncio.run(manage_profiles())
```

**How profile creation works:**
1. A browser window opens for you to interact with
2. You log in to websites, set preferences, etc.
3. When you're done, press 'q' in the terminal to close the browser
4. The profile is saved in the Crawl4AI profiles directory
5. You can use the returned path with `BrowserConfig.user_data_dir`

### Interactive Profile Management

The `BrowserProfiler` also offers an interactive management console that guides you through profile creation, listing, and deletion:

```python
import asyncio
from crawl4ai import BrowserProfiler, AsyncWebCrawler, BrowserConfig

# Define a function to use a profile for crawling
async def crawl_with_profile(profile_path, url):
    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        user_data_dir=profile_path
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url)
        return result

async def main():
    # Create a profiler instance
    profiler = BrowserProfiler()
    
    # Launch the interactive profile manager
    # Passing the crawl function as a callback adds a "crawl with profile" option
    await profiler.interactive_manager(crawl_callback=crawl_with_profile)
    
asyncio.run(main())
```

### Legacy Methods

For backward compatibility, the previous methods on `ManagedBrowser` are still available, but they delegate to the new `BrowserProfiler` class:

```python
from crawl4ai.browser_manager import ManagedBrowser

# These methods still work but use BrowserProfiler internally
profiles = ManagedBrowser.list_profiles()
```

### Complete Example

See the full example in `docs/examples/identity_based_browsing.py` for a complete demonstration of creating and using profiles for authenticated browsing using the new `BrowserProfiler` class.

---

## 7. Locale, Timezone, and Geolocation Control

In addition to using persistent profiles, Crawl4AI supports customizing your browser's locale, timezone, and geolocation settings. These features enhance your identity-based browsing experience by allowing you to control how websites perceive your location and regional settings.

### Setting Locale and Timezone

You can set the browser's locale and timezone through `CrawlerRunConfig`:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://example.com",
        config=CrawlerRunConfig(
            # Set browser locale (language and region formatting)
            locale="fr-FR",  # French (France)
            
            # Set browser timezone
            timezone_id="Europe/Paris",
            
            # Other normal options...
            magic=True,
            page_timeout=60000
        )
    )
```

**How it works:**
- `locale` affects language preferences, date formats, number formats, etc.
- `timezone_id` affects JavaScript's Date object and time-related functionality
- These settings are applied when creating the browser context and maintained throughout the session

### Configuring Geolocation

Control the GPS coordinates reported by the browser's geolocation API:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, GeolocationConfig

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://maps.google.com",  # Or any location-aware site
        config=CrawlerRunConfig(
            # Configure precise GPS coordinates
            geolocation=GeolocationConfig(
                latitude=48.8566,   # Paris coordinates
                longitude=2.3522,
                accuracy=100        # Accuracy in meters (optional)
            ),
            
            # This site will see you as being in Paris
            page_timeout=60000
        )
    )
```

**Important notes:**
- When `geolocation` is specified, the browser is automatically granted permission to access location
- Websites using the Geolocation API will receive the exact coordinates you specify
- This affects map services, store locators, delivery services, etc.
- Combined with the appropriate `locale` and `timezone_id`, you can create a fully consistent location profile

### Combining with Managed Browsers

These settings work perfectly with managed browsers for a complete identity solution:

```python
from crawl4ai import (
    AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, 
    GeolocationConfig
)

browser_config = BrowserConfig(
    use_managed_browser=True,
    user_data_dir="/path/to/my-profile",
    browser_type="chromium"
)

crawl_config = CrawlerRunConfig(
    # Location settings
    locale="es-MX",                  # Spanish (Mexico)
    timezone_id="America/Mexico_City",
    geolocation=GeolocationConfig(
        latitude=19.4326,            # Mexico City
        longitude=-99.1332
    )
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com", config=crawl_config)
```

Combining persistent profiles with precise geolocation and region settings gives you complete control over your digital identity.

## 8. Summary

- **Create** your user-data directory either:
  - By launching Chrome/Chromium externally with `--user-data-dir=/some/path` 
  - Or by using the built-in `BrowserProfiler.create_profile()` method
  - Or through the interactive interface with `profiler.interactive_manager()`
- **Log in** or configure sites as needed, then close the browser
- **Reference** that folder in `BrowserConfig(user_data_dir="...")` + `use_managed_browser=True`
- **Customize** identity aspects with `locale`, `timezone_id`, and `geolocation`
- **List and reuse** profiles with `BrowserProfiler.list_profiles()`
- **Manage** your profiles with the dedicated `BrowserProfiler` class
- Enjoy **persistent** sessions that reflect your real identity
- If you only need quick, ephemeral automation, **Magic Mode** might suffice

**Recommended**: Always prefer a **Managed Browser** for robust, identity-based crawling and simpler interactions with complex sites. Use **Magic Mode** for quick tasks or prototypes where persistent data is unnecessary.

With these approaches, you preserve your **authentic** browsing environment, ensuring the site sees you exactly as a normal user—no repeated logins or wasted time.