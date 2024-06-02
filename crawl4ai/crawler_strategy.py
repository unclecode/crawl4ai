from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidArgumentException
import logging
logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
logger.setLevel(logging.WARNING)

logger_driver = logging.getLogger('selenium.webdriver.common.service')
logger_driver.setLevel(logging.WARNING)

urllib3_logger = logging.getLogger('urllib3.connectionpool')
urllib3_logger.setLevel(logging.WARNING)

# Disable http.client logging
http_client_logger = logging.getLogger('http.client')
http_client_logger.setLevel(logging.WARNING)

# Disable driver_finder and service logging
driver_finder_logger = logging.getLogger('selenium.webdriver.common.driver_finder')
driver_finder_logger.setLevel(logging.WARNING)


from typing import List
import requests
import os
from pathlib import Path

class CrawlerStrategy(ABC):
    @abstractmethod
    def crawl(self, url: str, **kwargs) -> str:
        pass

class CloudCrawlerStrategy(CrawlerStrategy):
    def __init__(self, use_cached_html = False):
        super().__init__()
        self.use_cached_html = use_cached_html
        
    def crawl(self, url: str) -> str:
        data = {
            "urls": [url],
            "include_raw_html": True,
            "forced": True,
            "extract_blocks": False,
        }

        response = requests.post("http://crawl4ai.uccode.io/crawl", json=data)
        response = response.json()
        html = response["results"][0]["html"]
        return html

class LocalSeleniumCrawlerStrategy(CrawlerStrategy):
    def __init__(self, use_cached_html=False, js_code=None, **kwargs):
        super().__init__()
        print("[LOG] 🚀 Initializing LocalSeleniumCrawlerStrategy")
        self.options = Options()
        self.options.headless = True
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--headless")
        # self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        # self.options.add_argument("--disable-extensions")
        # self.options.add_argument("--disable-infobars")
        # self.options.add_argument("--disable-logging")
        # self.options.add_argument("--disable-popup-blocking")
        # self.options.add_argument("--disable-translate")
        # self.options.add_argument("--disable-default-apps")
        # self.options.add_argument("--disable-background-networking")
        # self.options.add_argument("--disable-sync")
        # self.options.add_argument("--disable-features=NetworkService,NetworkServiceInProcess")
        # self.options.add_argument("--disable-browser-side-navigation")
        # self.options.add_argument("--dns-prefetch-disable")
        # self.options.add_argument("--disable-web-security")
        self.options.add_argument("--log-level=3")
        self.use_cached_html = use_cached_html
        self.use_cached_html = use_cached_html
        self.js_code = js_code
        self.verbose = kwargs.get("verbose", False)

        # chromedriver_autoinstaller.install()
        import chromedriver_autoinstaller
        self.service = Service(chromedriver_autoinstaller.install())
        self.service.log_path = "NUL"
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def crawl(self, url: str) -> str:
        if self.use_cached_html:
            cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", url.replace("/", "_"))
            if os.path.exists(cache_file_path):
                with open(cache_file_path, "r") as f:
                    return f.read()

        try:
            if self.verbose:
                print(f"[LOG] 🕸️ Crawling {url} using LocalSeleniumCrawlerStrategy...")
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "html"))
            )
            
            # Execute JS code if provided
            if self.js_code and type(self.js_code) == str:
                self.driver.execute_script(self.js_code)
                # Optionally, wait for some condition after executing the JS code
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            elif self.js_code and type(self.js_code) == list:
                for js in self.js_code:
                    self.driver.execute_script(js)
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
            
            html = self.driver.page_source
            
            # Store in cache
            cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", url.replace("/", "_"))
            with open(cache_file_path, "w") as f:
                f.write(html)
                
            if self.verbose:
                print(f"[LOG] ✅ Crawled {url} successfully!")
            
            return html
        except InvalidArgumentException:
            raise InvalidArgumentException(f"Invalid URL {url}")
        except Exception as e:
            raise Exception(f"Failed to crawl {url}: {str(e)}")

    def quit(self):
        self.driver.quit()