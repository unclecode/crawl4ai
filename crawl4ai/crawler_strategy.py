from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidArgumentException
import chromedriver_autoinstaller
from typing import List
import requests
import os
from pathlib import Path

class CrawlerStrategy(ABC):
    @abstractmethod
    def crawl(self, url: str, **kwargs) -> str:
        pass

class CloudCrawlerStrategy(CrawlerStrategy):
    def crawl(self, url: str, use_cached_html = False, css_selector = None) -> str:
        data = {
            "urls": [url],
            "provider_model": "",
            "api_token": "token",
            "include_raw_html": True,
            "forced": True,
            "extract_blocks": False,
            "word_count_threshold": 10
        }

        response = requests.post("http://crawl4ai.uccode.io/crawl", json=data)
        response = response.json()
        html = response["results"][0]["html"]
        return html

class LocalSeleniumCrawlerStrategy(CrawlerStrategy):
    def __init__(self):
        self.options = Options()
        self.options.headless = True
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--headless")

        # chromedriver_autoinstaller.install()
        self.service = Service(chromedriver_autoinstaller.install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def crawl(self, url: str, use_cached_html = False, css_selector = None) -> str:
        if use_cached_html:
            cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", url.replace("/", "_"))
            if os.path.exists(cache_file_path):
                with open(cache_file_path, "r") as f:
                    return f.read()

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "html"))
            )
            html = self.driver.page_source
            
            # Store in cache
            cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", url.replace("/", "_"))
            with open(cache_file_path, "w") as f:
                f.write(html)
            
            return html
        except InvalidArgumentException:
            raise InvalidArgumentException(f"Invalid URL {url}")
        except Exception as e:
            raise Exception(f"Failed to crawl {url}: {str(e)}")

    def quit(self):
        self.driver.quit()