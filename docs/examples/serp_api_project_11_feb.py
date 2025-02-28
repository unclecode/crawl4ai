import asyncio
import json
from typing import Any, Dict, List, Optional

from regex import P
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMExtractionStrategy,
    JsonCssExtractionStrategy,
    CrawlerHub,
    CrawlResult,
    DefaultMarkdownGenerator,
    PruningContentFilter,
)
from pathlib import Path
from pydantic import BaseModel

__current_dir = Path(__file__).parent

# Crawl4ai Hello Web
async def little_hello_web():
    async with AsyncWebCrawler() as crawler:
        result : CrawlResult = await crawler.arun(
            url="https://www.helloworld.org"
        )
        print(result.markdown.raw_markdown[:500])

async def hello_web():
    browser_config = BrowserConfig(headless=True, verbose=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48, threshold_type="fixed", min_word_threshold=0
                )
            ),        
        )
        result : CrawlResult = await crawler.arun(
            url="https://www.helloworld.org", config=crawler_config
        )
        print(result.markdown.fit_markdown[:500])

# Naive Approach Using Large Language Models
async def extract_using_llm():
    print("Extracting using Large Language Models")

    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler = AsyncWebCrawler(config=browser_config) 

    await crawler.start()
    try:
        class Sitelink(BaseModel):
            title: str
            link: str

        class GoogleSearchResult(BaseModel):
            title: str
            link: str
            snippet: str
            sitelinks: Optional[List[Sitelink]] = None        

        llm_extraction_strategy = LLMExtractionStrategy(
            provider = "openai/gpt-4o",
            schema = GoogleSearchResult.model_json_schema(),
            instruction="""I want to extract the title, link, snippet, and sitelinks from a Google search result. I shared here the content of div#search from the search result page. We are just interested in organic search results.
            Example: 
            {
                "title": "Google",
                "link": "https://www.google.com",
                "snippet": "Google is a search engine.",
                "sitelinks": [
                    {
                        "title": "Gmail",
                        "link": "https://mail.google.com"
                    },
                    {
                        "title": "Google Drive",
                        "link": "https://drive.google.com"
                    }
                ]
            }""",
            # apply_chunking=False,
            chunk_token_threshold=2 ** 12, # 2^12 = 4096
            verbose=True,
            # input_format="html", # html, markdown, cleaned_html
            input_format="cleaned_html"
        )


        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            keep_attrs=["id", "class"],
            keep_data_attributes=True,
            delay_before_return_html=2,
            extraction_strategy=llm_extraction_strategy,
            css_selector="div#search",
        )

        result : CrawlResult = await crawler.arun(
            url="https://www.google.com/search?q=apple%20inc&start=0&num=10",
            config=crawl_config,
        )
    
        search_result = {}
        if result.success:
            search_result = json.loads(result.extracted_content)

            # save search result to file
            with open(__current_dir / "search_result_using_llm.json", "w") as f:
                f.write(json.dumps(search_result, indent=4))
            print(json.dumps(search_result, indent=4)) 

    finally:
        await crawler.close()

# Example of using CrawlerHub
async def schema_generator():
    print("Generating schema")
    html = ""

    # Load html from file
    with open(__current_dir / "google_search_item.html", "r") as f:
        html = f.read()
    
    organic_schema = JsonCssExtractionStrategy.generate_schema(
            html=html,
            target_json_example="""{
                "title": "...",
                "link": "...",
                "snippet": "...",
                "date": "1 hour ago",
                "sitelinks": [
                    {
                        "title": "...",
                        "link": "..."
                    }
                ]
            }""",
            query="""The given HTML is the crawled HTML from the Google search result, which refers to one HTML element representing one organic Google search result. Please find the schema for the organic search item based on the given HTML. I am interested in the title, link, snippet text, sitelinks, and date.""",
        )
    
    print(json.dumps(organic_schema, indent=4))    
    pass

# Golden Standard
async def build_schema(html:str, force: bool = False) -> Dict[str, Any]:
    print("Building schema")
    schemas = {}
    if (__current_dir / "organic_schema.json").exists() and not force:
        with open(__current_dir / "organic_schema.json", "r") as f:
            schemas["organic"] = json.loads(f.read())
    else:        
        # Extract schema from html
        organic_schema = JsonCssExtractionStrategy.generate_schema(
            html=html,
            target_json_example="""{
                "title": "...",
                "link": "...",
                "snippet": "...",
                "date": "1 hour ago",
                "sitelinks": [
                    {
                        "title": "...",
                        "link": "..."
                    }
                ]
            }""",
            query="""The given html is the crawled html from Google search result. Please find the schema for organic search item in the given html, I am interested in title, link, snippet text, sitelinks and date. Usually they are all inside a div#search.""",
        )

        # Save schema to file current_dir/organic_schema.json
        with open(__current_dir / "organic_schema.json", "w") as f:
            f.write(json.dumps(organic_schema, indent=4))
        
        schemas["organic"] = organic_schema    

    # Repeat the same for top_stories_schema
    if (__current_dir / "top_stories_schema.json").exists():
        with open(__current_dir / "top_stories_schema.json", "r") as f:
            schemas["top_stories"] = json.loads(f.read())
    else:
        top_stories_schema = JsonCssExtractionStrategy.generate_schema(
            html=html,
            target_json_example="""{
            "title": "...",
            "link": "...",
            "source": "Insider Monkey",
            "date": "1 hour ago",
        }""",
            query="""The given HTML is the crawled HTML from the Google search result. Please find the schema for the Top Stories item in the given HTML. I am interested in the title, link, source, and date.""",
        )

        with open(__current_dir / "top_stories_schema.json", "w") as f:
            f.write(json.dumps(top_stories_schema, indent=4))
        
        schemas["top_stories"] = top_stories_schema

    # Repeat the same for suggested_queries_schema
    if (__current_dir / "suggested_queries_schema.json").exists():
        with open(__current_dir / "suggested_queries_schema.json", "r") as f:
            schemas["suggested_queries"] = json.loads(f.read())
    else:
        suggested_queries_schema = JsonCssExtractionStrategy.generate_schema(
            html=html,
            target_json_example="""{
            "query": "A for Apple",
        }""",
            query="""The given HTML contains the crawled HTML from Google search results. Please find the schema for each suggested query in the section "relatedSearches" at the bottom of the page. I am interested in the queries only.""",
        )

        with open(__current_dir / "suggested_queries_schema.json", "w") as f:
            f.write(json.dumps(suggested_queries_schema, indent=4))
        
        schemas["suggested_queries"] = suggested_queries_schema
    
    return schemas

async def search(q: str = "apple inc") -> Dict[str, Any]:
    print("Searching for:", q)

    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler = AsyncWebCrawler(config=browser_config)
    search_result: Dict[str, List[Dict[str, Any]]] = {} 

    await crawler.start()
    try:
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            keep_attrs=["id", "class"],
            keep_data_attributes=True,
            delay_before_return_html=2,
        )
        from urllib.parse import quote
        result: CrawlResult = await crawler.arun(
            f"https://www.google.com/search?q={quote(q)}&start=0&num=10",
            config=crawl_config
        )

        if result.success:
            schemas : Dict[str, Any] = await build_schema(result.html)

            for schema in schemas.values():
                schema_key = schema["name"].lower().replace(' ', '_')
                search_result[schema_key] = JsonCssExtractionStrategy(
                    schema=schema
                ).run(
                    url="",
                    sections=[result.html],
                )

            # save search result to file
            with open(__current_dir / "search_result.json", "w") as f:
                f.write(json.dumps(search_result, indent=4))
            print(json.dumps(search_result, indent=4))        

    finally:
        await crawler.close()

    return search_result

# Example of using CrawlerHub
async def hub_example(query: str = "apple inc"):
    print("Using CrawlerHub")
    crawler_cls = CrawlerHub.get("google_search")
    crawler = crawler_cls()

    # Text search
    text_results = await crawler.run(
        query=query,
        search_type="text",  
        schema_cache_path="/Users/unclecode/.crawl4ai"
    )
    # Save search result to file
    with open(__current_dir / "search_result_using_hub.json", "w") as f:
        f.write(json.dumps(json.loads(text_results), indent=4))

    print(json.dumps(json.loads(text_results), indent=4))


async def demo():
    # Step 1: Introduction & Overview 
    # await little_hello_web()
    # await hello_web()

    # Step 2: Demo end result, using hub
    # await hub_example()

    # Step 3: Using LLm for extraction
    # await extract_using_llm()

    # Step 4: GEt familiar with schema generation
    # await schema_generator()

    # Step 5: Golden Standard
    # await search()

    # Step 6: Introduction to CrawlerHub
    await hub_example()

if __name__ == "__main__":
    asyncio.run(demo())
