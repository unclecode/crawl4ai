import os
import time
import json
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *

url = r'https://marketplace.visualstudio.com/items?itemName=Unclecode.groqopilot'

crawler = WebCrawler()
crawler.warmup()

from pydantic import BaseModel, Field

class PageSummary(BaseModel):
    title: str = Field(..., description="Title of the page.")
    summary: str = Field(..., description="Summary of the page.")
    brief_summary: str = Field(..., description="Brief summary of the page.")
    keywords: list = Field(..., description="Keywords assigned to the page.")

result = crawler.run(
    url=url,
    word_count_threshold=1,
    extraction_strategy= LLMExtractionStrategy(
        provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY'), 
        schema=PageSummary.model_json_schema(),
        extraction_type="schema",
        apply_chunking =False,
        instruction="From the crawled content, extract the following details: "\
            "1. Title of the page "\
            "2. Summary of the page, which is a detailed summary "\
            "3. Brief summary of the page, which is a paragraph text "\
            "4. Keywords assigned to the page, which is a list of keywords. "\
            'The extracted JSON format should look like this: '\
            '{ "title": "Page Title", "summary": "Detailed summary of the page.", "brief_summary": "Brief summary in a paragraph.", "keywords": ["keyword1", "keyword2", "keyword3"] }'
    ),
    bypass_cache=True,
)

page_summary = json.loads(result.extracted_content)

print(page_summary)

with open(".data/page_summary.json", "w", encoding="utf-8") as f:
    f.write(result.extracted_content)
