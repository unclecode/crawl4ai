import os
import time
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *
from rich import print
from rich.console import Console
from functools import lru_cache

console = Console()

@lru_cache()
def create_crawler():
    crawler = WebCrawler(verbose=True)
    crawler.warmup()
    return crawler

def print_result(result):
    # Print each key in one line and just the first 10 characters of each one's value and three dots
    console.print(f"\t[bold]Result:[/bold]")
    for key, value in result.model_dump().items():
        if isinstance(value, str) and value:
            console.print(f"\t{key}: [green]{value[:20]}...[/green]")
    if result.extracted_content:
        items = json.loads(result.extracted_content)
        print(f"\t[bold]{len(items)} blocks is extracted![/bold]")


def cprint(message, press_any_key=False):
    console.print(message)
    if press_any_key:
        console.print("Press any key to continue...", style="")
        input()

def basic_usage(crawler):
    cprint("🛠️ [bold cyan]Basic Usage: Simply provide a URL and let Crawl4ai do the magic![/bold cyan]")
    result = crawler.run(url="https://www.nbcnews.com/business", only_text = True)
    cprint("[LOG] 📦 [bold yellow]Basic crawl result:[/bold yellow]")
    print_result(result)

def basic_usage_some_params(crawler):
    cprint("🛠️ [bold cyan]Basic Usage: Simply provide a URL and let Crawl4ai do the magic![/bold cyan]")
    result = crawler.run(url="https://www.nbcnews.com/business", word_count_threshold=1, only_text = True)
    cprint("[LOG] 📦 [bold yellow]Basic crawl result:[/bold yellow]")
    print_result(result)

def screenshot_usage(crawler):
    cprint("\n📸 [bold cyan]Let's take a screenshot of the page![/bold cyan]")
    result = crawler.run(url="https://www.nbcnews.com/business", screenshot=True)
    cprint("[LOG] 📦 [bold yellow]Screenshot result:[/bold yellow]")
    # Save the screenshot to a file
    with open("screenshot.png", "wb") as f:
        f.write(base64.b64decode(result.screenshot))
    cprint("Screenshot saved to 'screenshot.png'!")
    print_result(result)

def understanding_parameters(crawler):
    cprint("\n🧠 [bold cyan]Understanding 'bypass_cache' and 'include_raw_html' parameters:[/bold cyan]")
    cprint("By default, Crawl4ai caches the results of your crawls. This means that subsequent crawls of the same URL will be much faster! Let's see this in action.")
    
    # First crawl (reads from cache)
    cprint("1️⃣ First crawl (caches the result):", True)
    start_time = time.time()
    result = crawler.run(url="https://www.nbcnews.com/business")
    end_time = time.time()
    cprint(f"[LOG] 📦 [bold yellow]First crawl took {end_time - start_time} seconds and result (from cache):[/bold yellow]")
    print_result(result)

    # Force to crawl again
    cprint("2️⃣ Second crawl (Force to crawl again):", True)
    start_time = time.time()
    result = crawler.run(url="https://www.nbcnews.com/business", bypass_cache=True)
    end_time = time.time()
    cprint(f"[LOG] 📦 [bold yellow]Second crawl took {end_time - start_time} seconds and result (forced to crawl):[/bold yellow]")
    print_result(result)

def add_chunking_strategy(crawler):
    # Adding a chunking strategy: RegexChunking
    cprint("\n🧩 [bold cyan]Let's add a chunking strategy: RegexChunking![/bold cyan]", True)
    cprint("RegexChunking is a simple chunking strategy that splits the text based on a given regex pattern. Let's see it in action!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        chunking_strategy=RegexChunking(patterns=["\n\n"])
    )
    cprint("[LOG] 📦 [bold yellow]RegexChunking result:[/bold yellow]")
    print_result(result)

    # Adding another chunking strategy: NlpSentenceChunking
    cprint("\n🔍 [bold cyan]Time to explore another chunking strategy: NlpSentenceChunking![/bold cyan]", True)
    cprint("NlpSentenceChunking uses NLP techniques to split the text into sentences. Let's see how it performs!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        chunking_strategy=NlpSentenceChunking()
    )
    cprint("[LOG] 📦 [bold yellow]NlpSentenceChunking result:[/bold yellow]")
    print_result(result)

def add_extraction_strategy(crawler):
    # Adding an extraction strategy: CosineStrategy
    cprint("\n🧠 [bold cyan]Let's get smarter with an extraction strategy: CosineStrategy![/bold cyan]", True)
    cprint("CosineStrategy uses cosine similarity to extract semantically similar blocks of text. Let's see it in action!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=CosineStrategy(word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3, sim_threshold = 0.3, verbose=True)
    )
    cprint("[LOG] 📦 [bold yellow]CosineStrategy result:[/bold yellow]")
    print_result(result)
    
    # Using semantic_filter with CosineStrategy
    cprint("You can pass other parameters like 'semantic_filter' to the CosineStrategy to extract semantically similar blocks of text. Let's see it in action!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=CosineStrategy(
            semantic_filter="inflation rent prices",
        )
    )
    cprint("[LOG] 📦 [bold yellow]CosineStrategy result with semantic filter:[/bold yellow]")
    print_result(result)

def add_llm_extraction_strategy(crawler):
    # Adding an LLM extraction strategy without instructions
    cprint("\n🤖 [bold cyan]Time to bring in the big guns: LLMExtractionStrategy without instructions![/bold cyan]", True)
    cprint("LLMExtractionStrategy uses a large language model to extract relevant information from the web page. Let's see it in action!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=LLMExtractionStrategy(provider="openai/gpt-4o", api_token=os.getenv('OPENAI_API_KEY'))
    )
    cprint("[LOG] 📦 [bold yellow]LLMExtractionStrategy (no instructions) result:[/bold yellow]")
    print_result(result)
    
    # Adding an LLM extraction strategy with instructions
    cprint("\n📜 [bold cyan]Let's make it even more interesting: LLMExtractionStrategy with instructions![/bold cyan]", True)
    cprint("Let's say we are only interested in financial news. Let's see how LLMExtractionStrategy performs with instructions!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=LLMExtractionStrategy(
            provider="openai/gpt-4o",
            api_token=os.getenv('OPENAI_API_KEY'),
            instruction="I am interested in only financial news"
        )
    )
    cprint("[LOG] 📦 [bold yellow]LLMExtractionStrategy (with instructions) result:[/bold yellow]")
    print_result(result)
    
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=LLMExtractionStrategy(
            provider="openai/gpt-4o",
            api_token=os.getenv('OPENAI_API_KEY'),
            instruction="Extract only content related to technology"
        )
    )
    cprint("[LOG] 📦 [bold yellow]LLMExtractionStrategy (with technology instruction) result:[/bold yellow]")
    print_result(result)

def targeted_extraction(crawler):
    # Using a CSS selector to extract only H2 tags
    cprint("\n🎯 [bold cyan]Targeted extraction: Let's use a CSS selector to extract only H2 tags![/bold cyan]", True)
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        css_selector="h2"
    )
    cprint("[LOG] 📦 [bold yellow]CSS Selector (H2 tags) result:[/bold yellow]")
    print_result(result)

def interactive_extraction(crawler):
    # Passing JavaScript code to interact with the page
    cprint("\n🖱️ [bold cyan]Let's get interactive: Passing JavaScript code to click 'Load More' button![/bold cyan]", True)
    cprint("In this example we try to click the 'Load More' button on the page using JavaScript code.")
    js_code = """
    const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
    loadMoreButton && loadMoreButton.click();
    """
    # crawler_strategy = LocalSeleniumCrawlerStrategy(js_code=js_code)
    # crawler = WebCrawler(crawler_strategy=crawler_strategy, always_by_pass_cache=True)
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        js = js_code
    )
    cprint("[LOG] 📦 [bold yellow]JavaScript Code (Load More button) result:[/bold yellow]")
    print_result(result)

def multiple_scrip(crawler):
    # Passing JavaScript code to interact with the page
    cprint("\n🖱️ [bold cyan]Let's get interactive: Passing JavaScript code to click 'Load More' button![/bold cyan]", True)
    cprint("In this example we try to click the 'Load More' button on the page using JavaScript code.")
    js_code = ["""
    const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
    loadMoreButton && loadMoreButton.click();
    """] * 2
    # crawler_strategy = LocalSeleniumCrawlerStrategy(js_code=js_code)
    # crawler = WebCrawler(crawler_strategy=crawler_strategy, always_by_pass_cache=True)
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        js = js_code  
    )
    cprint("[LOG] 📦 [bold yellow]JavaScript Code (Load More button) result:[/bold yellow]")
    print_result(result)

def using_crawler_hooks(crawler):
    # Example usage of the hooks for authentication and setting a cookie
    def on_driver_created(driver):
        print("[HOOK] on_driver_created")
        # Example customization: maximize the window
        driver.maximize_window()
        
        # Example customization: logging in to a hypothetical website
        driver.get('https://example.com/login')
        
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        driver.find_element(By.NAME, 'username').send_keys('testuser')
        driver.find_element(By.NAME, 'password').send_keys('password123')
        driver.find_element(By.NAME, 'login').click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'welcome'))
        )
        # Add a custom cookie
        driver.add_cookie({'name': 'test_cookie', 'value': 'cookie_value'})
        return driver        
        

    def before_get_url(driver):
        print("[HOOK] before_get_url")
        # Example customization: add a custom header
        # Enable Network domain for sending headers
        driver.execute_cdp_cmd('Network.enable', {})
        # Add a custom header
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'X-Test-Header': 'test'}})
        return driver
    
    def after_get_url(driver):
        print("[HOOK] after_get_url")
        # Example customization: log the URL
        print(driver.current_url)
        return driver

    def before_return_html(driver, html):
        print("[HOOK] before_return_html")
        # Example customization: log the HTML
        print(len(html))
        return driver
    
    cprint("\n🔗 [bold cyan]Using Crawler Hooks: Let's see how we can customize the crawler using hooks![/bold cyan]", True)
    
    crawler_strategy = LocalSeleniumCrawlerStrategy(verbose=True)
    crawler_strategy.set_hook('on_driver_created', on_driver_created)
    crawler_strategy.set_hook('before_get_url', before_get_url)
    crawler_strategy.set_hook('after_get_url', after_get_url)
    crawler_strategy.set_hook('before_return_html', before_return_html)
    
    crawler = WebCrawler(verbose=True, crawler_strategy=crawler_strategy)
    crawler.warmup()    
    result = crawler.run(url="https://example.com")
    
    cprint("[LOG] 📦 [bold yellow]Crawler Hooks result:[/bold yellow]")
    print_result(result= result)
    
def using_crawler_hooks_dleay_example(crawler):
    def delay(driver):
        print("Delaying for 5 seconds...")
        time.sleep(5)
        print("Resuming...")
        
    def create_crawler():
        crawler_strategy = LocalSeleniumCrawlerStrategy(verbose=True)
        crawler_strategy.set_hook('after_get_url', delay)
        crawler = WebCrawler(verbose=True, crawler_strategy=crawler_strategy)
        crawler.warmup()
        return crawler

    cprint("\n🔗 [bold cyan]Using Crawler Hooks: Let's add a delay after fetching the url to make sure entire page is fetched.[/bold cyan]")
    crawler = create_crawler()
    result = crawler.run(url="https://google.com", bypass_cache=True)    
    
    cprint("[LOG] 📦 [bold yellow]Crawler Hooks result:[/bold yellow]")
    print_result(result)
    
    

def main():
    cprint("🌟 [bold green]Welcome to the Crawl4ai Quickstart Guide! Let's dive into some web crawling fun! 🌐[/bold green]")
    cprint("⛳️ [bold cyan]First Step: Create an instance of WebCrawler and call the `warmup()` function.[/bold cyan]")
    cprint("If this is the first time you're running Crawl4ai, this might take a few seconds to load required model files.")

    crawler = create_crawler()

    crawler.always_by_pass_cache = True
    basic_usage(crawler)
    # basic_usage_some_params(crawler)
    understanding_parameters(crawler)
    
    crawler.always_by_pass_cache = True
    screenshot_usage(crawler)
    add_chunking_strategy(crawler)
    add_extraction_strategy(crawler)
    add_llm_extraction_strategy(crawler)
    targeted_extraction(crawler)
    interactive_extraction(crawler)
    multiple_scrip(crawler)

    cprint("\n🎉 [bold green]Congratulations! You've made it through the Crawl4ai Quickstart Guide! Now go forth and crawl the web like a pro! 🕸️[/bold green]")

if __name__ == "__main__":
    main()

