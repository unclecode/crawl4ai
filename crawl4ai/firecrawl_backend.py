from firecrawl import Firecrawl

class FirecrawlBackend:
    def __init__(self, api_key: str):
        self.client = Firecrawl(api_key=api_key)

    def crawl(self, url: str, limit: int = 10):
        return self.client.crawl(url=url, limit=limit)

    def scrape(self, url: str):
        return self.client.scrape(url=url, formats=["markdown", "html"])

    def search(self, query: str):
        return self.client.search(query=query)
