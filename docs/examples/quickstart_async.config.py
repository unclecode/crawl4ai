import os, sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import asyncio
import time
import json
import re
from typing import Dict
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CacheMode, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    LLMExtractionStrategy,
)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

print("Crawl4AI: Advanced Web Crawling and Data Extraction")
print("GitHub Repository: https://github.com/unclecode/crawl4ai")
print("Twitter: @unclecode")
print("Website: https://crawl4ai.com")


# Basic Example - Simple Crawl
async def simple_crawl():
    print("\n--- Basic Usage ---")
    browser_config = BrowserConfig(headless=True)
    crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business", config=crawler_config
        )
        print(result.markdown[:500])


async def clean_content():
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        excluded_tags=["nav", "footer", "aside"],
        remove_overlay_elements=True,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48, threshold_type="fixed", min_word_threshold=0
            ),
            options={"ignore_links": True},
        ),
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/Apple",
            config=crawler_config,
        )
        full_markdown_length = len(result.markdown_v2.raw_markdown)
        fit_markdown_length = len(result.markdown_v2.fit_markdown)
        print(f"Full Markdown Length: {full_markdown_length}")
        print(f"Fit Markdown Length: {fit_markdown_length}")


async def link_analysis():
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        exclude_external_links=True,
        exclude_social_media_links=True,
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            config=crawler_config,
        )
        print(f"Found {len(result.links['internal'])} internal links")
        print(f"Found {len(result.links['external'])} external links")

        for link in result.links["internal"][:5]:
            print(f"Href: {link['href']}\nText: {link['text']}\n")


# JavaScript Execution Example
async def simple_example_with_running_js_code():
    print("\n--- Executing JavaScript and Using CSS Selectors ---")

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code="const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();",
        # wait_for="() => { return Array.from(document.querySelectorAll('article.tease-card')).length > 10; }"
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business", config=crawler_config
        )
        print(result.markdown[:500])


# CSS Selector Example
async def simple_example_with_css_selector():
    print("\n--- Using CSS Selectors ---")
    browser_config = BrowserConfig(headless=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, css_selector=".wide-tease-item__description"
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business", config=crawler_config
        )
        print(result.markdown[:500])


async def media_handling():
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, exclude_external_images=True, screenshot=True
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business", config=crawler_config
        )
        for img in result.media["images"][:5]:
            print(f"Image URL: {img['src']}, Alt: {img['alt']}, Score: {img['score']}")


async def custom_hook_workflow(verbose=True):
    async with AsyncWebCrawler() as crawler:
        # Set a 'before_goto' hook to run custom code just before navigation
        crawler.crawler_strategy.set_hook(
            "before_goto",
            lambda page, context: print("[Hook] Preparing to navigate..."),
        )

        # Perform the crawl operation
        result = await crawler.arun(url="https://crawl4ai.com")
        print(result.markdown_v2.raw_markdown[:500].replace("\n", " -- "))


# Proxy Example
async def use_proxy():
    print("\n--- Using a Proxy ---")
    browser_config = BrowserConfig(
        headless=True,
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "username",
            "password": "password",
        },
    )
    crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business", config=crawler_config
        )
        if result.success:
            print(result.markdown[:500])


# Screenshot Example
async def capture_and_save_screenshot(url: str, output_path: str):
    browser_config = BrowserConfig(headless=True)
    crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, screenshot=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result.success and result.screenshot:
            import base64

            screenshot_data = base64.b64decode(result.screenshot)
            with open(output_path, "wb") as f:
                f.write(screenshot_data)
            print(f"Screenshot saved successfully to {output_path}")
        else:
            print("Failed to capture screenshot")


# LLM Extraction Example
class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(
        ..., description="Fee for output token for the OpenAI model."
    )


async def extract_structured_data_using_llm(
    provider: str, api_token: str = None, extra_headers: Dict[str, str] = None
):
    print(f"\n--- Extracting Structured Data with {provider} ---")

    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}. Skipping this example.")
        return

    browser_config = BrowserConfig(headless=True)

    extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=1,
        page_timeout=80000,
        extraction_strategy=LLMExtractionStrategy(
            provider=provider,
            api_token=api_token,
            schema=OpenAIModelFee.model_json_schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
            Do not miss any models in the entire content.""",
            extra_args=extra_args,
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://openai.com/api/pricing/", config=crawler_config
        )
        print(result.extracted_content)


# CSS Extraction Example
async def extract_structured_data_using_css_extractor():
    print("\n--- Using JsonCssExtractionStrategy for Fast Structured Output ---")
    schema = {
        "name": "KidoCode Courses",
        "baseSelector": "section.charge-methodology .framework-collection-item.w-dyn-item",
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
                "attribute": "src",
            },
        ],
    }

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    js_click_tabs = """
    (async () => {
        const tabs = document.querySelectorAll("section.charge-methodology .tabs-menu-3 > div");
        for(let tab of tabs) {
            tab.scrollIntoView();
            tab.click();
            await new Promise(r => setTimeout(r, 500));
        }
    })();
    """

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        js_code=[js_click_tabs],
        delay_before_return_html=1
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/technology", config=crawler_config
        )

        companies = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(companies)} companies")
        print(json.dumps(companies[0], indent=2))


# Dynamic Content Examples - Method 1
async def crawl_dynamic_content_pages_method_1():
    print("\n--- Advanced Multi-Page Crawling with JavaScript Execution ---")
    first_commit = ""

    async def on_execution_started(page, **kwargs):
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

    browser_config = BrowserConfig(headless=False, java_script_enabled=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)

        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []

        js_next_page = """
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();
        """

        for page in range(3):
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                css_selector="li.Box-sc-g0xbh4-0",
                js_code=js_next_page if page > 0 else None,
                js_only=page > 0,
                session_id=session_id,
            )

            result = await crawler.arun(url=url, config=crawler_config)
            assert result.success, f"Failed to crawl page {page + 1}"

            soup = BeautifulSoup(result.cleaned_html, "html.parser")
            commits = soup.select("li")
            all_commits.extend(commits)

            print(f"Page {page + 1}: Found {len(commits)} commits")

        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")


# Dynamic Content Examples - Method 2
async def crawl_dynamic_content_pages_method_2():
    print("\n--- Advanced Multi-Page Crawling with JavaScript Execution ---")

    browser_config = BrowserConfig(headless=False, java_script_enabled=True)

    js_next_page_and_wait = """
    (async () => {
        const getCurrentCommit = () => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            return commits.length > 0 ? commits[0].textContent.trim() : null;
        };

        const initialCommit = getCurrentCommit();
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();

        while (true) {
            await new Promise(resolve => setTimeout(resolve, 100));
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

    async with AsyncWebCrawler(config=browser_config) as crawler:
        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []

        extraction_strategy = JsonCssExtractionStrategy(schema)

        for page in range(3):
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                css_selector="li.Box-sc-g0xbh4-0",
                extraction_strategy=extraction_strategy,
                js_code=js_next_page_and_wait if page > 0 else None,
                js_only=page > 0,
                session_id=session_id,
            )

            result = await crawler.arun(url=url, config=crawler_config)
            assert result.success, f"Failed to crawl page {page + 1}"

            commits = json.loads(result.extracted_content)
            all_commits.extend(commits)
            print(f"Page {page + 1}: Found {len(commits)} commits")

        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")


async def cosine_similarity_extraction():
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=CosineStrategy(
            word_count_threshold=10,
            max_dist=0.2,  # Maximum distance between two words
            linkage_method="ward",  # Linkage method for hierarchical clustering (ward, complete, average, single)
            top_k=3,  # Number of top keywords to extract
            sim_threshold=0.3,  # Similarity threshold for clustering
            semantic_filter="McDonald's economic impact, American consumer trends",  # Keywords to filter the content semantically using embeddings
            verbose=True,
        ),
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business/consumer/how-mcdonalds-e-coli-crisis-inflation-politics-reflect-american-story-rcna177156",
            config=crawl_config,
        )
        print(json.loads(result.extracted_content)[:5])


# Browser Comparison
async def crawl_custom_browser_type():
    print("\n--- Browser Comparison ---")

    # Firefox
    browser_config_firefox = BrowserConfig(browser_type="firefox", headless=True)
    start = time.time()
    async with AsyncWebCrawler(config=browser_config_firefox) as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        print("Firefox:", time.time() - start)
        print(result.markdown[:500])

    # WebKit
    browser_config_webkit = BrowserConfig(browser_type="webkit", headless=True)
    start = time.time()
    async with AsyncWebCrawler(config=browser_config_webkit) as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        print("WebKit:", time.time() - start)
        print(result.markdown[:500])

    # Chromium (default)
    browser_config_chromium = BrowserConfig(browser_type="chromium", headless=True)
    start = time.time()
    async with AsyncWebCrawler(config=browser_config_chromium) as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        print("Chromium:", time.time() - start)
        print(result.markdown[:500])


# Anti-Bot and User Simulation
async def crawl_with_user_simulation():
    browser_config = BrowserConfig(
        headless=True,
        user_agent_mode="random",
        user_agent_generator_config={"device_type": "mobile", "os_type": "android"},
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        magic=True,
        simulate_user=True,
        override_navigator=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="YOUR-URL-HERE", config=crawler_config)
        print(result.markdown)


async def ssl_certification():
    # Configure crawler to fetch SSL certificate
    config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS,  # Bypass cache to always get fresh certificates
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)

        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate

            # 1. Access certificate properties directly
            print("\nCertificate Information:")
            print(f"Issuer: {cert.issuer.get('CN', '')}")
            print(f"Valid until: {cert.valid_until}")
            print(f"Fingerprint: {cert.fingerprint}")

            # 2. Export certificate in different formats
            cert.to_json(os.path.join(tmp_dir, "certificate.json"))  # For analysis
            print("\nCertificate exported to:")
            print(f"- JSON: {os.path.join(tmp_dir, 'certificate.json')}")

            pem_data = cert.to_pem(
                os.path.join(tmp_dir, "certificate.pem")
            )  # For web servers
            print(f"- PEM: {os.path.join(tmp_dir, 'certificate.pem')}")

            der_data = cert.to_der(
                os.path.join(tmp_dir, "certificate.der")
            )  # For Java apps
            print(f"- DER: {os.path.join(tmp_dir, 'certificate.der')}")


# Speed Comparison
async def speed_comparison():
    print("\n--- Speed Comparison ---")

    # Firecrawl comparison
    from firecrawl import FirecrawlApp

    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
    start = time.time()
    scrape_status = app.scrape_url(
        "https://www.nbcnews.com/business", params={"formats": ["markdown", "html"]}
    )
    end = time.time()
    print("Firecrawl:")
    print(f"Time taken: {end - start:.2f} seconds")
    print(f"Content length: {len(scrape_status['markdown'])} characters")
    print(f"Images found: {scrape_status['markdown'].count('cldnry.s-nbcnews.com')}")
    print()

    # Crawl4AI comparisons
    browser_config = BrowserConfig(headless=True)

    # Simple crawl
    async with AsyncWebCrawler(config=browser_config) as crawler:
        start = time.time()
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS, word_count_threshold=0
            ),
        )
        end = time.time()
        print("Crawl4AI (simple crawl):")
        print(f"Time taken: {end - start:.2f} seconds")
        print(f"Content length: {len(result.markdown)} characters")
        print(f"Images found: {result.markdown.count('cldnry.s-nbcnews.com')}")
        print()

        # Advanced filtering
        start = time.time()
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=0,
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter(
                        threshold=0.48, threshold_type="fixed", min_word_threshold=0
                    )
                ),
            ),
        )
        end = time.time()
        print("Crawl4AI (Markdown Plus):")
        print(f"Time taken: {end - start:.2f} seconds")
        print(f"Content length: {len(result.markdown_v2.raw_markdown)} characters")
        print(f"Fit Markdown: {len(result.markdown_v2.fit_markdown)} characters")
        print(f"Images found: {result.markdown.count('cldnry.s-nbcnews.com')}")
        print()


# Main execution
async def main():
    # Basic examples
    await simple_crawl()
    await simple_example_with_running_js_code()
    await simple_example_with_css_selector()

    # Advanced examples
    await extract_structured_data_using_css_extractor()
    await extract_structured_data_using_llm(
        "openai/gpt-4o", os.getenv("OPENAI_API_KEY")
    )
    await crawl_dynamic_content_pages_method_1()
    await crawl_dynamic_content_pages_method_2()

    # Browser comparisons
    await crawl_custom_browser_type()

    # Screenshot example
    await capture_and_save_screenshot(
        "https://www.example.com",
        os.path.join(__location__, "tmp/example_screenshot.jpg")
    )


if __name__ == "__main__":
    asyncio.run(main())
