# 🚀🤖 Crawl4AI: the open-source web crawler for LLMs and AI agents

<div class = "badges" align="center">

  <p>
    <a href="https://trendshift.io/repositories/11716" target="_blank">
      <img src="https://trendshift.io/api/badge/repositories/11716"
           alt="unclecode%2Fcrawl4ai | Trendshift"
           style="width: 250px; height: 55px;"
           width="250" height="55"/>
    </a>

  </p>

  <p>
    <a href="https://github.com/unclecode/crawl4ai/stargazers">
      <img src="https://img.shields.io/github/stars/unclecode/crawl4ai?style=social"
           alt="GitHub Stars"/>
    </a>
    <a href="https://github.com/unclecode/crawl4ai/network/members">
      <img src="https://img.shields.io/github/forks/unclecode/crawl4ai?style=social"
           alt="GitHub Forks"/>
    </a>
    <a href="https://badge.fury.io/py/crawl4ai">
      <img src="https://badge.fury.io/py/crawl4ai.svg"
           alt="PyPI version"/>
    </a>
  </p>

  <p>
    <a href="https://pypi.org/project/crawl4ai/">
      <img src="https://img.shields.io/pypi/pyversions/crawl4ai"
           alt="Python Version"/>
    </a>
    <a href="https://pepy.tech/project/crawl4ai">
      <img src="https://static.pepy.tech/badge/crawl4ai/month"
           alt="Downloads"/>
    </a>
    <a href="https://github.com/unclecode/crawl4ai/blob/main/LICENSE">
      <img src="https://img.shields.io/github/license/unclecode/crawl4ai"
           alt="License"/>
    </a>
  </p>
  <p align="center">
    <a href="https://x.com/crawl4ai">
      <img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X" />
    </a>
    <a href="https://www.linkedin.com/company/crawl4ai">
      <img src="https://img.shields.io/badge/Follow%20on%20LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Follow on LinkedIn" />
    </a>
    <a href="https://discord.gg/jP8KfhDhyN">
      <img src="https://img.shields.io/badge/Join%20our%20Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join our Discord" />
    </a>
  </p>
  
</div>

Crawl4AI turns any website into clean, LLM-ready Markdown for RAG, AI agents and data pipelines. Run the open-source web crawler and scraper yourself, free forever, or use it hosted with one key: scrape, search and extract through one API, with MCP for your agent.

## Two ways to use Crawl4AI

### 🐍 Run it yourself: open source, forever

```bash
pip install -U crawl4ai
crawl4ai-setup        # installs the browser, once
```

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com")
        print(result.markdown)

asyncio.run(main())
```

Docker server, CLI and every option: [Installation](core/installation.md) · [Self-hosting](core/self-hosting.md)

### ☁️ Or use the cloud: no browsers, no proxies

1. [![Get a key in 10 seconds](https://img.shields.io/badge/Get_a_key_in_10_seconds-%241_pass%2C_no_signup-f5a300?style=for-the-badge&labelColor=0d0d10)](https://crawl4ai.com/?ref=docs)  
   Verify your email and your first $10 pack is on us (until 31 December 2026, then $5 to start). No card.
2. Get any page as Markdown:

   ```bash
   curl -s https://api.crawl4ai.com/scrape \
     -H "Authorization: Bearer $CRAWL4AI_KEY" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://news.ycombinator.com"}' | jq -r .markdown
   ```

   The same key works for `/search`, `/answer`, `/extract` and many URLs at once (`/scrape/batch`, `/scrape/jobs`). Pay as you go: [live prices](https://crawl4ai.com/docs?ref=docs#pricing).
3. Give it to your AI agent. Claude Code shown; [Codex, Cursor and OpenCode →](https://crawl4ai.com/docs?ref=docs#mcp)

   ```bash
   claude mcp add --transport http crawl4ai https://api.crawl4ai.com/mcp \
     --header "Authorization: Bearer $CRAWL4AI_KEY"
   ```

### Which one?

| | 🐍 Library | 🐳 Your own server | ☁️ Crawl4AI Cloud |
|---|---|---|---|
| **Runs the browsers** | you, in your Python process | you, in Docker on your machine | we do |
| **JS-heavy pages and bot walls** | your settings, your proxies | your settings, your proxies | handled for you, automatically |
| **Web search** | – | – | `/search` and `/answer` |
| **Price** | free, forever | free (your hosting) | pay as you go; your first $10 is on us |

## 🆕 AI Assistant Skill Now Available!

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
  <h3 style="color: white; margin: 0 0 10px 0;">🤖 Crawl4AI Skill for Claude & AI Assistants</h3>
  <p style="color: white; margin: 10px 0;">Supercharge your AI coding assistant with complete Crawl4AI knowledge! Download our comprehensive skill package that includes:</p>
  <ul style="color: white; margin: 10px 0;">
    <li>📚 Complete SDK reference (23K+ words)</li>
    <li>🚀 Ready-to-use extraction scripts</li>
    <li>⚡ Schema generation for efficient scraping</li>
    <li>🔧 Version 0.7.4 compatible</li>
  </ul>
  <div style="text-align: center; margin-top: 15px;">
    <a href="assets/crawl4ai-skill.zip" download style="background: white; color: #667eea; padding: 12px 30px; border-radius: 5px; text-decoration: none; font-weight: bold; display: inline-block; transition: transform 0.2s;">
      📦 Download Skill Package
    </a>
  </div>
  <p style="color: white; margin: 15px 0 0 0; font-size: 0.9em; text-align: center;">
    Works with Claude, Cursor, Windsurf, and other AI coding assistants. Import the .zip file into your AI assistant's skill/knowledge system.
  </p>
</div>

## 🎯 New: Adaptive Web Crawling

Crawl4AI now features intelligent adaptive crawling that knows when to stop! Using advanced information foraging algorithms, it determines when sufficient information has been gathered to answer your query.

[Learn more about Adaptive Crawling →](core/adaptive-crawling.md)


## Video Tutorial

<div align="center">
  <iframe width="560" height="315" src="https://www.youtube.com/embed/xo3qK6Hg9AA?start=15" title="Crawl4AI Tutorial" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</div>

---

## What Does Crawl4AI Do?

Crawl4AI is a feature-rich crawler and scraper that aims to:

1. **Generate Clean Markdown**: Perfect for RAG pipelines or direct ingestion into LLMs.  
2. **Structured Extraction**: Parse repeated patterns with CSS, XPath, or LLM-based extraction.  
3. **Advanced Browser Control**: Hooks, proxies, stealth modes, session re-use—fine-grained control.  
4. **High Performance**: Parallel crawling, chunk-based extraction, real-time use cases.  
5. **Open Source**: No forced API keys, no paywalls—everyone can access their data.  

**Core Philosophies**:
- **Democratize Data**: Free to use, transparent, and highly configurable.  
- **LLM Friendly**: Minimally processed, well-structured text, images, and metadata, so AI models can easily consume it.

---

## Documentation Structure

To help you get started, we’ve organized our docs into clear sections:

- **Setup & Installation**  
  Basic instructions to install Crawl4AI via pip or Docker.  
- **Quick Start**  
  A hands-on introduction showing how to do your first crawl, generate Markdown, and do a simple extraction.  
- **Core**  
  Deeper guides on single-page crawling, advanced browser/crawler parameters, content filtering, and caching.  
- **Advanced**  
  Explore link & media handling, lazy loading, hooking & authentication, proxies, session management, and more.  
- **Extraction**  
  Detailed references for no-LLM (CSS, XPath) vs. LLM-based strategies, chunking, and clustering approaches.  
- **API Reference**  
  Find the technical specifics of each class and method, including `AsyncWebCrawler`, `arun()`, and `CrawlResult`.

Throughout these sections, you’ll find code samples you can **copy-paste** into your environment. If something is missing or unclear, raise an issue or PR.

---

## How You Can Support

- **Star & Fork**: If you find Crawl4AI helpful, star the repo on GitHub or fork it to add your own features.  
- **File Issues**: Encounter a bug or missing feature? Let us know by filing an issue, so we can improve.  
- **Pull Requests**: Whether it’s a small fix, a big feature, or better docs—contributions are always welcome.  
- **Join Discord**: Come chat about web scraping, crawling tips, or AI workflows with the community.  
- **Spread the Word**: Mention Crawl4AI in your blog posts, talks, or on social media.  

**Our mission**: to empower everyone—students, researchers, entrepreneurs, data scientists—to access, parse, and shape the world’s data with speed, cost-efficiency, and creative freedom.

---

## Quick Links

- **[GitHub Repo](https://github.com/unclecode/crawl4ai)**  
- **[Installation Guide](./core/installation.md)**  
- **[Quick Start](./core/quickstart.md)**  
- **[API Reference](./api/async-webcrawler.md)**  
- **[Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)**  

Thank you for joining me on this journey. Let’s keep building an **open, democratic** approach to data extraction and AI together.

Happy Crawling!  
— *Unclecode, Founder & Maintainer of Crawl4AI*  
