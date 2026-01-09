# Claude Code Provider

Use your Claude Code CLI subscription for LLM-powered web extraction without managing API keys.

## Overview

The Claude Code provider enables Crawl4AI users with Claude Code subscriptions to leverage their existing authentication for LLM extraction:

- **No API Keys Required**: Uses local Claude Code CLI authentication
- **Familiar Models**: Access Claude Sonnet, Opus, and Haiku models
- **Seamless Integration**: Works with all existing `LLMExtractionStrategy` features

## Prerequisites

1. **Claude Code CLI** installed and authenticated:
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude login
   ```

2. **Crawl4AI with claude-code extra**:
   ```bash
   pip install crawl4ai[claude-code]
   ```

## Quick Start

```python
import asyncio
from crawl4ai import AsyncWebCrawler, LLMConfig, CrawlerRunConfig
from crawl4ai import LLMExtractionStrategy

async def main():
    # No API token needed - uses local Claude Code authentication
    llm_config = LLMConfig(provider="claude-code/claude-sonnet-4-20250514")

    strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        instruction="Extract article titles and summaries as JSON"
    )

    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        print(result.extracted_content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Supported Models

| Model ID | Description | Use Case |
|----------|-------------|----------|
| `claude-code/claude-haiku-3-5-latest` | Fastest, most economical | Quick extractions, high volume |
| `claude-code/claude-sonnet-4-20250514` | Balanced performance | **Recommended default** |
| `claude-code/claude-opus-4-20250514` | Most capable | Complex reasoning tasks |

## Configuration

The Claude Code provider works with standard `LLMConfig`:

```python
llm_config = LLMConfig(
    provider="claude-code/claude-sonnet-4-20250514"
    # api_token is optional (uses "no-token-needed" internally)
)
```

## Examples

### Schema-Based Extraction

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: str
    rating: float

strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="claude-code/claude-sonnet-4-20250514"),
    schema=Product.model_json_schema(),
    extraction_type="schema",
    instruction="Extract all products"
)
```

### With Chunking for Large Pages

```python
strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="claude-code/claude-sonnet-4-20250514"),
    instruction="Extract all article summaries",
    chunk_token_threshold=2000,
    overlap_rate=0.1,
    apply_chunking=True
)
```

### Verbose Mode with Model Logging

```python
strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="claude-code/claude-sonnet-4-20250514"),
    instruction="Extract main content",
    verbose=True  # Logs which provider/model is being used
)
```

Output:
```
[LOG] LLM Provider: claude-code | Model: claude-sonnet-4-20250514
[LOG] Call LLM for https://example.com - block index: 0
```

## Comparison with API Providers

| Feature | Claude Code | Anthropic API |
|---------|-------------|---------------|
| Authentication | Local CLI | API Key |
| Billing | Subscription | Per-token |
| Setup | CLI login once | Environment variable |

## Docker Deployment

When running Crawl4AI in Docker, mount your Claude Code credentials:

```bash
docker run -d \
  -p 11235:11235 \
  -v /path/to/.claude:/home/appuser/.claude:rw \
  crawl4ai-claude:latest
```

Set the provider via environment variable:

```bash
-e LLM_PROVIDER=claude-code/claude-sonnet-4-20250514
```

## Troubleshooting

### "claude-agent-sdk is not installed"

```bash
pip install crawl4ai[claude-code]
```

### "Failed to connect to Claude Code service"

```bash
claude --version  # Check installation
claude login      # Re-authenticate
```

### Empty Responses

Verify CLI works: `claude "Hello"`

### Permission Denied (Docker)

Ensure the credentials directory is readable by the container user (uid 999):

```bash
sudo chown -R 999:999 /path/to/.claude
```

## See Also

- [LLM Extraction Strategies](./llm-strategies.md)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code/)
