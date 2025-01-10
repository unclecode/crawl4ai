# Installation & Setup (2023 Edition)

## 1. Basic Installation

```bash
pip install crawl4ai
```

This installs the **core** Crawl4AI library along with essential dependencies. **No** advanced features (like transformers or PyTorch) are included yet.

## 2. Initial Setup & Diagnostics

### 2.1 Run the Setup Command
After installing, call:

```bash
crawl4ai-setup
```

**What does it do?**
- Installs or updates required Playwright browsers (Chromium, Firefox, etc.)
- Performs OS-level checks (e.g., missing libs on Linux)
- Confirms your environment is ready to crawl

### 2.2 Diagnostics
Optionally, you can run **diagnostics** to confirm everything is functioning:

```bash
crawl4ai-doctor
```

This command attempts to:
- Check Python version compatibility
- Verify Playwright installation
- Inspect environment variables or library conflicts

If any issues arise, follow its suggestions (e.g., installing additional system packages) and re-run `crawl4ai-setup`.

---

## 3. Verifying Installation: A Simple Crawl (Skip this step if you already run `crawl4ai-doctor`)

Below is a minimal Python script demonstrating a **basic** crawl. It uses our new **`BrowserConfig`** and **`CrawlerRunConfig`** for clarity, though no custom settings are passed in this example:

```python
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

## 4. Advanced Installation (Optional)

**Warning**: Only install these **if you truly need them**. They bring in larger dependencies, including big models, which can increase disk usage and memory load significantly.

### 4.1 Torch, Transformers, or All

- **Text Clustering (Torch)**  
  ```bash
  pip install crawl4ai[torch]
  crawl4ai-setup
  ```
  Installs PyTorch-based features (e.g., cosine similarity or advanced semantic chunking).

- **Transformers**  
  ```bash
  pip install crawl4ai[transformer]
  crawl4ai-setup
  ```
  Adds Hugging Face-based summarization or generation strategies.

- **All Features**  
  ```bash
  pip install crawl4ai[all]
  crawl4ai-setup
  ```

#### (Optional) Pre-Fetching Models
```bash
crawl4ai-download-models
```
This step caches large models locally (if needed). **Only do this** if your workflow requires them.

---

## 5. Docker (Experimental)

We provide a **temporary** Docker approach for testing. **It’s not stable and may break** with future releases. We plan a major Docker revamp in a future stable version, 2025 Q1. If you still want to try:

```bash
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
```

You can then make POST requests to `http://localhost:11235/crawl` to perform crawls. **Production usage** is discouraged until our new Docker approach is ready (planned in Jan or Feb 2025).

---

## 6. Local Server Mode (Legacy)

Some older docs mention running Crawl4AI as a local server. This approach has been **partially replaced** by the new Docker-based prototype and upcoming stable server release. You can experiment, but expect major changes. Official local server instructions will arrive once the new Docker architecture is finalized.

---

## Summary

1. **Install** with `pip install crawl4ai` and run `crawl4ai-setup`.
2. **Diagnose** with `crawl4ai-doctor` if you see errors.
3. **Verify** by crawling `example.com` with minimal `BrowserConfig` + `CrawlerRunConfig`.
4. **Advanced** features (Torch, Transformers) are **optional**—avoid them if you don’t need them (they significantly increase resource usage).
5. **Docker** is **experimental**—use at your own risk until the stable version is released.
6. **Local server** references in older docs are largely deprecated; a new solution is in progress.

**Got questions?** Check [GitHub issues](https://github.com/unclecode/crawl4ai/issues) for updates or ask the community!