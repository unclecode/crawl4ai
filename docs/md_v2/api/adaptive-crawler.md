# AdaptiveCrawler

The `AdaptiveCrawler` class implements intelligent web crawling that automatically determines when sufficient information has been gathered to answer a query. It uses a three-layer scoring system to evaluate coverage, consistency, and saturation.

## Constructor

```python
AdaptiveCrawler(
    crawler: AsyncWebCrawler,
    config: Optional[AdaptiveConfig] = None
)
```

### Parameters

- **crawler** (`AsyncWebCrawler`): The underlying web crawler instance to use for fetching pages
- **config** (`Optional[AdaptiveConfig]`): Configuration settings for adaptive crawling behavior. If not provided, uses default settings.

## Primary Method

### digest()

The main method that performs adaptive crawling starting from a URL with a specific query.

```python
async def digest(
    start_url: str,
    query: str,
    resume_from: Optional[Union[str, Path]] = None
) -> CrawlState
```

#### Parameters

- **start_url** (`str`): The starting URL for crawling
- **query** (`str`): The search query that guides the crawling process
- **resume_from** (`Optional[Union[str, Path]]`): Path to a saved state file to resume from

#### Returns

- **CrawlState**: The final crawl state containing all crawled URLs, knowledge base, and metrics

#### Example

```python
async with AsyncWebCrawler() as crawler:
    adaptive = AdaptiveCrawler(crawler)
    state = await adaptive.digest(
        start_url="https://docs.python.org",
        query="async context managers"
    )
```

## Properties

### confidence

Current confidence score (0-1) indicating information sufficiency.

```python
@property
def confidence(self) -> float
```

### coverage_stats

Dictionary containing detailed coverage statistics.

```python
@property  
def coverage_stats(self) -> Dict[str, float]
```

Returns:
- **coverage**: Query term coverage score
- **consistency**: Information consistency score  
- **saturation**: Content saturation score
- **confidence**: Overall confidence score

### is_sufficient

Boolean indicating whether sufficient information has been gathered.

```python
@property
def is_sufficient(self) -> bool
```

### state

Access to the current crawl state.

```python
@property
def state(self) -> CrawlState
```

## Methods

### get_relevant_content()

Retrieve the most relevant content from the knowledge base.

```python
def get_relevant_content(
    self,
    top_k: int = 5
) -> List[Dict[str, Any]]
```

#### Parameters

- **top_k** (`int`): Number of top relevant documents to return (default: 5)

#### Returns

List of dictionaries containing:
- **url**: The URL of the page
- **content**: The page content
- **score**: Relevance score
- **metadata**: Additional page metadata

### print_stats()

Display crawl statistics in formatted output.

```python
def print_stats(
    self,
    detailed: bool = False
) -> None
```

#### Parameters

- **detailed** (`bool`): If True, shows detailed metrics with colors. If False, shows summary table.

### export_knowledge_base()

Export the collected knowledge base to a JSONL file.

```python
def export_knowledge_base(
    self,
    path: Union[str, Path]
) -> None
```

#### Parameters

- **path** (`Union[str, Path]`): Output file path for JSONL export

#### Example

```python
adaptive.export_knowledge_base("my_knowledge.jsonl")
```

### import_knowledge_base()

Import a previously exported knowledge base.

```python
def import_knowledge_base(
    self,
    path: Union[str, Path]
) -> None
```

#### Parameters

- **path** (`Union[str, Path]`): Path to JSONL file to import

## Configuration

The `AdaptiveConfig` class controls the behavior of adaptive crawling:

```python
@dataclass
class AdaptiveConfig:
    confidence_threshold: float = 0.8      # Stop when confidence reaches this
    max_pages: int = 50                    # Maximum pages to crawl
    top_k_links: int = 5                   # Links to follow per page
    min_gain_threshold: float = 0.1        # Minimum expected gain to continue
    save_state: bool = False               # Auto-save crawl state
    state_path: Optional[str] = None       # Path for state persistence
```

### Example with Custom Config

```python
config = AdaptiveConfig(
    confidence_threshold=0.7,
    max_pages=20,
    top_k_links=3
)

adaptive = AdaptiveCrawler(crawler, config=config)
```

## Complete Example

```python
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
```

## See Also

- [digest() Method Reference](digest.md)
- [Adaptive Crawling Guide](../core/adaptive-crawling.md)
- [Advanced Adaptive Strategies](../advanced/adaptive-strategies.md)