from crawl4ai.hub import BaseCrawler

__meta__ = {
    "version": "1.2.0",
    "tested_on": ["amazon.com"],
    "rate_limit": "50 RPM",
    "schema": {"product": ["name", "price"]}
}

class AmazonProductCrawler(BaseCrawler):
    async def run(self, url: str, **kwargs) -> str:
        try:
            self.logger.info(f"Crawling {url}")
            return '{"product": {"name": "Test Amazon Product"}}'
        except Exception as e:
            self.logger.error(f"Crawl failed: {str(e)}")
            return json.dumps({
                "error": str(e),
                "metadata": self.meta  # Include meta in error response
            })            