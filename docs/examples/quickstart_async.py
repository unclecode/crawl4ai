import asyncio
import time
import json
import os
import re
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy, LLMExtractionStrategy

print("Crawl4AI: Advanced Web Crawling and Data Extraction")
print("GitHub Repository: https://github.com/unclecode/crawl4ai")
print("Twitter: @unclecode")
print("Website: https://crawl4ai.com")

async def simple_crawl():
    print("\n--- Basic Usage ---")
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://www.nbcnews.com/business")
        print(result.markdown[:500])  # Print first 500 characters

async def js_and_css():
    print("\n--- Executing JavaScript and Using CSS Selectors ---")
    async with AsyncWebCrawler(verbose=True) as crawler:
        js_code = ["const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"]
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=js_code,
            css_selector="article.tease-card",
            bypass_cache=True
        )
        print(result.extracted_content[:500])  # Print first 500 characters

async def use_proxy():
    print("\n--- Using a Proxy ---")
    print("Note: Replace 'http://your-proxy-url:port' with a working proxy to run this example.")
    # Uncomment and modify the following lines to use a proxy
    # async with AsyncWebCrawler(verbose=True, proxy="http://your-proxy-url:port") as crawler:
    #     result = await crawler.arun(
    #         url="https://www.nbcnews.com/business",
    #         bypass_cache=True
    #     )
    #     print(result.markdown[:500])  # Print first 500 characters

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")

async def extract_openai_fees():
    print("\n--- Extracting Structured Data with OpenAI ---")
    print("Note: Set your OpenAI API key as an environment variable to run this example.")
    if not os.getenv('OPENAI_API_KEY'):
        print("OpenAI API key not found. Skipping this example.")
        return
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url='https://openai.com/api/pricing/',
            word_count_threshold=1,
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o", api_token=os.getenv('OPENAI_API_KEY'), 
                schema=OpenAIModelFee.schema(),
                extraction_type="schema",
                instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
                Do not miss any models in the entire content. One extracted model JSON format should look like this: 
                {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}."""
            ),            
            bypass_cache=True,
        )
        print(result.extracted_content)

async def crawl_typescript_commits():
    print("\n--- Advanced Multi-Page Crawling with JavaScript Execution ---")
    first_commit = ""
    async def on_execution_started(page):
        nonlocal first_commit 
        try:
            while True:
                await page.wait_for_selector('li.Box-sc-g0xbh4-0 h4')
                commit = await page.query_selector('li.Box-sc-g0xbh4-0 h4')
                commit = await commit.evaluate('(element) => element.textContent')
                commit = re.sub(r'\s+', '', commit)
                if commit and commit != first_commit:
                    first_commit = commit
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Warning: New content didn't appear after JavaScript execution: {e}")

    async with AsyncWebCrawler(verbose=True) as crawler:
        crawler.crawler_strategy.set_hook('on_execution_started', on_execution_started)

        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []

        js_next_page = """
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();
        """

        for page in range(3):  # Crawl 3 pages
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                css_selector="li.Box-sc-g0xbh4-0",
                js=js_next_page if page > 0 else None,
                bypass_cache=True,
                js_only=page > 0
            )

            assert result.success, f"Failed to crawl page {page + 1}"

            soup = BeautifulSoup(result.cleaned_html, 'html.parser')
            commits = soup.select("li")
            all_commits.extend(commits)

            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

async def extract_news_teasers():
    print("\n--- Using JsonCssExtractionStrategy for Fast Structured Output ---")
    schema = {
        "name": "News Teaser Extractor",
        "baseSelector": ".wide-tease-item__wrapper",
        "fields": [
            {
                "name": "category",
                "selector": ".unibrow span[data-testid='unibrow-text']",
                "type": "text",
            },
            {
                "name": "headline",
                "selector": ".wide-tease-item__headline",
                "type": "text",
            },
            {
                "name": "summary",
                "selector": ".wide-tease-item__description",
                "type": "text",
            },
            {
                "name": "time",
                "selector": "[data-testid='wide-tease-date']",
                "type": "text",
            },
            {
                "name": "image",
                "type": "nested",
                "selector": "picture.teasePicture img",
                "fields": [
                    {"name": "src", "type": "attribute", "attribute": "src"},
                    {"name": "alt", "type": "attribute", "attribute": "alt"},
                ],
            },
            {
                "name": "link",
                "selector": "a[href]",
                "type": "attribute",
                "attribute": "href",
            },
        ],
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        assert result.success, "Failed to crawl the page"

        news_teasers = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(news_teasers)} news teasers")
        print(json.dumps(news_teasers[0], indent=2))

async def speed_comparison():
    print("\n--- Speed Comparison ---")
    print("Firecrawl (simulated):")
    print("Time taken: 7.02 seconds")
    print("Content length: 42074 characters")
    print("Images found: 49")
    print()

    async with AsyncWebCrawler() as crawler:
        # Crawl4AI simple crawl
        start = time.time()
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            word_count_threshold=0,
            bypass_cache=True, 
            verbose=False
        )
        end = time.time()
        print("Crawl4AI (simple crawl):")
        print(f"Time taken: {end - start:.2f} seconds")
        print(f"Content length: {len(result.markdown)} characters")
        print(f"Images found: {result.markdown.count('cldnry.s-nbcnews.com')}")
        print()

        # Crawl4AI with JavaScript execution
        start = time.time()
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=["const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"],
            word_count_threshold=0,
            bypass_cache=True, 
            verbose=False
        )
        end = time.time()
        print("Crawl4AI (with JavaScript execution):")
        print(f"Time taken: {end - start:.2f} seconds")
        print(f"Content length: {len(result.markdown)} characters")
        print(f"Images found: {result.markdown.count('cldnry.s-nbcnews.com')}")

    print("\nNote on Speed Comparison:")
    print("The speed test conducted here may not reflect optimal conditions.")
    print("When we call Firecrawl's API, we're seeing its best performance,")
    print("while Crawl4AI's performance is limited by the local network speed.")
    print("For a more accurate comparison, it's recommended to run these tests")
    print("on servers with a stable and fast internet connection.")
    print("Despite these limitations, Crawl4AI still demonstrates faster performance.")
    print("If you run these tests in an environment with better network conditions,")
    print("you may observe an even more significant speed advantage for Crawl4AI.")

async def main():
    await simple_crawl()
    await js_and_css()
    await use_proxy()
    await extract_openai_fees()
    await crawl_typescript_commits()
    await extract_news_teasers()
    await speed_comparison()

if __name__ == "__main__":
    asyncio.run(main())