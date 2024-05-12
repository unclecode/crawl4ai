import asyncio
import os, time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from pydantic import parse_obj_as
from .models import UrlModel, CrawlResult
from .database import init_db, get_cached_url, cache_url
from .utils import *
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import * 

class WebCrawler:
    def __init__(self, db_path: str):
        self.db_path = db_path
        init_db(self.db_path)
        self.options = Options()
        self.options.headless = True
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        # make it headless
        self.options.add_argument("--headless")

        # Automatically install or update chromedriver
        chromedriver_autoinstaller.install()
        
        # Initialize WebDriver for crawling     
        self.service = Service(chromedriver_autoinstaller.install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        
        # Create the .crawl4ai folder in the user's home directory if it doesn't exist
        self.crawl4ai_folder = os.path.join(Path.home(), ".crawl4ai")
        os.makedirs(self.crawl4ai_folder, exist_ok=True)        
        os.makedirs(f"{self.crawl4ai_folder}/cache", exist_ok=True)
       

    def fetch_page(self, 
                   url_model: UrlModel, 
                   provider: str = DEFAULT_PROVIDER, 
                   api_token: str = None, 
                   extract_blocks_flag: bool = True, 
                   word_count_threshold = MIN_WORD_THRESHOLD,
                   use_cached_html: bool = False) -> CrawlResult:
        # make sure word_count_threshold is not lesser than MIN_WORD_THRESHOLD
        # if word_count_threshold < MIN_WORD_THRESHOLD:
        #     word_count_threshold = MIN_WORD_THRESHOLD
            
        # Check cache first
        cached = get_cached_url(self.db_path, str(url_model.url))
        if cached and not url_model.forced:
            return CrawlResult(**{
                "url": cached[0],
                "html": cached[1],
                "cleaned_html": cached[2],
                "markdown": cached[3],
                "parsed_json": cached[4],
                "success": cached[5],
                "error_message": ""
            })
            

        # Initialize WebDriver for crawling
        if use_cached_html:
            # load html from crawl4ai_folder/cache
            valid_file_name = str(url_model.url).replace("/", "_").replace(":", "_")
            if os.path.exists(os.path.join(self.crawl4ai_folder, "cache", valid_file_name)):
                with open(os.path.join(self.crawl4ai_folder, "cache", valid_file_name), "r") as f:
                    html = f.read()
            else:
                raise Exception("Cached HTML file not found")
            
            success = True
            error_message = ""
        else:
            service = self.service
            driver = self.driver

            try:
                driver.get(str(url_model.url))
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "html"))
                )
                html = driver.page_source
                success = True
                error_message = ""
                
                # Save html in crawl4ai_folder/cache
                valid_file_name = str(url_model.url).replace("/", "_").replace(":", "_")
                with open(os.path.join(self.crawl4ai_folder, "cache", valid_file_name), "w") as f:
                    f.write(html)
                
            except Exception as e:
                html = ""
                success = False
                error_message = str(e)
            finally:
                driver.quit()

        # Extract content from HTML
        result = get_content_of_website(html, word_count_threshold)
        cleaned_html = result.get('cleaned_html', html)
        markdown = result.get('markdown', "")
        
        print("Crawling is done 🚀")

        parsed_json = []
        if extract_blocks_flag:
            # Split markdown into sections
            paragraphs = markdown.split('\n\n')
            sections = []
            chunks = []
            total_token_so_far = 0

            for paragraph in paragraphs:
                if total_token_so_far < CHUNK_TOKEN_THRESHOLD:
                    chunk = paragraph.split(' ')
                    total_token_so_far += len(chunk) * 1.3
                    chunks.append(paragraph)
                else:
                    sections.append('\n\n'.join(chunks))
                    chunks = [paragraph]
                    total_token_so_far = len(paragraph.split(' ')) * 1.3

            if chunks:
                sections.append('\n\n'.join(chunks))

            # Process sections to extract blocks
            parsed_json = []
            if provider.startswith("groq/"):
                # Sequential processing with a delay
                for section in sections:
                    parsed_json.extend(extract_blocks(str(url_model.url), section, provider, api_token))
                    time.sleep(0.5)  # 500 ms delay between each processing
            else:
                # Parallel processing using ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(extract_blocks, str(url_model.url), section, provider, api_token) for section in sections]
                    for future in as_completed(futures):
                        parsed_json.extend(future.result())

            parsed_json = json.dumps(parsed_json)
        else:
            parsed_json = "{}"

        # Cache the result
        cleaned_html = beautify_html(cleaned_html)
        cache_url(self.db_path, str(url_model.url), html, cleaned_html, markdown, parsed_json, success)

        return CrawlResult(
            url=str(url_model.url), 
            html=html, 
            cleaned_html=cleaned_html, 
            markdown=markdown, 
            parsed_json=parsed_json, 
            success=success, 
            error_message=error_message
        )

    def fetch_pages(self, url_models: List[UrlModel], provider: str = DEFAULT_PROVIDER, api_token: str = None) -> List[CrawlResult]:
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(self.fetch_page, url_models, [provider] * len(url_models), [api_token] * len(url_models)))
        return results