"""
Example: Robust Error Handling with Claude Code Provider

Demonstrates proper error handling patterns for production applications.
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import LLMConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy


async def extraction_with_retry(url: str, max_retries: int = 3):
    """Extract content with automatic retry on transient failures."""
    from crawl4ai.providers.claude_code_provider import (
        ClaudeCodeError,
        ClaudeCodeConnectionError,
        ClaudeCodeSDKError,
    )

    llm_config = LLMConfig(provider="claude-code/claude-sonnet-4-20250514")
    strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        instruction="Extract the main content as a summary"
    )
    run_config = CrawlerRunConfig(extraction_strategy=strategy)

    for attempt in range(max_retries):
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=run_config)
                if result.success:
                    return result.extracted_content
                else:
                    print(f"Crawl failed: {result.error_message}")

        except ClaudeCodeSDKError as e:
            # SDK not installed - no point retrying
            print(f"SDK Error (no retry): {e}")
            raise

        except ClaudeCodeConnectionError as e:
            # Connection issue - may be transient, worth retrying
            wait_time = 2 ** attempt
            print(f"Connection error (attempt {attempt + 1}/{max_retries}), "
                  f"retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)

        except ClaudeCodeError as e:
            # Other Claude Code errors
            wait_time = 2 ** attempt
            print(f"Claude Code error (attempt {attempt + 1}/{max_retries}), "
                  f"retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)

    raise Exception(f"Max retries ({max_retries}) exceeded")


async def main():
    print("Claude Code Error Handling Example")
    print("=" * 50)

    try:
        result = await extraction_with_retry("https://example.com")
        print(f"\nSuccess! Extracted content:\n{result[:500]}...")
    except Exception as e:
        print(f"\nFailed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
