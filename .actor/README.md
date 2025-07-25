## 🔥🕷️ Crawl4AI: Crawl Smarter, Faster, Freely. For AI.

Crawl4AI is an Apify Actor that wraps the powerful [Crawl4AI](https://crawl4ai.com/) library, providing you with a feature-packed web crawler and scraper with additional functionalities like link-following and automatic retries for failed requests.

The Actor can:
- Crawl and scrape websites with precision using CSS, XPath, or LLM-based extraction methods.
- Generate clean Markdown output, suitable for RAG pipelines or direct ingestion into large language models.
- Automatically follow links to explore websites further without manual intervention.
- Retry failed requests to ensure maximum data collection with minimal effort.

## Usage
Scraping with Crawl4AI is straightforward. Just follow these steps to get your data quickly:

1. Input your target URLs.
2. Set your extraction method (optional - CSS, XPath, or LLM-based).
3. Configure advanced options like proxies or session settings (optional).
4. Run the Actor to start crawling, link-following, and retrying failed requests automatically.
5. Retrieve your data in structured Markdown format for further use in your projects.

## How much will it cost?
Apify provides $5 free usage credits every month on the [Apify Free plan](https://apify.com/pricing). With Crawl4AI, you can enjoy a certain number of results per month for free.

For larger data needs, consider upgrading to the [$49/month Starter plan](https://apify.com/pricing) for increased monthly results volume. Or opt for the [Scale plan](https://apify.com/pricing) for even higher result limits.

## Results
Here is an example of the data that the Actor produces:

```json
[{
  "url": "https://docs.crawl4ai.com/",
  "markdown": "https://api.apify.com/v2/key-value-stores/m1Sqnke1KWM0AI8co/records/content_4242424242.md",
  "html": "https://api.apify.com/v2/key-value-stores/m1Sqnke1KWM0AI8co/records/content_4242424242.html",
  "metadata": {
    "title": "Home - Crawl4AI Documentation (v0.5.x)",
    "description": "🚀🤖 Crawl4AI, Open-source LLM-Friendly Web Crawler & Scraper"
  }
},
{
  "url": "https://docs.crawl4ai.com/advanced/ssl-certificate/",
  "markdown": "https://api.apify.com/v2/key-value-stores/m1Sqnke1KWM0AI8co/records/content_4242424242.md",
  "html": "https://api.apify.com/v2/key-value-stores/m1Sqnke1KWM0AI8co/records/content_4242424242.html",
  "metadata": {
    "title": "SSL Certificate - Crawl4AI Documentation (v0.5.x)",
    "description": "🚀🤖 Crawl4AI, Open-source LLM-Friendly Web Crawler & Scraper"
  }
},
// ...
]
```
