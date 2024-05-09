from crawler.web_crawler import WebCrawler
from crawler.models import UrlModel
from crawler.utils import get_content_of_website
import os

def main():
    # Initialize the WebCrawler with just the database path
    crawler = WebCrawler(db_path='crawler_data.db')

    # Fetch a single page
    single_url = UrlModel(url='https://kidocode.com', forced=True)
    result = crawler.fetch_page(
        single_url, 
        provider= "openai/gpt-3.5-turbo", 
        api_token = os.getenv('OPENAI_API_KEY'), 
        extract_blocks_flag=True,
        word_count_threshold=5
    )
    print(result.model_dump())

    # Fetch multiple pages
    # urls = [
    #     UrlModel(url='http://example.com', forced=False),
    #     UrlModel(url='http://example.org', forced=False)
    # ]
    # results = crawler.fetch_pages(urls, provider= "openai/gpt-4-turbo", api_token = os.getenv('OPENAI_API_KEY'))
    # for res in results:
    #     print(res.model_copy())
    
if __name__ == '__main__':
    main()