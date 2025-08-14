Installation & Setup (2023 Edition)
===================================

1. Basic Installation
---------------------

```
pip install crawl4ai
```

This installs the **core** Crawl4AI library along with essential dependencies. **No** advanced features (like transformers or PyTorch) are included yet.

2. Initial Setup & Diagnostics
------------------------------

### 2.1 Run the Setup Command

After installing, call:

```
crawl4ai-setup
```

**What does it do?**
- Installs or updates required browser dependencies for both regular and undetected modes
- Performs OS-level checks (e.g., missing libs on Linux)
- Confirms your environment is ready to crawl

### 2.2 Diagnostics

Optionally, you can run **diagnostics** to confirm everything is functioning:

```
crawl4ai-doctor
```

This command attempts to:
- Check Python version compatibility
- Verify Playwright installation
- Inspect environment variables or library conflicts

If any issues arise, follow its suggestions (e.g., installing additional system packages) and re-run `crawl4ai-setup`.

---

3. Verifying Installation: A Simple Crawl (Skip this step if you already run `crawl4ai-doctor`)
-----------------------------------------------------------------------------------------------

Below is a minimal Python script demonstrating a **basic** crawl. It uses our new **`BrowserConfig`** and **`CrawlerRunConfig`** for clarity, though no custom settings are passed in this example:

```
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
        )
        print(result.markdown[:300])  # Show the first 300 characters of extracted text

if __name__ == "__main__":
    asyncio.run(main())
```

**Expected** outcome:
- A headless browser session loads `example.com`
- Crawl4AI returns ~300 characters of markdown.
If errors occur, rerun `crawl4ai-doctor` or manually ensure Playwright is installed correctly.

---