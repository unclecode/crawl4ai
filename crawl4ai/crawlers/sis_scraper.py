import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy, CacheMode
import json
import datetime
import re
import os

# Define CSS selectors for the forum
THREAD_LIST_SCHEMA = {
    "baseSelector": "tbody[id^='normalthread_']",
    "fields": [
        {
            "name": "title",
            "selector": "span[id^='thread_'] a",
            "type": "text"
        },
        {
            "name": "url",
            "selector": "span[id^='thread_'] a",
            "type": "attribute",
            "attribute": "href"
        }
    ]
}

THREAD_PAGE_SCHEMA = {
    "baseSelector": "#postlist > div:first-child",
    "fields": [
        {
            "name": "title",
            "selector": "#thread_subject",
            "type": "text"
        },
        {
            "name": "author",
            "selector": ".authi a",
            "type": "text"
        },
        {
            "name": "content",
            "selector": ".t_fsz",
            "type": "text"
        }
    ]
}

BASE_URL = "https://www.sis001.com/bbs/"

async def scrape_thread(crawler: AsyncWebCrawler, thread_url: str):
    """Scrapes a single thread page."""
    # The URL from the list is relative, so construct the full URL
    full_url = f"{BASE_URL}{thread_url}"
    print(f"Scraping thread: {full_url}")

    run_config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema=THREAD_PAGE_SCHEMA),
        cache_mode=CacheMode.BYPASS
    )

    result = await crawler.arun(url=full_url, config=run_config)

    if result.success and result.extracted_content:
        try:
            data = json.loads(result.extracted_content)
            # The result is a list, we want the first item
            if data and data[0]:
                return data[0]
        except (json.JSONDecodeError, IndexError):
            print(f"Failed to parse content from {full_url}")
    return None

def save_to_markdown(data, url):
    """Saves the scraped data to a markdown file."""
    title = data.get('title', 'No Title').strip()
    author = data.get('author', 'No Author').strip()
    content = data.get('content', '').strip()

    # Clean filename to be safe for all OS
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    safe_author = re.sub(r'[\\/*?:"<>|]', "", author)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    filename = f"[{safe_title}]_[{safe_author}]_[{date_str}].md"

    # Prepare metadata
    crawl_time = datetime.datetime.now().isoformat()
    # A simple quality score, could be more sophisticated
    quality_score = len(content)

    metadata = f"""---
URL: {url}
Crawl Time: {crawl_time}
Quality Score: {quality_score}
---

"""

    full_content = metadata + f"# {title}\\n\\n**Author:** {author}\\n\\n{content}"

    # Ensure output directory exists
    output_dir = "scraped_novels"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"Saved novel to {filepath}")


async def run_sis_scraper(keyword: str):
    """
    Scrapes the SIS001 forum for novels with a specific keyword.
    """
    print(f"Starting SIS001 scraper for keyword: {keyword}")

    async with AsyncWebCrawler() as crawler:
        for page_num in range(1, 4): # Scrape pages 1 to 3
            forum_url = f"{BASE_URL}forum-500-{page_num}.html"
            print(f"Scraping forum page: {forum_url}")

            run_config = CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(schema=THREAD_LIST_SCHEMA),
                cache_mode=CacheMode.BYPASS
            )

            list_result = await crawler.arun(url=forum_url, config=run_config)

            if not list_result.success or not list_result.extracted_content:
                print(f"Failed to scrape thread list from {forum_url}")
                continue

            try:
                threads = json.loads(list_result.extracted_content)
            except json.JSONDecodeError:
                print(f"Failed to parse thread list from {forum_url}")
                continue

            for thread in threads:
                title = thread.get("title")
                url = thread.get("url")

                if title and url and keyword in title:
                    print(f"Found matching thread: '{title}'")

                    scraped_data = await scrape_thread(crawler, url)

                    if scraped_data and scraped_data.get('content'):
                        content_length = len(scraped_data['content'])
                        if content_length > 500:
                            print(f"Content length ({content_length}) is sufficient. Saving.")
                            # Add the original URL to the data for saving
                            scraped_data['url'] = f"{BASE_URL}{url}"
                            save_to_markdown(scraped_data, scraped_data['url'])
                        else:
                            print(f"Content length ({content_length}) is too short. Skipping.")
                    else:
                        print("No content extracted from thread. Skipping.")

if __name__ == "__main__":
    # This allows running the scraper directly for testing purposes
    # To run: python -m crawl4ai.crawlers.sis_scraper
    asyncio.run(run_sis_scraper(keyword="母子"))
