import asyncio
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai import *
from pydantic import BaseModel, Field
from crawl4ai.async_configs import CrawlerRunConfig, LLMConfig
import json

url = r"https://marketplace.visualstudio.com/items?itemName=Unclecode.groqopilot"


class PageSummary(BaseModel):
    title: str = Field(..., description="Title of the page.")
    summary: str = Field(..., description="Summary of the page.")
    brief_summary: str = Field(..., description="Brief summary of the page.")
    keywords: list = Field(..., description="Keywords assigned to the page.")


llm_config = LLMConfig(
    provider="openai/gpt-4o",
)


async def summarize_page():
    crawler_run_config = CrawlerRunConfig(
        url=url,
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=llm_config,
            schema=PageSummary.model_json_schema(),
            extraction_type="schema",
            apply_chunking=False,
            instruction="From the crawled content, extract the following details: "
            "1. Title of the page "
            "2. Summary of the page, which is a detailed summary "
            "3. Brief summary of the page, which is a paragraph text "
            "4. Keywords assigned to the page, which is a list of keywords. "
            "The extracted JSON format should look like this: "
            '{ "title": "Page Title", "summary": "Detailed summary of the page.", "brief_summary": "Brief summary in a paragraph.", "keywords": ["keyword1", "keyword2", "keyword3"] }',
        ),
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=crawler_run_config)

        page_summary = json.loads(result.extracted_content)

        print(page_summary)

        import os

        os.makedirs(".data", exist_ok=True)
        with open(".data/page_summary.json", "w", encoding="utf-8") as f:
            f.write(result.extracted_content)


if __name__ == "__main__":
    asyncio.run(summarize_page())
