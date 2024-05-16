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
    crawler = WebCrawler()
    crawler.warmup()
    return crawler

def print_result(result):
    # Print each key in one line and just the first 10 characters of each one's value and three dots
    console.print(f"\t[bold]Result:[/bold]")
    for key, value in result.model_dump().items():
        if isinstance(value, str) and value:
            console.print(f"\t{key}: [green]{value[:20]}...[/green]")

def cprint(message, press_any_key=False):
    console.print(message)
    if press_any_key:
        console.print("Press any key to continue...", style="")
        input()

def basic_usage(crawler):
    cprint("🛠️ [bold cyan]Basic Usage: Simply provide a URL and let Crawl4ai do the magic![/bold cyan]")
    result = crawler.run(url="https://www.nbcnews.com/business")
    cprint("[LOG] 📦 [bold yellow]Basic crawl result:[/bold yellow]")
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

    # Retrieve raw HTML content
    cprint("\n🔄 [bold cyan]'include_raw_html' parameter example:[/bold cyan]", True)
    result = crawler.run(url="https://www.nbcnews.com/business", include_raw_html=False)
    cprint("[LOG] 📦 [bold yellow]Crawl result (without raw HTML content):[/bold yellow]")
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
        extraction_strategy=CosineStrategy(word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3)
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
        url="https://www.example.com",
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
    crawler_strategy = LocalSeleniumCrawlerStrategy(js_code=js_code)
    crawler = WebCrawler(crawler_strategy=crawler_strategy, always_by_pass_cache=True)
    result = crawler.run(
        url="https://www.nbcnews.com/business",
    )
    cprint("[LOG] 📦 [bold yellow]JavaScript Code (Load More button) result:[/bold yellow]")
    print_result(result)

def main():
    cprint("🌟 [bold green]Welcome to the Crawl4ai Quickstart Guide! Let's dive into some web crawling fun! 🌐[/bold green]")
    cprint("⛳️ [bold cyan]First Step: Create an instance of WebCrawler and call the `warmup()` function.[/bold cyan]")
    cprint("If this is the first time you're running Crawl4ai, this might take a few seconds to load required model files.")

    crawler = create_crawler()
    
    cprint("For the rest of this guide, I set crawler.always_by_pass_cache to True to force the crawler to bypass the cache. This is to ensure that we get fresh results for each run.", True)
    crawler.always_by_pass_cache = True

    basic_usage(crawler)
    understanding_parameters(crawler)
    add_chunking_strategy(crawler)
    add_extraction_strategy(crawler)
    add_llm_extraction_strategy(crawler)
    targeted_extraction(crawler)
    interactive_extraction(crawler)

    cprint("\n🎉 [bold green]Congratulations! You've made it through the Crawl4ai Quickstart Guide! Now go forth and crawl the web like a pro! 🕸️[/bold green]")

if __name__ == "__main__":
    main()

