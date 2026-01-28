"""
Example: Using Claude Code Provider for LLM Extraction

Demonstrates using your Claude Code CLI subscription for web content extraction
with Crawl4AI.

Prerequisites:
    - Claude Code CLI installed and authenticated (run `claude` in terminal)
    - pip install crawl4ai[claude-code]

Usage:
    python examples/claude_code_extraction.py
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import LLMConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy


async def basic_extraction():
    """Basic example: Extract article titles from Hacker News."""
    print("=" * 60)
    print("Example 1: Basic Extraction with Claude Code")
    print("=" * 60)

    # Configure Claude Code provider (no API token needed - uses local auth)
    llm_config = LLMConfig(
        provider="claude-code/claude-sonnet-4-20250514"  # Recommended model
    )

    strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        instruction="Extract all article titles and their point counts as a JSON array"
    )

    run_config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=run_config
        )

        if result.success:
            print("\nExtracted Content:")
            print(result.extracted_content[:500])  # First 500 chars
        else:
            print(f"\nExtraction failed: {result.error_message}")


async def model_comparison():
    """Compare different Claude models."""
    print("\n" + "=" * 60)
    print("Example 2: Model Comparison")
    print("=" * 60)

    models = [
        ("claude-code/claude-haiku-3-5-latest", "Haiku (fastest, cheapest)"),
        ("claude-code/claude-sonnet-4-20250514", "Sonnet (balanced)"),
        # Uncomment to test Opus (slowest, most capable):
        # ("claude-code/claude-opus-4-20250514", "Opus (most capable)"),
    ]

    html = "<html><body><h1>Product: Widget Pro</h1><p>Price: $99.99</p><p>Rating: 4.5 stars</p></body></html>"

    for provider, description in models:
        print(f"\nTesting {description}...")

        llm_config = LLMConfig(provider=provider)
        strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            instruction="Extract product name, price, and rating as JSON"
        )

        result = await strategy.aextract(
            url="https://example.com",
            ix=0,
            html=html
        )

        print(f"  Result: {result}")


async def structured_extraction():
    """Extract structured data with a schema."""
    print("\n" + "=" * 60)
    print("Example 3: Structured Extraction with Schema")
    print("=" * 60)

    llm_config = LLMConfig(
        provider="claude-code/claude-sonnet-4-20250514"
    )

    # Define expected schema
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"},
                "date": {"type": "string"}
            }
        }
    }

    strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        instruction="Extract all blog posts with their titles, authors, and dates",
        schema=schema,
        extraction_type="schema"
    )

    html = """
    <html>
    <body>
        <article>
            <h2>First Post</h2>
            <span class="author">John Doe</span>
            <time>2024-01-15</time>
        </article>
        <article>
            <h2>Second Post</h2>
            <span class="author">Jane Smith</span>
            <time>2024-01-16</time>
        </article>
    </body>
    </html>
    """

    result = await strategy.aextract(
        url="https://example.com",
        ix=0,
        html=html
    )

    print(f"\nExtracted Posts:")
    print(result)


async def main():
    """Run all examples."""
    print("\nClaude Code Provider Examples for Crawl4AI")
    print("=" * 60)
    print("Using your Claude Code subscription for LLM extraction")
    print("No API keys required - uses local Claude Code authentication")
    print("=" * 60)

    try:
        await basic_extraction()
        await model_comparison()
        await structured_extraction()
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nMake sure to install the claude-code extras:")
        print("  pip install crawl4ai[claude-code]")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Claude Code CLI is installed and authenticated:")
        print("  1. Install: npm install -g @anthropic-ai/claude-code")
        print("  2. Authenticate: claude login")


if __name__ == "__main__":
    asyncio.run(main())
