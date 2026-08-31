from crawl4ai.llmtxt import AsyncLLMTextManager  # Changed to AsyncLLMTextManager
from crawl4ai.async_logger import AsyncLogger
from pathlib import Path
import asyncio


async def main():
    current_file = Path(__file__).resolve()
    # base_dir = current_file.parent.parent / "local/_docs/llm.txt/test_docs"
    base_dir = current_file.parent.parent / "local/_docs/llm.txt"
    docs_dir = base_dir

    # Create directory if it doesn't exist
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Initialize logger
    logger = AsyncLogger()
    # Updated initialization with default batching params
    # manager = AsyncLLMTextManager(docs_dir, logger, max_concurrent_calls=3, batch_size=2)
    manager = AsyncLLMTextManager(docs_dir, logger, batch_size=2)

    # Let's first check what files we have
    print("\nAvailable files:")
    for f in docs_dir.glob("*.md"):
        print(f"- {f.name}")

    # Generate index files
    print("\nGenerating index files...")
    await manager.generate_index_files(
        force_generate_facts=False, clear_bm25_cache=False
    )

    # Test some relevant queries about Crawl4AI
    test_queries = [
        "How is using the `arun_many` method?",
    ]

    print("\nTesting search functionality:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = manager.search(query, top_k=2)
        print(f"Results length: {len(results)} characters")
        if results:
            print(
                "First 200 chars of results:", results[:200].replace("\n", " "), "..."
            )
        else:
            print("No results found")


if __name__ == "__main__":
    asyncio.run(main())
