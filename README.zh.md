# 🚀🤖 Crawl4AI: 开源、对大模型友好的网页爬虫与抓取工具

<div align="center">

<a href="https://trendshift.io/repositories/11716" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11716" alt="unclecode%2Fcrawl4ai | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)

[![PyPI version](https://badge.fury.io/py/crawl4ai.svg)](https://badge.fury.io/py/crawl4ai)
[![Python Version](https://img.shields.io/pypi/pyversions/crawl4ai)](https://pypi.org/project/crawl4ai/)
[![Downloads](https://static.pepy.tech/badge/crawl4ai/month)](https://pepy.tech/project/crawl4ai)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/unclecode?style=flat&logo=GitHub-Sponsors&label=Sponsors&color=pink)](https://github.com/sponsors/unclecode)

---
#### 🚀 Crawl4AI Cloud API — 封闭内测中 (即将推出)
可靠、大规模的网页提取，旨在比现有任何解决方案都**大幅降低成本**。

👉 **在此申请 [早期访问](https://forms.gle/E9MyPaNXACnAMaqG7)**  
_我们将分阶段引入用户，并与早期用户紧密合作。名额有限。_

---

<p align="center">
    <a href="https://x.com/crawl4ai">
      <img src="https://img.shields.io/badge/在_X_上关注-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X" />
    </a>
    <a href="https://www.linkedin.com/company/crawl4ai">
      <img src="https://img.shields.io/badge/在_LinkedIn_上关注-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Follow on LinkedIn" />
    </a>
    <a href="https://discord.gg/jP8KfhDhyN">
      <img src="https://img.shields.io/badge/加入我们的_Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join our Discord" />
    </a>
  </p>
</div>

<p align="center">
  <strong>简体中文</strong> | <a href="README.md">English</a>
</p>

Crawl4AI 将互联网转化为干净、可供大语言模型（LLM）使用的 Markdown 格式，适用于 RAG、智能体（Agents）和数据流水线。速度快、可控性强，经受过 50k+ 星标社区的实战检验。

[✨ 查看最新更新 v0.8.0](#-最近更新)

✨ **v0.8.0 新特性**：崩溃恢复与预取模式！深度爬取（Deep crawl）现支持崩溃恢复，通过 `resume_state` 和 `on_state_change` 回调确保护理长时运行的爬取任务。新增 `prefetch=True` 模式，使 URL 发现速度提升 5-10 倍。针对 Docker API 的关键安全修复（默认禁用 Hook，屏蔽 file:// 协议 URL）。[发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.8.0.md)

✨ **近期 v0.7.8**：稳定性与 Bug 修复版本！修复了 11 个 Bug，涵盖 Docker API 问题、LLM 提取改进、URL 处理修复以及依赖更新。[发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.8.md)

✨ **前一版本 v0.7.7**：具备实时监控功能的完整自托管平台！企业级监控仪表盘、全面的 REST API、WebSocket 流式传输以及智能浏览器池管理。[发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.7.md)

<details>
  <summary>🤓 <strong>我的个人故事</strong></summary>

多亏了我的父亲，我从小在 Amstrad 电脑上长大，且从未停止过构建。在研究生阶段，我专注于自然语言处理（NLP）并为研究构建爬虫。正是在那里，我意识到提取质量是多么重要。

2023 年，我需要将网页转换为 Markdown。当时唯一的“开源”方案要求注册账号、获取 API 令牌并支付 16 美元，结果却依然不尽人意。我一怒之下，在几天内构建了 Crawl4AI，它迅速走红。现在它是 GitHub 上星标最多的爬虫项目。

我将其开源是为了**可用性**，任何人都可以无门槛使用。现在我正在构建这个平台是为了**可负担性**，让任何人都能在不倾家荡产的情况下运行大规模爬取。如果你对此有共鸣，欢迎加入、提供反馈，或者只是用它爬取一些令人惊叹的内容。
</details>


<details>
  <summary>为什么开发者选择 Crawl4AI</summary>

- **大模型就绪的输出**：智能生成的 Markdown，包含标题、表格、代码及引用提示。
- **实战速度极快**：异步浏览器池、缓存机制、最小化跳转。
- **完全控制**：会话（Sessions）、代理、Cookie、用户脚本、钩子（Hooks）。
- **自适应智能**：学习站点模式，仅探索核心内容。
- **随处部署**：无需 API 密钥，支持 CLI 和 Docker，对云端友好。
</details>


## 🚀 快速开始 

1. 安装 Crawl4AI:
```bash
# 安装包
pip install -U crawl4ai

# 安装预发布版本
pip install crawl4ai --pre

# 运行安装后设置
crawl4ai-setup

# 验证安装
crawl4ai-doctor
```

如果遇到任何与浏览器相关的错误，可以手动安装：
```bash
python -m playwright install --with-deps chromium
```

2. 使用 Python 运行简单的网页爬取：
```python
import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

3. 或使用全新的命令行界面（CLI）：
```bash
# 基础爬取并输出为 markdown
crwl https://www.nbcnews.com/business -o markdown

# 深度爬取，使用广度优先搜索 (BFS) 策略，最多 10 页
crwl https://docs.crawl4ai.com --deep-crawl bfs --max-pages 10

# 使用 LLM 提取并针对特定问题提问
crwl https://www.example.com/products -q "提取所有产品价格"
```

## 💖 支持 Crawl4AI

> 🎉 **赞助计划现已开启！** 在助力 5.1 万多名开发者并经历一年的成长后，Crawl4AI 正式推出针对**创业公司**和**企业**的专项支持。成为首批 50 位**创始赞助商**，您的名字将永久留在我们的名人堂中。

Crawl4AI 是 GitHub 上排名第一的开源网页爬虫。您的支持能让它保持独立、创新并对社区免费——同时让您直接获得高级权益。

<div align="">
  
[![成为赞助商](https://img.shields.io/badge/成为赞助商-pink?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/unclecode)  
[![当前赞助商](https://img.shields.io/github/sponsors/unclecode?style=for-the-badge&logo=github&label=当前赞助商&color=green)](https://github.com/sponsors/unclecode)

</div>

### 🤝 赞助等级

- **🌱 信仰者 ($5/月)** — 加入数据民主化运动
- **🚀 建设者 ($50/月)** — 优先支持 & 优先体验新功能
- **💼 成长团队 ($500/月)** — 双周沟通会 & 优化建议
- **🏢 数据基础设施伙伴 ($2000/月)** — 全方位合作伙伴关系及专项支持
  *可根据需求定制 - 详见 [SPONSORS.md](SPONSORS.md) 获取详情及联系方式*

**为什么提供赞助？**  
没有频率限制的 API。没有厂商锁定。在 Crawl4AI 作者的直接指导下，构建并拥有您自己的数据流水线。

[查看所有等级与权益 →](https://github.com/sponsors/unclecode)


## ✨ 功能特性 

<details>
<summary>📝 <strong>Markdown 生成</strong></summary>

- 🧹 **干净的 Markdown**：生成结构清晰、格式准确的 Markdown。
- 🎯 **精简 Markdown (Fit Markdown)**：基于启发式的过滤，移除噪音和无关部分，方便 AI 处理。
- 🔗 **引用与参考**：将页面链接转换为编号参考列表，并附带清晰的引用。
- 🛠️ **自定义策略**：用户可以根据特定需求定制自己的 Markdown 生成策略。
- 📚 **BM25 算法**：采用基于 BM25 的过滤，用于提取核心信息并移除无关内容。
</details>

<details>
<summary>📊 <strong>结构化数据提取</strong></summary>

- 🤖 **LLM 驱动的提取**：支持所有大模型（开源及商业模型）进行结构化数据提取。
- 🧱 **分块策略**：实现分块机制（基于主题、正则、句子级别），用于针对性内容处理。
- 🌌 **余弦相似度**：根据用户查询查找相关内容块进行语义提取。
- 🔎 **基于 CSS 的提取**：使用 XPath 和 CSS 选择器进行快速、基于模式的数据提取。
- 🔧 **模式定义 (Schema Definition)**：定义自定义模式，从重复模式中提取结构化 JSON。

</details>

<details>
<summary>🌐 <strong>浏览器集成</strong></summary>

- 🖥️ **托管浏览器**：使用用户自有的浏览器并拥有完全控制权，避免机器人检测。
- 🔄 **远程浏览器控制**：连接到 Chrome 开发者工具协议（CDP），进行远程、大规模数据提取。
- 👤 **浏览器配置管理 (Profiler)**：创建并管理持久化配置文件，保存登录状态、Cookie 和设置。
- 🔒 **会话管理**：保留浏览器状态并重用于多步爬取任务。
- 🧩 **代理支持**：无缝连接到带认证的代理，确保护理访问安全性。
- ⚙️ **完整的浏览器控制**：修改请求头、Cookie、User-Agent 等，实现定制化爬取设置。
- 🌍 **多浏览器支持**：兼容 Chromium、Firefox 和 WebKit。
- 📐 **动态视口调整**：根据页面内容自动调整浏览器视口，确保完整渲染并捕获所有元素。

</details>

<details>
<summary>🔎 <strong>爬取与抓取</strong></summary>

- 🖼️ **多媒体支持**：提取图片、音频、视频，以及 `srcset` 和 `picture` 等响应式图片格式。
- 🚀 **动态爬取**：执行 JS 并等待异步或同步加载，用于抓取动态内容。
- 📸 **截图**：在爬取过程中捕获页面截图，用于调试或分析。
- 📂 **原始数据爬取**：直接处理原始 HTML (`raw:`) 或本地文件 (`file://`)。
- 🔗 **全方位链接提取**：提取内链、外链以及嵌入的 iframe 内容。
- 🛠️ **可定制钩子 (Hooks)**：在每一步定义钩子以自定义爬取行为（支持字符串和函数式 API）。
- 💾 **缓存机制**：缓存数据以提高速度并避免重复请求。
- 📄 **元数据提取**：从网页中获取结构化元数据。
- 📡 **IFrame 内容提取**：无缝从嵌入的 iframe 内容中提取数据。
- 🕵️ **处理延迟加载 (Lazy Load)**：等待图片完全加载，确保不会遗漏任何延迟加载的内容。
- 🔄 **全页扫描**：模拟滚动以加载并捕获所有动态内容，非常适合无限滚动页面。

</details>

<details>
<summary>🚀 <strong>部署</strong></summary>

- 🐳 **Docker 化设置**：优化的 Docker 镜像，内置 FastAPI 服务器，易于部署。
- 🔑 **安全认证**：内置 JWT 令牌认证，保障 API 安全。
- 🔄 **API 网关**：支持带安全令牌认证的一键部署 API 工作流。
- 🌐 **可扩展架构**：专为大规模生产设计，优化服务器性能。
- ☁️ **云端部署**：为主要云平台提供开箱即用的配置。

</details>

<details>
<summary>🎯 <strong>其他特性</strong></summary>

- 🕶️ **隐身模式**：通过模拟真实用户避开机器人检测。
- 🏷️ **基于标签的内容提取**：基于自定义标签、标题或元数据细化爬取过程。
- 🔗 **链接分析**：提取并分析所有链接，进行详细的数据探索。
- 🛡️ **错误处理**：健全的错误管理，确保执行无间断。
- 🔐 **CORS 与静态服务**：支持基于文件系统的缓存和跨域请求。
- 📖 **清晰的文档**：简化且更新后的指南，涵盖入门及高级用法。
- 🙌 **社区认可**：对贡献者和 Pull Request 进行致谢，保持透明度。

</details>

## 立即体验！

✨ 在此体验 [![在 Colab 运行](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1SgRPrByQLzjRfwoRNq1wSGE9nYY_EE8C?usp=sharing)

✨ 访问我们的 [官方文档网站](https://docs.crawl4ai.com/)

## 安装 🛠️

Crawl4AI 提供灵活的安装选项以适应不同的使用场景。您可以作为 Python 包安装或使用 Docker。

<details>
<summary>🐍 <strong>使用 pip</strong></summary>

选择最适合您需求的安装选项：

### 基础安装

对于基础的网页爬取与抓取任务：

```bash
pip install crawl4ai
crawl4ai-setup # 设置浏览器
```

默认情况下，这将安装 Crawl4AI 的异步版本，并使用 Playwright 进行爬取。

👉 **注意**：安装 Crawl4AI 时，`crawl4ai-setup` 应该会自动安装并设置 Playwright。但是，如果您遇到任何与 Playwright 相关的错误，可以手动使用以下方法之一进行安装：

1. 通过命令行：

   ```bash
   playwright install
   ```

2. 如果上述方法无效，请尝试这个更具体的命令：

   ```bash
   python -m playwright install chromium
   ```

在某些情况下，第二种方法被证明更为可靠。

---

### 同步版本安装

同步版本已弃用，并将在未来版本中移除。如果您需要使用 Selenium 的同步版本：

```bash
pip install crawl4ai[sync]
```

---

### 开发版安装

对于计划修改源代码的贡献者：

```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .                    # 以可编辑模式进行基础安装
```

安装可选功能：

```bash
pip install -e ".[torch]"           # 包含 PyTorch 功能
pip install -e ".[transformer]"     # 包含 Transformer 功能
pip install -e ".[cosine]"          # 包含余弦相似度功能
pip install -e ".[sync]"            # 包含同步爬取 (Selenium)
pip install -e ".[all]"             # 安装所有可选功能
```

</details>

<details>
<summary>🐳 <strong>Docker 部署</strong></summary>

> 🚀 **现已推出！** 我们完全重新设计的 Docker 实现上线了！这一新方案让部署比以往任何时候都更高效、更无缝。

### Docker 新特性

新的 Docker 实现包括：
- **实时监控仪表盘**：具备实时系统指标和浏览器池可见性。
- **浏览器池化**：支持页面预热，响应时间更快。
- **交互式游乐场**：测试并生成请求代码。
- **MCP 集成**：直接连接到 Claude Code 等 AI 工具。
- **全面的 API 端点**：包括 HTML 提取、截图、PDF 生成和 JavaScript 执行。
- **多架构支持**：自动检测（AMD64/ARM64）。
- **资源优化**：改进了内存管理。

### 开始使用

```bash
# 拉取并运行最新版本
docker pull unclecode/crawl4ai:latest
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g unclecode/crawl4ai:latest

# 访问监控仪表盘：http://localhost:11235/dashboard
# 或访问游乐场：http://localhost:11235/playground
```

### 快速测试

运行快速测试（对两种 Docker 选项均有效）：

```python
import requests

# 提交一个爬取任务
response = requests.post(
    "http://localhost:11235/crawl",
    json={"urls": ["https://example.com"], "priority": 10}
)
if response.status_code == 200:
    print("爬取任务提交成功。")
    
if "results" in response.json():
    results = response.json()["results"]
    print("爬取任务完成。结果：")
    for result in results:
        print(result)
else:
    task_id = response.json()["task_id"]
    print(f"爬取任务已提交。任务 ID：{task_id}")
    result = requests.get(f"http://localhost:11235/task/{task_id}")
```

更多示例请参见我们的 [Docker 示例](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_example.py)。有关高级配置、监控功能和生产环境部署，请参见我们的 [自托管指南](https://docs.crawl4ai.com/core/self-hosting/)。

</details>

---

## 🔬 高级用法示例 🔬

您可以在 [docs/examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples) 目录中查看项目结构。在那里您可以找到各种示例；这里分享了一些热门示例。

<details>
<summary>📝 <strong>基于启发式的 Markdown 生成（干净且精简）</strong></summary>

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    browser_config = BrowserConfig(
        headless=True,  
        verbose=True,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0)
        ),
        # markdown_generator=DefaultMarkdownGenerator(
        #     content_filter=BM25ContentFilter(user_query="在此输入用户查询以聚焦内容", bm25_threshold=1.0)
        # ),
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://docs.micronaut.io/4.9.9/guide/",
            config=run_config
        )
        print(len(result.markdown.raw_markdown))
        print(len(result.markdown.fit_markdown))

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>🖥️ <strong>执行 JavaScript 并提取结构化数据（无需 LLM）</strong></summary>

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
import json

async def main():
    schema = {
    "name": "KidoCode 课程",
    "baseSelector": "section.charge-methodology .w-tab-content > div",
    "fields": [
        {
            "name": "section_title",
            "selector": "h3.heading-50",
            "type": "text",
        },
        {
            "name": "section_description",
            "selector": ".charge-content",
            "type": "text",
        },
        {
            "name": "course_name",
            "selector": ".text-block-93",
            "type": "text",
        },
        {
            "name": "course_description",
            "selector": ".course-content-text",
            "type": "text",
        },
        {
            "name": "course_icon",
            "selector": ".image-92",
            "type": "attribute",
            "attribute": "src"
        }
    ]
}

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    browser_config = BrowserConfig(
        headless=False,
        verbose=True
    )
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        js_code=["""(async () => {const tabs = document.querySelectorAll("section.charge-methodology .tabs-menu-3 > div");for(let tab of tabs) {tab.scrollIntoView();tab.click();await new Promise(r => setTimeout(r, 500));}})();"""],
        cache_mode=CacheMode.BYPASS
    )
        
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/technology",
            config=run_config
        )

        companies = json.loads(result.extracted_content)
        print(f"成功提取了 {len(companies)} 个公司信息")
        print(json.dumps(companies[0], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>📚 <strong>使用 LLM 提取结构化数据</strong></summary>

```python
import os
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import LLMExtractionStrategy
from pydantic import BaseModel, Field

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="OpenAI 模型名称")
    input_fee: str = Field(..., description="OpenAI 模型的输入 Token 费用")
    output_fee: str = Field(..., description="OpenAI 模型的输出 Token 费用")

async def main():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategy(
            # 这里可以使用 Litellm 库支持的任何供应商，例如：ollama/qwen2
            # provider="ollama/qwen2", api_token="no-token", 
            llm_config = LLMConfig(provider="openai/gpt-4o", api_token=os.getenv('OPENAI_API_KEY')), 
            schema=OpenAIModelFee.schema(),
            extraction_type="schema",
            instruction="""从爬取的内容中，提取所有提到的模型名称及其输入和输出 Token 费用。
            不要遗漏整个内容中的任何模型。一个提取出的模型 JSON 格式应如下：
            {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}。"""
        ),            
        cache_mode=CacheMode.BYPASS,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='https://openai.com/api/pricing/',
            config=run_config
        )
        print(result.extracted_content)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>🤖 <strong>使用自带的浏览器和自定义用户配置文件</strong></summary>

```python
import os, sys
from pathlib import Path
import asyncio, time
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def test_news_crawl():
    # 创建持久化的用户数据目录
    user_data_dir = os.path.join(Path.home(), ".crawl4ai", "browser_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    browser_config = BrowserConfig(
        verbose=True,
        headless=True,
        user_data_dir=user_data_dir,
        use_persistent_context=True,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        url = "在此输入具有挑战性的网站地址"
        
        result = await crawler.arun(
            url,
            config=run_config,
            magic=True,
        )
        
        print(f"成功爬取了 {url}")
        print(f"内容长度：{len(result.markdown)}")
```

</details>

---

> **💡 提示：** 某些网站可能会使用 **CAPTCHA（验证码）** 验证机制来防止自动访问。如果您的工作流遇到此类挑战，您可以选择集成第三方验证码处理服务，例如 <strong>[CapSolver](https://www.capsolver.com/blog/Partners/crawl4ai-capsolver/?utm_source=crawl4ai&utm_medium=github_pr&utm_campaign=crawl4ai_integration)</strong>。他们支持 reCAPTCHA v2/v3、Cloudflare Turnstile、Challenge、AWS WAF 等。请确保您的使用符合目标网站的服务条款及相关法律。

## ✨ 最近更新

<details open>
<summary><strong>版本 0.8.0 发布亮点 - 崩溃恢复与预取模式</strong></summary>

此版本引入了针对深度爬取的崩溃恢复功能、用于快速 URL 发现的新预取模式，以及针对 Docker 部署的关键安全修复。

- **🔄 深度爬取崩溃恢复**：
  - `on_state_change` 回调在每个 URL 爬取后触发，实现实时状态持久化。
  - `resume_state` 参数支持从保存的检查点继续。
  - JSON 序列化状态，方便存入 Redis/数据库。
  - 适用于 BFS、DFS 和 Best-First 策略。
  ```python
  from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

  strategy = BFSDeepCrawlStrategy(
      max_depth=3,
      resume_state=saved_state,  # 从检查点继续
      on_state_change=save_to_redis,  # 每个 URL 爬取后调用
  )
  ```

- **⚡ 快速 URL 发现的预取模式**：
  - `prefetch=True` 跳过 Markdown、提取和媒体处理。
  - 比完整处理快 5-10 倍。
  - 非常适合两阶段爬取：先发现，后选择性处理。
  ```python
  config = CrawlerRunConfig(prefetch=True)
  result = await crawler.arun("https://example.com", config=config)
  # 仅返回 HTML 和链接 - 不生成 markdown
  ```

- **🔒 安全修复 (Docker API)**：
  - 默认禁用 Hook (`CRAWL4AI_HOOKS_ENABLED=false`)。
  - API 端点屏蔽 `file://` URL 以防止 LFI（本地文件包含）攻击。
  - 从 Hook 执行沙箱中移除了 `__import__`。

[查看 v0.8.0 完整发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.8.0.md)

</details>

<details>
<summary><strong>版本 0.7.8 发布亮点 - 稳定性与 Bug 修复版本</strong></summary>

此版本专注于稳定性，修复了社区报告的 11 个 Bug。没有新功能，但显著提升了可靠性。

- **🐳 Docker API 修复**：
  - 修复了深度爬取请求中 `ContentRelevanceFilter` 的反序列化问题 (#1642)。
  - 修复了 `BrowserConfig.to_dict()` 中 `ProxyConfig` 的 JSON 序列化问题 (#1629)。
  - 修复了 Docker 镜像中 `.cache` 文件夹的权限问题 (#1638)。

- **🤖 LLM 提取改进**：
  - 通过新的 `LLMConfig` 参数支持可配置的速率限制退避 (#1269)：
    ```python
    from crawl4ai import LLMConfig

    config = LLMConfig(
        provider="openai/gpt-4o-mini",
        backoff_base_delay=5,           # 第一次重试等待 5秒
        backoff_max_attempts=5,          # 最多尝试 5 次
        backoff_exponential_factor=3     # 每次尝试延迟翻 3 倍
    )
    ```
  - `LLMExtractionStrategy` 现支持 HTML 输入格式 (#1178)：
    ```python
    from crawl4ai import LLMExtractionStrategy

    strategy = LLMExtractionStrategy(
        llm_config=config,
        instruction="提取表格数据",
        input_format="html"  # 现支持："html", "markdown", "fit_markdown"
    )
    ```
  - 修复了原始 HTML URL 变量 - 提取策略现在接收 `"Raw HTML"` 而非 HTML 块 (#1116)。

- **🔗 URL 处理**：
  - 修复了 JavaScript 重定向后的相对 URL 解析 (#1268)。
  - 修复了提取代码中 import 语句的格式 (#1181)。

- **📦 依赖更新**：
  - 使用 pypdf 替换了已弃用的 PyPDF2 (#1412)。
  - Pydantic v2 ConfigDict 兼容性 - 不再有弃用警告 (#678)。

- **🧠 AdaptiveCrawler**：
  - 修复了查询扩展，使其真正使用 LLM 而非硬编码的模拟数据 (#1621)。

[查看 v0.7.8 完整发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.8.md)

</details>

<details>
<summary><strong>版本 0.7.7 发布亮点 - 自托管与监控更新</strong></summary>

- **📊 实时监控仪表盘**：具有实时系统指标和浏览器池可见性的交互式 Web UI。
  ```python
  # 访问监控仪表盘
  # 访问：http://localhost:11235/dashboard

  # 实时指标包括：
  # - 系统健康状况 (CPU, 内存, 网络, 运行时间)
  # - 活动中及已完成的请求跟踪
  # - 浏览器池管理 (permanent/hot/cold)
  # - Janitor 清理事件
  # - 带完整上下文的错误监控
  ```

- **🔌 全面的监控 API**：完整的 REST API，用于程序化访问所有监控数据。
  ```python
  import httpx

  async with httpx.AsyncClient() as client:
      # 系统健康
      health = await client.get("http://localhost:11235/monitor/health")

      # 请求跟踪
      requests = await client.get("http://localhost:11235/monitor/requests")

      # 浏览器池状态
      browsers = await client.get("http://localhost:11235/monitor/browsers")

      # 端点统计
      stats = await client.get("http://localhost:11235/monitor/endpoints/stats")
  ```

- **⚡ WebSocket 流式传输**：每 2 秒实时更新，用于自定义仪表盘。
- **🔥 智能浏览器池**：具有自动晋升和清理功能的 3 层架构（永久/热/冷）。
- **🧹 Janitor 系统**：具有事件记录功能的自动资源管理。
- **🎮 控制操作**：通过 API 手动管理浏览器（杀掉、重启、清理）。
- **📈 生产指标**：集成 Prometheus 的 6 个关键运维指标。
- **🐛 关键 Bug 修复**：
  - 修复了异步 LLM 提取阻塞问题 (#1055)。
  - 增强了 DFS 深度爬取策略 (#1607)。
  - 修复了 AsyncUrlSeeder 中的站点地图解析 (#1598)。
  - 解决了浏览器视口配置问题 (#1495)。
  - 修复了带指数退避的 CDP 计时问题 (#1528)。
  - pyOpenSSL 安全更新 (>=25.3.0)。

[查看 v0.7.7 完整发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.7.md)

</details>

<details>
<summary><strong>版本 0.7.5 发布亮点 - Docker Hooks 与安全更新</strong></summary>

- **🔧 Docker Hooks 系统**：通过用户提供的 Python 函数在 8 个关键点实现完整的流程定制。
- **✨ 基于函数的 Hooks API (新)**：以普通 Python 函数形式编写 Hook，具备完整的 IDE 支持：
  ```python
  from crawl4ai import hooks_to_string
  from crawl4ai.docker_client import Crawl4aiDockerClient

  # 将 Hook 定义为普通的 Python 函数
  async def on_page_context_created(page, context, **kwargs):
      """屏蔽图片以加快爬取速度"""
      await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
      await page.set_viewport_size({"width": 1920, "height": 1080})
      return page

  async def before_goto(page, context, url, **kwargs):
      """添加自定义请求头"""
      await page.set_extra_http_headers({'X-Crawl4AI': 'v0.7.5'})
      return page

  # 选项 1：对 REST API 使用 hooks_to_string() 工具
  hooks_code = hooks_to_string({
      "on_page_context_created": on_page_context_created,
      "before_goto": before_goto
  })

  # 选项 2：使用具备自动转换功能的 Docker 客户端 (推荐)
  client = Crawl4aiDockerClient(base_url="http://localhost:11235")
  results = await client.crawl(
      urls=["https://httpbin.org/html"],
      hooks={
          "on_page_context_created": on_page_context_created,
          "before_goto": before_goto
      }
  )
  # ✓ 完整的 IDE 支持、类型检查和可重用性！
  ```

- **🤖 增强的 LLM 集成**：支持带温度控制和 base_url 配置的自定义供应商。
- **🔒 HTTPS 保留**：通过 `preserve_https_for_internal_links=True` 确保护理内部链接的安全性。
- **🐍 支持 Python 3.10+**：利用现代语言特性并提升性能。
- **🛠️ Bug 修复**：解决了社区报告的多个问题，包括 URL 处理、JWT 认证和代理配置。

[查看 v0.7.5 完整发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.5.md)

</details>

<details>
<summary><strong>版本 0.7.4 发布亮点 - 智能表格提取与性能更新</strong></summary>

- **🚀 LLMTableExtraction**：革命性的表格提取，具备针对超大表格的智能分块功能：
  ```python
  from crawl4ai import LLMTableExtraction, LLMConfig
  
  # 配置智能表格提取
  table_strategy = LLMTableExtraction(
      llm_config=LLMConfig(provider="openai/gpt-4.1-mini"),
      enable_chunking=True,           # 处理超大表格
      chunk_token_threshold=5000,     # 智能分块阈值
      overlap_threshold=100,          # 保持块间上下文
      extraction_type="structured"    # 获取结构化数据输出
  )
  
  config = CrawlerRunConfig(table_extraction_strategy=table_strategy)
  result = await crawler.arun("https://complex-tables-site.com", config=config)
  
  # 表格会自动分块、处理并合并
  for table in result.tables:
      print(f"提取的表格：{len(table['data'])} 行")
  ```

- **⚡ 调度器 Bug 修复**：修复了 arun_many 中快速完成任务的顺序处理瓶颈。
- **🧹 内存管理重构**：将内存工具整合到主 utils 模块中，架构更清晰。
- **🔧 浏览器管理器修复**：通过线程安全锁解决了并发创建页面时的竞争条件。
- **🔗 高级 URL 处理**：更好地处理 raw:// URL 和 base 标签链接解析。
- **🛡️ 增强的代理支持**：灵活的代理配置，同时支持字典和字符串格式。

[查看 v0.7.4 完整发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.4.md)

</details>

<details>
<summary><strong>版本 0.7.3 发布亮点 - 多配置智能更新</strong></summary>

- **🕵️ 支持 Undetected 浏览器**：绕过复杂的机器人检测系统：
  ```python
  from crawl4ai import AsyncWebCrawler, BrowserConfig
  
  browser_config = BrowserConfig(
      browser_type="undetected",  # 使用 undetected Chrome
      headless=True,              # 可以在静默模式下运行
      extra_args=[
          "--disable-blink-features=AutomationControlled",
          "--disable-web-security"
      ]
  )
  
  async with AsyncWebCrawler(config=browser_config) as crawler:
      result = await crawler.arun("https://protected-site.com")
  # 成功绕过 Cloudflare, Akamai 及自定义机器人检测
  ```

- **🎨 多 URL 配置**：在一批任务中对不同的 URL 模式使用不同的策略：
  ```python
  from crawl4ai import CrawlerRunConfig, MatchMode
  
  configs = [
      # 文档站点 - 激进缓存
      CrawlerRunConfig(
          url_matcher=["*docs*", "*documentation*"],
          cache_mode="write",
          markdown_generator_options={"include_links": True}
      ),
      
      # 新闻/博客站点 - 获取新鲜内容
      CrawlerRunConfig(
          url_matcher=lambda url: 'blog' in url or 'news' in url,
          cache_mode="bypass"
      ),
      
      # 其他所有站点的后备方案
      CrawlerRunConfig()
  ]
  
  results = await crawler.arun_many(urls, config=configs)
  # 每个 URL 自动获得最匹配的配置
  ```

- **🧠 内存监控**：在爬取过程中跟踪并优化内存使用：
  ```python
  from crawl4ai.memory_utils import MemoryMonitor
  
  monitor = MemoryMonitor()
  monitor.start_monitoring()
  
  results = await crawler.arun_many(large_url_list)
  
  report = monitor.get_report()
  print(f"峰值内存：{report['peak_mb']:.1f} MB")
  print(f"效率：{report['efficiency']:.1f}%")
  # 获取优化建议
  ```

- **📊 增强的表格提取**：支持从网页表格直接转换为 DataFrame：
  ```python
  result = await crawler.arun("https://site-with-tables.com")
  
  # 新方式 - 直接访问表格
  if result.tables:
      import pandas as pd
      for table in result.tables:
          df = pd.DataFrame(table['data'])
          print(f"表格：{df.shape[0]} 行 × {df.shape[1]} 列")
  ```

- **💰 GitHub Sponsors**：为了项目的可持续发展，推出了 4 级赞助体系。
- **🐳 Docker LLM 灵活性**：通过环境变量配置供应商。

[查看 v0.7.3 完整发布日志 →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.3.md)

</details>

<details>
<summary><strong>版本 0.7.0 发布亮点 - 自适应智能更新</strong></summary>

- **🧠 自适应爬取**：您的爬虫现在可以自动学习并适应网站模式：
  ```python
  config = AdaptiveConfig(
      confidence_threshold=0.7, # 停止爬取的最小置信度
      max_depth=5, # 最大爬取深度
      max_pages=20, # 最大爬取页数
      strategy="statistical"
  )
  
  async with AsyncWebCrawler() as crawler:
      adaptive_crawler = AdaptiveCrawler(crawler, config)
      state = await adaptive_crawler.digest(
          start_url="https://news.example.com",
          query="最新新闻内容"
      )
  # 爬虫会学习模式并随时间不断改进提取效果
  ```

- **🌊 支持虚拟滚动**：从无限滚动页面中完整提取内容：
  ```python
  scroll_config = VirtualScrollConfig(
      container_selector="[data-testid='feed']",
      scroll_count=20,
      scroll_by="container_height",
      wait_after_scroll=1.0
  )
  
  result = await crawler.arun(url, config=CrawlerRunConfig(
      virtual_scroll_config=scroll_config
  ))
  ```

- **🔗 智能链接分析**：具备智能链接优先级的 3 层评分系统：
  ```python
  link_config = LinkPreviewConfig(
      query="机器学习教程",
      score_threshold=0.3,
      concurrent_requests=10
  )
  
  result = await crawler.arun(url, config=CrawlerRunConfig(
      link_preview_config=link_config,
      score_links=True
  ))
  # 链接按相关性和质量排序
  ```

- **🎣 Async URL Seeder**：在几秒钟内发现数千个 URL：
  ```python
  seeder = AsyncUrlSeeder(SeedingConfig(
      source="sitemap+cc",
      pattern="*/blog/*",
      query="python 教程",
      score_threshold=0.4
  ))
  
  urls = await seeder.discover("https://example.com")
  ```

- **⚡ 性能提升**：通过优化的资源处理和内存效率，速度提升高达 3 倍。

在我们的 [0.7.0 发布日志](https://docs.crawl4ai.com/blog/release-v0.7.0) 中阅读详细信息，或查看 [CHANGELOG](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)。

</details>

## Crawl4AI 中的版本命名

Crawl4AI 遵循标准的 Python 版本命名约定 (PEP 440)，以帮助用户了解每个版本的稳定性和功能。

<details>
<summary>📈 <strong>版本号详解</strong></summary>

我们的版本号遵循此模式：`主版本号.次版本号.修订号` (例如：0.4.3)

#### 预发布版本
我们使用不同的后缀来指示开发阶段：

- `dev` (0.4.3dev1)：开发版本，不稳定。
- `a` (0.4.3a1)：Alpha 版本，包含实验性功能。
- `b` (0.4.3b1)：Beta 版本，功能完整但需要测试。
- `rc` (0.4.3)：发布候选版本，潜在的最终版本。

#### 安装方式
- 常规安装（稳定版）：
  ```bash
  pip install -U crawl4ai
  ```

- 安装预发布版本：
  ```bash
  pip install crawl4ai --pre
  ```

- 安装特定版本：
  ```bash
  pip install crawl4ai==0.4.3b1
  ```

#### 为什么使用预发布版本？
我们使用预发布版本来：
- 在真实场景中测试新功能。
- 在正式发布前收集反馈。
- 为生产环境用户确保护理稳定性。
- 允许早期采用者尝试新功能。

对于生产环境，我们建议使用稳定版本。对于测试新功能，您可以使用 `--pre` 标志选择加入预发布版本。

</details>

## 📖 文档与路线图 

> 🚨 **文档更新警报**：我们下周将进行重大的文档大修，以反映最近的更新和改进。敬请期待更全面、更新的指南！

有关当前文档，包括安装指南、高级功能和 API 参考，请访问我们的 [官方文档网站](https://docs.crawl4ai.com/)。

要查看我们的开发计划和即将推出的功能，请访问我们的 [路线图 (Roadmap)](https://github.com/unclecode/crawl4ai/blob/main/ROADMAP.md)。

<details>
<summary>📈 <strong>开发待办事项 (TODOs)</strong></summary>

- [x] 0. 图爬虫：使用图搜索算法进行智能网站遍历，实现全面的嵌套页面提取。
- [x] 1. 基于问题的爬虫：自然语言驱动的网页发现与内容提取。
- [x] 2. 知识最优爬虫：在最小化数据提取的同时最大化知识获取的智能爬取。
- [x] 3. Agent 爬虫：用于复杂多步爬取操作的自主系统。
- [x] 4. 自动化模式生成器：将自然语言转换为提取模式（Schemas）。
- [x] 5. 特定领域抓取器：为常见平台（学术、电商）预配置的提取器。
- [x] 6. 网页嵌入索引：爬取内容的语义搜索基础设施。
- [x] 7. 交互式游乐场：用于在 AI 协助下测试、比较策略的 Web UI。
- [x] 8. 性能监控器：爬虫运行状态的实时洞察。
- [ ] 9. 云端集成：跨云服务商的一键部署解决方案。
- [x] 10. 赞助计划：具有分级权益的结构化支持系统。
- [ ] 11. 教育内容：“如何爬取”视频系列和交互式教程。

</details>

## 🤝 参与贡献 

我们欢迎来自开源社区的贡献。请查看我们的 [贡献指南](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTORS.md) 获取更多信息。

## 📄 开源协议与署名

本项目采用 Apache License 2.0 协议，建议通过下方的徽章进行署名。详见 [Apache 2.0 开源协议](https://github.com/unclecode/crawl4ai/blob/main/LICENSE) 文件。

### 署名要求
在使用 Crawl4AI 时，您必须包含以下署名方式之一：

<details>
<summary>📈 <strong>1. 徽章署名 (推荐)</strong></summary>
在您的 README、文档或网站中添加以下徽章之一：

| 主题 | 徽章 |
|-------|-------|
| **迪斯科主题 (动画)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **暗夜主题 (霓虹黑)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-night.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **深色主题 (经典)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-dark.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **浅色主题 (经典)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-light.svg" alt="Powered by Crawl4AI" width="200"/></a> |
 

添加徽章的 HTML 代码：
```html
<!-- 迪斯科主题 (动画) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- 暗夜主题 (霓虹黑) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-night.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- 深色主题 (经典) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-dark.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- 浅色主题 (经典) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-light.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- 简单盾牌徽章 -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://img.shields.io/badge/Powered%20by-Crawl4AI-blue?style=flat-square" alt="Powered by Crawl4AI"/>
</a>
```

</details>

<details>
<summary>📖 <strong>2. 文本署名</strong></summary>
在您的文档中添加此行：
```
本项目使用 Crawl4AI (https://github.com/unclecode/crawl4ai) 进行网页数据提取。
```
</details>

## 📚 引用

如果您在研究或项目中使用 Crawl4AI，请引用：

```bibtex
@software{crawl4ai2024,
  author = {UncleCode},
  title = {Crawl4AI: 开源、对大模型友好的网页爬虫与抓取工具},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub Repository},
  howpublished = {\url{https://github.com/unclecode/crawl4ai}},
  commit = {请使用您正在使用的 commit 哈希值}
}
```

文本引用格式：
```
UncleCode. (2024). Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper [Computer software]. 
GitHub. https://github.com/unclecode/crawl4ai
```

## 📧 联系方式 

如有疑问、建议或反馈，欢迎随时联系：

- GitHub: [unclecode](https://github.com/unclecode)
- Twitter: [@unclecode](https://twitter.com/unclecode)
- 官方网站: [crawl4ai.com](https://crawl4ai.com)

祝爬取愉快！🕸️🚀

## 🗾 愿景与使命

我们的愿景是通过将数字足迹转化为结构化的、可交易的资产，解锁个人和企业数据的价值。Crawl4AI 为个人和组织提供开源工具来提取并结构化数据，培育共享的数据经济。

我们憧憬未来的人工智能是由真实的人类知识驱动的，确保数据创造者直接从他们的贡献中受益。通过使数据民主化并确保护理伦理共享，我们正在为真实可靠的 AI 进步奠定基础。

<details>
<summary>🔑 <strong>关键机遇</strong></summary>
 
- **数据资本化**：将数字足迹转化为可衡量、有价值的资产。
- **真实的 AI 数据**：为 AI 系统提供真实的人类洞察。
- **共享经济**：创建一个惠及数据创造者的公平数据市场。

</details>

<details>
<summary>🚀 <strong>发展路径</strong></summary>

1. **开源工具**：社区驱动的透明数据提取平台。
2. **数字资产结构化**：组织并评估数字知识价值的工具。
3. **伦理数据市场**：一个安全、公平的结构化数据交换平台。

更多详情请参阅我们的 [完整愿景说明](./MISSION.md)。
</details>

## 🌟 当前赞助商

### 🏢 企业赞助商与伙伴

我们的企业赞助商和技术合作伙伴助力 Crawl4AI 扩展至能够驱动生产级的数据流水线。

| 公司 | 简介 | 赞助等级 |
|------|------|----------------------------|
| <a href="https://www.thordata.com/?ls=github&lk=crawl4ai" target="_blank"><img src="https://gist.github.com/aravindkarnam/dfc598a67be5036494475acece7e54cf/raw/thor_data.svg" alt="Thor Data" width="120"/></a>  | 使用 Thordata 确保与任何 AI/ML 工作流及数据基础设施无缝兼容，支持大规模获取网页数据，拥有 99.9% 的正常运行时间，并提供一对一客户支持。 | 🥈 银牌 |
| <a href="https://app.nstproxy.com/register?i=ecOqW9" target="_blank"><picture><source width="250" media="(prefers-color-scheme: dark)" srcset="https://gist.github.com/aravindkarnam/62f82bd4818d3079d9dd3c31df432cf8/raw/nst-light.svg"><source width="250" media="(prefers-color-scheme: light)" srcset="https://www.nstproxy.com/logo.svg"><img alt="nstproxy" src="ttps://www.nstproxy.com/logo.svg"></picture></a>  | NstProxy 是一家值得信赖的代理供应商，拥有超过 1.1 亿真实住宅 IP，支持城市级定位，拥有 99.99% 的正常运行时间，且价格低至 $0.1/GB，提供无与伦比的稳定性、规模及成本效益。 | 🥈 银牌 |
| <a href="https://app.scrapeless.com/passport/register?utm_source=official&utm_term=crawl4ai" target="_blank"><picture><source width="250" media="(prefers-color-scheme: dark)" srcset="https://gist.githubusercontent.com/aravindkarnam/0d275b942705604263e5c32d2db27bc1/raw/Scrapeless-light-logo.svg"><source width="250" media="(prefers-color-scheme: light)" srcset="https://gist.githubusercontent.com/aravindkarnam/22d0525cc0f3021bf19ebf6e11a69ccd/raw/Scrapeless-dark-logo.svg"><img alt="Scrapeless" src="https://gist.githubusercontent.com/aravindkarnam/22d0525cc0f3021bf19ebf6e11a69ccd/raw/Scrapeless-dark-logo.svg"></picture></a>  | Scrapeless 为爬取、自动化及 AI 智能体提供生产级基础设施，提供抓取浏览器、4 种代理类型及通用抓取 API。 | 🥈 银牌 |
| <a href="https://dashboard.capsolver.com/passport/register?inviteCode=ESVSECTX5Q23" target="_blank"><picture><source width="120" media="(prefers-color-scheme: dark)" srcset="https://docs.crawl4ai.com/uploads/sponsors/20251013045338_72a71fa4ee4d2f40.png"><source width="120" media="(prefers-color-scheme: light)" srcset="https://www.capsolver.com/assets/images/logo-text.png"><img alt="Capsolver" src="https://www.capsolver.com/assets/images/logo-text.png"></picture></a> | AI 驱动的验证码处理服务。支持所有主流验证码类型，包括 reCAPTCHA、Cloudflare 等。 | 🥉 铜牌 |
| <a href="https://kipo.ai" target="_blank"><img src="https://docs.crawl4ai.com/uploads/sponsors/20251013045751_2d54f57f117c651e.png" alt="DataSync" width="120"/></a> | 帮助工程师和买家在几秒钟内查找、比较并采购电子及工业零件，提供规格、价格、提前期及替代方案。| 🥇 金牌 |
| <a href="https://www.kidocode.com/" target="_blank"><img src="https://docs.crawl4ai.com/uploads/sponsors/20251013045045_bb8dace3f0440d65.svg" alt="Kidocode" width="120"/><p align="center">KidoCode</p></a> | Kidocode 是一所面向 5-18 岁青少年的混合技术与创业学校，提供在线及线下校区教育。 | 🥇 金牌 |
| <a href="https://www.alephnull.sg/" target="_blank"><img src="https://docs.crawl4ai.com/uploads/sponsors/20251013050323_a9e8e8c4c3650421.svg" alt="Aleph null" width="120"/></a> | 总部位于新加坡的 Aleph Null 是亚洲领先的教育技术中心，致力于以学生为中心、AI 驱动的教育，为学习者提供在快速变化的世界中蓬勃发展的工具。 | 🥇 金牌 |



### 🧑‍🤝 个人赞助商

由衷感谢我们的个人支持者！每一次贡献都帮助我们的开源使命保持活力并不断发展！

<p align="left">
  <a href="https://github.com/hafezparast"><img src="https://avatars.githubusercontent.com/u/14273305?s=60&v=4" style="border-radius:50%;" width="64px;"/></a>
  <a href="https://github.com/ntohidi"><img src="https://avatars.githubusercontent.com/u/17140097?s=60&v=4" style="border-radius:50%;"width="64px;"/></a>
  <a href="https://github.com/Sjoeborg"><img src="https://avatars.githubusercontent.com/u/17451310?s=60&v=4" style="border-radius:50%;"width="64px;"/></a>
  <a href="https://github.com/romek-rozen"><img src="https://avatars.githubusercontent.com/u/30595969?s=60&v=4" style="border-radius:50%;"width="64px;"/></a>
  <a href="https://github.com/Kourosh-Kiyani"><img src="https://avatars.githubusercontent.com/u/34105600?s=60&v=4" style="border-radius:50%;"width="64px;"/></a>
  <a href="https://github.com/Etherdrake"><img src="https://avatars.githubusercontent.com/u/67021215?s=60&v=4" style="border-radius:50%;"width="64px;"/></a>
  <a href="https://github.com/shaman247"><img src="https://avatars.githubusercontent.com/u/211010067?s=60&v=4" style="border-radius:50%;"width="64px;"/></a>
  <a href="https://github.com/work-flow-manager"><img src="https://avatars.githubusercontent.com/u/217665461?s=60&v=4" style="border-radius:50%;"width="64px;"/></a>
</p>

> 想加入他们吗？[赞助 Crawl4AI →](https://github.com/sponsors/unclecode)

## 星标历史 (Star History)

[![Star History Chart](https://api.star-history.com/svg?repos=unclecode/crawl4ai&type=Date)](https://star-history.com/#unclecode/crawl4ai&Date)
