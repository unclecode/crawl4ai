import os, time
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *
from rich import print
from rich.console import Console

console = Console()

def print_result(result):
    # Print each key in one line and just the first 10 characters of each one's value and three dots
    console.print(f"\t[bold]Result:[/bold]")
    for key, value in result.model_dump().items():
        if type(value) == str and value:
            console.print(f"\t{key}: [green]{value[:20]}...[/green]")

def cprint(message, press_any_key=False):
    console.print(message)
    if press_any_key:
        console.print("Press any key to continue...", style="")
        input()

def main():
    # 🚀 Let's get started with the basics!
    cprint("🌟 [bold green]Welcome to the Crawl4ai Quickstart Guide! Let's dive into some web crawling fun! 🌐[/bold green]")

    # Basic usage: Just provide the URL
    cprint("⛳️ [bold cyan]First Step: Create an instance of WebCrawler and call the `warmup()` function.[/bold cyan]")
    cprint("If this is the first time you're running Crawl4ai, this might take a few seconds to lead required model files.", True)

    crawler = WebCrawler()
    crawler.warmup()
    cprint("🛠️ [bold cyan]Basic Usage: Simply provide a URL and let Crawl4ai do the magic![/bold cyan]")
    result = crawler.run(url="https://www.nbcnews.com/business")
    cprint("[LOG] 📦 [bold yellow]Basic crawl result:[/bold yellow]")
    print_result(result)

    # Explanation of bypass_cache and include_raw_html
    cprint("\n🧠 [bold cyan]Understanding 'bypass_cache' and 'include_raw_html' parameters:[/bold cyan]")
    cprint("By default, Crawl4ai caches the results of your crawls. This means that subsequent crawls of the same URL will be much faster! Let's see this in action. Becuase we already crawled this URL, the result will be fetched from the cache. Let's try it out!")
    
    # Reads from cache
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
    cprint("\n🔄 [bold cyan]By default 'include_raw_html' is set to True, which includes the raw HTML content in the response.[/bold cyan]", True)
    result = crawler.run(url="https://www.nbcnews.com/business", include_raw_html=False)
    cprint("[LOG] 📦 [bold yellow]Craw result  (without raw HTML content):[/bold yellow]")
    print_result(result)

    cprint("\n📄 The 'include_raw_html' parameter, when set to True, includes the raw HTML content in the response. By default is set to True. Let's move on to exploring different chunking strategies now!")
    
    cprint("For the rest of this guide, I set crawler.always_by_pass_cache to True to force the crawler to bypass the cache. This is to ensure that we get fresh results for each run.", True)
    crawler.always_by_pass_cache = True

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
    
    cprint("There are more chunking strategies to explore, make sure to check document, but let's move on to extraction strategies now!")

    # Adding an extraction strategy: CosineStrategy
    cprint("\n🧠 [bold cyan]Let's get smarter with an extraction strategy: CosineStrategy![/bold cyan]", True)
    cprint("CosineStrategy uses cosine similarity to extract semantically similar blocks of text. Let's see it in action!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=CosineStrategy(word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3)
    )
    cprint("[LOG] 📦 [bold yellow]CosineStrategy result:[/bold yellow]")
    print_result(result)
    
    cprint("You can pass other parameters like 'semantic_filter' to the CosineStrategy to extract semantically similar blocks of text. Let's see it in action!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=CosineStrategy(
            semantic_filter="inflation rent prices",
        )
    )

    cprint("[LOG] 📦 [bold yellow]CosineStrategy result with semantic filter:[/bold yellow]")
    print_result(result)    

    # Adding an LLM extraction strategy without instructions
    cprint("\n🤖 [bold cyan]Time to bring in the big guns: LLMExtractionStrategy without instructions![/bold cyan]", True)
    cprint("LLMExtractionStrategy uses a large language model to extract relevant information from the web page. Let's see it in action!")
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=LLMExtractionStrategy(provider="openai/gpt-4o", api_token=os.getenv('OPENAI_API_KEY'))
    )
    cprint("[LOG] 📦 [bold yellow]LLMExtractionStrategy (no instructions) result:[/bold yellow]")
    print_result(result)
    
    cprint("You can pass other providers like 'groq/llama3-70b-8192' or 'ollama/llama3' to the LLMExtractionStrategy.")

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
    
    cprint("You can pass other instructions like 'Extract only content related to technology' to the LLMExtractionStrategy.")
    
    cprint("There are more extraction strategies to explore, make sure to check the documentation!")

    # Using a CSS selector to extract only H2 tags
    cprint("\n🎯 [bold cyan]Targeted extraction: Let's use a CSS selector to extract only H2 tags![/bold cyan]", True)
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        css_selector="h2"
    )
    cprint("[LOG] 📦 [bold yellow]CSS Selector (H2 tags) result:[/bold yellow]")
    print_result(result)

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

    cprint("\n🎉 [bold green]Congratulations! You've made it through the Crawl4ai Quickstart Guide! Now go forth and crawl the web like a pro! 🕸️[/bold green]")

if __name__ == "__main__":
    main()

def old_main():    
    js_code = """const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"""
    # js_code = None
    crawler = WebCrawler( crawler_strategy=LocalSeleniumCrawlerStrategy(use_cached_html=False, js_code=js_code))
    crawler.warmup()
    # Single page crawl
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        word_count_threshold=5,  # Minimum word count for a HTML tag to be considered as a worthy block
        chunking_strategy=RegexChunking(patterns=["\n\n"]),  # Default is RegexChunking
        # extraction_strategy=CosineStrategy(word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3),  # Default is CosineStrategy
        extraction_strategy= LLMExtractionStrategy(provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY'), instruction = "I am intrested in only financial news"),
        bypass_cache=True,
        extract_blocks=True,  # Whether to extract semantical blocks of text from the HTML
        css_selector="",  # Eg: "div.article-body" or all H2 tags liek "h2"
        verbose=True,
        include_raw_html=True,  # Whether to include the raw HTML content in the response
    )
    

    print("[LOG] 📦 Crawl result:")
    print(result.model_dump())

