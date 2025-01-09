# Installation 💻

Crawl4AI offers flexible installation options to suit various use cases. You can install it as a Python package, use it with Docker, or run it as a local server.

## Option 1: Python Package Installation (Recommended)

Crawl4AI is now available on PyPI, making installation easier than ever. Choose the option that best fits your needs:

### Basic Installation

For basic web crawling and scraping tasks:

```bash
pip install crawl4ai
playwright install # Install Playwright dependencies
```

### Installation with PyTorch

For advanced text clustering (includes CosineSimilarity cluster strategy):

```bash
pip install crawl4ai[torch]
```

### Installation with Transformers

For text summarization and Hugging Face models:

```bash
pip install crawl4ai[transformer]
```

### Full Installation

For all features:

```bash
pip install crawl4ai[all]
```

### Development Installation

For contributors who plan to modify the source code:

```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e ".[all]"
playwright install # Install Playwright dependencies
```

💡 After installation with "torch", "transformer", or "all" options, it's recommended to run the following CLI command to load the required models:

```bash
crawl4ai-download-models
```

This is optional but will boost the performance and speed of the crawler. You only need to do this once after installation.

## Playwright Installation Note for Ubuntu

If you encounter issues with Playwright installation on Ubuntu, you may need to install additional dependencies:

```bash
sudo apt-get install -y \
    libwoff1 \
    libopus0 \
    libwebp7 \
    libwebpdemux2 \
    libenchant-2-2 \
    libgudev-1.0-0 \
    libsecret-1-0 \
    libhyphen0 \
    libgdk-pixbuf2.0-0 \
    libegl1 \
    libnotify4 \
    libxslt1.1 \
    libevent-2.1-7 \
    libgles2 \
    libxcomposite1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libepoxy0 \
    libgtk-3-0 \
    libharfbuzz-icu0 \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    libxt6 \
    libxaw7 \
    xvfb \
    fonts-noto-color-emoji \
    libfontconfig \
    libfreetype6 \
    xfonts-cyrillic \
    xfonts-scalable \
    fonts-liberation \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-tlwg-loma-otf \
    fonts-freefont-ttf
```

## Option 2: Using Docker (Coming Soon)

Docker support for Crawl4AI is currently in progress and will be available soon. This will allow you to run Crawl4AI in a containerized environment, ensuring consistency across different systems.

## Option 3: Local Server Installation

For those who prefer to run Crawl4AI as a local server, instructions will be provided once the Docker implementation is complete.

## Verifying Your Installation

After installation, you can verify that Crawl4AI is working correctly by running a simple Python script:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://www.example.com")
        print(result.markdown[:500])  # Print first 500 characters

if __name__ == "__main__":
    asyncio.run(main())
```

This script should successfully crawl the example website and print the first 500 characters of the extracted content.

## Getting Help

If you encounter any issues during installation or usage, please check the [documentation](https://docs.crawl4ai.com/) or raise an issue on the [GitHub repository](https://github.com/unclecode/crawl4ai/issues).

Happy crawling! 🕷️🤖