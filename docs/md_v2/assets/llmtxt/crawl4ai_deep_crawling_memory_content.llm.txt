Okay, I have read and processed the information. I will now generate the detailed "Foundational Memory" document for the `deep_crawling` component of `crawl4ai`, based on the outline from the previous step and the provided code snippets.

```markdown
# Detailed Foundational Memory for crawl4ai - deep_crawling Component

**Target Document Type:** memory
**Target Output Filename Suggestion:** `llm_memory_deep_crawling.md`
**Library Version Context:** 0.6.3 (from `crawl4ai/__version__.py`)
**Outline Generation Date:** 2024-05-24
---

## 1. Introduction to Deep Crawling

*   1.1. Purpose: The `deep_crawling` component provides functionalities for recursively crawling web pages starting from an initial URL. It includes strategies for different traversal orders (BFS, DFS, Best-First), mechanisms for filtering which URLs to visit, and methods for scoring URLs to prioritize crawling.
*   1.2. Core Concepts:
    *   1.2.1. Definition of Deep Crawling in Crawl4ai context: The process of discovering and fetching multiple web pages by following links from an initial set of URLs, adhering to specified depth, page limits, and filtering/scoring rules.
    *   1.2.2. Key Abstractions:
        *   `DeepCrawlStrategy`: Defines the algorithm for traversing linked web pages (e.g., BFS, DFS).
        *   `URLFilter`: Determines whether a discovered URL should be considered for crawling.
        *   `URLScorer`: Assigns a score to URLs to influence crawling priority, especially in strategies like Best-First.

## 2. `DeepCrawlStrategy` Interface and Implementations

*   **2.1. `DeepCrawlStrategy` (Abstract Base Class)**
    *   Source: `crawl4ai/deep_crawling/base_strategy.py`
    *   2.1.1. Purpose: Defines the abstract base class for all deep crawling strategies, outlining the core methods required for traversal logic, resource management, URL validation, and link discovery.
    *   2.1.2. Key Abstract Methods:
        *   `async def _arun_batch(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> List[CrawlResult]`:
            *   Description: Core logic for batch (non-streaming) deep crawling. Processes URLs level by level (or according to strategy) and returns all results once the crawl is complete or limits are met.
        *   `async def _arun_stream(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> AsyncGenerator[CrawlResult, None]`:
            *   Description: Core logic for streaming deep crawling. Processes URLs and yields `CrawlResult` objects as they become available.
        *   `async def shutdown(self) -> None`:
            *   Description: Cleans up any resources used by the deep crawl strategy, such as signaling cancellation events.
        *   `async def can_process_url(self, url: str, depth: int) -> bool`:
            *   Description: Validates a given URL and current depth against configured filters and limits to decide if it should be processed.
        *   `async def link_discovery(self, result: CrawlResult, source_url: str, current_depth: int, visited: Set[str], next_level: List[tuple], depths: Dict[str, int]) -> None`:
            *   Description: Extracts links from a `CrawlResult`, validates them using `can_process_url`, optionally scores them, and appends valid URLs (and their parent references) to the `next_level` list. Updates the `depths` dictionary for newly discovered URLs.
    *   2.1.3. Key Concrete Methods:
        *   `async def arun(self, start_url: str, crawler: AsyncWebCrawler, config: Optional[CrawlerRunConfig] = None) -> RunManyReturn`:
            *   Description: Main entry point for initiating a deep crawl. It checks if a `CrawlerRunConfig` is provided and then delegates to either `_arun_stream` or `_arun_batch` based on the `config.stream` flag.
        *   `def __call__(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig)`:
            *   Description: Makes the strategy instance callable, directly invoking the `arun` method.
    *   2.1.4. Attributes:
        *   `_cancel_event (asyncio.Event)`: Event to signal cancellation of the crawl.
        *   `_pages_crawled (int)`: Counter for the number of pages successfully crawled.

*   **2.2. `BFSDeepCrawlStrategy`**
    *   Source: `crawl4ai/deep_crawling/bfs_strategy.py`
    *   2.2.1. Purpose: Implements a Breadth-First Search (BFS) deep crawling strategy, exploring all URLs at the current depth level before moving to the next.
    *   2.2.2. Inheritance: `DeepCrawlStrategy`
    *   2.2.3. Initialization (`__init__`)
        *   2.2.3.1. Signature:
            ```python
            def __init__(
                self,
                max_depth: int,
                filter_chain: FilterChain = FilterChain(),
                url_scorer: Optional[URLScorer] = None,
                include_external: bool = False,
                score_threshold: float = -float('inf'),
                max_pages: int = float('inf'),
                logger: Optional[logging.Logger] = None,
            ):
            ```
        *   2.2.3.2. Parameters:
            *   `max_depth (int)`: Maximum depth to crawl relative to the `start_url`.
            *   `filter_chain (FilterChain`, default: `FilterChain()`)`: A `FilterChain` instance to apply to discovered URLs.
            *   `url_scorer (Optional[URLScorer]`, default: `None`)`: An optional `URLScorer` to score URLs. If provided, URLs below `score_threshold` are skipped, and for crawls exceeding `max_pages`, higher-scored URLs are prioritized.
            *   `include_external (bool`, default: `False`)`: If `True`, allows crawling of URLs from external domains.
            *   `score_threshold (float`, default: `-float('inf')`)`: Minimum score (if `url_scorer` is used) for a URL to be processed.
            *   `max_pages (int`, default: `float('inf')`)`: Maximum total number of pages to crawl.
            *   `logger (Optional[logging.Logger]`, default: `None`)`: An optional logger instance. If `None`, a default logger is created.
    *   2.2.4. Key Implemented Methods:
        *   `_arun_batch(...)`: Implements BFS traversal by processing URLs level by level. It collects all results from a level before discovering links for the next level. All results are returned as a list upon completion.
        *   `_arun_stream(...)`: Implements BFS traversal, yielding `CrawlResult` objects as soon as they are processed within a level. Link discovery for the next level happens after all URLs in the current level are processed and their results yielded.
        *   `can_process_url(...)`: Validates URL format, applies the `filter_chain`, and checks depth limits. For the start URL (depth 0), filtering is bypassed.
        *   `link_discovery(...)`: Extracts internal (and optionally external) links, normalizes them, checks against `visited` set and `can_process_url`. If a `url_scorer` is present and `max_pages` limit is a concern, it scores and sorts valid links, selecting the top ones within `remaining_capacity`.
        *   `shutdown(...)`: Sets an internal `_cancel_event` to signal graceful termination and records the end time in `stats`.
    *   2.2.5. Key Attributes/Properties:
        *   `stats (TraversalStats)`: [Read-only] - Instance of `TraversalStats` tracking the progress and statistics of the crawl.
        *   `max_depth (int)`: Maximum crawl depth.
        *   `filter_chain (FilterChain)`: The filter chain used.
        *   `url_scorer (Optional[URLScorer])`: The URL scorer used.
        *   `include_external (bool)`: Flag for including external URLs.
        *   `score_threshold (float)`: URL score threshold.
        *   `max_pages (int)`: Maximum pages to crawl.

*   **2.3. `DFSDeepCrawlStrategy`**
    *   Source: `crawl4ai/deep_crawling/dfs_strategy.py`
    *   2.3.1. Purpose: Implements a Depth-First Search (DFS) deep crawling strategy, exploring as far as possible along each branch before backtracking.
    *   2.3.2. Inheritance: `BFSDeepCrawlStrategy` (Note: Leverages much of the `BFSDeepCrawlStrategy`'s infrastructure but overrides traversal logic to use a stack.)
    *   2.3.3. Initialization (`__init__`)
        *   2.3.3.1. Signature: (Same as `BFSDeepCrawlStrategy`)
            ```python
            def __init__(
                self,
                max_depth: int,
                filter_chain: FilterChain = FilterChain(),
                url_scorer: Optional[URLScorer] = None,
                include_external: bool = False,
                score_threshold: float = -float('inf'),
                max_pages: int = infinity,
                logger: Optional[logging.Logger] = None,
            ):
            ```
        *   2.3.3.2. Parameters: Same as `BFSDeepCrawlStrategy`.
    *   2.3.4. Key Overridden/Implemented Methods:
        *   `_arun_batch(...)`: Implements DFS traversal using a LIFO stack. Processes one URL at a time, discovers its links, and adds them to the stack (typically in reverse order of discovery to maintain a natural DFS path). Collects all results in a list.
        *   `_arun_stream(...)`: Implements DFS traversal using a LIFO stack, yielding `CrawlResult` for each processed URL as it becomes available. Discovered links are added to the stack for subsequent processing.

*   **2.4. `BestFirstCrawlingStrategy`**
    *   Source: `crawl4ai/deep_crawling/bff_strategy.py`
    *   2.4.1. Purpose: Implements a Best-First Search deep crawling strategy, prioritizing URLs based on scores assigned by a `URLScorer`. It uses a priority queue to manage URLs to visit.
    *   2.4.2. Inheritance: `DeepCrawlStrategy`
    *   2.4.3. Initialization (`__init__`)
        *   2.4.3.1. Signature:
            ```python
            def __init__(
                self,
                max_depth: int,
                filter_chain: FilterChain = FilterChain(),
                url_scorer: Optional[URLScorer] = None,
                include_external: bool = False,
                max_pages: int = float('inf'),
                logger: Optional[logging.Logger] = None,
            ):
            ```
        *   2.4.3.2. Parameters:
            *   `max_depth (int)`: Maximum depth to crawl.
            *   `filter_chain (FilterChain`, default: `FilterChain()`)`: Chain of filters to apply.
            *   `url_scorer (Optional[URLScorer]`, default: `None`)`: Scorer to rank URLs. Crucial for this strategy; if not provided, URLs might effectively be processed in FIFO order (score 0).
            *   `include_external (bool`, default: `False`)`: Whether to include external links.
            *   `max_pages (int`, default: `float('inf')`)`: Maximum number of pages to crawl.
            *   `logger (Optional[logging.Logger]`, default: `None`)`: Logger instance.
    *   2.4.4. Key Implemented Methods:
        *   `_arun_batch(...)`: Aggregates results from `_arun_best_first` into a list.
        *   `_arun_stream(...)`: Yields results from `_arun_best_first` as they are generated.
        *   `_arun_best_first(...)`: Core logic for best-first traversal. Uses an `asyncio.PriorityQueue` where items are `(score, depth, url, parent_url)`. URLs are processed in batches (default size 10) from the priority queue. Discovered links are scored and added to the queue.
    *   2.4.5. Key Attributes/Properties:
        *   `stats (TraversalStats)`: [Read-only] - Traversal statistics object.
        *   `BATCH_SIZE (int)`: [Class constant, default: 10] - Number of URLs to process concurrently from the priority queue.

## 3. URL Filtering Mechanisms

*   **3.1. `URLFilter` (Abstract Base Class)**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.1.1. Purpose: Defines the abstract base class for all URL filters, providing a common interface for deciding whether a URL should be processed.
    *   3.1.2. Key Abstract Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Abstract method that must be implemented by subclasses. It takes a URL string and returns `True` if the URL passes the filter (should be processed), and `False` otherwise.
    *   3.1.3. Key Attributes/Properties:
        *   `name (str)`: [Read-only] - The name of the filter, typically the class name.
        *   `stats (FilterStats)`: [Read-only] - An instance of `FilterStats` to track how many URLs were processed, passed, and rejected by this filter.
        *   `logger (logging.Logger)`: [Read-only] - A logger instance specific to this filter, initialized lazily.
    *   3.1.4. Key Concrete Methods:
        *   `_update_stats(self, passed: bool) -> None`: Updates the `stats` object (total, passed, rejected counts).

*   **3.2. `FilterChain`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.2.1. Purpose: Manages a sequence of `URLFilter` instances. A URL must pass all filters in the chain to be considered valid.
    *   3.2.2. Initialization (`__init__`)
        *   3.2.2.1. Signature:
            ```python
            def __init__(self, filters: List[URLFilter] = None):
            ```
        *   3.2.2.2. Parameters:
            *   `filters (List[URLFilter]`, default: `None`)`: An optional list of `URLFilter` instances to initialize the chain with. If `None`, an empty chain is created.
    *   3.2.3. Key Public Methods:
        *   `add_filter(self, filter_: URLFilter) -> FilterChain`:
            *   Description: Adds a new `URLFilter` instance to the end of the chain.
            *   Returns: `(FilterChain)` - The `FilterChain` instance itself, allowing for method chaining.
        *   `async def apply(self, url: str) -> bool`:
            *   Description: Applies each filter in the chain to the given URL. If any filter returns `False` (rejects the URL), this method immediately returns `False`. If all filters pass, it returns `True`. Handles both synchronous and asynchronous `apply` methods of individual filters.
            *   Returns: `(bool)` - `True` if the URL passes all filters, `False` otherwise.
    *   3.2.4. Key Attributes/Properties:
        *   `filters (Tuple[URLFilter, ...])`: [Read-only] - An immutable tuple containing the `URLFilter` instances in the chain.
        *   `stats (FilterStats)`: [Read-only] - An instance of `FilterStats` tracking the aggregated statistics for the entire chain (total URLs processed, passed, and rejected by the chain as a whole).

*   **3.3. `URLPatternFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.3.1. Purpose: Filters URLs based on whether they match a list of specified string patterns. Supports glob-style wildcards and regular expressions.
    *   3.3.2. Inheritance: `URLFilter`
    *   3.3.3. Initialization (`__init__`)
        *   3.3.3.1. Signature:
            ```python
            def __init__(
                self,
                patterns: Union[str, Pattern, List[Union[str, Pattern]]],
                use_glob: bool = True, # Deprecated, glob is always used for strings if not regex
                reverse: bool = False,
            ):
            ```
        *   3.3.3.2. Parameters:
            *   `patterns (Union[str, Pattern, List[Union[str, Pattern]]])`: A single pattern string/compiled regex, or a list of such patterns. String patterns are treated as glob patterns by default unless they are identifiable as regex (e.g., start with `^`, end with `$`, contain `\d`).
            *   `use_glob (bool`, default: `True`)`: [Deprecated] This parameter's functionality is now implicitly handled by pattern detection.
            *   `reverse (bool`, default: `False`)`: If `True`, the filter rejects URLs that match any of the patterns. If `False` (default), it accepts URLs that match any pattern and rejects those that don't match any.
    *   3.3.4. Key Implemented Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Checks if the URL matches any of the configured patterns. Simple suffix/prefix/domain patterns are checked first for performance. For more complex patterns, it uses `fnmatch.translate` (for glob-like strings) or compiled regex objects. The outcome is affected by the `reverse` flag.
    *   3.3.5. Internal Categorization:
        *   `PATTERN_TYPES`: A dictionary mapping pattern types (SUFFIX, PREFIX, DOMAIN, PATH, REGEX) to integer constants.
        *   `_simple_suffixes (Set[str])`: Stores simple suffix patterns (e.g., `.html`).
        *   `_simple_prefixes (Set[str])`: Stores simple prefix patterns (e.g., `/blog/`).
        *   `_domain_patterns (List[Pattern])`: Stores compiled regex for domain-specific patterns (e.g., `*.example.com`).
        *   `_path_patterns (List[Pattern])`: Stores compiled regex for more general path patterns.

*   **3.4. `ContentTypeFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.4.1. Purpose: Filters URLs based on their expected content type, primarily by inferring it from the file extension in the URL.
    *   3.4.2. Inheritance: `URLFilter`
    *   3.4.3. Initialization (`__init__`)
        *   3.4.3.1. Signature:
            ```python
            def __init__(
                self,
                allowed_types: Union[str, List[str]],
                check_extension: bool = True,
                ext_map: Dict[str, str] = _MIME_MAP, # _MIME_MAP is internal
            ):
            ```
        *   3.4.3.2. Parameters:
            *   `allowed_types (Union[str, List[str]])`: A single MIME type string (e.g., "text/html") or a list of allowed MIME types. Can also be partial types like "image/" to allow all image types.
            *   `check_extension (bool`, default: `True`)`: If `True` (default), the filter attempts to determine the content type by looking at the URL's file extension. If `False`, all URLs pass this filter (unless `allowed_types` is empty).
            *   `ext_map (Dict[str, str]`, default: `ContentTypeFilter._MIME_MAP`)`: A dictionary mapping file extensions to their corresponding MIME types. A comprehensive default map is provided.
    *   3.4.4. Key Implemented Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Extracts the file extension from the URL. If `check_extension` is `True` and an extension is found, it checks if the inferred MIME type (or the extension itself if MIME type is unknown) is among the `allowed_types`. If no extension is found, it typically allows the URL (assuming it might be an HTML page or similar).
    *   3.4.5. Static Methods:
        *   `_extract_extension(url: str) -> str`: [Cached] Extracts the file extension from a URL path, handling query parameters and fragments.
    *   3.4.6. Class Variables:
        *   `_MIME_MAP (Dict[str, str])`: A class-level dictionary mapping common file extensions to MIME types.

*   **3.5. `DomainFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.5.1. Purpose: Filters URLs based on a whitelist of allowed domains or a blacklist of blocked domains. Supports subdomain matching.
    *   3.5.2. Inheritance: `URLFilter`
    *   3.5.3. Initialization (`__init__`)
        *   3.5.3.1. Signature:
            ```python
            def __init__(
                self,
                allowed_domains: Union[str, List[str]] = None,
                blocked_domains: Union[str, List[str]] = None,
            ):
            ```
        *   3.5.3.2. Parameters:
            *   `allowed_domains (Union[str, List[str]]`, default: `None`)`: A single domain string or a list of domain strings. If provided, only URLs whose domain (or a subdomain thereof) is in this list will pass.
            *   `blocked_domains (Union[str, List[str]]`, default: `None`)`: A single domain string or a list of domain strings. URLs whose domain (or a subdomain thereof) is in this list will be rejected.
    *   3.5.4. Key Implemented Methods:
        *   `apply(self, url: str) -> bool`:
            *   Description: Extracts the domain from the URL. First, checks if the domain is in `_blocked_domains` (rejects if true). Then, if `_allowed_domains` is specified, checks if the domain is in that list (accepts if true). If `_allowed_domains` is not specified and the URL was not blocked, it passes.
    *   3.5.5. Static Methods:
        *   `_normalize_domains(domains: Union[str, List[str]]) -> Set[str]`: Converts input domains to a set of lowercase strings.
        *   `_is_subdomain(domain: str, parent_domain: str) -> bool`: Checks if `domain` is a subdomain of (or equal to) `parent_domain`.
        *   `_extract_domain(url: str) -> str`: [Cached] Extracts the domain name from a URL.

*   **3.6. `ContentRelevanceFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.6.1. Purpose: Filters URLs by fetching their `<head>` section, extracting text content (title, meta tags), and scoring its relevance against a given query using the BM25 algorithm.
    *   3.6.2. Inheritance: `URLFilter`
    *   3.6.3. Initialization (`__init__`)
        *   3.6.3.1. Signature:
            ```python
            def __init__(
                self,
                query: str,
                threshold: float,
                k1: float = 1.2,
                b: float = 0.75,
                avgdl: int = 1000,
            ):
            ```
        *   3.6.3.2. Parameters:
            *   `query (str)`: The query string to assess relevance against.
            *   `threshold (float)`: The minimum BM25 score required for the URL to be considered relevant and pass the filter.
            *   `k1 (float`, default: `1.2`)`: BM25 k1 parameter (term frequency saturation).
            *   `b (float`, default: `0.75`)`: BM25 b parameter (length normalization).
            *   `avgdl (int`, default: `1000`)`: Assumed average document length for BM25 calculations (typically based on the head content).
    *   3.6.4. Key Implemented Methods:
        *   `async def apply(self, url: str) -> bool`:
            *   Description: Asynchronously fetches the HTML `<head>` content of the URL using `HeadPeeker.peek_html`. Extracts title and meta description/keywords. Calculates the BM25 score of this combined text against the `query`. Returns `True` if the score is >= `threshold`.
    *   3.6.5. Helper Methods:
        *   `_build_document(self, fields: Dict) -> str`: Constructs a weighted document string from title and meta tags.
        *   `_tokenize(self, text: str) -> List[str]`: Simple whitespace tokenizer.
        *   `_bm25(self, document: str) -> float`: Calculates the BM25 score.

*   **3.7. `SEOFilter`**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.7.1. Purpose: Filters URLs by performing a quantitative SEO quality assessment based on the content of their `<head>` section (e.g., title length, meta description presence, canonical tags, robots meta tags, schema.org markup).
    *   3.7.2. Inheritance: `URLFilter`
    *   3.7.3. Initialization (`__init__`)
        *   3.7.3.1. Signature:
            ```python
            def __init__(
                self,
                threshold: float = 0.65,
                keywords: List[str] = None,
                weights: Dict[str, float] = None,
            ):
            ```
        *   3.7.3.2. Parameters:
            *   `threshold (float`, default: `0.65`)`: The minimum aggregated SEO score (typically 0.0 to 1.0 range, though individual factor weights can exceed 1) required for the URL to pass.
            *   `keywords (List[str]`, default: `None`)`: A list of keywords to check for presence in the title.
            *   `weights (Dict[str, float]`, default: `None`)`: A dictionary to override default weights for various SEO factors (e.g., `{"title_length": 0.2, "canonical": 0.15}`).
    *   3.7.4. Key Implemented Methods:
        *   `async def apply(self, url: str) -> bool`:
            *   Description: Asynchronously fetches the HTML `<head>` content. Calculates scores for individual SEO factors (title length, keyword presence, meta description, canonical tag, robots meta tag, schema.org presence, URL quality). Aggregates these scores using the defined `weights`. Returns `True` if the total score is >= `threshold`.
    *   3.7.5. Helper Methods (Scoring Factors):
        *   `_score_title_length(self, title: str) -> float`
        *   `_score_keyword_presence(self, text: str) -> float`
        *   `_score_meta_description(self, desc: str) -> float`
        *   `_score_canonical(self, canonical: str, original: str) -> float`
        *   `_score_schema_org(self, html: str) -> float`
        *   `_score_url_quality(self, parsed_url) -> float`
    *   3.7.6. Class Variables:
        *   `DEFAULT_WEIGHTS (Dict[str, float])`: Default weights for each SEO factor.

*   **3.8. `FilterStats` Data Class**
    *   Source: `crawl4ai/deep_crawling/filters.py`
    *   3.8.1. Purpose: A data class to track statistics for URL filtering operations, including total URLs processed, passed, and rejected.
    *   3.8.2. Fields:
        *   `_counters (array.array)`: An array of unsigned integers storing counts for `[total, passed, rejected]`.
    *   3.8.3. Properties:
        *   `total_urls (int)`: Returns the total number of URLs processed.
        *   `passed_urls (int)`: Returns the number of URLs that passed the filter.
        *   `rejected_urls (int)`: Returns the number of URLs that were rejected.

## 4. URL Scoring Mechanisms

*   **4.1. `URLScorer` (Abstract Base Class)**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.1.1. Purpose: Defines the abstract base class for all URL scorers. Scorers assign a numerical value to URLs, which can be used to prioritize crawling.
    *   4.1.2. Key Abstract Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Abstract method to be implemented by subclasses. It takes a URL string and returns a raw numerical score.
    *   4.1.3. Key Concrete Methods:
        *   `score(self, url: str) -> float`:
            *   Description: Calculates the final score for a URL by calling `_calculate_score` and multiplying the result by the scorer's `weight`. It also updates the internal `ScoringStats`.
            *   Returns: `(float)` - The weighted score.
    *   4.1.4. Key Attributes/Properties:
        *   `weight (ctypes.c_float)`: [Read-write] - The weight assigned to this scorer. The raw score calculated by `_calculate_score` will be multiplied by this weight. Default is 1.0. Stored as `ctypes.c_float` for memory efficiency.
        *   `stats (ScoringStats)`: [Read-only] - An instance of `ScoringStats` that tracks statistics for this scorer (number of URLs scored, total score, min/max scores).

*   **4.2. `KeywordRelevanceScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.2.1. Purpose: Scores URLs based on the presence and frequency of specified keywords within the URL string itself.
    *   4.2.2. Inheritance: `URLScorer`
    *   4.2.3. Initialization (`__init__`)
        *   4.2.3.1. Signature:
            ```python
            def __init__(self, keywords: List[str], weight: float = 1.0, case_sensitive: bool = False):
            ```
        *   4.2.3.2. Parameters:
            *   `keywords (List[str])`: A list of keyword strings to search for in the URL.
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
            *   `case_sensitive (bool`, default: `False`)`: If `True`, keyword matching is case-sensitive. Otherwise, both the URL and keywords are converted to lowercase for matching.
    *   4.2.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Counts how many of the provided `keywords` are present in the `url`. The score is the ratio of matched keywords to the total number of keywords (0.0 to 1.0).
    *   4.2.5. Helper Methods:
        *   `_url_bytes(self, url: str) -> bytes`: [Cached] Converts URL to bytes, lowercasing if not case-sensitive.

*   **4.3. `PathDepthScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.3.1. Purpose: Scores URLs based on their path depth (number of segments in the URL path). It favors URLs closer to an `optimal_depth`.
    *   4.3.2. Inheritance: `URLScorer`
    *   4.3.3. Initialization (`__init__`)
        *   4.3.3.1. Signature:
            ```python
            def __init__(self, optimal_depth: int = 3, weight: float = 1.0):
            ```
        *   4.3.3.2. Parameters:
            *   `optimal_depth (int`, default: `3`)`: The path depth considered ideal. URLs at this depth get the highest score.
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
    *   4.3.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Calculates the path depth of the URL. The score is `1.0 / (1.0 + abs(depth - optimal_depth))`, meaning URLs at `optimal_depth` score 1.0, and scores decrease as depth deviates. Uses a lookup table for common small differences for speed.
    *   4.3.5. Static Methods:
        *   `_quick_depth(path: str) -> int`: [Cached] Efficiently calculates path depth without full URL parsing.

*   **4.4. `ContentTypeScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.4.1. Purpose: Scores URLs based on their inferred content type, typically derived from the file extension.
    *   4.4.2. Inheritance: `URLScorer`
    *   4.4.3. Initialization (`__init__`)
        *   4.4.3.1. Signature:
            ```python
            def __init__(self, type_weights: Dict[str, float], weight: float = 1.0):
            ```
        *   4.4.3.2. Parameters:
            *   `type_weights (Dict[str, float])`: A dictionary mapping file extensions (e.g., "html", "pdf") or MIME type patterns (e.g., "text/html", "image/") to scores. Patterns ending with '$' are treated as exact extension matches.
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
    *   4.4.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Extracts the file extension from the URL. Looks up the score in `type_weights` first by exact extension match (if pattern ends with '$'), then by general extension. If no direct match, it might try matching broader MIME type categories if defined in `type_weights`. Returns 0.0 if no match found.
    *   4.4.5. Static Methods:
        *   `_quick_extension(url: str) -> str`: [Cached] Efficiently extracts file extension.

*   **4.5. `FreshnessScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.5.1. Purpose: Scores URLs based on dates found within the URL string, giving higher scores to more recent dates.
    *   4.5.2. Inheritance: `URLScorer`
    *   4.5.3. Initialization (`__init__`)
        *   4.5.3.1. Signature:
            ```python
            def __init__(self, weight: float = 1.0, current_year: int = [datetime.date.today().year]): # Actual default is dynamic
            ```
        *   4.5.3.2. Parameters:
            *   `weight (float`, default: `1.0`)`: The weight to apply to the calculated score.
            *   `current_year (int`, default: `datetime.date.today().year`)`: The reference year to calculate freshness against.
    *   4.5.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Uses a regex to find year patterns (YYYY) in the URL. If multiple years are found, it uses the latest valid year. The score is higher for years closer to `current_year`, using a predefined lookup for small differences or a decay function for larger differences. If no year is found, a default score (0.5) is returned.
    *   4.5.5. Helper Methods:
        *   `_extract_year(self, url: str) -> Optional[int]`: [Cached] Extracts the most recent valid year from the URL.

*   **4.6. `DomainAuthorityScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.6.1. Purpose: Scores URLs based on a predefined list of domain authority weights. This allows prioritizing or de-prioritizing URLs from specific domains.
    *   4.6.2. Inheritance: `URLScorer`
    *   4.6.3. Initialization (`__init__`)
        *   4.6.3.1. Signature:
            ```python
            def __init__(
                self,
                domain_weights: Dict[str, float],
                default_weight: float = 0.5,
                weight: float = 1.0,
            ):
            ```
        *   4.6.3.2. Parameters:
            *   `domain_weights (Dict[str, float])`: A dictionary mapping domain names (e.g., "example.com") to their authority scores (typically between 0.0 and 1.0).
            *   `default_weight (float`, default: `0.5`)`: The score to assign to URLs whose domain is not found in `domain_weights`.
            *   `weight (float`, default: `1.0`)`: The overall weight to apply to the calculated score.
    *   4.6.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Extracts the domain from the URL. If the domain is in `_domain_weights`, its corresponding score is returned. Otherwise, `_default_weight` is returned. Prioritizes top domains for faster lookup.
    *   4.6.5. Static Methods:
        *   `_extract_domain(url: str) -> str`: [Cached] Efficiently extracts the domain from a URL.

*   **4.7. `CompositeScorer`**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.7.1. Purpose: Combines the scores from multiple `URLScorer` instances. Each constituent scorer contributes its weighted score to the final composite score.
    *   4.7.2. Inheritance: `URLScorer`
    *   4.7.3. Initialization (`__init__`)
        *   4.7.3.1. Signature:
            ```python
            def __init__(self, scorers: List[URLScorer], normalize: bool = True):
            ```
        *   4.7.3.2. Parameters:
            *   `scorers (List[URLScorer])`: A list of `URLScorer` instances to be combined.
            *   `normalize (bool`, default: `True`)`: If `True`, the final composite score is normalized by dividing the sum of weighted scores by the number of scorers. This can help keep scores in a more consistent range.
    *   4.7.4. Key Implemented Methods:
        *   `_calculate_score(self, url: str) -> float`:
            *   Description: Iterates through all scorers in its list, calls their `score(url)` method (which applies individual weights), and sums up these scores. If `normalize` is `True`, divides the total sum by the number of scorers.
    *   4.7.5. Key Concrete Methods (overrides `URLScorer.score`):
        *   `score(self, url: str) -> float`:
            *   Description: Calculates the composite score and updates its own `ScoringStats`. Note: The individual scorers' stats are updated when their `score` methods are called internally.

*   **4.8. `ScoringStats` Data Class**
    *   Source: `crawl4ai/deep_crawling/scorers.py`
    *   4.8.1. Purpose: A data class to track statistics for URL scoring operations, including the number of URLs scored, total score, and min/max scores.
    *   4.8.2. Fields:
        *   `_urls_scored (int)`: Count of URLs scored.
        *   `_total_score (float)`: Sum of all scores.
        *   `_min_score (Optional[float])`: Minimum score encountered.
        *   `_max_score (Optional[float])`: Maximum score encountered.
    *   4.8.3. Key Methods:
        *   `update(self, score: float) -> None`: Updates the statistics with a new score.
        *   `get_average(self) -> float`: Calculates and returns the average score.
        *   `get_min(self) -> float`: Lazily initializes and returns the minimum score.
        *   `get_max(self) -> float`: Lazily initializes and returns the maximum score.

## 5. `DeepCrawlDecorator`

*   Source: `crawl4ai/deep_crawling/base_strategy.py`
*   5.1. Purpose: A decorator class that transparently adds deep crawling functionality to the `AsyncWebCrawler.arun` method if a `deep_crawl_strategy` is specified in the `CrawlerRunConfig`.
*   5.2. Initialization (`__init__`)
    *   5.2.1. Signature:
        ```python
        def __init__(self, crawler: AsyncWebCrawler):
        ```
    *   5.2.2. Parameters:
        *   `crawler (AsyncWebCrawler)`: The `AsyncWebCrawler` instance whose `arun` method is to be decorated.
*   5.3. `__call__` Method
    *   5.3.1. Signature:
        ```python
        @wraps(original_arun)
        async def wrapped_arun(url: str, config: CrawlerRunConfig = None, **kwargs):
        ```
    *   5.3.2. Functionality: This method wraps the original `arun` method of the `AsyncWebCrawler`.
        *   It checks if `config` is provided, has a `deep_crawl_strategy` set, and if `DeepCrawlDecorator.deep_crawl_active` context variable is `False` (to prevent recursion).
        *   If these conditions are met:
            *   It sets `DeepCrawlDecorator.deep_crawl_active` to `True`.
            *   It calls the `arun` method of the specified `config.deep_crawl_strategy`.
            *   It handles potential streaming results from the strategy by wrapping them in an async generator.
            *   Finally, it resets `DeepCrawlDecorator.deep_crawl_active` to `False`.
        *   If the conditions are not met, it calls the original `arun` method of the crawler.
*   5.4. Class Variable:
    *   `deep_crawl_active (ContextVar)`:
        *   Purpose: A `contextvars.ContextVar` used as a flag to indicate if a deep crawl is currently in progress for the current asynchronous context. This prevents the decorator from re-triggering deep crawling if the strategy itself calls the crawler's `arun` or `arun_many` methods.
        *   Default Value: `False`.

## 6. `TraversalStats` Data Model

*   Source: `crawl4ai/models.py`
*   6.1. Purpose: A data class for storing and tracking statistics related to a deep crawl traversal.
*   6.2. Fields:
    *   `start_time (datetime)`: The timestamp (Python `datetime` object) when the traversal process began. Default: `datetime.now()`.
    *   `end_time (Optional[datetime])`: The timestamp when the traversal process completed. Default: `None`.
    *   `urls_processed (int)`: The total number of URLs that were successfully fetched and processed. Default: `0`.
    *   `urls_failed (int)`: The total number of URLs that resulted in an error during fetching or processing. Default: `0`.
    *   `urls_skipped (int)`: The total number of URLs that were skipped (e.g., due to filters, already visited, or depth limits). Default: `0`.
    *   `total_depth_reached (int)`: The maximum depth reached from the start URL during the crawl. Default: `0`.
    *   `current_depth (int)`: The current depth level being processed by the crawler (can fluctuate during the crawl, especially for BFS). Default: `0`.

## 7. Configuration for Deep Crawling (`CrawlerRunConfig`)

*   Source: `crawl4ai/async_configs.py`
*   7.1. Purpose: `CrawlerRunConfig` is the primary configuration object passed to `AsyncWebCrawler.arun()` and `AsyncWebCrawler.arun_many()`. It contains various settings that control the behavior of a single crawl run, including those specific to deep crawling.
*   7.2. Relevant Fields:
    *   `deep_crawl_strategy (Optional[DeepCrawlStrategy])`:
        *   Type: `Optional[DeepCrawlStrategy]` (where `DeepCrawlStrategy` is the ABC from `crawl4ai.deep_crawling.base_strategy`)
        *   Default: `None`
        *   Description: Specifies the deep crawling strategy instance (e.g., `BFSDeepCrawlStrategy`, `DFSDeepCrawlStrategy`, `BestFirstCrawlingStrategy`) to be used for the crawl. If `None`, deep crawling is disabled, and only the initial URL(s) will be processed.
    *   *Note: Parameters like `max_depth`, `max_pages`, `filter_chain`, `url_scorer`, `score_threshold`, and `include_external` are not direct attributes of `CrawlerRunConfig` for deep crawling. Instead, they are passed to the constructor of the chosen `DeepCrawlStrategy` instance, which is then assigned to `CrawlerRunConfig.deep_crawl_strategy`.*

## 8. Utility Functions

*   **8.1. `normalize_url_for_deep_crawl(url: str, source_url: str) -> str`**
    *   Source: `crawl4ai/deep_crawling/utils.py` (or `crawl4ai/utils.py` if it's a general utility)
    *   8.1.1. Purpose: Normalizes a URL found during deep crawling. This typically involves resolving relative URLs against the `source_url` to create absolute URLs and removing URL fragments (`#fragment`).
    *   8.1.2. Signature: `def normalize_url_for_deep_crawl(url: str, source_url: str) -> str:`
    *   8.1.3. Parameters:
        *   `url (str)`: The URL string to be normalized.
        *   `source_url (str)`: The URL of the page where the `url` was discovered. This is used as the base for resolving relative paths.
    *   8.1.4. Returns: `(str)` - The normalized, absolute URL without fragments.

*   **8.2. `efficient_normalize_url_for_deep_crawl(url: str, source_url: str) -> str`**
    *   Source: `crawl4ai/deep_crawling/utils.py` (or `crawl4ai/utils.py`)
    *   8.2.1. Purpose: Provides a potentially more performant version of URL normalization specifically for deep crawling scenarios, likely employing optimizations to avoid repeated or complex parsing operations. (Note: Based on the provided code, this appears to be the same as `normalize_url_for_deep_crawl` if only one is present, or it might contain specific internal optimizations not exposed differently at the API level but used by strategies).
    *   8.2.2. Signature: `def efficient_normalize_url_for_deep_crawl(url: str, source_url: str) -> str:`
    *   8.2.3. Parameters:
        *   `url (str)`: The URL string to be normalized.
        *   `source_url (str)`: The URL of the page where the `url` was discovered.
    *   8.2.4. Returns: `(str)` - The normalized, absolute URL, typically without fragments.

## 9. PDF Processing Integration (`crawl4ai.processors.pdf`)
    *   9.1. Overview of PDF processing in Crawl4ai: While not directly part of the `deep_crawling` package, PDF processing components can be used in conjunction if a deep crawl discovers PDF URLs and they need to be processed. The `PDFCrawlerStrategy` can fetch PDFs, and `PDFContentScrapingStrategy` can extract content from them.
    *   **9.2. `PDFCrawlerStrategy`**
        *   Source: `crawl4ai/processors/pdf/__init__.py`
        *   9.2.1. Purpose: An `AsyncCrawlerStrategy` designed to "crawl" PDF files. In practice, this usually means downloading the PDF content. It returns a minimal `AsyncCrawlResponse` that signals to a `ContentScrapingStrategy` (like `PDFContentScrapingStrategy`) that the content is a PDF.
        *   9.2.2. Inheritance: `AsyncCrawlerStrategy`
        *   9.2.3. Initialization (`__init__`)
            *   9.2.3.1. Signature: `def __init__(self, logger: AsyncLogger = None):`
            *   9.2.3.2. Parameters:
                *   `logger (AsyncLogger`, default: `None`)`: An optional logger instance.
        *   9.2.4. Key Methods:
            *   `async def crawl(self, url: str, **kwargs) -> AsyncCrawlResponse`:
                *   Description: For a PDF URL, this method typically signifies that the URL points to a PDF. It constructs an `AsyncCrawlResponse` with a `Content-Type` header of `application/pdf` and a placeholder HTML. The actual PDF processing (downloading and content extraction) is usually handled by a subsequent scraping strategy.
    *   **9.3. `PDFContentScrapingStrategy`**
        *   Source: `crawl4ai/processors/pdf/__init__.py`
        *   9.3.1. Purpose: A `ContentScrapingStrategy` specialized in extracting text, images (optional), and metadata from PDF files. It uses a `PDFProcessorStrategy` (like `NaivePDFProcessorStrategy`) internally.
        *   9.3.2. Inheritance: `ContentScrapingStrategy`
        *   9.3.3. Initialization (`__init__`)
            *   9.3.3.1. Signature:
                ```python
                def __init__(self,
                             save_images_locally: bool = False,
                             extract_images: bool = False,
                             image_save_dir: str = None,
                             batch_size: int = 4,
                             logger: AsyncLogger = None):
                ```
            *   9.3.3.2. Parameters:
                *   `save_images_locally (bool`, default: `False`)`: If `True`, extracted images will be saved to the local disk.
                *   `extract_images (bool`, default: `False`)`: If `True`, attempts to extract images from the PDF.
                *   `image_save_dir (str`, default: `None`)`: The directory where extracted images will be saved if `save_images_locally` is `True`.
                *   `batch_size (int`, default: `4`)`: The number of PDF pages to process in parallel batches (if the underlying processor supports it).
                *   `logger (AsyncLogger`, default: `None`)`: An optional logger instance.
        *   9.3.4. Key Methods:
            *   `scrape(self, url: str, html: str, **params) -> ScrapingResult`:
                *   Description: Takes the URL (which should point to a PDF or a local PDF path) and processes it. It downloads the PDF if it's a remote URL, then uses the internal `pdf_processor` to extract content. It formats the extracted text into basic HTML and collects image and link information.
            *   `async def ascrape(self, url: str, html: str, **kwargs) -> ScrapingResult`:
                *   Description: Asynchronous version of the `scrape` method, typically by running the synchronous `scrape` method in a separate thread.
        *   9.3.5. Helper Methods:
            *   `_get_pdf_path(self, url: str) -> str`: Downloads a PDF from a URL to a temporary file if it's not a local path.
    *   **9.4. `NaivePDFProcessorStrategy`**
        *   Source: `crawl4ai/processors/pdf/processor.py`
        *   9.4.1. Purpose: A concrete implementation of `PDFProcessorStrategy` that uses `PyPDF2` (or similar libraries if extended) to extract text, images, and metadata from PDF documents page by page or in batches.
        *   9.4.2. Initialization (`__init__`)
            *   Signature: `def __init__(self, image_dpi: int = 144, image_quality: int = 85, extract_images: bool = True, save_images_locally: bool = False, image_save_dir: Optional[Path] = None, batch_size: int = 4)`
            *   Parameters: [Details parameters for image extraction quality, saving, and batch processing size.]
        *   9.4.3. Key Methods:
            *   `process(self, pdf_path: Path) -> PDFProcessResult`:
                *   Description: Processes a single PDF file sequentially, page by page. Extracts metadata, text, and optionally images from each page.
            *   `process_batch(self, pdf_path: Path) -> PDFProcessResult`:
                *   Description: Processes a PDF file by dividing its pages into batches and processing these batches in parallel using a thread pool, potentially speeding up extraction for large PDFs.
        *   9.4.4. Helper Methods:
            *   `_process_page(self, page, image_dir: Optional[Path]) -> PDFPage`: Processes a single PDF page object.
            *   `_extract_images(self, page, image_dir: Optional[Path]) -> List[Dict]`: Extracts images from a page.
            *   `_extract_links(self, page) -> List[str]`: Extracts hyperlinks from a page.
            *   `_extract_metadata(self, pdf_path: Path, reader=None) -> PDFMetadata`: Extracts metadata from the PDF.
    *   **9.5. PDF Data Models**
        *   Source: `crawl4ai/processors/pdf/processor.py`
        *   9.5.1. `PDFMetadata`:
            *   Purpose: Stores metadata extracted from a PDF document.
            *   Fields:
                *   `title (Optional[str])`: The title of the PDF.
                *   `author (Optional[str])`: The author(s) of the PDF.
                *   `producer (Optional[str])`: The software used to produce the PDF.
                *   `created (Optional[datetime])`: The creation date of the PDF.
                *   `modified (Optional[datetime])`: The last modification date of the PDF.
                *   `pages (int)`: The total number of pages in the PDF. Default: `0`.
                *   `encrypted (bool)`: `True` if the PDF is encrypted, `False` otherwise. Default: `False`.
                *   `file_size (Optional[int])`: The size of the PDF file in bytes. Default: `None`.
        *   9.5.2. `PDFPage`:
            *   Purpose: Stores content extracted from a single page of a PDF document.
            *   Fields:
                *   `page_number (int)`: The page number (1-indexed).
                *   `raw_text (str)`: The raw text extracted from the page. Default: `""`.
                *   `markdown (str)`: Markdown representation of the page content. Default: `""`.
                *   `html (str)`: Basic HTML representation of the page content. Default: `""`.
                *   `images (List[Dict])`: A list of dictionaries, each representing an extracted image with details like format, path/data, dimensions. Default: `[]`.
                *   `links (List[str])`: A list of hyperlink URLs found on the page. Default: `[]`.
                *   `layout (List[Dict])`: Information about the layout of text elements on the page (e.g., coordinates). Default: `[]`.
        *   9.5.3. `PDFProcessResult`:
            *   Purpose: Encapsulates the results of processing a PDF document.
            *   Fields:
                *   `metadata (PDFMetadata)`: The metadata of the processed PDF.
                *   `pages (List[PDFPage])`: A list of `PDFPage` objects, one for each page processed.
                *   `processing_time (float)`: The time taken to process the PDF, in seconds. Default: `0.0`.
                *   `version (str)`: The version of the PDF processor. Default: `"1.1"`.

## 10. Version Information (`crawl4ai.__version__`)
*   Source: `crawl4ai/__version__.py`
*   10.1. `__version__ (str)`: A string representing the current installed version of the `crawl4ai` library (e.g., "0.6.3").

## 11. Asynchronous Configuration (`crawl4ai.async_configs`)
    *   11.1. Overview: The `crawl4ai.async_configs` module contains configuration classes used throughout the library, including those relevant for network requests like proxies (`ProxyConfig`) and general crawler/browser behavior.
    *   **11.2. `ProxyConfig`**
        *   Source: `crawl4ai/async_configs.py` (and `crawl4ai/proxy_strategy.py`)
        *   11.2.1. Purpose: Represents the configuration for a single proxy server, including its address, port, and optional authentication credentials.
        *   11.2.2. Initialization (`__init__`)
            *   11.2.2.1. Signature:
                ```python
                def __init__(
                    self,
                    server: str,
                    username: Optional[str] = None,
                    password: Optional[str] = None,
                    ip: Optional[str] = None,
                ):
                ```
            *   11.2.2.2. Parameters:
                *   `server (str)`: The proxy server URL (e.g., "http://proxy.example.com:8080", "socks5://proxy.example.com:1080").
                *   `username (Optional[str]`, default: `None`)`: The username for proxy authentication, if required.
                *   `password (Optional[str]`, default: `None`)`: The password for proxy authentication, if required.
                *   `ip (Optional[str]`, default: `None`)`: Optionally, the specific IP address of the proxy server. If not provided, it's inferred from the `server` URL.
        *   11.2.3. Key Static Methods:
            *   `from_string(proxy_str: str) -> ProxyConfig`:
                *   Description: Creates a `ProxyConfig` instance from a string representation. Expected format is "ip:port:username:password" or "ip:port".
                *   Returns: `(ProxyConfig)`
            *   `from_dict(proxy_dict: Dict) -> ProxyConfig`:
                *   Description: Creates a `ProxyConfig` instance from a dictionary.
                *   Returns: `(ProxyConfig)`
            *   `from_env(env_var: str = "PROXIES") -> List[ProxyConfig]`:
                *   Description: Loads a list of proxy configurations from a comma-separated string in an environment variable.
                *   Returns: `(List[ProxyConfig])`
        *   11.2.4. Key Methods:
            *   `to_dict(self) -> Dict`: Converts the `ProxyConfig` instance to a dictionary.
            *   `clone(self, **kwargs) -> ProxyConfig`: Creates a copy of the instance, optionally updating attributes with `kwargs`.

    *   **11.3. `ProxyRotationStrategy` (ABC)**
        *   Source: `crawl4ai/proxy_strategy.py`
        *   11.3.1. Purpose: Abstract base class defining the interface for proxy rotation strategies.
        *   11.3.2. Key Abstract Methods:
            *   `async def get_next_proxy(self) -> Optional[ProxyConfig]`: Asynchronously gets the next `ProxyConfig` from the strategy.
            *   `def add_proxies(self, proxies: List[ProxyConfig])`: Adds a list of `ProxyConfig` objects to the strategy's pool.
    *   **11.4. `RoundRobinProxyStrategy`**
        *   Source: `crawl4ai/proxy_strategy.py`
        *   11.4.1. Purpose: A simple proxy rotation strategy that cycles through a list of proxies in a round-robin fashion.
        *   11.4.2. Inheritance: `ProxyRotationStrategy`
        *   11.4.3. Initialization (`__init__`)
            *   11.4.3.1. Signature: `def __init__(self, proxies: List[ProxyConfig] = None):`
            *   11.4.3.2. Parameters:
                *   `proxies (List[ProxyConfig]`, default: `None`)`: An optional initial list of `ProxyConfig` objects.
        *   11.4.4. Key Implemented Methods:
            *   `add_proxies(self, proxies: List[ProxyConfig])`: Adds new proxies to the internal list and reinitializes the cycle.
            *   `async def get_next_proxy(self) -> Optional[ProxyConfig]`: Returns the next proxy from the cycle. Returns `None` if no proxies are available.

## 12. HTML to Markdown Conversion (`crawl4ai.markdown_generation_strategy`)
    *   12.1. `MarkdownGenerationStrategy` (ABC)
        *   Source: `crawl4ai/markdown_generation_strategy.py`
        *   12.1.1. Purpose: Abstract base class defining the interface for strategies that convert HTML content to Markdown.
        *   12.1.2. Key Abstract Methods:
            *   `generate_markdown(self, input_html: str, base_url: str = "", html2text_options: Optional[Dict[str, Any]] = None, content_filter: Optional[RelevantContentFilter] = None, citations: bool = True, **kwargs) -> MarkdownGenerationResult`:
                *   Description: Abstract method to convert the given `input_html` string into a `MarkdownGenerationResult` object.
                *   Parameters:
                    *   `input_html (str)`: The HTML content to convert.
                    *   `base_url (str`, default: `""`)`: The base URL used for resolving relative links within the HTML.
                    *   `html2text_options (Optional[Dict[str, Any]]`, default: `None`)`: Options to pass to the underlying HTML-to-text conversion library.
                    *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: An optional filter to apply to the HTML before Markdown conversion, potentially to extract only relevant parts.
                    *   `citations (bool`, default: `True`)`: If `True`, attempts to convert hyperlinks into Markdown citations with a reference list.
                    *   `**kwargs`: Additional keyword arguments.
                *   Returns: `(MarkdownGenerationResult)`
    *   12.2. `DefaultMarkdownGenerator`
        *   Source: `crawl4ai/markdown_generation_strategy.py`
        *   12.2.1. Purpose: The default implementation of `MarkdownGenerationStrategy`. It uses the `CustomHTML2Text` class (an enhanced `html2text.HTML2Text`) for the primary conversion and can optionally apply a `RelevantContentFilter`.
        *   12.2.2. Inheritance: `MarkdownGenerationStrategy`
        *   12.2.3. Initialization (`__init__`)
            *   12.2.3.1. Signature:
                ```python
                def __init__(
                    self,
                    content_filter: Optional[RelevantContentFilter] = None,
                    options: Optional[Dict[str, Any]] = None,
                    content_source: str = "cleaned_html", # "raw_html", "fit_html"
                ):
                ```
            *   12.2.3.2. Parameters:
                *   `content_filter (Optional[RelevantContentFilter]`, default: `None`)`: An instance of a content filter strategy (e.g., `BM25ContentFilter`, `PruningContentFilter`) to be applied to the `input_html` before Markdown conversion. If `None`, no pre-filtering is done.
                *   `options (Optional[Dict[str, Any]]`, default: `None`)`: A dictionary of options to configure the `CustomHTML2Text` converter (e.g., `{"body_width": 0, "ignore_links": False}`).
                *   `content_source (str`, default: `"cleaned_html"`)`: Specifies which HTML source to use for Markdown generation if multiple are available (e.g., from `CrawlResult`). Options: `"cleaned_html"` (default), `"raw_html"`, `"fit_html"`. This parameter is primarily used when the generator is part of a larger crawling pipeline.
        *   12.2.4. Key Methods:
            *   `generate_markdown(self, input_html: str, base_url: str = "", html2text_options: Optional[Dict[str, Any]] = None, content_filter: Optional[RelevantContentFilter] = None, citations: bool = True, **kwargs) -> MarkdownGenerationResult`:
                *   Description: Converts HTML to Markdown. If a `content_filter` is provided (either at init or as an argument), it's applied first to get "fit_html". Then, `CustomHTML2Text` converts the chosen HTML (input_html or fit_html) to raw Markdown. If `citations` is True, links in the raw Markdown are converted to citation format.
                *   Returns: `(MarkdownGenerationResult)`
            *   `convert_links_to_citations(self, markdown: str, base_url: str = "") -> Tuple[str, str]`:
                *   Description: Parses Markdown text, identifies links, replaces them with citation markers (e.g., `[text]^(1)`), and generates a corresponding list of references.
                *   Returns: `(Tuple[str, str])` - A tuple containing the Markdown with citations and the Markdown string of references.

## 13. Content Filtering (`crawl4ai.content_filter_strategy`)
    *   13.1. `RelevantContentFilter` (ABC)
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.1.1. Purpose: Abstract base class for strategies that filter HTML content to extract only the most relevant parts, typically before Markdown conversion or further processing.
        *   13.1.2. Key Abstract Methods:
            *   `filter_content(self, html: str) -> List[str]`:
                *   Description: Abstract method that takes an HTML string and returns a list of strings, where each string is a chunk of HTML deemed relevant.
    *   13.2. `BM25ContentFilter`
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.2.1. Purpose: Filters HTML content by extracting text chunks and scoring their relevance to a user query (or an inferred page query) using the BM25 algorithm.
        *   13.2.2. Inheritance: `RelevantContentFilter`
        *   13.2.3. Initialization (`__init__`)
            *   13.2.3.1. Signature:
                ```python
                def __init__(
                    self,
                    user_query: Optional[str] = None,
                    bm25_threshold: float = 1.0,
                    language: str = "english",
                ):
                ```
            *   13.2.3.2. Parameters:
                *   `user_query (Optional[str]`, default: `None`)`: The query to compare content against. If `None`, the filter attempts to extract a query from the page's metadata.
                *   `bm25_threshold (float`, default: `1.0`)`: The minimum BM25 score for a text chunk to be considered relevant.
                *   `language (str`, default: `"english"`)`: The language used for stemming tokens.
        *   13.2.4. Key Implemented Methods:
            *   `filter_content(self, html: str, min_word_threshold: int = None) -> List[str]`: Parses HTML, extracts text chunks (paragraphs, list items, etc.), scores them with BM25 against the query, and returns the HTML of chunks exceeding the threshold.
    *   13.3. `PruningContentFilter`
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.3.1. Purpose: Filters HTML content by recursively pruning less relevant parts of the DOM tree based on a composite score (text density, link density, tag weights, etc.).
        *   13.3.2. Inheritance: `RelevantContentFilter`
        *   13.3.3. Initialization (`__init__`)
            *   13.3.3.1. Signature:
                ```python
                def __init__(
                    self,
                    user_query: Optional[str] = None,
                    min_word_threshold: Optional[int] = None,
                    threshold_type: str = "fixed", # or "dynamic"
                    threshold: float = 0.48,
                ):
                ```
            *   13.3.3.2. Parameters:
                *   `user_query (Optional[str]`, default: `None`)`: [Not directly used by pruning logic but inherited].
                *   `min_word_threshold (Optional[int]`, default: `None`)`: Minimum word count for an element to be considered for scoring initially (default behavior might be more nuanced).
                *   `threshold_type (str`, default: `"fixed"`)`: Specifies how the `threshold` is applied. "fixed" uses the direct value. "dynamic" adjusts the threshold based on content characteristics.
                *   `threshold (float`, default: `0.48`)`: The score threshold for pruning. Elements below this score are removed.
        *   13.3.4. Key Implemented Methods:
            *   `filter_content(self, html: str, min_word_threshold: int = None) -> List[str]`: Parses HTML, applies the pruning algorithm to the body, and returns the remaining significant HTML blocks as a list of strings.
    *   13.4. `LLMContentFilter`
        *   Source: `crawl4ai/content_filter_strategy.py`
        *   13.4.1. Purpose: Uses a Large Language Model (LLM) to determine the relevance of HTML content chunks based on a given instruction.
        *   13.4.2. Inheritance: `RelevantContentFilter`
        *   13.4.3. Initialization (`__init__`)
            *   13.4.3.1. Signature:
                ```python
                def __init__(
                    self,
                    llm_config: Optional[LLMConfig] = None,
                    instruction: Optional[str] = None,
                    chunk_token_threshold: int = CHUNK_TOKEN_THRESHOLD, # Default from config
                    overlap_rate: float = OVERLAP_RATE,            # Default from config
                    word_token_rate: float = WORD_TOKEN_RATE,        # Default from config
                    verbose: bool = False,
                    logger: Optional[AsyncLogger] = None,
                    ignore_cache: bool = True
                ):
                ```
            *   13.4.3.2. Parameters:
                *   `llm_config (Optional[LLMConfig])`: Configuration for the LLM (provider, API key, model, etc.).
                *   `instruction (Optional[str])`: The instruction given to the LLM to guide content filtering (e.g., "Extract only the main article content, excluding headers, footers, and ads.").
                *   `chunk_token_threshold (int)`: Maximum number of tokens per chunk sent to the LLM.
                *   `overlap_rate (float)`: Percentage of overlap between consecutive chunks.
                *   `word_token_rate (float)`: Estimated ratio of words to tokens, used for chunking.
                *   `verbose (bool`, default: `False`)`: Enables verbose logging for LLM operations.
                *   `logger (Optional[AsyncLogger]`, default: `None`)`: Custom logger instance.
                *   `ignore_cache (bool`, default: `True`)`: If `True`, bypasses any LLM response caching for this operation.
        *   13.4.4. Key Implemented Methods:
            *   `filter_content(self, html: str, ignore_cache: bool = True) -> List[str]`:
                *   Description: Chunks the input HTML. For each chunk, it sends a request to the configured LLM with the chunk and the `instruction`. The LLM is expected to return the relevant part of the chunk. These relevant parts are then collected and returned.
```