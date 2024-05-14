import os
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *


def main():
    crawler = WebCrawler()
    crawler.warmup()
    
    # Single page crawl
    result = crawler.run(
        url="https://www.nbcnews.com/business",
        word_count_threshold=5,  # Minimum word count for a HTML tag to be considered as a worthy block
        chunking_strategy=RegexChunking(patterns=["\n\n"]),  # Default is RegexChunking
        extraction_strategy=CosineStrategy(
            word_count_threshold=20, max_dist=0.2, linkage_method="ward", top_k=3
        ),  # Default is CosineStrategy
        # extraction_strategy= LLMExtractionStrategy(provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY')),
        bypass_cache=True,
        extract_blocks=True,  # Whether to extract semantical blocks of text from the HTML
        css_selector="",  # Eg: "div.article-body" or all H2 tags liek "h2"
        verbose=True,
        include_raw_html=True,  # Whether to include the raw HTML content in the response
    )
    

    print("[LOG] 📦 Crawl result:")
    print(result.model_dump())


if __name__ == "__main__":
    main()
