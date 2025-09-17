from crawl4ai.firecrawl_backend import FirecrawlBackend


def main():
    backend = FirecrawlBackend(api_key="fc-fa43e06d8c1348b58200a39911a4ae9c")
    docs = backend.scrape("https://docs.firecrawl.dev")
    print(docs)

if __name__ == "__main__":
    main()
