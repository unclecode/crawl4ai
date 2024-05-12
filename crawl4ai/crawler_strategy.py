from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from typing import List
import requests


class CrawlerStrategy(ABC):
    @abstractmethod
    def crawl(self, url: str) -> str:
        pass

class CloudCrawlerStrategy(CrawlerStrategy):
    def crawl(self, url: str) -> str:
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

        chromedriver_autoinstaller.install()
        self.service = Service(chromedriver_autoinstaller.install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def crawl(self, url: str, use_cached_html = False) -> str:
        if use_cached_html:
            return get_content_of_website(url)
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "html"))
        )
        html = self.driver.page_source
        return html

    def quit(self):
        self.driver.quit()