import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://docs.crawl4ai.com/")
        
        if result.success:
            markdown = result.markdown or ""
            if "<.>" in markdown or "<#>" in markdown:
                print("Bug reproduced: Relative URLs are incorrectly formatted with brackets (e.g., <.>).")
            else:
                print("Fixed: No malformed relative URL brackets found in markdown.")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
    