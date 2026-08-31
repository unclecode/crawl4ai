# Builtin Browser in Crawl4AI

This document explains the builtin browser feature in Crawl4AI and how to use it effectively.

## What is the Builtin Browser?

The builtin browser is a persistent Chrome instance that Crawl4AI manages for you. It runs in the background and can be used by multiple crawling operations, eliminating the need to start and stop browsers for each crawl.

Benefits include:
- **Faster startup times** - The browser is already running, so your scripts start faster
- **Shared resources** - All your crawling scripts can use the same browser instance
- **Simplified management** - No need to worry about CDP URLs or browser processes
- **Persistent cookies and sessions** - Browser state persists between script runs
- **Less resource usage** - Only one browser instance for multiple scripts

## Using the Builtin Browser

### In Python Code

Using the builtin browser in your code is simple:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Create browser config with builtin mode
browser_config = BrowserConfig(
    browser_mode="builtin",  # This is the key setting!
    headless=True            # Can be headless or not
)

# Create the crawler
crawler = AsyncWebCrawler(config=browser_config)

# Use it - no need to explicitly start()
result = await crawler.arun("https://example.com")
```

Key points:
1. Set `browser_mode="builtin"` in your BrowserConfig
2. No need for explicit `start()` call - the crawler will automatically connect to the builtin browser
3. No need to use a context manager or call `close()` - the browser stays running

### Via CLI

The CLI provides commands to manage the builtin browser:

```bash
# Start the builtin browser
crwl browser start

# Check its status
crwl browser status

# Open a visible window to see what the browser is doing
crwl browser view --url https://example.com

# Stop it when no longer needed
crwl browser stop

# Restart with different settings
crwl browser restart --no-headless
```

When crawling via CLI, simply add the builtin browser mode:

```bash
crwl https://example.com -b "browser_mode=builtin"
```

## How It Works

1. When a crawler with `browser_mode="builtin"` is created:
   - It checks if a builtin browser is already running
   - If not, it automatically launches one
   - It connects to the browser via CDP (Chrome DevTools Protocol)

2. The browser process continues running after your script exits
   - This means it's ready for the next crawl
   - You can manage it via the CLI commands

3. During installation, Crawl4AI attempts to create a builtin browser automatically

## Example

See the [builtin_browser_example.py](builtin_browser_example.py) file for a complete example.

Run it with:

```bash
python builtin_browser_example.py
```

## When to Use

The builtin browser is ideal for:
- Scripts that run frequently
- Development and testing workflows
- Applications that need to minimize startup time
- Systems where you want to manage browser instances centrally

You might not want to use it when:
- Running one-off scripts
- When you need different browser configurations for different tasks
- In environments where persistent processes are not allowed

## Troubleshooting

If you encounter issues:

1. Check the browser status:
   ```
   crwl browser status
   ```

2. Try restarting it:
   ```
   crwl browser restart
   ```

3. If problems persist, stop it and let Crawl4AI start a fresh one:
   ```
   crwl browser stop
   ```