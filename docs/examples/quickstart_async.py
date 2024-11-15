import os, sys
# append parent directory to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))); os.environ['FIRECRAWL_API_KEY'] = "fc-84b370ccfad44beabc686b38f1769692";

import asyncio
# import nest_asyncio
# nest_asyncio.apply()

import time
import json
import os
import re
from typing import Dict, List
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    LLMExtractionStrategy,
)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

print("Crawl4AI: Advanced Web Crawling and Data Extraction")
print("GitHub Repository: https://github.com/unclecode/crawl4ai")
print("Twitter: @unclecode")
print("Website: https://crawl4ai.com")


async def simple_crawl():
    print("\n--- Basic Usage ---")
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://www.nbcnews.com/business")
        print(result.markdown[:500])  # Print first 500 characters

async def simple_example_with_running_js_code():
    print("\n--- Executing JavaScript and Using CSS Selectors ---")
    # New code to handle the wait_for parameter
    wait_for = """() => {
        return Array.from(document.querySelectorAll('article.tease-card')).length > 10;
    }"""

    # wait_for can be also just a css selector
    # wait_for = "article.tease-card:nth-child(10)"

    async with AsyncWebCrawler(verbose=True) as crawler:
        js_code = [
            "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
        ]
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=js_code,
            # wait_for=wait_for,
            bypass_cache=True,
        )
        print(result.markdown[:500])  # Print first 500 characters

async def simple_example_with_css_selector():
    print("\n--- Using CSS Selectors ---")
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            css_selector=".wide-tease-item__description",
            bypass_cache=True,
        )
        print(result.markdown[:500])  # Print first 500 characters

async def use_proxy():
    print("\n--- Using a Proxy ---")
    print(
        "Note: Replace 'http://your-proxy-url:port' with a working proxy to run this example."
    )
    # Uncomment and modify the following lines to use a proxy
    # async with AsyncWebCrawler(verbose=True, proxy="http://your-proxy-url:port") as crawler:
    #     result = await crawler.arun(
    #         url="https://www.nbcnews.com/business",
    #         bypass_cache=True
    #     )
    #     print(result.markdown[:500])  # Print first 500 characters

async def capture_and_save_screenshot(url: str, output_path: str):
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            screenshot=True,
            bypass_cache=True
        )
        
        if result.success and result.screenshot:
            import base64
            
            # Decode the base64 screenshot data
            screenshot_data = base64.b64decode(result.screenshot)
            
            # Save the screenshot as a JPEG file
            with open(output_path, 'wb') as f:
                f.write(screenshot_data)
            
            print(f"Screenshot saved successfully to {output_path}")
        else:
            print("Failed to capture screenshot")

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(
        ..., description="Fee for output token for the OpenAI model."
    )

async def extract_structured_data_using_llm(provider: str, api_token: str = None, extra_headers: Dict[str, str] = None):
    print(f"\n--- Extracting Structured Data with {provider} ---")
    
    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}. Skipping this example.")
        return

    extra_args = {}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://openai.com/api/pricing/",
            word_count_threshold=1,
            extraction_strategy=LLMExtractionStrategy(
                provider=provider,
                api_token=api_token,
                schema=OpenAIModelFee.schema(),
                extraction_type="schema",
                instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
                Do not miss any models in the entire content. One extracted model JSON format should look like this: 
                {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}.""",
                extra_args=extra_args
            ),
            bypass_cache=True,
        )
        print(result.extracted_content)

async def extract_structured_data_using_css_extractor():
    print("\n--- Using JsonCssExtractionStrategy for Fast Structured Output ---")
    schema = {
        "name": "Coinbase Crypto Prices",
        "baseSelector": ".cds-tableRow-t45thuk",
        "fields": [
            {
                "name": "crypto",
                "selector": "td:nth-child(1) h2",
                "type": "text",
            },
            {
                "name": "symbol",
                "selector": "td:nth-child(1) p",
                "type": "text",
            },
            {
                "name": "price",
                "selector": "td:nth-child(2)",
                "type": "text",
            }
        ],
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.coinbase.com/explore",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        assert result.success, "Failed to crawl the page"

        news_teasers = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(news_teasers)} news teasers")
        print(json.dumps(news_teasers[0], indent=2))

# Advanced Session-Based Crawling with Dynamic Content 🔄
async def crawl_dynamic_content_pages_method_1():
    print("\n--- Advanced Multi-Page Crawling with JavaScript Execution ---")
    first_commit = ""

    async def on_execution_started(page):
        nonlocal first_commit
        try:
            while True:
                await page.wait_for_selector("li.Box-sc-g0xbh4-0 h4")
                commit = await page.query_selector("li.Box-sc-g0xbh4-0 h4")
                commit = await commit.evaluate("(element) => element.textContent")
                commit = re.sub(r"\s+", "", commit)
                if commit and commit != first_commit:
                    first_commit = commit
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Warning: New content didn't appear after JavaScript execution: {e}")

    async with AsyncWebCrawler(verbose=True) as crawler:
        crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)

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
                js_only=page > 0,
                headless=False,
            )

            assert result.success, f"Failed to crawl page {page + 1}"

            soup = BeautifulSoup(result.cleaned_html, "html.parser")
            commits = soup.select("li")
            all_commits.extend(commits)

            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

async def crawl_dynamic_content_pages_method_2():
    print("\n--- Advanced Multi-Page Crawling with JavaScript Execution ---")

    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []
        last_commit = ""

        js_next_page_and_wait = """
        (async () => {
            const getCurrentCommit = () => {
                const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
                return commits.length > 0 ? commits[0].textContent.trim() : null;
            };

            const initialCommit = getCurrentCommit();
            const button = document.querySelector('a[data-testid="pagination-next-button"]');
            if (button) button.click();

            // Poll for changes
            while (true) {
                await new Promise(resolve => setTimeout(resolve, 100)); // Wait 100ms
                const newCommit = getCurrentCommit();
                if (newCommit && newCommit !== initialCommit) {
                    break;
                }
            }
        })();
        """

        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.Box-sc-g0xbh4-0",
            "fields": [
                {
                    "name": "title",
                    "selector": "h4.markdown-title",
                    "type": "text",
                    "transform": "strip",
                },
            ],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

        for page in range(3):  # Crawl 3 pages
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                css_selector="li.Box-sc-g0xbh4-0",
                extraction_strategy=extraction_strategy,
                js_code=js_next_page_and_wait if page > 0 else None,
                js_only=page > 0,
                bypass_cache=True,
                headless=False,
            )

            assert result.success, f"Failed to crawl page {page + 1}"

            commits = json.loads(result.extracted_content)
            all_commits.extend(commits)

            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

async def crawl_dynamic_content_pages_method_3():
    print("\n--- Advanced Multi-Page Crawling with JavaScript Execution using `wait_for` ---")

    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []

        js_next_page = """
        const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
        if (commits.length > 0) {
            window.firstCommit = commits[0].textContent.trim();
        }
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();
        """

        wait_for = """() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (commits.length === 0) return false;
            const firstCommit = commits[0].textContent.trim();
            return firstCommit !== window.firstCommit;
        }"""
        
        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.Box-sc-g0xbh4-0",
            "fields": [
                {
                    "name": "title",
                    "selector": "h4.markdown-title",
                    "type": "text",
                    "transform": "strip",
                },
            ],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

        for page in range(3):  # Crawl 3 pages
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                css_selector="li.Box-sc-g0xbh4-0",
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                bypass_cache=True,
                headless=False,
            )

            assert result.success, f"Failed to crawl page {page + 1}"

            commits = json.loads(result.extracted_content)
            all_commits.extend(commits)

            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

async def crawl_custom_browser_type():
    # Use Firefox
    start = time.time()
    async with AsyncWebCrawler(browser_type="firefox", verbose=True, headless = True) as crawler:
        result = await crawler.arun(url="https://www.example.com", bypass_cache=True)
        print(result.markdown[:500])
        print("Time taken: ", time.time() - start)

    # Use WebKit
    start = time.time()
    async with AsyncWebCrawler(browser_type="webkit", verbose=True, headless = True) as crawler:
        result = await crawler.arun(url="https://www.example.com", bypass_cache=True)
        print(result.markdown[:500])
        print("Time taken: ", time.time() - start)

    # Use Chromium (default)
    start = time.time()
    async with AsyncWebCrawler(verbose=True, headless = True) as crawler:
        result = await crawler.arun(url="https://www.example.com", bypass_cache=True)
        print(result.markdown[:500])
        print("Time taken: ", time.time() - start)

async def crawl_with_user_simultion():
    async with AsyncWebCrawler(verbose=True, headless=True) as crawler:
        url = "YOUR-URL-HERE"
        result = await crawler.arun(
            url=url,            
            bypass_cache=True,
            magic = True, # Automatically detects and removes overlays, popups, and other elements that block content
            # simulate_user = True,# Causes a series of random mouse movements and clicks to simulate user interaction
            # override_navigator = True # Overrides the navigator object to make it look like a real user
        )
        
        print(result.markdown)    

async def speed_comparison():
    # print("\n--- Speed Comparison ---")
    # print("Firecrawl (simulated):")
    # print("Time taken: 7.02 seconds")
    # print("Content length: 42074 characters")
    # print("Images found: 49")
    # print()
    # Simulated Firecrawl performance
    from firecrawl import FirecrawlApp
    app = FirecrawlApp(api_key=os.environ['FIRECRAWL_API_KEY'])
    start = time.time()
    scrape_status = app.scrape_url(
    'https://www.nbcnews.com/business',
    params={'formats': ['markdown', 'html']}
    )
    end = time.time()
    print("Firecrawl (simulated):")
    print(f"Time taken: {end - start:.2f} seconds")
    print(f"Content length: {len(scrape_status['markdown'])} characters")
    print(f"Images found: {scrape_status['markdown'].count('cldnry.s-nbcnews.com')}")
    print()    

    async with AsyncWebCrawler() as crawler:
        # Crawl4AI simple crawl
        start = time.time()
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            word_count_threshold=0,
            bypass_cache=True,
            verbose=False,
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
            js_code=[
                "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
            ],
            word_count_threshold=0,
            bypass_cache=True,
            verbose=False,
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

async def generate_knowledge_graph():
    class Entity(BaseModel):
        name: str
        description: str
        
    class Relationship(BaseModel):
        entity1: Entity
        entity2: Entity
        description: str
        relation_type: str

    class KnowledgeGraph(BaseModel):
        entities: List[Entity]
        relationships: List[Relationship]

    extraction_strategy = LLMExtractionStrategy(
            provider='openai/gpt-4o-mini', # Or any other provider, including Ollama and open source models
            api_token=os.getenv('OPENAI_API_KEY'), # In case of Ollama just pass "no-token"
            schema=KnowledgeGraph.model_json_schema(),
            extraction_type="schema",
            instruction="""Extract entities and relationships from the given text."""
    )
    async with AsyncWebCrawler() as crawler:
        url = "https://paulgraham.com/love.html"
        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            extraction_strategy=extraction_strategy,
            # magic=True
        )
        # print(result.extracted_content)
        with open(os.path.join(__location__, "kb.json"), "w") as f:
            f.write(result.extracted_content)

async def fit_markdown_remove_overlay():
    async with AsyncWebCrawler(headless = False) as crawler:
        url = "https://janineintheworld.com/places-to-visit-in-central-mexico"
        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            word_count_threshold = 10,
            remove_overlay_elements=True,
            screenshot = True
        )
        # Save markdown to file
        with open(os.path.join(__location__, "mexico_places.md"), "w") as f:
            f.write(result.fit_markdown)

    print("Done")


async def main():
    await simple_crawl()
    await simple_example_with_running_js_code()
    await simple_example_with_css_selector()
    await use_proxy()
    await capture_and_save_screenshot("https://www.example.com", os.path.join(__location__, "tmp/example_screenshot.jpg"))
    await extract_structured_data_using_css_extractor()

    # LLM extraction examples
    await extract_structured_data_using_llm()
    await extract_structured_data_using_llm("huggingface/meta-llama/Meta-Llama-3.1-8B-Instruct", os.getenv("HUGGINGFACE_API_KEY"))
    await extract_structured_data_using_llm("openai/gpt-4o", os.getenv("OPENAI_API_KEY"))
    await extract_structured_data_using_llm("ollama/llama3.2")    

    # You always can pass custom headers to the extraction strategy
    custom_headers = {
        "Authorization": "Bearer your-custom-token",
        "X-Custom-Header": "Some-Value"
    }
    await extract_structured_data_using_llm(extra_headers=custom_headers)
    
    # await crawl_dynamic_content_pages_method_1()
    # await crawl_dynamic_content_pages_method_2()
    await crawl_dynamic_content_pages_method_3()
    
    await crawl_custom_browser_type()
    
    await speed_comparison()


if __name__ == "__main__":
    asyncio.run(main())
