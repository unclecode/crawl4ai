[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/api/adaptive-crawler/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [AdaptiveCrawler](https://docs.crawl4ai.com/api/adaptive-crawler/#adaptivecrawler)
  * [Constructor](https://docs.crawl4ai.com/api/adaptive-crawler/#constructor)
  * [Primary Method](https://docs.crawl4ai.com/api/adaptive-crawler/#primary-method)
  * [Properties](https://docs.crawl4ai.com/api/adaptive-crawler/#properties)
  * [Methods](https://docs.crawl4ai.com/api/adaptive-crawler/#methods)
  * [Configuration](https://docs.crawl4ai.com/api/adaptive-crawler/#configuration)
  * [Complete Example](https://docs.crawl4ai.com/api/adaptive-crawler/#complete-example)
  * [See Also](https://docs.crawl4ai.com/api/adaptive-crawler/#see-also)


# AdaptiveCrawler
The `AdaptiveCrawler` class implements intelligent web crawling that automatically determines when sufficient information has been gathered to answer a query. It uses a three-layer scoring system to evaluate coverage, consistency, and saturation.
## Constructor
```
AdaptiveCrawler(
    crawler: AsyncWebCrawler,
    config: Optional[AdaptiveConfig] = None
)
Copy
```

### Parameters
  * **crawler** (`AsyncWebCrawler`): The underlying web crawler instance to use for fetching pages
  * **config** (`Optional[AdaptiveConfig]`): Configuration settings for adaptive crawling behavior. If not provided, uses default settings.


## Primary Method
### digest()
The main method that performs adaptive crawling starting from a URL with a specific query.
```
async def digest(
    start_url: str,
    query: str,
    resume_from: Optional[Union[str, Path]] = None
) -> CrawlState
Copy
```

#### Parameters
  * **start_url** (`str`): The starting URL for crawling
  * **query** (`str`): The search query that guides the crawling process
  * **resume_from** (`Optional[Union[str, Path]]`): Path to a saved state file to resume from


#### Returns
  * **CrawlState** : The final crawl state containing all crawled URLs, knowledge base, and metrics


#### Example
```
async with AsyncWebCrawler() as crawler:
    adaptive = AdaptiveCrawler(crawler)
    state = await adaptive.digest(
        start_url="https://docs.python.org",
        query="async context managers"
    )
Copy
```

## Properties
### confidence
Current confidence score (0-1) indicating information sufficiency.
```
@property
def confidence(self) -> float
Copy
```

### coverage_stats
Dictionary containing detailed coverage statistics.
```
@property
def coverage_stats(self) -> Dict[str, float]
Copy
```

Returns: - **coverage** : Query term coverage score - **consistency** : Information consistency score
- **saturation** : Content saturation score - **confidence** : Overall confidence score
### is_sufficient
Boolean indicating whether sufficient information has been gathered.
```
@property
def is_sufficient(self) -> bool
Copy
```

### state
Access to the current crawl state.
```
@property
def state(self) -> CrawlState
Copy
```

## Methods
### get_relevant_content()
Retrieve the most relevant content from the knowledge base.
```
def get_relevant_content(
    self,
    top_k: int = 5
) -> List[Dict[str, Any]]
Copy
```

#### Parameters
  * **top_k** (`int`): Number of top relevant documents to return (default: 5)


#### Returns
List of dictionaries containing: - **url** : The URL of the page - **content** : The page content - **score** : Relevance score - **metadata** : Additional page metadata
### print_stats()
Display crawl statistics in formatted output.
```
def print_stats(
    self,
    detailed: bool = False
) -> None
Copy
```

#### Parameters
  * **detailed** (`bool`): If True, shows detailed metrics with colors. If False, shows summary table.


### export_knowledge_base()
Export the collected knowledge base to a JSONL file.
```
def export_knowledge_base(
    self,
    path: Union[str, Path]
) -> None
Copy
```

#### Parameters
  * **path** (`Union[str, Path]`): Output file path for JSONL export


#### Example
```
adaptive.export_knowledge_base("my_knowledge.jsonl")
Copy
```

### import_knowledge_base()
Import a previously exported knowledge base.
```
def import_knowledge_base(
    self,
    path: Union[str, Path]
) -> None
Copy
```

#### Parameters
  * **path** (`Union[str, Path]`): Path to JSONL file to import


## Configuration
The `AdaptiveConfig` class controls the behavior of adaptive crawling:
```
@dataclass
class AdaptiveConfig:
    confidence_threshold: float = 0.8      # Stop when confidence reaches this
    max_pages: int = 50                    # Maximum pages to crawl
    top_k_links: int = 5                   # Links to follow per page
    min_gain_threshold: float = 0.1        # Minimum expected gain to continue
    save_state: bool = False               # Auto-save crawl state
    state_path: Optional[str] = None       # Path for state persistence
Copy
```

### Example with Custom Config
```
config = AdaptiveConfig(
    confidence_threshold=0.7,
    max_pages=20,
    top_k_links=3
)

adaptive = AdaptiveCrawler(crawler, config=config)
Copy
```

## Complete Example
```
import asyncio
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig

async def main():
    # Configure adaptive crawling
    config = AdaptiveConfig(
        confidence_threshold=0.75,
        max_pages=15,
        save_state=True,
        state_path="my_crawl.json"
    )

    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler, config)

        # Start crawling
        state = await adaptive.digest(
            start_url="https://example.com/docs",
            query="authentication oauth2 jwt"
        )

        # Check results
        print(f"Confidence achieved: {adaptive.confidence:.0%}")
        adaptive.print_stats()

        # Get most relevant pages
        for page in adaptive.get_relevant_content(top_k=3):
            print(f"- {page['url']} (score: {page['score']:.2f})")

        # Export for later use
        adaptive.export_knowledge_base("auth_knowledge.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

## See Also
  * [digest() Method Reference](https://docs.crawl4ai.com/api/digest/)
  * [Adaptive Crawling Guide](https://docs.crawl4ai.com/core/adaptive-crawling/)
  * [Advanced Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)


#### On this page
  * [Constructor](https://docs.crawl4ai.com/api/adaptive-crawler/#constructor)
  * [Parameters](https://docs.crawl4ai.com/api/adaptive-crawler/#parameters)
  * [Primary Method](https://docs.crawl4ai.com/api/adaptive-crawler/#primary-method)
  * [digest()](https://docs.crawl4ai.com/api/adaptive-crawler/#digest)
  * [Parameters](https://docs.crawl4ai.com/api/adaptive-crawler/#parameters_1)
  * [Returns](https://docs.crawl4ai.com/api/adaptive-crawler/#returns)
  * [Example](https://docs.crawl4ai.com/api/adaptive-crawler/#example)
  * [Properties](https://docs.crawl4ai.com/api/adaptive-crawler/#properties)
  * [confidence](https://docs.crawl4ai.com/api/adaptive-crawler/#confidence)
  * [coverage_stats](https://docs.crawl4ai.com/api/adaptive-crawler/#coverage_stats)
  * [is_sufficient](https://docs.crawl4ai.com/api/adaptive-crawler/#is_sufficient)
  * [state](https://docs.crawl4ai.com/api/adaptive-crawler/#state)
  * [Methods](https://docs.crawl4ai.com/api/adaptive-crawler/#methods)
  * [get_relevant_content()](https://docs.crawl4ai.com/api/adaptive-crawler/#get_relevant_content)
  * [Parameters](https://docs.crawl4ai.com/api/adaptive-crawler/#parameters_2)
  * [Returns](https://docs.crawl4ai.com/api/adaptive-crawler/#returns_1)
  * [print_stats()](https://docs.crawl4ai.com/api/adaptive-crawler/#print_stats)
  * [Parameters](https://docs.crawl4ai.com/api/adaptive-crawler/#parameters_3)
  * [export_knowledge_base()](https://docs.crawl4ai.com/api/adaptive-crawler/#export_knowledge_base)
  * [Parameters](https://docs.crawl4ai.com/api/adaptive-crawler/#parameters_4)
  * [Example](https://docs.crawl4ai.com/api/adaptive-crawler/#example_1)
  * [import_knowledge_base()](https://docs.crawl4ai.com/api/adaptive-crawler/#import_knowledge_base)
  * [Parameters](https://docs.crawl4ai.com/api/adaptive-crawler/#parameters_5)
  * [Configuration](https://docs.crawl4ai.com/api/adaptive-crawler/#configuration)
  * [Example with Custom Config](https://docs.crawl4ai.com/api/adaptive-crawler/#example-with-custom-config)
  * [Complete Example](https://docs.crawl4ai.com/api/adaptive-crawler/#complete-example)
  * [See Also](https://docs.crawl4ai.com/api/adaptive-crawler/#see-also)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
