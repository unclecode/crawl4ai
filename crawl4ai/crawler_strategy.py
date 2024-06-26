from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidArgumentException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import logging
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import List, Callable
import requests
import os
from pathlib import Path
from .utils import wrap_text

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




class CrawlerStrategy(ABC):
    @abstractmethod
    def crawl(self, url: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def take_screenshot(self, save_path: str):
        pass
    
    @abstractmethod
    def update_user_agent(self, user_agent: str):
        pass
    
    @abstractmethod
    def set_hook(self, hook_type: str, hook: Callable):
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
        if kwargs.get("user_agent"):
            self.options.add_argument("--user-agent=" + kwargs.get("user_agent"))
        else:
            # Set user agent
            user_agent = kwargs.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            self.options.add_argument(f"--user-agent={user_agent}")          
            
        self.options.add_argument("--no-sandbox")
        self.options.headless = kwargs.get("headless", True)
        if self.options.headless:
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
        
        # Hooks
        self.hooks = {
            'on_driver_created': None,
            'on_user_agent_updated': None,
            'before_get_url': None,
            'after_get_url': None,
            'before_return_html': None
        }

        # chromedriver_autoinstaller.install()
        # import chromedriver_autoinstaller
        # crawl4ai_folder = os.path.join(Path.home(), ".crawl4ai")
        # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.options)
        # chromedriver_path = chromedriver_autoinstaller.install()
        # chromedriver_path = chromedriver_autoinstaller.utils.download_chromedriver()
        # self.service = Service(chromedriver_autoinstaller.install())
        
        
        chromedriver_path = ChromeDriverManager().install()
        self.service = Service(chromedriver_path)
        self.service.log_path = "NUL"
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.driver = self.execute_hook('on_driver_created', self.driver)
        
        if kwargs.get("cookies"):
            for cookie in kwargs.get("cookies"):
                self.driver.add_cookie(cookie)
            
        

    def set_hook(self, hook_type: str, hook: Callable):
        if hook_type in self.hooks:
            self.hooks[hook_type] = hook
        else:
            raise ValueError(f"Invalid hook type: {hook_type}")
    
    def execute_hook(self, hook_type: str, *args):
        hook = self.hooks.get(hook_type)
        if hook:
            result = hook(*args)
            if result is not None:
                if isinstance(result, webdriver.Chrome):
                    return result
                else:
                    raise TypeError(f"Hook {hook_type} must return an instance of webdriver.Chrome or None.")
        # If the hook returns None or there is no hook, return self.driver
        return self.driver

    def update_user_agent(self, user_agent: str):
        self.options.add_argument(f"user-agent={user_agent}")
        self.driver.quit()
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.driver = self.execute_hook('on_user_agent_updated', self.driver)

    def set_custom_headers(self, headers: dict):
        # Enable Network domain for sending headers
        self.driver.execute_cdp_cmd('Network.enable', {})
        # Set extra HTTP headers
        self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})


    def crawl(self, url: str) -> str:
        # Create md5 hash of the URL
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        if self.use_cached_html:
            cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", url_hash)
            if os.path.exists(cache_file_path):
                with open(cache_file_path, "r") as f:
                    return f.read()

        try:
            self.driver = self.execute_hook('before_get_url', self.driver)
            if self.verbose:
                print(f"[LOG] 🕸️ Crawling {url} using LocalSeleniumCrawlerStrategy...")
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "html"))
            )
            self.driver = self.execute_hook('after_get_url', self.driver)
            
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
            self.driver = self.execute_hook('before_return_html', self.driver, html)
            
            # Store in cache
            cache_file_path = os.path.join(Path.home(), ".crawl4ai", "cache", url_hash)
            with open(cache_file_path, "w") as f:
                f.write(html)
                
            if self.verbose:
                print(f"[LOG] ✅ Crawled {url} successfully!")
            
            return html
        except InvalidArgumentException:
            if not hasattr(e, 'msg'):
                e.msg = str(e)
            raise InvalidArgumentException(f"Failed to crawl {url}: {e.msg}")
        except WebDriverException as e:
            # If e does nlt have msg attribute create it and set it to str(e)
            if not hasattr(e, 'msg'):
                e.msg = str(e)
            raise WebDriverException(f"Failed to crawl {url}: {e.msg}")  
        except Exception as e:
            if not hasattr(e, 'msg'):
                e.msg = str(e)
            raise Exception(f"Failed to crawl {url}: {e.msg}")

    def take_screenshot(self) -> str:
        try:
            # Get the dimensions of the page
            total_width = self.driver.execute_script("return document.body.scrollWidth")
            total_height = self.driver.execute_script("return document.body.scrollHeight")

            # Set the window size to the dimensions of the page
            self.driver.set_window_size(total_width, total_height)

            # Take screenshot
            screenshot = self.driver.get_screenshot_as_png()

            # Open the screenshot with PIL
            image = Image.open(BytesIO(screenshot))

            # Convert to JPEG and compress
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            if self.verbose:
                print(f"[LOG] 📸 Screenshot taken and converted to base64")

            return img_base64

        except Exception as e:
            error_message = f"Failed to take screenshot: {str(e)}"
            print(error_message)

            # Generate an image with black background
            img = Image.new('RGB', (800, 600), color='black')
            draw = ImageDraw.Draw(img)
            
            # Load a font
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except IOError:
                font = ImageFont.load_default(size=40)

            # Define text color and wrap the text
            text_color = (255, 255, 255)
            max_width = 780
            wrapped_text = wrap_text(draw, error_message, font, max_width)

            # Calculate text position
            text_position = (10, 10)
            
            # Draw the text on the image
            draw.text(text_position, wrapped_text, fill=text_color, font=font)
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            return img_base64

    def quit(self):
        self.driver.quit()