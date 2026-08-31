from crawl4ai import BrowserConfig, AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.hub import BaseCrawler
from crawl4ai.utils import optimize_html, get_home_folder, preprocess_html_for_schema
from crawl4ai import JsonCssExtractionStrategy
from pathlib import Path
import json
import os
from typing import Dict


class GoogleSearchCrawler(BaseCrawler):
    __meta__ = {
        "version": "1.0.0",
        "tested_on": ["google.com/search*"],
        "rate_limit": "10 RPM",
        "description": "Crawls Google Search results (text + images)",
    }

    def __init__(self):
        super().__init__()
        self.js_script = (Path(__file__).parent /
                          "script.js").read_text()

    async def run(self, url="", query: str = "", search_type: str = "text", schema_cache_path = None, **kwargs) -> str:
        """Crawl Google Search results for a query"""
        url = f"https://www.google.com/search?q={query}&gl=sg&hl=en" if search_type == "text" else f"https://www.google.com/search?q={query}&gl=sg&hl=en&tbs=qdr:d&udm=2"
        if kwargs.get("page_start", 1) > 1:
            url = f"{url}&start={kwargs['page_start'] * 10}"
        if kwargs.get("page_length", 1) > 1:
            url = f"{url}&num={kwargs['page_length']}"
            
        browser_config = BrowserConfig(headless=True, verbose=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                cache_mode=kwargs.get("cache_mode", CacheMode.BYPASS),
                keep_attrs=["id", "class"],
                keep_data_attributes=True,
                delay_before_return_html=kwargs.get(
                    "delay", 2 if search_type == "image" else 1),
                js_code=self.js_script if search_type == "image" else None,
            )

            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return json.dumps({"error": result.error})

            if search_type == "image":
                if result.js_execution_result.get("success", False) is False:
                    return json.dumps({"error": result.js_execution_result.get("error", "Unknown error")})
                if "results" in result.js_execution_result:
                    image_result = result.js_execution_result['results'][0]
                    if image_result.get("success", False) is False:
                        return json.dumps({"error": image_result.get("error", "Unknown error")})
                    return json.dumps(image_result["result"], indent=4)

            # For text search, extract structured data
            schemas = await self._build_schemas(result.cleaned_html, schema_cache_path)
            extracted = {
                key: JsonCssExtractionStrategy(schema=schemas[key]).run(
                    url=url, sections=[result.html]
                )
                for key in schemas
            }
            return json.dumps(extracted, indent=4)

    async def _build_schemas(self, html: str, schema_cache_path: str = None) -> Dict[str, Dict]:
        """Build extraction schemas (organic, top stories, etc.)"""
        home_dir = get_home_folder() if not schema_cache_path else schema_cache_path
        os.makedirs(f"{home_dir}/schema", exist_ok=True)

        # cleaned_html = optimize_html(html, threshold=100)
        cleaned_html = preprocess_html_for_schema(html) 

        organic_schema = None
        if os.path.exists(f"{home_dir}/schema/organic_schema.json"):
            with open(f"{home_dir}/schema/organic_schema.json", "r") as f:
                organic_schema = json.load(f)
        else:
            organic_schema = JsonCssExtractionStrategy.generate_schema(
                html=cleaned_html,
                target_json_example="""{
            "title": "...",
            "link": "...",
            "snippet": "...",
            "date": "1 hour ago",
        }""",
                query="""The given html is the crawled html from Google search result. Please find the schema for organic search item in the given html, I am interested in title, link, snippet text. date."""
            )

            with open(f"{home_dir}/schema/organic_schema.json", "w") as f:
                f.write(json.dumps(organic_schema))

        top_stories_schema = None
        if os.path.exists(f"{home_dir}/schema/top_stories_schema.json"):
            with open(f"{home_dir}/schema/top_stories_schema.json", "r") as f:
                top_stories_schema = json.load(f)
        else:
            top_stories_schema = JsonCssExtractionStrategy.generate_schema(
                html=cleaned_html,
                target_json_example="""{
            "title": "...",
            "link": "...",
            "source": "Insider Monkey",
            "date": "1 hour ago",
        }""",
                query="""The given html is the crawled html from Google search result. Please find the schema for Top Story item int he given html, I am interested in title, link, source. date and imageUrl."""
            )

            with open(f"{home_dir}/schema/top_stories_schema.json", "w") as f:
                f.write(json.dumps(top_stories_schema))

        suggested_query_schema = None
        if os.path.exists(f"{home_dir}/schema/suggested_query_schema.json"):
            with open(f"{home_dir}/schema/suggested_query_schema.json", "r") as f:
                suggested_query_schema = json.load(f)
        else:
            suggested_query_schema = JsonCssExtractionStrategy.generate_schema(
                html=cleaned_html,
                target_json_example="""{
            "query": "A for Apple",
        }""",
                query="""The given HTML contains the crawled HTML from Google search results. Please find the schema for each suggested query in the section "People also search for" within the given HTML. I am interested in the queries only."""
            )
            with open(f"{home_dir}/schema/suggested_query_schema.json", "w") as f:
                f.write(json.dumps(suggested_query_schema))

        return {
            "organic_schema": organic_schema,
            "top_stories_schema": top_stories_schema,
            "suggested_query_schema": suggested_query_schema,
        }
