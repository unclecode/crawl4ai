import argparse
import asyncio
import os
import pathlib
import json
import re
import sys

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BFSDeepCrawlStrategy,
    KeywordRelevanceScorer,
    LXMLWebScrapingStrategy,
    LLMConfig
)
from crawl4ai.content_filter_strategy import LLMContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def sanitize_filename(url_or_title: str) -> str:
    """
    Sanitizes a string (URL or page title) to be a valid filename.
    Removes or replaces invalid characters and truncates if too long.
    Returns a default name if sanitization results in an empty string.
    """
    # Replace non-alphanumeric characters (except dots and hyphens) with underscores
    sanitized = re.sub(r'[^\w\.\-]', '_', url_or_title)
    # Remove leading/trailing underscores that might result from replacements
    sanitized = sanitized.strip('_')
    # Truncate to 100 characters
    sanitized = sanitized[:100]
    if not sanitized:
        return "default_scraped_page"
    return sanitized


async def main():
    """
    Main function to handle argument parsing, crawling logic, and output generation.
    """
    parser = argparse.ArgumentParser(description="Prompt-driven web crawler.")

    parser.add_argument("start_url", type=str, help="The initial URL to start crawling.")
    parser.add_argument("user_prompt", type=str, help="User's description of the data they are looking for.")
    parser.add_argument("--output_dir", type=str, default="./crawled_output",
                        help="Directory where output files will be saved (default: ./crawled_output).")
    parser.add_argument("--max_depth", type=int, default=2,
                        help="Maximum crawl depth (default: 2).")

    args = parser.parse_args()

    print("Parsed arguments:")
    print(f"  Start URL: {args.start_url}")
    print(f"  User Prompt: {args.user_prompt}")
    print(f"  Output Directory: {args.output_dir}")
    print(f"  Max Depth: {args.max_depth}")

    # --- Output Directory Setup ---
    output_dir_path = pathlib.Path(args.output_dir)
    markdown_dir_path = output_dir_path / "markdown"
    try:
        markdown_dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Output directory for markdown: {markdown_dir_path.resolve()}")
    except OSError as e:
        print(f"Error creating output directory {markdown_dir_path}: {e}", file=sys.stderr)
        sys.exit(1)

    all_scraped_data = []

    # --- LLM and Crawler Setup ---
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: The OPENAI_API_KEY environment variable is not set. This key is required for LLM processing.", file=sys.stderr)
        sys.exit(1)

    llm_config = LLMConfig(provider="openai/gpt-4o", api_token=api_key)

    # Instantiate LLMContentFilter
    llm_content_filter = LLMContentFilter(
        llm_config=llm_config,
        instruction=args.user_prompt,
        verbose=True
    )

    # Instantiate DefaultMarkdownGenerator
    default_markdown_generator = DefaultMarkdownGenerator(
        content_filter=llm_content_filter
    )

    # Derive keywords from user prompt for URL scoring
    keywords = args.user_prompt.split()
    print(f"  Keywords for URL scoring: {keywords}")

    # Instantiate KeywordRelevanceScorer
    keyword_scorer = KeywordRelevanceScorer(keywords=keywords)

    # Instantiate BFSDeepCrawlStrategy
    bfs_strategy = BFSDeepCrawlStrategy(
        max_depth=args.max_depth,
        include_external=False,
        url_scorer=keyword_scorer
    )

    # Instantiate CrawlerRunConfig
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=bfs_strategy,
        scraping_strategy=LXMLWebScrapingStrategy(), # Using LXML for initial HTML structure
        verbose=True,
        stream=True
    )

    print("\nInitializing crawler...")
    async with AsyncWebCrawler() as crawler:
        print(f"Starting crawl from URL: {args.start_url}")
        results = await crawler.arun(url=args.start_url, config=run_config)

        print("\nProcessing and saving crawled content...")
        async for result in results:
            try:
                if not result.html:
                    print(f"  Skipping URL (no HTML content): {result.url}")
                    continue

                print(f"  Processing: {result.url} (Score: {result.metadata.get('score', 'N/A')})")

                markdown_result = await default_markdown_generator.generate_markdown(
                    input_html=result.html,
                    base_url=result.url,
                    citations=True
                )

                primary_markdown = markdown_result.fit_markdown
                if not primary_markdown or primary_markdown.strip() == "":
                    # Fallback to markdown_with_citations if fit_markdown is empty
                    primary_markdown = markdown_result.markdown_with_citations
                
                if not primary_markdown or primary_markdown.strip() == "":
                    print(f"    Skipping {result.url} due to empty markdown result after LLM processing and fallback.")
                    continue


                filename_base = result.title if result.title else result.url
                sanitized_filename_str = sanitize_filename(filename_base) + ".md"
                markdown_output_path = markdown_dir_path / sanitized_filename_str

                try:
                    with open(markdown_output_path, "w", encoding="utf-8") as f:
                        f.write(primary_markdown)
                    print(f"    Saved markdown to: {markdown_output_path.resolve()}")
                except OSError as e:
                    print(f"    Error saving markdown for {result.url} to {markdown_output_path}: {e}", file=sys.stderr)
                    continue # Skip this page for JSON summary if saving fails

                page_data = {
                    "url": result.url,
                    "prompt": args.user_prompt,
                    "markdown_file_path": str(markdown_output_path.resolve()),
                    "title": result.title if result.title else "N/A",
                    "relevance_score": result.metadata.get("score")
                }
                all_scraped_data.append(page_data)

            except Exception as e:
                print(f"  Error processing page {result.url if result else 'Unknown URL'}: {e}", file=sys.stderr)
                # Optionally, log more details or save error information
                continue # Continue to the next page

    # --- Save JSON Summary ---
    if all_scraped_data:
        json_output_path = output_dir_path / "scraped_data.json"
        try:
            with open(json_output_path, "w", encoding="utf-8") as f:
                json.dump(all_scraped_data, f, indent=4, ensure_ascii=False)
            print(f"\nJSON summary saved to: {json_output_path.resolve()}")
        except OSError as e:
            print(f"\nError saving JSON summary to {json_output_path}: {e}", file=sys.stderr)
    else:
        print("\nNo data successfully scraped, JSON summary not created.")

    print("\nCrawling process finished.")

if __name__ == "__main__":
    asyncio.run(main())
