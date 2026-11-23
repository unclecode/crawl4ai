import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        # Target a page explicitly known for HTML tables
        result = await crawler.arun(url="https://www.w3schools.com/html/html_tables.asp")
        
        if result.success:
            if "<table" not in result.cleaned_html.lower():
                print("Bug reproduced: <table> tags are stripped from cleaned_html.")
            else:
                print("Fixed: Tables are preserved in cleaned_html.")
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
    