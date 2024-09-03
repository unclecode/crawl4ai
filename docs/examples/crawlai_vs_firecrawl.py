import os, time
# append the path to the root of the project
import sys
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from firecrawl import FirecrawlApp
from crawl4ai import AsyncWebCrawler
__data__ = os.path.join(os.path.dirname(__file__), '..', '..') + '/.data'

async def compare():
    app = FirecrawlApp(api_key=os.environ['FIRECRAWL_API_KEY'])

    # Tet Firecrawl with a simple crawl
    start = time.time()
    scrape_status = app.scrape_url(
    'https://www.nbcnews.com/business',
    params={'formats': ['markdown', 'html']}
    )
    end = time.time()
    print(f"Time taken: {end - start} seconds")
    print(len(scrape_status['markdown']))
    # save the markdown content with provider name
    with open(f"{__data__}/firecrawl_simple.md", "w") as f:
        f.write(scrape_status['markdown'])
    # Count how many "cldnry.s-nbcnews.com" are in the markdown
    print(scrape_status['markdown'].count("cldnry.s-nbcnews.com"))
    


    async with AsyncWebCrawler() as crawler:
        start = time.time()
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            # js_code=["const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"],
            word_count_threshold=0,
            bypass_cache=True, 
            verbose=False
        )
        end = time.time()
        print(f"Time taken: {end - start} seconds")
        print(len(result.markdown))
        # save the markdown content with provider name  
        with open(f"{__data__}/crawl4ai_simple.md", "w") as f:
            f.write(result.markdown)
        # count how many "cldnry.s-nbcnews.com" are in the markdown
        print(result.markdown.count("cldnry.s-nbcnews.com"))

        start = time.time()
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=["const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"],
            word_count_threshold=0,
            bypass_cache=True, 
            verbose=False
        )
        end = time.time()
        print(f"Time taken: {end - start} seconds")
        print(len(result.markdown))
        # save the markdown content with provider name
        with open(f"{__data__}/crawl4ai_js.md", "w") as f:
            f.write(result.markdown)
        # count how many "cldnry.s-nbcnews.com" are in the markdown
        print(result.markdown.count("cldnry.s-nbcnews.com"))
        
if __name__ == "__main__":
    asyncio.run(compare())
    