# 🚀🤖 Crawl4AI: 面向大语言模型与 AI Agent 的开源网络爬虫

<p align="center">
  <a href="README.md">English</a> · <b>简体中文</b>
</p>

<div align="center">

<a href="https://trendshift.io/repositories/11716" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11716" alt="unclecode%2Fcrawl4ai | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![PyPI version](https://badge.fury.io/py/crawl4ai.svg)](https://badge.fury.io/py/crawl4ai)
[![Downloads](https://static.pepy.tech/badge/crawl4ai/month)](https://pepy.tech/project/crawl4ai)
[![Discord](https://img.shields.io/badge/Discord-join%20us-5865F2?logo=discord&logoColor=white)](https://discord.gg/jP8KfhDhyN)
[![Crawl4AI Cloud](https://img.shields.io/badge/Crawl4AI_Cloud-try_it_free-f5a300?style=flat&labelColor=0d0d10)](https://crawl4ai.com/?ref=readme-badge)

**最新版本: [v0.9.4](https://github.com/unclecode/crawl4ai/releases/tag/v0.9.4) (2026年9月23日)** · [查看所有版本 →](https://github.com/unclecode/crawl4ai/releases)

<a href="https://crawl4ai.com/?ref=readme-banner">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/cloud-launch-banner-dark.svg">
    <img alt="Crawl4AI Cloud 现已上线。试运行：免费赠送初始额度，无需绑卡。立即获取 API Key。" src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/cloud-launch-banner-light.svg" width="960">
  </picture>
</a>

</div>

Crawl4AI 能将任意网站转换为干净且适合 LLM 理解的 Markdown 格式，专为 RAG、AI Agent 及数据处理管道设计。你可以选择自行运行这款开源网页爬虫与提取工具（永久免费），也可以使用单个 API Key 调用云端托管服务：统一接口涵盖爬取、搜索与提取，并支持为你的 Agent 提供 MCP 协议集成。

## 使用 Crawl4AI 的两种方式

### 🐍 自行本地运行：完全开源，永久免费

```bash
pip install -U crawl4ai
crawl4ai-setup        # 安装浏览器内核（仅需执行一次）
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

Docker 服务端、CLI 及全部配置选项：[安装指南](#installation) · [官方文档 docs.crawl4ai.com](https://docs.crawl4ai.com)

### ☁️ 使用云端服务：免装浏览器，无需配置代理

1. [![10 秒获取 API Key](https://img.shields.io/badge/Get_a_key_in_10_seconds-%241_pass%2C_no_signup-f5a300?style=for-the-badge&labelColor=0d0d10)](https://crawl4ai.com/?ref=readme)  
   验证邮箱即可获得初始免费体验额度，无需绑定信用卡。试运行阶段：价格可能会调整，购买的额度永久有效。
2. 将任意网页转换为 Markdown：

   ```bash
   curl -s https://api.crawl4ai.com/scrape \
     -H "Authorization: Bearer $CRAWL4AI_KEY" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://news.ycombinator.com"}' | jq -r .markdown
   ```

   同一个 API Key 同样适用于 `/search`、`/answer`、`/extract` 以及多 URL 批量任务（`/scrape/batch`, `/scrape/jobs`）。按量付费：[查看实时定价](https://crawl4ai.com/docs?ref=readme#pricing)。
3. 为你的 AI Agent 接入 MCP。以 Claude Code 为例；[查看 Codex、Cursor 与 OpenCode 配置指南 →](https://crawl4ai.com/docs?ref=readme#mcp)

   ```bash
   claude mcp add --transport http crawl4ai https://api.crawl4ai.com/mcp \
     --header "Authorization: Bearer $CRAWL4AI_KEY"
   ```

### 哪种方式适合你？

| | 🐍 Python 库 | 🐳 独立 Docker 服务 | ☁️ Crawl4AI Cloud |
|---|---|---|---|
| **浏览器运行方** | 本地 Python 进程运行 | 本地机器 Docker 容器中运行 | 云端全托管运行 |
| **高 JS 渲染与反爬防护** | 自行调整配置与代理 | 自行调整配置与代理 | 云端全自动智能处理 |
| **网页搜索能力** | – | – | 支持 `/search` 与 `/answer` |
| **使用成本** | 永久完全免费 | 免费（自行承担算力） | 按需付费；注册即送免费额度 |

<details>
  <summary>🤓 <strong>作者自述</strong></summary>

在父亲的启蒙下，我从小就在一台 Amstrad 电脑上写代码，从那以后便从未停止过探索。读研期间我主修自然语言处理（NLP），为了学术研究编写了大量的爬虫。正是在那个时候，我深刻体会到了高质量数据提取对于模型的重要性。

2023 年，我急需一个将网页高质量转换为 Markdown 的工具。当时市面上的“开源”方案要么要求注册账号、申请 API Token 并付费 16 美元，要么效果远远不及预期。这彻底激怒了我，我在几天内编写出了 Crawl4AI 的雏形并开源。项目迅速走红，如今已经成为 GitHub 上星标最多的网络爬虫。

我选择开源是为了让所有人都能**无门槛使用**。现在我打造云平台，则是为了让大规模专业抓取更加**经济实惠**，让任何人都能在预算内运行真正工业级的爬取。如果你认同这个理念，欢迎加入社区、提交反馈，或者用它爬取一些令人惊叹的内容。

云平台现已正式上线：[Crawl4AI Cloud](https://crawl4ai.com/?ref=readme)。
</details>

<details>
  <summary>为什么开发者选择 Crawl4AI</summary>

- **专为 LLM 优化的输出**：智能 Markdown，具备规范标题、表格、代码块以及引用溯源信息
- **极致的实际执行速度**：异步浏览器池、多级缓存机制、极小跳步
- **掌控全局**：会话复用、代理池管理、Cookie、自定义用户脚本与生命周期 Hooks
- **自适应智能**：自主学习站点规律，只探索和提取核心内容
- **任意环境部署**：无需鉴权密钥、支持 CLI 与 Docker，或开箱即用的全托管云服务
</details>

## ✨ 功能特性

<details>
<summary>📝 <strong>Markdown 生成</strong></summary>

- 🧹 **纯净 Markdown**：保留标题、列表、表格与代码块，排版结构极度契合 LLM 阅读偏好。
- 🎯 **自适应精简 (Fit Markdown)**：智能过滤菜单、页脚及模板杂讯：支持 `PruningContentFilterLXML`、针对特定查询的 `BM25ContentFilter` 以及 `LLMContentFilter`。
- 🔗 **引用标注**：网页链接自动转换为带编号的参考文献列表。
- 🛠️ **自定义策略**：可插拔自定义 Markdown 生成器。

☁️ 云端同样具备此能力：`POST /scrape` 直接返回该 Markdown，无需在本地启动浏览器。[查看文档 →](https://crawl4ai.com/docs?ref=readme#scrape)
</details>

<details>
<summary>📊 <strong>结构化数据提取</strong></summary>

- 🔎 **CSS 与 XPath 提取方案**：无需消耗 LLM 即可实现毫秒级快速提取（`JsonCssExtractionStrategy`、`JsonXPathExtractionStrategy`、`RegexExtractionStrategy`）。
- 🪄 **模式生成器**：仅需描述一次提取目标，`generate_schema` 即可自动生成可复用的提取 Schema。
- 🤖 **LLM 提取**：支持任意模型供应商（开源模型或商业 API），提取为强类型 JSON Schema（`LLMExtractionStrategy`）。
- 🧱 **文本分块**：针对超长网页提供按主题、正则或句子的智能分块支持。
</details>

<details>
<summary>⚡ <strong>强大的爬虫内核</strong></summary>

- 🌱 **URL 发现**：`AsyncUrlSeeder`（支持 Sitemaps、Common Crawl）与 `DomainMapper`；开启 `prefetch=True` 模式可提速 5 到 10 倍。
- 🚀 **动态渲染**：执行自定义 JavaScript、等待页面元素出现、整页智能滚动（`scan_full_page`），完美支持无限滚动与懒加载图片。
- 📸 **页面快照与 PDF**：支持对任意网页生成高清截图与 PDF 归档。
- 🖼️ **富媒体与链接解析**：图片、音频、视频、`srcset`、站内/站外链接、iframe 及元数据提取。
- 📂 **原始 HTML 与本地文件**：支持直接爬取 `raw:` 字符串与 `file://` 本地文件。
- 🛠️ **全流程 Hooks**：在页面生命周期的每一个阶段注入钩子函数。
- 💾 **智能缓存**：自动跳过重复请求，显著提升抓取效率。
- ⚡ **海量并发调度**：`arun_many` 配合内存自适应分发器，稳定应对大规模采集。

☁️ 云端同样具备此能力：单次流式请求支持多达 50 个 URL，后台任务支持多达 10,000 个 URL。[查看文档 →](https://crawl4ai.com/docs?ref=readme#batch)
</details>

<details>
<summary>🐳 <strong>自托管服务 (Docker)</strong></summary>

- 🔐 **开箱即用高安全**：所有端点均受到 `CRAWL4AI_API_TOKEN` 严格保护。
- 🧰 **全功能 REST API**：`/md`、`/html`、`/crawl`、`/crawl/stream`、`/screenshot`、`/pdf`、`/execute_js`。
- 🤖 **MCP 协议支持**：直接连接 Claude Code 及其他 Agent 到你的私有服务。
- 📊 **可视化监控面板与调试演练场**：内置活跃浏览器池与预热页面管理。
- 🏗️ **跨平台镜像**：原生支持 AMD64 与 ARM64 架构。

☁️ 不想维护服务器？云端提供完全相同能力的托管体验。[获取 API Key →](https://crawl4ai.com/?ref=readme)
</details>

<details>
<summary>☁️ <strong>云端专享增值能力</strong></summary>

- 🔍 **网页搜索 API**：`GET /search`，无需浏览器，直接返回排序清洗后的搜索结果。[查看文档 →](https://crawl4ai.com/docs?ref=readme#search)
- 💬 **智能答疑**：`GET /answer` 针对提问直接给出综合答案（实验特性）。[查看文档 →](https://crawl4ai.com/docs?ref=readme#answer)
- 🧪 **免配置 LLM 提取**：`POST /extract`，无需自带模型 API Key。[查看文档 →](https://crawl4ai.com/docs?ref=readme#extract)
- 🧗 **复杂 JS 渲染与反爬拦截突破**：后台全自动智能处理，免去手动挑选引擎的烦恼。[查看文档 →](https://crawl4ai.com/docs?ref=readme#scrape)
- 🤝 **Agent 原生 MCP 插件**：在 Claude Code、Codex、Cursor 或 OpenCode 中仅需一行命令配置。[查看文档 →](https://crawl4ai.com/docs?ref=readme#mcp)
</details>

<a id="installation"></a>

## 🛠️ 安装指南

<details>
<summary>🐍 <strong>pip 安装</strong></summary>

```bash
pip install -U crawl4ai
crawl4ai-setup      # 安装并配置浏览器环境
crawl4ai-doctor     # 诊断环境与安装完整性
```

若自动浏览器安装失败，可手动执行：

```bash
python -m playwright install --with-deps chromium
```

安装预览版：`pip install crawl4ai --pre`

**源码开发安装**（面向贡献者）：

```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e ".[all]"     # 或仅安装核心组件: pip install -e .
```
</details>

<details>
<summary>🐳 <strong>Docker 服务器</strong></summary>

启动服务需要提供安全 Token。若未提供，服务仅允许容器内部访问。

```bash
export CRAWL4AI_API_TOKEN="$(openssl rand -hex 32)"
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g \
  -e CRAWL4AI_API_TOKEN="$CRAWL4AI_API_TOKEN" \
  unclecode/crawl4ai:latest
```

测试服务可用性（容器启动约需 10 秒）：

```bash
curl -s http://localhost:11235/md \
  -H "Authorization: Bearer $CRAWL4AI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.ycombinator.com"}' | jq -r .markdown
```

监控面板地址为 `http://localhost:11235/dashboard`，演练场地址为 `http://localhost:11235/playground`。LLM 密钥、MCP 及全量配置说明详见：[自托管指南](https://docs.crawl4ai.com/core/self-hosting/)。
</details>

<details>
<summary>⌨️ <strong>命令行工具 (`crwl`)</strong></summary>

```bash
# 将网页提取为 Markdown
crwl https://news.ycombinator.com -o markdown

# 广度优先深度爬取，最多 10 个页面
crwl https://docs.crawl4ai.com --deep-crawl bfs --max-pages 10

# 针对页面内容进行提问（需要配置 LLM Key: crwl config）
crwl https://www.example.com/products -q "Extract all product prices"
```
</details>

## 🔬 高级使用示例

更多示例可参阅 [docs/examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples)。

<details>
<summary>📝 <strong>清洁与精简 Markdown (Fit Markdown)</strong></summary>

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilterLXML
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilterLXML(threshold=0.48, threshold_type="fixed", min_word_threshold=0)
        ),
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun(url="https://en.wikipedia.org/wiki/Web_crawler", config=run_config)
        print(len(result.markdown.raw_markdown), "characters of raw Markdown")
        print(len(result.markdown.fit_markdown), "characters after the filter")

asyncio.run(main())
```
</details>

<details>
<summary>🖥️ <strong>无 LLM 解析 JavaScript 渲染页面的结构化数据</strong></summary>

```python
import asyncio, json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, JsonCssExtractionStrategy

schema = {
    "name": "Quotes",
    "baseSelector": "div.quote",
    "fields": [
        {"name": "text", "selector": "span.text", "type": "text"},
        {"name": "author", "selector": "small.author", "type": "text"},
        {"name": "tags", "selector": "a.tag", "type": "list", "fields": [{"name": "tag", "type": "text"}]},
    ],
}

async def main():
    run_config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema),
        scan_full_page=True,   # 滚动到底部以加载所有名言数据
        scroll_delay=0.5,
        cache_mode=CacheMode.BYPASS,
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun(url="https://quotes.toscrape.com/scroll", config=run_config)
        quotes = json.loads(result.extracted_content)
        print(f"Extracted {len(quotes)} quotes")
        print(json.dumps(quotes[0], indent=2))

asyncio.run(main())
```
</details>

<details>
<summary>📚 <strong>基于 LLM 的结构化数据提取</strong></summary>

```python
import os, asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, LLMConfig, LLMExtractionStrategy

class ModelFee(BaseModel):
    model_name: str = Field(..., description="模型名称")
    input_fee: str = Field(..., description="输入 Token 单价")
    output_fee: str = Field(..., description="输出 Token 单价")

async def main():
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=LLMExtractionStrategy(
            # 支持 LiteLLM 支持的任意供应商，例如 "ollama/llama3.3" (api_token="no-token")
            llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY")),
            schema=ModelFee.model_json_schema(),
            extraction_type="schema",
            instruction="提取每个模型的名称及其输入和输出 Token 费用。",
        ),
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://openai.com/api/pricing/", config=run_config)
        print(result.extracted_content)

asyncio.run(main())
```
</details>

<details>
<summary>🤖 <strong>持久化浏览器配置环境 (Browser Profile)</strong></summary>

```python
import os, asyncio
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    user_data_dir = os.path.join(Path.home(), ".crawl4ai", "browser_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    browser_config = BrowserConfig(headless=True, user_data_dir=user_data_dir, use_persistent_context=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, magic=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="ADDRESS_OF_A_CHALLENGING_WEBSITE", config=run_config)
        print(result.success, len(result.markdown))

asyncio.run(main())
```
</details>

## 📖 文档中心

- Python 库文档、指南与 API 参考：[docs.crawl4ai.com](https://docs.crawl4ai.com/)
- 云平台文档：[crawl4ai.com/docs](https://crawl4ai.com/docs?ref=readme)
- 版本发布说明：[Releases](https://github.com/unclecode/crawl4ai/releases) · 路线图：[ROADMAP.md](https://github.com/unclecode/crawl4ai/blob/main/ROADMAP.md)

## 🤝 参与贡献

我们热烈欢迎开源社区的贡献。请参阅[贡献指南](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTORS.md)获取更多详细信息。

## 📄 开源许可证与署名要求

本项目基于 Apache License 2.0 许可证开源，建议通过下方徽章进行署名。详情请参阅 [Apache 2.0 License](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)。

### 署名方式
在使用 Crawl4AI 时，建议选择以下方式之一进行署名：

<details>
<summary>📈 <strong>1. 徽章署名（推荐）</strong></summary>
在你的 README、文档或网站中添加以下徽章之一：

| 主题风格 | 徽章展示 |
|-------|-------|
| **Disco 动效主题** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **Night 暗黑霓虹主题** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-night.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **Dark 经典暗色主题** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-dark.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **Light 经典明亮主题** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-light.svg" alt="Powered by Crawl4AI" width="200"/></a> |

添加徽章的 HTML 代码：
```html
<!-- Disco 动效主题 -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- Night 暗黑霓虹主题 -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-night.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- Dark 经典暗色主题 -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-dark.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- Light 经典明亮主题 -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-light.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- 极简 Shield 徽章 -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://img.shields.io/badge/Powered%20by-Crawl4AI-blue?style=flat-square" alt="Powered by Crawl4AI"/>
</a>
```

</details>

<details>
<summary>📖 <strong>2. 文本署名</strong></summary>
在你的文档中添加以下说明：
```
This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.
```
</details>

## 📚 论文与学术引用

如果您在研究或项目中使用了 Crawl4AI，请按如下格式引用：

```bibtex
@software{crawl4ai2024,
  author = {UncleCode},
  title = {Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub Repository},
  howpublished = {\url{https://github.com/unclecode/crawl4ai}},
  commit = {Please use the commit hash you're working with}
}
```

纯文本引用格式：
```
UncleCode. (2024). Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper [Computer software]. 
GitHub. https://github.com/unclecode/crawl4ai
```

## 🗾 使命与愿景

我们的使命是通过将数字足迹转化为结构化、有价值的资产，释放个人与企业数据的潜力。Crawl4AI 为个人和组织提供提取和构建数据的开源工具，并为之带来公平的收益回馈。[查看完整使命宣言 →](./MISSION.md)

## 💖 支持 Crawl4AI

1. ⭐ **给仓库点亮 Star**：帮助更多开发者发现本项目。
2. ☁️ **使用云平台**：[crawl4ai.com](https://crawl4ai.com/?ref=readme)。云端收益持续反哺开源库开发。
3. 💝 **GitHub Sponsors 赞助**：[github.com/sponsors/unclecode](https://github.com/sponsors/unclecode)
4. 🏢 **企业赞助**：赞助等级与权益详见 [SPONSORS.md](SPONSORS.md)。

## 🌟 当前赞助商

### 🤝 战略合作伙伴

这些公司提供核心基础设施与技术，为 Crawl4AI 提供强大支撑——从网络访问、代理网络到 AI 工具链和数据管道。

| 合作伙伴 | 简介 |
|------|------|
| <a href="https://www.joinmassive.com/" target="_blank"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/assets/sponsors/massive_light.svg"><source media="(prefers-color-scheme: light)" srcset="docs/assets/sponsors/massive.svg"><img alt="Massive" src="docs/assets/sponsors/massive.svg" height="40"/></picture></a> | Massive 是一款网络访问 API，依托分布在 195 多个国家和地区的数百万台志愿设备构建。AI Agent、大模型与数据管道借助它以高可靠、实时且大规模地触达互联网上的任何站点。 |

### 🏢 企业赞助商

我们的企业赞助商大力支持 Crawl4AI，助力其扩展至生产级数据流水线。

| 企业 | 简介 | 赞助级别 |
|------|------|----------------------------|
| <a href="https://kipo.ai" target="_blank"><img src="https://docs.crawl4ai.com/uploads/sponsors/20251013045751_2d54f57f117c651e.png" alt="DataSync" height="40"/></a> | 帮助工程师和采购人员在数秒内查找、对比并采购电子与工业元器件，提供规格参数、定价、交期与替代方案支持。| 🥇 黄金赞助商 |
| <a href="https://www.kidocode.com/" target="_blank"><img src="https://docs.crawl4ai.com/uploads/sponsors/20251013045045_bb8dace3f0440d65.svg" alt="Kidocode" height="40"/></a> | Kidocode 是一所面向 5-18 岁青少年的混合技术与创业教育学院，提供线上及线下教育。 | 🥇 黄金赞助商 |
| <a href="https://www.alephnull.sg/" target="_blank"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/assets/sponsors/aleph_null_light.svg"><source media="(prefers-color-scheme: light)" srcset="docs/assets/sponsors/aleph_null.svg"><img alt="Aleph null" src="docs/assets/sponsors/aleph_null.svg" height="40"/></picture></a> | 新加坡 Aleph Null 是亚洲领先的教育科技中心，致力于以学生为中心、AI 驱动的创新教育体系。 | 🥇 黄金赞助商 |

---

### 💼 成为战略合作伙伴或赞助商

有兴趣与 Crawl4AI 建立合作关系？

无论您是代理服务提供商、AI 基础设施企业、云平台，还是希望支持 Crawl4AI 生态发展的组织，我们都非常期待与您交流。

📩 商务合作邮箱：hello@crawl4ai.com

### 🧑‍🤝 个人赞助者

衷心感谢所有个人支持者！每一份赞助都在帮助我们的开源使命生生不息！

<p align="left">
  <a href="https://github.com/hafezparast"><img src="https://avatars.githubusercontent.com/u/14273305?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/ntohidi"><img src="https://avatars.githubusercontent.com/u/17140097?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/Sjoeborg"><img src="https://avatars.githubusercontent.com/u/17451310?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/romek-rozen"><img src="https://avatars.githubusercontent.com/u/30595969?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/Kourosh-Kiyani"><img src="https://avatars.githubusercontent.com/u/34105600?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/Etherdrake"><img src="https://avatars.githubusercontent.com/u/67021215?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/shaman247"><img src="https://avatars.githubusercontent.com/u/211010067?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/work-flow-manager"><img src="https://avatars.githubusercontent.com/u/217665461?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
</p>

> 想加入赞助者行列？ [赞助 Crawl4AI →](https://github.com/sponsors/unclecode)

## 📧 联系方式

[Discord 社区](https://discord.gg/jP8KfhDhyN) · [X @unclecode](https://x.com/unclecode) · [GitHub @unclecode](https://github.com/unclecode) · hello@crawl4ai.com

- **专业从事爬虫或 AI Agent 开发？** 欢迎在 X 上私信我。我们求贤若渴，正在广纳英才。
- **来自企业用户？** 我们提供定制化企业解决方案。已完成 SOC 2 Type I 认证，Type II 认证正在推进中。欢迎来信洽谈：hello@crawl4ai.com。

<p align="center">
  <a href="https://github.com/unclecode/crawl4ai/network/members"><img src="https://img.shields.io/github/forks/unclecode/crawl4ai?style=social" alt="GitHub Forks"/></a>
  <a href="https://pypi.org/project/crawl4ai/"><img src="https://img.shields.io/pypi/pyversions/crawl4ai" alt="Python Version"/></a>
  <a href="https://github.com/sponsors/unclecode"><img src="https://img.shields.io/github/sponsors/unclecode?style=flat&logo=GitHub-Sponsors&label=Sponsors&color=pink" alt="GitHub Sponsors"/></a>
  <a href="https://x.com/crawl4ai"><img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=flat&logo=x&logoColor=white" alt="Follow on X"/></a>
  <a href="https://www.linkedin.com/company/crawl4ai"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white" alt="Follow on LinkedIn"/></a>
</p>

祝爬取愉快！🕸️🚀

## Star History

<a href="https://www.star-history.com/?type=date&repos=unclecode%2Fcrawl4ai">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=unclecode/crawl4ai&type=date&theme=dark&legend=top-left&sealed_token=KuajrA7ScH8VT4KagC7nm1xbazTVaNs6rdok4At2dV6tDl91YR_dxmHhmsffjhFiWdLYlzdACxZ-cWLwp8tZHCYxSDMjITf3Vnu4mPns7YdLetyQBPHMQ2f_KakXdbvbVP6PofI82GNqGCVEXtPnZWHC8WM6CzZe6s6cJb6_ga_kn-jh-BeHdyuRRdVR" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=unclecode/crawl4ai&type=date&legend=top-left&sealed_token=KuajrA7ScH8VT4KagC7nm1xbazTVaNs6rdok4At2dV6tDl91YR_dxmHhmsffjhFiWdLYlzdACxZ-cWLwp8tZHCYxSDMjITf3Vnu4mPns7YdLetyQBPHMQ2f_KakXdbvbVP6PofI82GNqGCVEXtPnZWHC8WM6CzZe6s6cJb6_ga_kn-jh-BeHdyuRRdVR" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=unclecode/crawl4ai&type=date&legend=top-left&sealed_token=KuajrA7ScH8VT4KagC7nm1xbazTVaNs6rdok4At2dV6tDl91YR_dxmHhmsffjhFiWdLYlzdACxZ-cWLwp8tZHCYxSDMjITf3Vnu4mPns7YdLetyQBPHMQ2f_KakXdbvbVP6PofI82GNqGCVEXtPnZWHC8WM6CzZe6s6cJb6_ga_kn-jh-BeHdyuRRdVR" />
 </picture>
</a>

---

> 💡 **文档维护说明**：本中文文档由社区志愿者（@JasonYeYuhe）翻译维护，最后同步更新于 2026年10月08日。如发现内容与官方英文原版存在差异或新特性滞后，欢迎提交 PR 共同完善！
