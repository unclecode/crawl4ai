```markdown
# Detailed Outline for crawl4ai - deep_crawling Component

**Target Document Type:** reasoning
**Target Output Filename Suggestion:** `reasoning_deep_crawling.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2025-05-24
---

## 1. Introduction to Deep Crawling with Crawl4ai

Deep crawling is a fundamental capability for comprehensive web data extraction. This section introduces what deep crawling means in the context of Crawl4ai, why it's essential, and provides an overview of how Crawl4ai empowers you to perform sophisticated, multi-page crawls.

*   **1.1. What is Deep Crawling and Why Do You Need It?**
    *   **Explanation of deep crawling:** Deep crawling, unlike single-page scraping, involves systematically discovering and fetching web pages by following hyperlinks from an initial set of "seed" URLs. It's the process of exploring a website's structure to gather information spread across multiple pages. Crawl4ai's deep crawling component automates this exploration, allowing you to define the boundaries and priorities of your crawl.
    *   **Common scenarios requiring deep crawling:**
        *   **Building a comprehensive site index:** Discovering all pages within a website for search engine indexing or sitemap generation. For example, indexing all articles on a news website or all products on an e-commerce site.
        *   **Scraping data from multiple interconnected pages:** Extracting detailed information that isn't available on a single page, such as product specifications from individual product pages linked from a category page.
        *   **Discovering all content within a specific domain or sub-domain:** Ensuring all relevant content under `blog.example.com` is found and processed.
        *   **SEO analysis and site structure understanding:** Mapping out how pages are linked, identifying orphaned pages, or analyzing internal link distribution.
        *   **Monitoring website changes:** Regularly crawling a site to detect new content, updated pages, or broken links.
    *   **Core problems solved by Crawl4ai's `deep_crawling` component:**
        *   **URL Frontier Management:** Efficiently managing the queue of URLs to visit.
        *   **Visited URL Tracking:** Preventing re-crawling of already processed pages.
        *   **Depth Control:** Limiting how many "hops" the crawler takes from the seed URL.
        *   **Scope Management:** Using filters to define which URLs are relevant and should be processed.
        *   **Crawl Prioritization:** Using scorers to decide which URLs are more important to visit next.
        *   **Resource Management:** Providing mechanisms (`max_pages`) to limit the overall crawl size.

*   **1.2. When to Choose Deep Crawling Over Single-Page Crawling**
    *   **Decision factors:**
        *   **Data Distribution:** If the information you need is spread across multiple interlinked pages (e.g., an e-commerce site with category pages, product listing pages, and individual product detail pages), deep crawling is necessary. Single-page crawling is sufficient if all required data is on one page or a known, small set of URLs.
        *   **Link Discovery:** If you need to discover new URLs dynamically based on the content of previously crawled pages, deep crawling is the way to go.
        *   **Site Mapping/Full Site Analysis:** If your goal is to understand the structure of an entire site or a significant portion of it, deep crawling is essential.
    *   **Trade-offs:**
        *   **Comprehensiveness vs. Speed/Resources:** Deep crawling provides more comprehensive data but typically takes longer and consumes more bandwidth and processing resources than single-page crawls.
        *   **Complexity:** Configuring an effective deep crawl (with appropriate strategies, filters, and scorers) can be more complex than a simple single-page fetch.
        *   **Scope Control:** Without proper filters and limits (`max_depth`, `max_pages`), deep crawls can easily become too broad and inefficient.

*   **1.3. Overview of Crawl4ai's Deep Crawling Architecture**
    *   **High-level explanation:**
        Crawl4ai's deep crawling is orchestrated by a `DeepCrawlStrategy` (like `BFSDeepCrawlStrategy`, `DFSDeepCrawlStrategy`, or `BestFirstCrawlingStrategy`). When a page is crawled, this strategy is responsible for:
        1.  Extracting new links from the page.
        2.  Applying a `FilterChain` (a sequence of `URLFilter` instances) to determine if a discovered URL should be considered for further crawling.
        3.  Optionally, using a `URLScorer` (especially with `BestFirstCrawlingStrategy`) to assign a priority to valid URLs, influencing the order in which they are visited.
        4.  Adding valid (and potentially scored) URLs to a frontier (queue or priority queue) for future processing.
        5.  Managing visited URLs to avoid redundant crawls and controlling the depth and extent of the crawl.
    *   **Role of `DeepCrawlDecorator`:**
        This decorator is an internal mechanism that transparently adds deep crawling capabilities to the standard `AsyncWebCrawler.arun()` method when a `deep_crawl_strategy` is specified in `CrawlerRunConfig`. Users typically don't interact with it directly but should be aware that it's the component enabling this extended functionality.
    *   `* Diagram: [Conceptual diagram of the deep crawling workflow:
        Seed URL -> AsyncWebCrawler.arun() -> DeepCrawlDecorator -> (if deep_crawl_strategy in CrawlerRunConfig) -> DeepCrawlStrategy.arun()
        Within DeepCrawlStrategy.arun():
            Fetch Page -> Process Page (Extract Links) -> For each Link:
                -> FilterChain.apply(link) -> (if valid) -> URLScorer.score(link) -> Add to Frontier -> Select Next URL from Frontier -> Fetch Page ... ]`

## 2. Core Concepts: Strategies, Filters, and Scorers

To effectively use deep crawling, understanding its three main pillars is crucial: the strategy dictates *how* you explore, filters decide *what* to explore, and scorers (especially for Best-First) determine *in what order* to explore.

*   **2.1. Understanding `DeepCrawlStrategy`**
    *   **Purpose:** The `DeepCrawlStrategy` is the heart of the deep crawling process. It's an interface (an abstract base class) that defines the logic for traversing a website. Concrete implementations provide different exploration patterns.
    *   **Why different strategies exist:**
        *   **BFS (Breadth-First Search):** Explores websites level by level. Good for a complete, systematic scan up to a certain depth.
        *   **DFS (Depth-First Search):** Explores one branch of a website as deeply as possible before backtracking. Useful for following specific paths.
        *   **Best-First Search:** Uses a scoring mechanism to prioritize URLs, visiting the most "promising" ones first. Ideal for targeted crawling where relevance is key.
    *   **How to select the right strategy for your goal:**
        *   **Comprehensive Site Mapping:** BFS is often preferred.
        *   **Finding Specific Content Quickly (if path is known or can be guided):** DFS can be efficient.
        *   **Targeted Crawling (e.g., based on keywords, freshness, authority):** Best-First is the most powerful.
        *   **Resource Constraints:** BFS can be memory-intensive for wide sites. DFS might be better for deep, narrow sites if `max_depth` is managed. Best-First's resource usage depends on the scorer and queue size.
        *   `* Decision Table:
            | Goal                          | Recommended Strategy | Key Considerations                      |
            |-------------------------------|----------------------|-----------------------------------------|
            | Full site index up to depth X | BFS                  | Memory for wide sites, `max_depth`      |
            | Explore specific section deep | DFS                  | `max_depth`, avoiding traps             |
            | Find most relevant pages      | Best-First           | Scorer quality, `max_pages`             |
            | Quick overview of a site      | BFS with low `max_depth`| Speed vs. completeness                |
            `
*   **2.2. The Role of URL Filters (`URLFilter` & `FilterChain`)**
    *   **Purpose:** Filters are essential for controlling the scope and efficiency of your deep crawl. They decide whether a discovered URL should be added to the crawling queue or discarded. Without filters, a crawler might wander into irrelevant parts of a website, get stuck in "crawler traps" (like infinite calendars), or consume excessive resources.
    *   **How `FilterChain` allows combining multiple filters:** `FilterChain` takes a list of `URLFilter` instances. When a URL is evaluated, it's passed through each filter in the chain sequentially. If *any* filter in the chain rejects the URL (returns `False`), the URL is discarded. It must pass *all* filters to be considered valid. This allows for creating sophisticated, layered filtering logic.
    *   **Benefits of effective filtering:**
        *   **Efficiency:** Reduces the number of pages fetched and processed, saving time and bandwidth.
        *   **Relevance:** Focuses the crawl on content that matches your objectives.
        *   **Resource Management:** Prevents excessive memory usage by keeping the URL frontier manageable.
        *   **Avoiding Traps:** Helps avoid sections of a website that might lead to an infinite number of unique URLs (e.g., calendars, faceted search results with many parameter combinations).

*   **2.3. The Power of URL Scoring (`URLScorer` & `CompositeScorer`)**
    *   **Purpose:** URL scoring is primarily used by the `BestFirstCrawlingStrategy`. It assigns a numerical score to each valid URL, indicating its priority. The strategy then picks URLs from the frontier based on these scores (typically highest score first). This allows the crawler to intelligently prioritize which parts of a website to explore.
    *   **How `CompositeScorer` enables multi-faceted URL evaluation:** Often, a single criterion isn't enough to determine a URL's importance. `CompositeScorer` allows you to combine multiple individual `URLScorer` instances (e.g., one for keyword relevance, one for freshness, one for domain authority). Each individual scorer contributes to an overall score, often with weights you can define, providing a more nuanced and effective prioritization.
    *   **Impact of scoring on crawl efficiency and result quality:**
        *   **Efficiency:** Good scoring can dramatically improve efficiency by guiding the crawler to relevant content much faster, especially if you have a `max_pages` limit.
        *   **Result Quality:** By prioritizing high-value pages, scoring ensures that the most important data is collected even if the crawl is stopped before exploring the entire site. The definition of "high-value" is determined by your scoring logic.

## 3. Deep Crawling Strategies In-Depth

Let's dive into each specific strategy, understanding its mechanics, use cases, and how to configure it.

*   **3.1. Breadth-First Search (`BFSDeepCrawlStrategy`)**
    *   **3.1.1. Understanding BFS Traversal**
        *   **What is BFS?** Breadth-First Search explores a website layer by layer. It starts with the seed URL(s) (level 0), then crawls all pages directly linked from the seeds (level 1), then all pages linked from level 1 pages (level 2), and so on. It uses a FIFO (First-In, First-Out) queue to manage URLs for each level.
        *   **Pros:**
            *   Finds the shortest path to all reachable pages.
            *   Systematic and predictable exploration pattern.
            *   Good for getting a broad overview of a site's structure quickly, especially at shallow depths.
        *   **Cons:**
            *   Can consume significant memory for websites with a large number of links per page (wide sites), as it needs to store all URLs of a given level before moving to the next.
            *   May take a long time to reach content buried deep within the site structure.
        *   **Typical Use Cases:**
            *   Full site mapping up to a certain depth.
            *   Discovering all pages for a small to medium-sized website.
            *   Finding broken links or orphaned pages (when combined with analysis of all discovered URLs).
        *   `* Diagram: [Visual representation of BFS traversal, showing levels and queue behavior.
            Example:
                Level 0: A
                Queue: [A] -> Process A, discover B, C
                Level 1: B, C
                Queue: [B, C] -> Process B, discover D, E. Process C, discover F
                Level 2: D, E, F
                Queue: [D, E, F] -> ...
            ]`
    *   **3.1.2. Practical Usage of `BFSDeepCrawlStrategy`**
        *   **How to instantiate and pass it to `CrawlerRunConfig`:**
            ```python
            from crawl4ai import BFSDeepCrawlStrategy, CrawlerRunConfig

            bfs_strategy = BFSDeepCrawlStrategy(max_depth=3) # Example: crawl up to 3 levels deep
            run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)
            # ... then pass run_config to crawler.arun() or crawler.arun_many()
            ```
        *   **Key configuration parameters:**
            *   `max_depth (int)`: Crucial for BFS. Defines how many levels deep the crawl will go. A `max_depth` of 0 crawls only the seed URL(s). A `max_depth` of 1 crawls seeds and pages directly linked from them.
            *   `filter_chain (Optional[FilterChain])`: URLs discovered at each level are passed through this chain before being added to the next level's queue.
            *   `url_scorer (Optional[URLScorer])`: While BFS is primarily level-ordered, a scorer *can* be used to influence the processing order *within* a given level if multiple URLs are fetched concurrently in batches. However, it doesn't change the fundamental level-by-level exploration. (This is less common for pure BFS compared to Best-First).
            *   `max_pages (int, default=infinity)`: A global limit on the total number of pages to crawl. The crawl will stop if `max_pages` or `max_depth` is reached, whichever comes first.
            *   `include_external (bool, default=False)`: If `True`, BFS will also explore links to external domains, respecting `max_depth` for those external paths as well. Use with caution and strong `DomainFilter`s.
        *   `* Code Example: [Setting up a BFS crawl to explore 'example.com' up to depth 2, only HTML pages, max 100 pages]`
            ```python
            from crawl4ai import (
                AsyncWebCrawler, CrawlerRunConfig, BrowserConfig,
                BFSDeepCrawlStrategy, FilterChain, DomainFilter, ContentTypeFilter
            )
            import asyncio

            async def bfs_example_crawl():
                # Filters: Only allow 'example.com' and only HTML files
                filters = FilterChain(filters=[
                    DomainFilter(allowed_domains=["example.com"]),
                    ContentTypeFilter(allowed_types=['.html', '.htm'])
                ])

                # BFS Strategy: Max depth 2, max 100 pages, apply filters
                bfs_strategy = BFSDeepCrawlStrategy(
                    max_depth=2,
                    filter_chain=filters,
                    max_pages=100
                )

                run_config = CrawlerRunConfig(
                    deep_crawl_strategy=bfs_strategy,
                    verbose=True
                )

                browser_config = BrowserConfig(headless=True)
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    result_container = await crawler.arun(
                        url="https://example.com",
                        config=run_config
                    )
                    # In batch mode (default for arun without stream=True in strategy),
                    # result_container will be a list of CrawlResult objects
                    for i, result in enumerate(result_container):
                        if result.success:
                            print(f"Crawled {i+1}: {result.url} (Depth: {result.metadata.get('depth')})")
                        else:
                            print(f"Failed {i+1}: {result.url} - {result.error_message}")

            if __name__ == "__main__":
                asyncio.run(bfs_example_crawl())
            ```
    *   **3.1.3. Best Practices for BFS**
        *   **Memory Management:** For very wide sites (many links per page), BFS can consume a lot of memory because it holds all URLs of the current level. If memory is a concern, consider a lower `max_depth` or switching to DFS/Best-First for more targeted exploration.
        *   **Effective `max_depth`:** Choose `max_depth` carefully. A small increase in depth can lead to an exponential increase in pages crawled.
        *   **Filtering:** Always use `DomainFilter` to keep the crawl focused. Add other filters (`ContentTypeFilter`, `URLPatternFilter`) as needed to refine scope.
    *   **3.1.4. Common Pitfalls with BFS**
        *   **Excessive Memory on Large/Wide Sites:** Setting `max_depth` too high without considering site width can lead to out-of-memory errors.
        *   **Crawling Irrelevant Content:** Not using filters can result in crawling large, unwanted sections of a site or even external sites if `include_external` is accidentally enabled without proper domain filtering.
        *   **Time Consumption:** BFS aims for breadth, so reaching very specific, deep content might take longer than with DFS or a well-tuned Best-First strategy.

*   **3.2. Depth-First Search (`DFSDeepCrawlStrategy`)**
    *   **3.2.1. Understanding DFS Traversal**
        *   **What is DFS?** Depth-First Search explores as far as possible along each branch before backtracking. It uses a LIFO (Last-In, First-Out) stack to manage URLs. When it discovers new links on a page, those links are added to the top of the stack, and the crawler immediately proceeds to the newest link.
        *   **Pros:**
            *   Can reach deep content very quickly if it happens to be on the current exploration path.
            *   Potentially lower memory footprint for deep, narrow sites compared to BFS, as it doesn't need to store all URLs at a given level.
        *   **Cons:**
            *   Can get "stuck" exploring a very deep or infinite branch, potentially missing content in other, shallower branches if `max_pages` or another limit is hit.
            *   The order of discovery is less predictable than BFS and may not provide a balanced view of the site quickly.
        *   **Typical Use Cases:**
            *   Following a specific path through a website (e.g., a series of articles, a product configuration wizard).
            *   Exploring a single section of a website as deeply as possible.
            *   When memory is a primary concern and the target content is known to be deep.
        *   `* Diagram: [Visual representation of DFS traversal, showing stack behavior.
            Example:
                Stack: [A] -> Pop A, discover B, C. Push C, then B.
                Stack: [B, C] -> Pop B, discover D, E. Push E, then D.
                Stack: [D, E, C] -> Pop D ... and so on.
            ]`
    *   **3.2.2. Practical Usage of `DFSDeepCrawlStrategy`**
        *   **How to instantiate and pass it to `CrawlerRunConfig`:**
            ```python
            from crawl4ai import DFSDeepCrawlStrategy, CrawlerRunConfig

            dfs_strategy = DFSDeepCrawlStrategy(max_depth=5) # Example: explore up to 5 links deep
            run_config = CrawlerRunConfig(deep_crawl_strategy=dfs_strategy)
            ```
        *   **Key configuration parameters:**
            *   `max_depth (int)`: Critically important for DFS to prevent infinite loops or excessively deep crawls.
            *   `filter_chain (Optional[FilterChain])`: Essential for guiding DFS and preventing it from exploring irrelevant paths.
            *   `url_scorer (Optional[URLScorer])`: Less commonly used with pure DFS, as the stack naturally dictates order. If used, it might influence which of the newly discovered links from a page gets pushed to the stack (and thus processed) first.
            *   `max_pages (int, default=infinity)`: Stops the crawl if this limit is reached.
            *   `include_external (bool, default=False)`: Controls whether DFS follows external links.
        *   `* Code Example: [Setting up a DFS crawl to explore a blog, prioritizing paths under '/blog/archive/']`
            ```python
            from crawl4ai import (
                AsyncWebCrawler, CrawlerRunConfig, BrowserConfig,
                DFSDeepCrawlStrategy, FilterChain, URLPatternFilter
            )
            import asyncio

            async def dfs_example_crawl():
                # Filter to keep crawl within /blog/ subdirectories
                filters = FilterChain(filters=[
                    URLPatternFilter(patterns=["https://example.com/blog/.*"])
                ])

                dfs_strategy = DFSDeepCrawlStrategy(
                    max_depth=10,      # Allow going reasonably deep
                    filter_chain=filters,
                    max_pages=50       # But limit total pages
                )

                run_config = CrawlerRunConfig(
                    deep_crawl_strategy=dfs_strategy,
                    verbose=True
                )

                browser_config = BrowserConfig(headless=True)
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    # Using stream=True in strategy for immediate results
                    dfs_strategy.stream = True # Overriding here for demo
                    async for result in await crawler.arun(
                        url="https://example.com/blog/",
                        config=run_config
                    ):
                        if result.success:
                            print(f"Crawled (DFS): {result.url} (Depth: {result.metadata.get('depth')})")
                        else:
                            print(f"Failed (DFS): {result.url} - {result.error_message}")

            if __name__ == "__main__":
                asyncio.run(dfs_example_crawl())
            ```
    *   **3.2.3. Best Practices for DFS**
        *   **Mandatory `max_depth`:** Always set a reasonable `max_depth` to prevent the crawler from getting lost in very deep or cyclical paths.
        *   **Targeted Filtering:** Use `URLPatternFilter` or other specific filters to guide the DFS along the paths you're interested in.
        *   **Monitor `max_pages`:** If `max_pages` is hit before `max_depth` in many branches, your DFS might not be exploring the site effectively.
    *   **3.2.4. Common Pitfalls with DFS**
        *   **Crawler Traps:** DFS is particularly susceptible to getting stuck in "crawler traps" (e.g., links generating unique URLs infinitely, like calendars or poorly designed filters).
        *   **Missing Broad Content:** If relevant content is spread across many shallow branches, DFS might miss much of it if it goes deep into one branch and hits `max_pages`.
        *   **Order of Discovery:** The order in which pages are discovered can feel random if the site structure isn't well understood or filters aren't guiding the crawl.

*   **3.3. Best-First Search (`BestFirstCrawlingStrategy`)**
    *   **3.3.1. Understanding Best-First Traversal**
        *   **What is Best-First?** This strategy uses a priority queue to manage the URL frontier. Each URL added to the frontier is assigned a score by a `URLScorer`. The crawler always picks the URL with the highest score from the priority queue to process next.
        *   **Pros:**
            *   Highly efficient for targeted crawling when you can define what makes a URL "good" or "relevant."
            *   Focuses crawler resources on the most promising areas of a website first.
            *   Adaptable: By changing the scoring logic, you can radically alter the crawl's focus.
        *   **Cons:**
            *   Effectiveness is *heavily* dependent on the quality and design of the `URLScorer`. A bad scorer leads to a bad crawl.
            *   Can be more complex to configure due to the need to design and implement scoring logic.
            *   Might miss some relevant content if it consistently scores low and `max_pages` is reached.
        *   **Typical Use Cases:**
            *   Finding pages most relevant to a specific set of keywords.
            *   Prioritizing pages from high-authority domains or known good sources.
            *   Crawling recently updated or fresh content first.
            *   Combining multiple factors (e.g., relevance, freshness, authority) for sophisticated prioritization.
        *   `* Diagram: [Visual representation of Best-First traversal.
            1. Seed URL -> Scorer -> Add to PriorityQueue (URL, Score)
            2. Pop highest score URL from PQ -> Fetch & Process -> Discover Links
            3. For each Link: Filter -> (if valid) -> Scorer -> Add to PQ (Link, Score)
            4. Repeat from step 2.
            Show PQ reordering as new items are added with different scores.]`
    *   **3.3.2. Practical Usage of `BestFirstCrawlingStrategy`**
        *   **How to instantiate and pass it to `CrawlerRunConfig`:**
            ```python
            from crawl4ai import (
                BestFirstCrawlingStrategy, CrawlerRunConfig,
                KeywordRelevanceScorer, DomainFilter, FilterChain
            )

            # Scorer: Prioritize URLs with 'ai' and 'ethics'
            keyword_scorer = KeywordRelevanceScorer(keywords=['ai', 'ethics'], weight=1.0)

            # Filter: Only 'example.com'
            domain_filter = DomainFilter(allowed_domains=['example.com'])
            filter_chain = FilterChain(filters=[domain_filter])

            best_first_strategy = BestFirstCrawlingStrategy(
                url_scorer=keyword_scorer,
                filter_chain=filter_chain,
                max_depth=5,
                max_pages=200
            )
            run_config = CrawlerRunConfig(deep_crawl_strategy=best_first_strategy)
            ```
        *   **Crucial role of `url_scorer`:** This is the defining component. You *must* provide a `URLScorer` instance. This could be a single scorer or a `CompositeScorer`.
        *   **Interaction with `filter_chain`:** Filters are applied *before* scoring. Only URLs that pass all filters are then scored and considered for the priority queue.
        *   **Parameters:**
            *   `max_depth (int)`: Still relevant to prevent excessively deep exploration, even if scores guide the way.
            *   `max_pages (int, default=infinity)`: Important for limiting the overall crawl size.
            *   `include_external (bool, default=False)`: If `True`, external URLs that pass filters will also be scored and added to the queue.
        *   `* Code Example: [Setting up a Best-First crawl using CompositeScorer to find recent articles about "AI in finance" from specific financial news domains]`
            ```python
            from crawl4ai import (
                AsyncWebCrawler, CrawlerRunConfig, BrowserConfig,
                BestFirstCrawlingStrategy, FilterChain, DomainFilter,
                KeywordRelevanceScorer, FreshnessScorer, CompositeScorer
            )
            import asyncio
            from datetime import datetime

            async def best_first_example_crawl():
                # Scorers
                keyword_scorer = KeywordRelevanceScorer(
                    keywords=['ai', 'finance', 'fintech'],
                    weight=0.6
                )
                freshness_scorer = FreshnessScorer(
                    current_year=datetime.now().year,
                    weight=0.4
                )
                composite_scorer = CompositeScorer(
                    scorers=[keyword_scorer, freshness_scorer]
                )

                # Filters
                allowed_domains = ["reputablefinance.news", "fintechinsider.com"]
                filters = FilterChain(filters=[
                    DomainFilter(allowed_domains=allowed_domains)
                ])

                best_first_strategy = BestFirstCrawlingStrategy(
                    url_scorer=composite_scorer,
                    filter_chain=filters,
                    max_depth=4,
                    max_pages=100,
                    stream=True # Get results as they come
                )

                run_config = CrawlerRunConfig(
                    deep_crawl_strategy=best_first_strategy,
                    verbose=True
                )
                browser_config = BrowserConfig(headless=True)

                async with AsyncWebCrawler(config=browser_config) as crawler:
                    start_urls = [f"https://{domain}/" for domain in allowed_domains]
                    async for result in await crawler.arun_many(
                        urls=start_urls,
                        config=run_config
                    ):
                        if result.success:
                            print(f"Crawled (Best-First): {result.url} (Score: {result.metadata.get('score', 'N/A')}, Depth: {result.metadata.get('depth')})")

            if __name__ == "__main__":
                asyncio.run(best_first_example_crawl())
            ```
    *   **3.3.3. Best Practices for Best-First**
        *   **Design Effective Scoring:** The success of Best-First hinges on this. Think carefully about what makes a URL valuable for your goal.
        *   **Iterative Refinement:** Test your scorers. Observe the crawl path. Adjust weights and logic in your `CompositeScorer` or custom scorers based on results.
        *   **Balance Complexity and Performance:** While `CompositeScorer` is powerful, very complex scoring logic involving many external calls or heavy computations per URL can slow down the decision-making process.
        *   **Combine with Strong Filters:** Filters reduce the number of URLs that need to be scored, improving efficiency.
    *   **3.3.4. Common Pitfalls with Best-First**
        *   **Poor Scorer Configuration:** If the scorer doesn't align with your goals, the crawl will be misguided and inefficient (e.g., a keyword scorer with irrelevant keywords).
        *   **Score Normalization (if building custom composite logic):** Ensure scores from different components are on a somewhat comparable scale or that weights account for differences. `CompositeScorer` handles weighting but doesn't inherently normalize scores from sub-scorers.
        *   **Ignoring Potentially Valuable Branches:** If a relevant section of a site consistently scores low due to a quirk in the scoring logic, it might be missed if `max_pages` is too restrictive. Consider periodic "exploration" phases or adjusting scores.
        *   **Over-reliance on a Single Metric:** A `CompositeScorer` is often better than relying on just one type of score (e.g., just keywords) which might be too narrow.

## 4. Fine-Tuning Your Crawl: URL Filtering

Filters are your first line of defense against an unmanageable or irrelevant crawl. They ensure that only URLs meeting your criteria are even considered for fetching and further processing.

*   **4.1. The Importance of Effective Filtering**
    *   **Why filter?**
        *   **Save Resources:** Every skipped URL saves bandwidth, processing time, and memory.
        *   **Improve Speed:** A focused crawl finishes faster.
        *   **Enhance Relevance:** Ensures the data you collect is pertinent to your objectives.
        *   **Avoid Crawler Traps:** Prevents the crawler from getting stuck in infinite loops (e.g., calendars, endlessly paginated archives with slight URL variations).
        *   **Respect Site Policies:** Can be used to avoid crawling sensitive or disallowed sections (though `robots.txt` is the primary mechanism for this).
    *   **How `FilterChain` processes filters sequentially:**
        When you provide a `FilterChain` with multiple filters, a URL must pass *all* of them to be accepted. If `Filter1.apply(url)` returns `False`, the URL is rejected, and `Filter2`, `Filter3`, etc., are not even called for that URL. This "short-circuiting" behavior means you should order your filters strategically.
        `* Diagram: [URL -> Filter1 -> (if True) -> Filter2 -> (if True) -> Filter3 -> (if True) -> Accepted | (if False at any step) -> Rejected]`

*   **4.2. `DomainFilter`**
    *   **4.2.1. Purpose:** The most fundamental filter. It restricts the crawl to specific domains or subdomains (`allowed_domains`) and/or explicitly blocks certain domains (`blocked_domains`).
    *   **4.2.2. How it Works:** It extracts the netloc (e.g., `www.example.com`) from a URL.
        *   If `allowed_domains` is specified, the URL's domain (or a parent domain) must be in this list.
        *   If `blocked_domains` is specified, the URL's domain (or a parent domain) must *not* be in this list.
        *   If both are specified, it must satisfy the allow condition AND not satisfy the block condition.
        *   It handles subdomains correctly: if `example.com` is allowed, `blog.example.com` is also allowed. If `example.com` is blocked, `blog.example.com` is also blocked.
    *   **4.2.3. Configuration & Usage:**
        ```python
        from crawl4ai import DomainFilter, FilterChain

        # Allow only 'example.com' and its subdomains
        allow_example = DomainFilter(allowed_domains=["example.com"])

        # Block 'ads.example.com' and 'tracker.com'
        block_ads = DomainFilter(blocked_domains=["ads.example.com", "tracker.com"])

        # Combine them: only example.com, but not ads.example.com
        combined_filter = FilterChain(filters=[allow_example, block_ads])
        ```
        *   Wildcard usage is not directly supported in the `allowed_domains` list itself (e.g., `*.example.com`). You'd typically allow `example.com` which implicitly covers subdomains. For more complex pattern matching, use `URLPatternFilter`.
        *   `* Code Example: [Allowing 'blog.example.com' and 'docs.example.com', explicitly blocking 'ads.example.com', assuming 'example.com' is the main domain for other content.]`
            ```python
            # This setup means only blog.example.com and docs.example.com are allowed
            # and ads.example.com (if it were a subdomain of an allowed domain) would be blocked.
            # A more typical setup to crawl ONLY these two subdomains:
            specific_subdomains_filter = DomainFilter(allowed_domains=["blog.example.com", "docs.example.com"])

            # If you wanted to crawl example.com but exclude ads.example.com:
            crawl_main_exclude_ads = FilterChain(filters=[
                DomainFilter(allowed_domains=["example.com"]),
                DomainFilter(blocked_domains=["ads.example.com"])
            ])
            ```
    *   **4.2.4. Best Practices:**
        *   Almost always start your `FilterChain` with a `DomainFilter` specifying `allowed_domains` to keep your crawl focused.
        *   Be precise if you only want specific subdomains. Allowing a TLD (Top-Level Domain) like `.com` is generally not what you want unless you intend a very broad crawl.

*   **4.3. `ContentTypeFilter`**
    *   **4.3.1. Purpose:** To filter URLs based on their likely file extension, thereby inferring the content type. This is a quick way to avoid downloading large binary files, images, or unwanted document types.
    *   **4.3.2. How it Works:** By default (`check_extension=True`), it extracts the extension from the URL's path (e.g., `.html`, `.pdf`, `.jpg`). It then checks if this extension (or its corresponding MIME type via an internal map) is present in the `allowed_types`.
    *   **4.3.3. Configuration & Usage:**
        ```python
        from crawl4ai import ContentTypeFilter

        # Only allow HTML and PDF files
        html_pdf_filter = ContentTypeFilter(allowed_types=['.html', '.htm', '.pdf'])
        # OR by MIME type partial match (less common for this filter but possible):
        # html_pdf_filter_mime = ContentTypeFilter(allowed_types=['text/html', 'application/pdf'])
        ```
        *   The `allowed_types` can be a list of extensions (e.g., `'.jpg'`) or partial MIME types (e.g., `'image/'`, `'text/html'`).
        *   `check_extension=True` (default) is generally faster as it avoids needing actual content type from HTTP headers. Set to `False` if you must rely on `Content-Type` headers (note: this filter as shown in `filters.py` primarily works on extensions for pre-fetch filtering).
        *   `* Code Example: [Filtering to only allow HTML, HTM, and PHP files]`
            ```python
            webpage_filter = ContentTypeFilter(allowed_types=['.html', '.htm', '.php'])
            # This would allow URLs like:
            # https://example.com/page.html
            # https://example.com/article.php
            # But would block:
            # https://example.com/image.jpg
            # https://example.com/document.pdf
            ```
    *   **4.3.4. Best Practices:** Use this early in your filter chain to quickly discard URLs pointing to unwanted file types, saving bandwidth and processing for HEAD requests or full fetches that later filters might trigger.

*   **4.4. `URLPatternFilter`**
    *   **4.4.1. Purpose:** Provides fine-grained control over which URLs to process based on matching them against regular expressions or glob-style patterns.
    *   **4.4.2. How it Works:** It takes a list of `patterns`. For each URL, it checks if the URL string matches any of these patterns. The behavior depends on the `reverse` flag.
    *   **4.4.3. Configuration & Usage:**
        ```python
        from crawl4ai import URLPatternFilter

        # Allow only URLs under '/blog/' or '/products/'
        blog_products_filter = URLPatternFilter(
            patterns=[r".*/blog/.*", r".*/products/.*"] # Regex patterns
        )

        # Exclude URLs containing '/archive/' or '/temp/'
        exclude_archive_filter = URLPatternFilter(
            patterns=[r".*/archive/.*", r".*/temp/.*"],
            reverse=True # Exclude if matches
        )
        ```
        *   `patterns`: A list of strings. These are treated as regular expressions by default (Python's `re` module). The provided code shows `fnmatch.translate` is used, which converts glob patterns to regex, but also handles direct regex if it detects regex-specific characters like `^`, `$`, `\d`.
        *   `reverse (bool, default=False)`: If `False` (default), the URL passes if it matches *any* pattern. If `True`, the URL passes only if it matches *none* of the patterns (effectively a blocklist).
        *   `* Code Example: [Allowing only URLs matching '/articles/[year]/[month]/[slug]' and excluding any URL containing '?replytocom=']`
            ```python
            article_path_filter = URLPatternFilter(
                patterns=[r"/articles/\d{4}/\d{2}/[\w-]+/?$"] # Matches /articles/YYYY/MM/slug
            )
            no_reply_filter = URLPatternFilter(
                patterns=[r"\?replytocom="],
                reverse=True # Exclude if it contains replytocom
            )
            # In a FilterChain, these would apply sequentially
            # final_chain = FilterChain(filters=[article_path_filter, no_reply_filter])
            ```
    *   **4.4.4. Best Practices:**
        *   Use for complex URL structures that `DomainFilter` or `ContentTypeFilter` can't handle.
        *   Test your regular expressions thoroughly to ensure they match what you intend and don't have unintended side effects or performance issues. Online regex testers can be very helpful.
        *   Prefer simpler string methods or other filters if a regex is overkill, as regex can be slower.

*   **4.5. `ContentRelevanceFilter` (Requires HEAD requests)**
    *   **4.5.1. Purpose:** To pre-filter URLs based on the relevance of their metadata (title, meta description, keywords found in the `<head>` section) to a given query, using the BM25 ranking algorithm. This helps in prioritizing or including only pages that are likely to be about a specific topic *before* downloading the full content.
    *   **4.5.2. How it Works:**
        1.  Performs an HTTP HEAD request to fetch the headers of the URL.
        2.  If successful, it uses `HeadPeek` to extract text content from `<title>`, `<meta name="description">`, and `<meta name="keywords">` tags from the response (if the HEAD response contains enough of the head, which is not guaranteed and server-dependent. Often, servers don't send body content with HEAD).
        3.  Calculates a BM25 relevance score between the extracted text and the user-provided `query`.
        4.  The URL passes if the score is above the specified `threshold`.
        *   **Important Note on HEAD requests:** While HEAD requests are designed to be lightweight, not all servers implement them correctly or return meaningful content previews in the head. Some servers might return the full HTML head, others might return very little, and some might even block HEAD requests. The effectiveness of this filter depends heavily on server behavior.
    *   **4.5.3. Configuration & Usage:**
        ```python
        from crawl4ai import ContentRelevanceFilter

        relevance_filter = ContentRelevanceFilter(
            query="AI in healthcare applications",
            threshold=0.3,  # Adjust based on desired strictness
            # k1=1.2, b=0.75, avgdl=1000 are BM25 parameters, defaults are usually fine
        )
        ```
        *   `query (str)`: The search query to compare against.
        *   `threshold (float)`: The minimum BM25 score for a URL to pass.
        *   `k1`, `b`, `avgdl`: BM25 algorithm parameters. Defaults are generally reasonable.
        *   `* Code Example: [Filtering for pages potentially relevant to "sustainable energy solutions" with a score threshold of 0.25]`
            ```python
            # Assuming this filter is part of a FilterChain
            sustainable_energy_filter = ContentRelevanceFilter(
                query="sustainable energy solutions impact",
                threshold=0.25
            )
            # This would attempt to fetch HEAD for candidate URLs and check their head content.
            ```
    *   **4.5.4. When to Use:**
        *   When you need a preliminary content relevance check before committing to a full page download and processing.
        *   For highly targeted crawls where topic relevance is paramount.
        *   Be mindful of the performance implications: each HEAD request adds network latency. This filter is best used after broader, faster filters (like `DomainFilter`, `ContentTypeFilter`).
        *   Test with target sites to see if their HEAD responses are useful for this filter.

*   **4.6. `SEOFilter` (Requires HEAD requests)**
    *   **4.6.1. Purpose:** To filter URLs based on a quantitative assessment of their basic on-page SEO quality, derived from elements in the `<head>` section.
    *   **4.6.2. How it Works:**
        1.  Similar to `ContentRelevanceFilter`, it performs an HTTP HEAD request.
        2.  It then uses `HeadPeek` to extract information like title length, presence and length of meta description, canonical URL validity, robots meta tag status (e.g., `noindex`), schema.org markup presence, and general URL "quality" heuristics (length, parameters, underscores).
        3.  Each factor is scored, and a weighted total score is calculated.
        4.  The URL passes if the total score is above the specified `threshold`.
    *   **4.6.3. Configuration & Usage:**
        ```python
        from crawl4ai import SEOFilter

        seo_quality_filter = SEOFilter(
            threshold=0.65,  # Pages must meet at least 65% of SEO quality checks
            keywords=['data science', 'machine learning'], # Optional: boost score if these appear
            # weights: Optional dict to customize scoring of different SEO factors
        )
        ```
        *   `threshold (float)`: Minimum overall SEO score (0.0 to 1.0) for the URL to pass.
        *   `keywords (Optional[List[str]])`: If provided, presence of these keywords in title or meta description can boost the score.
        *   `weights (Optional[Dict[str, float]])`: Allows customization of how much each SEO factor (e.g., `"title_length"`, `"meta_description"`, `"canonical"`) contributes to the total score. See `SEOFilter.DEFAULT_WEIGHTS` for default factors and their weights.
        *   `* Code Example: [Filtering for pages with an SEO score > 0.7, particularly looking for pages optimized for "python programming tutorials"]`
            ```python
            python_tutorial_seo_filter = SEOFilter(
                threshold=0.7,
                keywords=["python programming tutorials", "learn python"]
            )
            # This filter would favor pages that are generally well-optimized for SEO
            # and also contain the specified keywords.
            ```
    *   **4.6.4. When to Use:**
        *   Performing SEO audits to quickly identify pages with potential on-page issues.
        *   Targeting well-optimized pages for content scraping or analysis.
        *   Like `ContentRelevanceFilter`, be aware of HEAD request overhead. Use after faster filters.

*   **4.7. Building Effective `FilterChain`s**
    *   **Order of filters matters:** This is crucial for performance.
        1.  **Fastest, broadest filters first:** Start with `DomainFilter` to immediately exclude irrelevant domains. Follow with `ContentTypeFilter` to discard unwanted file types by extension. `URLPatternFilter` with simple patterns can also be early.
        2.  **More expensive filters later:** Filters requiring network requests (like `ContentRelevanceFilter`, `SEOFilter`) or complex computations should come last, so they only operate on a reduced set of URLs.
    *   **Combining allow and deny logic:** Use multiple `DomainFilter` or `URLPatternFilter` instances (some with `reverse=True`) to create include/exclude rules. For example, allow `example.com` but block `example.com/private/`.
    *   `* Code Example: [A FilterChain demonstrating strategic ordering]`
        ```python
        from crawl4ai import (
            FilterChain, DomainFilter, ContentTypeFilter, URLPatternFilter,
            ContentRelevanceFilter
        )

        # Goal: Crawl blog posts about "AI ethics" on 'myblog.com',
        #       excluding PDFs and archive sections, ensuring basic relevance.

        # 1. Domain Filter: Only 'myblog.com'
        domain_filter = DomainFilter(allowed_domains=["myblog.com"])

        # 2. Content Type Filter: Only HTML
        content_type_filter = ContentTypeFilter(allowed_types=['.html', '.htm'])

        # 3. URL Pattern Filter: Exclude '/archive/'
        archive_exclude_filter = URLPatternFilter(patterns=[r"/archive/"], reverse=True)

        # 4. Content Relevance Filter: Must be somewhat about "AI ethics"
        relevance_filter = ContentRelevanceFilter(query="AI ethics", threshold=0.2)


        effective_chain = FilterChain(filters=[
            domain_filter,
            content_type_filter,
            archive_exclude_filter,
            relevance_filter  # This one makes HEAD requests, so it's last
        ])

        # This chain would be passed to a DeepCrawlStrategy
        # bfs_strategy = BFSDeepCrawlStrategy(max_depth=3, filter_chain=effective_chain)
        ```
        This example shows how to layer filters: first, quickly narrow down by domain and content type, then apply URL pattern rules, and finally, perform the more costly relevance check on the remaining candidates.

## 5. Prioritizing URLs: Scoring Mechanisms

URL scoring is the cornerstone of the `BestFirstCrawlingStrategy`. It allows you to define what "best" means for your crawl, guiding the crawler to explore the most promising URLs first.

*   **5.1. Why Score URLs?**
    *   **Guided Exploration:** Directs the `BestFirstCrawlingStrategy` to URLs that are most likely to contain the information you seek.
    *   **Resource Optimization:** If you have a `max_pages` limit or a time constraint, scoring helps ensure that the most valuable pages are processed before the limit is reached.
    *   **Relevance Ranking:** Allows you to implicitly rank discovered pages by their potential importance or relevance to your task.
    *   **Focus:** Helps concentrate crawling efforts on specific types of content (e.g., fresh news, product pages, high-authority articles).

*   **5.2. `CompositeScorer`: Combining Multiple Signals**
    *   **How it works:** `CompositeScorer` takes a list of individual `URLScorer` instances. For a given URL, it calls the `score()` method of each child scorer. The final score for the URL is typically a weighted sum of the scores from these individual scorers. Each child scorer's raw score is multiplied by its assigned `weight` (which defaults to 1.0 if not specified when adding the scorer to the `CompositeScorer`).
        ```python
        from crawl4ai import CompositeScorer, KeywordRelevanceScorer, PathDepthScorer

        keyword_scorer = KeywordRelevanceScorer(keywords=["news", "update"], weight=0.7)
        path_scorer = PathDepthScorer(optimal_depth=2, weight=0.3)

        # The CompositeScorer will calculate:
        # final_score = (keyword_scorer.score(url) * 0.7) + (path_scorer.score(url) * 0.3)
        # Note: The individual scorers' `weight` parameter is used by CompositeScorer.
        # It is more common to set weights when adding to CompositeScorer if that API exists,
        # or ensure individual scorers output in a way that their inherent weight makes sense.
        # Based on the code: CompositeScorer sums the results of `scorer.score(url)` directly,
        # which already includes the scorer's own weight.
        # So, the weights are applied within each scorer before summing.

        # Corrected understanding based on code:
        # Each scorer's score() method already incorporates its own weight.
        # CompositeScorer simply sums these pre-weighted scores.
        composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])
        # final_score = keyword_scorer.score(url) + path_scorer.score(url)
        # where keyword_scorer.score(url) is raw_keyword_score * 0.7
        # and path_scorer.score(url) is raw_path_score * 0.3
        ```
    *   **Normalizing scores:** The individual scorers in Crawl4ai are generally designed to output scores that are somewhat normalized (often between 0 and 1 before their internal weight is applied). However, if you create custom scorers with vastly different output ranges, their contribution to the `CompositeScorer` might be skewed. It's good practice to design custom scorers to produce scores in a relatively consistent range (e.g., 0-1) before their `weight` is applied, or adjust their individual `weight`s accordingly to balance their influence in the `CompositeScorer`. The `CompositeScorer` itself simply sums the already weighted scores from its child scorers.
    *   `* Code Example: [Creating a CompositeScorer combining KeywordRelevanceScorer, FreshnessScorer, and DomainAuthorityScorer. Keyword relevance is most important, followed by freshness, then domain authority.]`
        ```python
        from crawl4ai import (
            CompositeScorer, KeywordRelevanceScorer, FreshnessScorer,
            DomainAuthorityScorer
        )
        from datetime import datetime

        # Scorer for keywords, highly weighted
        keyword_scorer = KeywordRelevanceScorer(
            keywords=["financial analysis", "market trends"],
            weight=0.5 # This weight is applied internally by KeywordRelevanceScorer
        )

        # Scorer for freshness, moderately weighted
        freshness_scorer = FreshnessScorer(
            current_year=datetime.now().year,
            weight=0.3
        )

        # Scorer for domain authority, less weighted
        domain_scorer = DomainAuthorityScorer(
            domain_weights={"bloomberg.com": 0.9, "reuters.com": 0.85, "wsj.com": 0.95},
            default_weight=0.5, # For other domains
            weight=0.2
        )

        # CompositeScorer sums the weighted scores from each child scorer
        final_url_scorer = CompositeScorer(
            scorers=[keyword_scorer, freshness_scorer, domain_scorer]
        )
        # Example URL score calculation:
        # url = "https://www.bloomberg.com/news/articles/2023-10-26/ai-impact-on-finance"
        # score_for_url = final_url_scorer.score(url)
        # This would be:
        # (raw_keyword_score_for_url * 0.5) + \
        # (raw_freshness_score_for_url * 0.3) + \
        # (raw_domain_score_for_url * 0.2)
        ```

*   **5.3. `KeywordRelevanceScorer`**
    *   **5.3.1. Purpose:** Scores URLs based on how many of the specified keywords appear within the URL string itself. This is a simple way to prioritize URLs that seem topically relevant by their path or query parameters.
    *   **5.3.2. How it Works:** It iterates through the provided list of `keywords`. For each keyword, it checks if it's present in the URL (case-insensitively by default). The score is typically proportional to the number of matched keywords, normalized by the total number of keywords, and then multiplied by the scorer's `weight`.
    *   **5.3.3. Configuration & Usage:**
        ```python
        from crawl4ai import KeywordRelevanceScorer

        # Prioritize URLs related to Python or Machine Learning
        tech_keyword_scorer = KeywordRelevanceScorer(
            keywords=["python", "machine learning", "pytorch"],
            weight=1.0,       # Overall weight for this scorer
            case_sensitive=False # Default
        )
        ```
        *   `keywords (List[str])`: A list of keywords to search for in the URL.
        *   `weight (float, default=1.0)`: A multiplier applied to the raw score.
        *   `case_sensitive (bool, default=False)`: Whether keyword matching should be case-sensitive.
        *   `* Code Example: [Scoring URLs for a job board, prioritizing those containing "remote", "engineer", or "developer"]`
            ```python
            job_url_scorer = KeywordRelevanceScorer(
                keywords=["remote", "engineer", "developer", "software"],
                weight=1.0
            )
            # Example scores:
            # score1 = job_url_scorer.score("https://jobs.example.com/remote-software-engineer-position") # high score
            # score2 = job_url_scorer.score("https://jobs.example.com/marketing-manager-sf")         # lower score
            ```

*   **5.4. `DomainAuthorityScorer` (Conceptual/External Data)**
    *   **5.4.1. Purpose:** To give preference to URLs from domains that are considered more authoritative or trustworthy. This requires you to provide the authority scores.
    *   **5.4.2. How it Works:** It uses a dictionary (`domain_weights`) that maps domain names (e.g., `"wikipedia.org"`) to numerical authority scores (e.g., `0.9`). When a URL is scored, its domain is extracted. If the domain is in `domain_weights`, its score is used; otherwise, `default_weight` is applied. This raw score is then multiplied by the scorer's overall `weight`.
    *   **5.4.3. Configuration & Usage:**
        ```python
        from crawl4ai import DomainAuthorityScorer

        authority_scorer = DomainAuthorityScorer(
            domain_weights={
                "wikipedia.org": 0.9,
                "scholar.google.com": 0.85,
                "archive.org": 0.7
            },
            default_weight=0.3, # Score for domains not in the list
            weight=1.0          # Overall weight for this scorer's contribution
        )
        ```
        *   `domain_weights (Dict[str, float])`: A dictionary mapping domain strings to their authority scores (typically 0-1).
        *   `default_weight (float, default=0.5)`: Score assigned to URLs from domains not explicitly listed in `domain_weights`.
        *   `weight (float, default=1.0)`: Multiplier for the final score from this scorer.
        *   `* Code Example: [In a news crawl, giving higher scores to URLs from 'bbc.com', 'nytimes.com', and 'reuters.com']`
            ```python
            news_authority_scorer = DomainAuthorityScorer(
                domain_weights={
                    "bbc.com": 0.95,
                    "nytimes.com": 0.9,
                    "reuters.com": 0.88
                },
                default_weight=0.4, # Other news sources
                weight=1.0
            )
            # score_bbc = news_authority_scorer.score("https://www.bbc.com/news/world-europe-12345")
            # score_local_blog = news_authority_scorer.score("https://my-local-blog.com/news-update")
            ```
    *   **5.4.4. Note:** This scorer's effectiveness depends entirely on the quality and relevance of the `domain_weights` you provide. There's no built-in mechanism in Crawl4ai to automatically determine domain authority; you must supply this data.

*   **5.5. `FreshnessScorer`**
    *   **5.5.1. Purpose:** To prioritize URLs that appear to contain more recent content, typically by looking for date patterns (especially years) in the URL string.
    *   **5.5.2. How it Works:** It uses regular expressions to find date patterns (like YYYY/MM/DD, YYYY-MM-DD, YYYY_MM_DD, or just YYYY) in the URL. It extracts the most recent valid year found. The score is then calculated based on the difference between this extracted year and the `current_year` provided during initialization. More recent years get higher scores. The pre-defined `_FRESHNESS_SCORES` list provides a quick lookup for common year differences.
    *   **5.5.3. Configuration & Usage:**
        ```python
        from crawl4ai import FreshnessScorer
        from datetime import datetime

        # Prioritize content from the current year or last few years
        current_year = datetime.now().year
        freshness_scorer = FreshnessScorer(
            current_year=current_year,
            weight=1.0
        )
        ```
        *   `current_year (int)`: The reference year for calculating freshness.
        *   `weight (float, default=1.0)`: Multiplier for the final score.
        *   Date patterns detected: The `_date_pattern` regex in `scorers.py` looks for common date formats.
        *   `* Code Example: [Prioritizing news articles or blog posts from 2023 onwards, assuming current year is 2024]`
            ```python
            # Assuming it's 2024
            recent_content_scorer = FreshnessScorer(current_year=2024, weight=1.0)
            # score_2023 = recent_content_scorer.score("https://example.com/blog/2023/10/my-article") # High score
            # score_2020 = recent_content_scorer.score("https://example.com/archive/2020/old-post") # Lower score
            # score_no_date = recent_content_scorer.score("https://example.com/about-us")      # Default score (0.5)
            ```

*   **5.6. `PathDepthScorer`**
    *   **5.6.1. Purpose:** Scores URLs based on their path depth, which is the number of segments in the URL path (e.g., `/folder1/folder2/page.html` has depth 3). This can be used to prefer shallower pages (often more important) or pages around a specific `optimal_depth`.
    *   **5.6.2. How it Works:** It parses the URL to count the number of segments in its path. The scoring logic (from `_LOOKUP_SCORES`) gives higher scores to depths closer to `optimal_depth`. Depths further away receive progressively lower scores.
    *   **5.6.3. Configuration & Usage:**
        ```python
        from crawl4ai import PathDepthScorer

        # Prefer pages with a path depth of 2 or 3
        path_scorer = PathDepthScorer(
            optimal_depth=2, # Or 3, depending on preference
            weight=1.0
        )
        ```
        *   `optimal_depth (int, default=3)`: The path depth considered most desirable.
        *   `weight (float, default=1.0)`: Multiplier for the final score.
        *   `* Code Example: [Slightly preferring top-level category pages (depth 1) or main articles (depth 2)]`
            ```python
            shallow_page_scorer = PathDepthScorer(optimal_depth=1, weight=1.0)
            # score_depth1 = shallow_page_scorer.score("https://example.com/products/")  # High score (closer to 1.0)
            # score_depth3 = shallow_page_scorer.score("https://example.com/products/category/item") # Lower score
            ```
        The scoring is based on the difference from `optimal_depth`, using `_SCORE_LOOKUP = [1.0, 0.5, 0.333..., 0.25]`. A difference of 0 gets 1.0, 1 gets 0.5, etc.

*   **5.7. `ContentTypeScorer`**
    *   **5.7.1. Purpose:** Assigns scores to URLs based on their inferred content type, primarily determined by the file extension. This allows prioritizing certain types of content (e.g., HTML pages over images or documents).
    *   **5.7.2. How it Works:** It extracts the file extension from the URL. If this extension is found as a key in the `type_weights` dictionary provided during initialization, the corresponding score is used. If the extension is not found, a default score of 0.0 is typically assigned (unless `type_weights` provides a wildcard or default). The raw score is then multiplied by the scorer's `weight`.
    *   **5.7.3. Configuration & Usage:**
        ```python
        from crawl4ai import ContentTypeScorer

        html_priority_scorer = ContentTypeScorer(
            type_weights={
                '.html': 1.0,
                '.htm': 1.0,
                '.pdf': 0.7,
                '.doc': 0.5,
                '.jpg': 0.2,
                '.png': 0.2
            },
            weight=1.0
        )
        ```
        *   `type_weights (Dict[str, float])`: A dictionary mapping file extensions (including the dot, e.g., `'.html'`) to scores.
        *   `weight (float, default=1.0)`: Multiplier for the final score.
        *   `* Code Example: [Prioritizing HTML and PDF documents, while down-weighting images and executables for a document-focused crawl]`
            ```python
            document_content_scorer = ContentTypeScorer(
                type_weights={
                    '.html': 1.0, '.htm': 1.0,
                    '.pdf': 0.9, '.doc': 0.8, '.docx': 0.8,
                    '.txt': 0.7,
                    '.jpg': 0.1, '.png': 0.1, '.gif': 0.1,
                    '.exe': 0.0, '.zip': 0.05
                },
                weight=1.0
            )
            # score_html = document_content_scorer.score("https://example.com/index.html") # High
            # score_zip = document_content_scorer.score("https://example.com/archive.zip") # Low
            ```

*   **5.8. `URLScorer` (Base Class)**
    *   If the built-in scorers or their combination via `CompositeScorer` don't meet your specific needs, you can create a highly custom scorer by inheriting from the `URLScorer` base class.
    *   **Key method to implement:** `_calculate_score(self, url: str) -> float`. This method should take a URL string and return a float representing its score. Remember that the `score(self, url:str)` public method will automatically multiply this by `self._weight`.
    *   Consider the range of scores your custom scorer produces to ensure it integrates well if used within a `CompositeScorer`.

## 6. Configuring and Running Deep Crawls

The `CrawlerRunConfig` object is central to configuring how any specific crawl, including deep crawls, behaves. You'll pass your chosen `DeepCrawlStrategy` (along with its configured filters and scorers) to it.

*   **6.1. The Role of `CrawlerRunConfig`**
    *   The `deep_crawl_strategy` parameter of `CrawlerRunConfig` is how you enable and configure deep crawling for a specific `arun()` or `arun_many()` call.
    *   You instantiate your chosen strategy (e.g., `BFSDeepCrawlStrategy`), configure it with any `FilterChain` and `URLScorer` instances, and then assign this strategy object to `CrawlerRunConfig.deep_crawl_strategy`.
    *   `* Code Example: [Illustrating how strategy is passed to CrawlerRunConfig]`
        ```python
        from crawl4ai import (
            AsyncWebCrawler, CrawlerRunConfig, BFSDeepCrawlStrategy,
            DomainFilter, FilterChain
        )
        import asyncio

        # 1. Define Filters and Scorers (if needed)
        my_filters = FilterChain(filters=[DomainFilter(allowed_domains=["example.com"])])

        # 2. Instantiate and Configure the Strategy
        my_bfs_strategy = BFSDeepCrawlStrategy(max_depth=2, filter_chain=my_filters)

        # 3. Create CrawlerRunConfig and assign the strategy
        my_run_config = CrawlerRunConfig(
            deep_crawl_strategy=my_bfs_strategy,
            # ... other run-specific settings like cache_mode, verbosity, etc.
            cache_mode=CacheMode.BYPASS,
            verbose=True
        )

        async def main():
            async with AsyncWebCrawler() as crawler:
                results = await crawler.arun(url="https://example.com", config=my_run_config)
                for result in results: # arun returns a CrawlResultContainer
                    if result.success:
                        print(f"Crawled: {result.url} - Depth: {result.metadata.get('depth')}")
        # asyncio.run(main())
        ```

*   **6.2. Essential Global Deep Crawl Parameters in `DeepCrawlStrategy` (and reflected in `CrawlerRunConfig`)**
    These parameters are generally set on the strategy object itself.
    *   **`max_depth`:**
        *   **Meaning:**
            *   **BFS:** The maximum number of levels to explore from the seed URL(s). Level 0 is the seed.
            *   **DFS:** The maximum number of links to follow down a single path before backtracking.
            *   **Best-First:** While primarily score-driven, `max_depth` still acts as an upper limit on how deep any single path can go, preventing infinite exploration even if scores are high.
        *   **Strategies for choosing `max_depth`:**
            *   Start small (e.g., 1 or 2) and observe the number of pages found.
            *   Increase incrementally based on your understanding of the target site's structure and your data needs.
            *   For very large sites, a high `max_depth` can lead to an enormous number of URLs.
        *   `* Diagram: [Show two small site graphs. One with max_depth=1, showing only direct links. Another with max_depth=2, showing links of links. Highlight the exponential growth potential.]`
    *   **`max_pages`:**
        *   **How it acts as a global stop condition:** Regardless of `max_depth` or strategy, the crawl will halt once `max_pages` have been successfully processed.
        *   **Interaction with `max_depth` and strategy:**
            *   A crawl might hit `max_pages` before reaching `max_depth` on all branches.
            *   For BFS, this means some deeper levels might not be touched.
            *   For DFS, this means some branches might not be fully explored.
            *   For Best-First, this means lower-scoring URLs might never be visited.
        *   **Use cases:**
            *   Budgeting crawl resources (time, bandwidth, API calls if any).
            *   Getting a quick sample or overview of a site.
            *   Preventing runaway crawls on unexpectedly large sites.
    *   **`include_external` (Context: Typically a parameter on the strategy, e.g., `BestFirstCrawlingStrategy` and other strategies in `crawl4ai`):**
        *   **What it does:** If `True`, the crawler will follow links to domains different from the seed URL's domain.
        *   **When to use it:**
            *   Discovering backlinks or references to your site from external sources (though this is usually done by starting crawls on those external sources).
            *   Exploring a small, trusted ecosystem of related websites.
        *   **Potential pitfalls:**
            *   **Crawl Scope Explosion:** The web is vast. Without *extremely* strict filters (`DomainFilter` for allowed external domains, `URLPatternFilter`), enabling `include_external` can lead to an unmanageably large and irrelevant crawl.
            *   **Resource Drain:** Crawling external sites consumes your resources for potentially off-topic content.
            *   **Best Practice:** Keep `include_external=False` (the default for most strategies) unless you have a very specific reason and robust filters in place. If you need to crawl multiple specific domains, it's often better to run separate, focused crawls for each or use `arun_many` with a list of seed URLs.

*   **6.3. Practical Examples of `CrawlerRunConfig` for Deep Crawls**
    *   `* Code Example: [BFS crawl limited to depth 3 within 'example.com', only HTML pages, verbose logging]`
        ```python
        bfs_strat_example = BFSDeepCrawlStrategy(
            max_depth=3,
            filter_chain=FilterChain(filters=[
                DomainFilter(allowed_domains=["example.com"]),
                ContentTypeFilter(allowed_types=['.html', '.htm'])
            ])
        )
        run_config_bfs = CrawlerRunConfig(
            deep_crawl_strategy=bfs_strat_example,
            verbose=True,
            cache_mode=CacheMode.BYPASS # Forcing fresh crawl for example
        )
        # Usage: await crawler.arun(url="https://example.com", config=run_config_bfs)
        ```
    *   `* Code Example: [DFS crawl following '/blog/' paths, max 50 pages, stream results]`
        ```python
        dfs_strat_example = DFSDeepCrawlStrategy(
            max_depth=10, # DFS can go deep
            max_pages=50,
            filter_chain=FilterChain(filters=[
                URLPatternFilter(patterns=[r"https://example.com/blog/.*"])
            ]),
            stream=True # Yield results as they are found
        )
        run_config_dfs = CrawlerRunConfig(
            deep_crawl_strategy=dfs_strat_example,
            verbose=True
        )
        # Usage:
        # async for result in await crawler.arun(url="https://example.com/blog/", config=run_config_dfs):
        #     # process result
        ```
    *   `* Code Example: [Best-First crawl for "AI ethics" articles, prioritizing recent, high-authority sources, excluding PDFs, max 100 pages]`
        ```python
        from crawl4ai import KeywordRelevanceScorer, FreshnessScorer, DomainAuthorityScorer, CompositeScorer, ContentTypeFilter
        from datetime import datetime

        # Scorers
        keyword_scorer_ai_ethics = KeywordRelevanceScorer(keywords=["AI ethics", "responsible AI"], weight=0.6)
        freshness_scorer_recent = FreshnessScorer(current_year=datetime.now().year, weight=0.25)
        authority_scorer_news = DomainAuthorityScorer(
            domain_weights={"techcrunch.com": 0.8, "wired.com": 0.85},
            default_weight=0.4,
            weight=0.15
        )
        composite_scorer_ai = CompositeScorer(scorers=[
            keyword_scorer_ai_ethics, freshness_scorer_recent, authority_scorer_news
        ])

        # Filters
        filter_chain_ai = FilterChain(filters=[
            DomainFilter(allowed_domains=["techcrunch.com", "wired.com", "another-news-site.com"]),
            ContentTypeFilter(allowed_types=['.html']) # Exclude PDFs by only allowing HTML
        ])

        best_first_strat_ai = BestFirstCrawlingStrategy(
            url_scorer=composite_scorer_ai,
            filter_chain=filter_chain_ai,
            max_pages=100,
            max_depth=5 # Still good to have a depth limit
        )
        run_config_best_first_ai = CrawlerRunConfig(
            deep_crawl_strategy=best_first_strat_ai,
            verbose=True
        )
        # Usage: await crawler.arun(url="https://techcrunch.com", config=run_config_best_first_ai)
        ```

*   **6.4. Integrating with `AsyncWebCrawler.arun()` and `AsyncWebCrawler.arun_many()`**
    *   **`arun(url="seed_url", config=run_config_with_deep_crawl)`:**
        When you call `arun` with a `CrawlerRunConfig` that includes a `deep_crawl_strategy`, the deep crawling process starts from the single `seed_url`. The `DeepCrawlDecorator` intercepts this and delegates to your strategy.
    *   **`arun_many(urls=["seed1", "seed2"], config=run_config_with_deep_crawl)`:**
        If you use `arun_many`, Crawl4ai will typically initiate *independent* deep crawls starting from each seed URL in the `urls` list. Each deep crawl will adhere to the `max_depth`, `max_pages`, filters, and scorers defined in the *same* `run_config_with_deep_crawl`.
        *   **Important Consideration:** The `max_pages` limit in this scenario usually applies *per seed URL's deep crawl task* if the dispatcher handles them as separate tasks. If you need a global `max_pages` across all seed URLs in an `arun_many` call, that would require a more custom dispatcher or a wrapper around `arun_many` to track the total pages. The default behavior is often per-task limits.
        *   If `stream=True` is set on the strategy (or within the `run_config`), results from the different deep crawls initiated by `arun_many` will be yielded as they become available.

## 7. Understanding the `DeepCrawlDecorator`

While you primarily interact with deep crawling through `CrawlerRunConfig` and strategy objects, it's helpful to have a conceptual understanding of the `DeepCrawlDecorator`.

*   **7.1. How Deep Crawling is Activated (Conceptual)**
    *   **Role of `DeepCrawlDecorator`:** The `DeepCrawlDecorator` is a Python decorator that wraps the `AsyncWebCrawler.arun()` method. When `arun()` is called, the decorator checks if the `config` argument (an instance of `CrawlerRunConfig`) has a `deep_crawl_strategy` defined.
    *   If a `deep_crawl_strategy` is present *and* deep crawling is not already active (see `deep_crawl_active` below), the decorator intercepts the call. Instead of the standard single-page crawl, it invokes the `arun()` method of your specified `deep_crawl_strategy` instance, passing along the crawler, seed URL, and configuration.
    *   If no `deep_crawl_strategy` is set, or if deep crawling is already active, the decorator allows the original `arun()` method (for single-page crawling) to proceed.
    *   **The `deep_crawl_active` `ContextVar`:** This is a context variable (from Python's `contextvars` module). The decorator sets `deep_crawl_active` to `True` before calling the strategy's `arun()` method and resets it to `False` afterwards.
        *   **Purpose:** Its primary function is to prevent accidental recursive deep crawls. If your `deep_crawl_strategy` internally calls `crawler.arun()` (which it typically does to fetch individual pages), this flag ensures that those internal calls perform standard single-page fetches and don't try to initiate another layer of deep crawling using the same strategy.

*   **7.2. What This Means for You as a User**
    *   **Transparency:** For most use cases, the `DeepCrawlDecorator` operates transparently. You don't need to instantiate or call it directly.
    *   **Centralized Configuration:** You enable and configure deep crawling by setting the `deep_crawl_strategy` attribute in your `CrawlerRunConfig` object. This is the main entry point.
    *   **Awareness for Advanced Scenarios:** Understanding its existence is useful if:
        *   You are debugging complex deep crawling behavior and want to trace the execution flow.
        *   You are developing very custom strategies that might need to interact with or be aware of this context.

## 8. Monitoring and Analyzing Deep Crawl Performance

Understanding what happened during your deep crawl is key to optimizing it.

*   **8.1. Using `TraversalStats`**
    *   **Accessing `TraversalStats`:**
        *   The `BFSDeepCrawlStrategy`, `DFSDeepCrawlStrategy`, and `BestFirstCrawlingStrategy` (and their base class `DeepCrawlStrategy`) maintain a `self.stats` attribute of type `TraversalStats`.
        *   After a crawl initiated by one of these strategies completes (or even during, if you have access to the strategy instance), you can inspect `strategy_instance.stats`.
        *   The strategies also log these stats upon completion (or at intervals if verbose logging is high).
    *   **Key Metrics and Their Meaning (from `TraversalStats` in `crawl4ai/deep_crawling/base_strategy.py` and related files):**
        *   `start_time`, `end_time`: The overall start and end Python `datetime` objects for the crawl.
        *   `urls_processed` (often part of `FilterStats` within a strategy or a general counter): Total number of unique URLs that were actually fetched and processed by the crawler.
        *   `urls_failed`: Count of URLs that resulted in an error during fetching or processing.
        *   `urls_skipped`: Count of URLs that were discovered but discarded by the `FilterChain` or other conditions (e.g., already visited, exceeded `max_depth`).
        *   `total_depth_reached`: The maximum depth level explored during the crawl.
        *   `current_depth` (Relevant for strategies like BFS/DFS): The current depth level being explored.
        *   Individual filters (`URLFilter` subclasses) also have their own `FilterStats` (`filter.stats`) which track `total_urls` processed by that filter, `passed_urls`, and `rejected_urls`. This is very useful for seeing which filter is having the most impact.
    *   **Interpreting Stats for Optimization:**
        *   **High `urls_skipped` (overall) or high `rejected_urls` (for a specific filter):** This indicates your filters are very active. Review them to ensure they aren't too restrictive or are correctly configured.
        *   **`total_depth_reached` < `max_depth` (when `max_pages` is high):** This could mean the crawl exhausted all discoverable links within the filter scope before reaching the maximum depth, or filters are preventing deeper exploration.
        *   **Crawl finishes too quickly and `urls_processed` is low:** Check seed URLs, initial filters, and `max_depth/max_pages` limits.
        *   **Crawl takes too long:**
            *   Are filters too loose?
            *   Is `max_depth` or `max_pages` too high for the site?
            *   Are expensive filters/scorers (requiring network or heavy computation) being used excessively?
    *   `* Code Example: [Accessing stats after a BFS crawl (assuming batch mode)]`
        ```python
        # ... (setup bfs_strategy and run_config as in previous examples) ...
        # async with AsyncWebCrawler(config=browser_config) as crawler:
        #     results_container = await crawler.arun(
        #         url="https://example.com",
        #         config=run_config_with_bfs_strategy # run_config_with_bfs_strategy.deep_crawl_strategy is bfs_strategy
        #     )
        #
        #     # Access stats from the strategy instance
        #     crawl_stats = run_config_with_bfs_strategy.deep_crawl_strategy.stats
        #     print(f"\n--- Crawl Statistics ---")
        #     print(f"Start Time: {crawl_stats.start_time}")
        #     # Note: urls_processed might be better tracked by summing successful results
        #     # or by inspecting filter stats on the FilterChain if available.
        #     # TraversalStats itself in the provided code doesn't explicitly have urls_processed.
        #     # Let's assume we count successful results:
        #     print(f"URLs Successfully Processed: {len([r for r in results_container if r.success])}")
        #     print(f"URLs Failed: {len([r for r in results_container if not r.success])}") # Approximation
        #     print(f"URLs Skipped by Filters (Example): {getattr(run_config_with_bfs_strategy.deep_crawl_strategy.filter_chain, 'stats', FilterStats()).rejected_urls if run_config_with_bfs_strategy.deep_crawl_strategy.filter_chain else 'N/A'}")
        #     print(f"Max Depth Reached: {crawl_stats.total_depth_reached}")
        #     if crawl_stats.end_time:
        #          print(f"End Time: {crawl_stats.end_time}")
        #          print(f"Duration: {crawl_stats.end_time - crawl_stats.start_time}")
        #     else:
        #          print("Crawl may still be in progress or ended prematurely.")

        # Note: The TraversalStats model has start_time, end_time, urls_processed, urls_failed, urls_skipped, total_depth_reached, current_depth
        # The strategy code increments self._pages_crawled for successful crawls towards max_pages
        # and self.stats.urls_skipped for links skipped by filters.
        ```

*   **8.2. Logging in Deep Crawls**
    *   Crawl4ai's `AsyncLogger` (if `verbose=True` in `CrawlerRunConfig` or `BrowserConfig`) provides valuable insights. During deep crawls, you'll see:
        *   URLs being added to the frontier/queue/stack.
        *   Actions taken by filters (e.g., "URL rejected by DomainFilter").
        *   Scores assigned to URLs if using `BestFirstCrawlingStrategy` with a `URLScorer`.
        *   Newly discovered links from each page.
        *   Errors encountered during fetching or processing.
    *   **Setting verbosity:**
        *   `verbose=True` (default) provides a good level of detail.
        *   For extremely detailed debugging, you might need to delve into the library's source or add custom logging within custom components.
        *   The logger uses tags (e.g., `[BFS]`, `[FILTER]`, `[SCORE]`) to help identify the source of log messages.

## 9. Best Practices for Effective Deep Crawling

Crafting an effective deep crawl involves more than just setting a strategy; it requires planning, careful configuration, and ethical considerations.

*   **9.1. Planning Your Crawl Strategy**
    *   **Define Clear Objectives:**
        *   What specific data are you trying to collect? (e.g., all product names and prices, all blog post titles and content, site structure).
        *   What is the precise scope of your crawl? (e.g., a single subdomain, specific path patterns, content related to certain keywords).
        *   Clearly defined objectives will guide your choice of strategy, filters, and scorers.
    *   **Analyze Target Website Structure:**
        *   **`robots.txt`:** Always check `robots.txt` first (e.g., `https://example.com/robots.txt`) to understand disallowed paths. Crawl4ai can do this automatically if `check_robots_txt=True` (in `CrawlerRunConfig`).
        *   **Sitemaps:** Look for XML sitemaps (`/sitemap.xml`). They often provide a good list of canonical URLs and can be a great source of seed URLs.
        *   **URL Patterns:** Observe common URL structures for different content types (e.g., `/blog/YYYY/MM/DD/slug`, `/product/category/item-id`). This helps in crafting `URLPatternFilter`s.
        *   **Navigation:** Understand how users (and thus crawlers) navigate the site. Are there clear menus, breadcrumbs, pagination?
    *   **Estimate Crawl Size:**
        *   Before launching a full deep crawl, try a very limited crawl (e.g., `max_depth=1` or `2`, `max_pages=50`) to get a sense of how many URLs are discovered per level.
        *   This helps in estimating resource consumption and setting realistic `max_depth` and `max_pages` for the full crawl.

*   **9.2. Configuring for Efficiency and Relevance**
    *   **Filter Aggressively, Then Loosen:**
        *   Start with a restrictive `DomainFilter` to stay within your target domain(s).
        *   Add `ContentTypeFilter` early to exclude unwanted file types.
        *   Use `URLPatternFilter` to include/exclude specific paths.
        *   Only if necessary, add more computationally expensive filters like `ContentRelevanceFilter` or `SEOFilter` later in the chain.
    *   **Control Scope with `max_depth` and `max_pages`:**
        *   These are your primary safety nets against runaway crawls.
        *   Set them based on your objectives and initial site analysis.
    *   **Choose the Right Strategy:**
        *   BFS for broad, systematic coverage of shallow sites.
        *   DFS for deep dives into specific paths (with careful depth control).
        *   Best-First for targeted crawling based on relevance, freshness, or other criteria (requires good scorer design).
    *   **Iterate on Scorer Design (for Best-First):**
        *   Start with simple scorers.
        *   Run test crawls, analyze the types of URLs being prioritized, and refine your scorer weights or logic.
        *   Use `CompositeScorer` to combine multiple weak signals into a stronger one.
    *   **Test Filter and Scorer Logic:**
        *   Before a large crawl, test your `FilterChain` and `URLScorer` logic with a small, representative set of sample URLs to ensure they behave as expected.

*   **9.3. Ethical and Respectful Crawling**
    *   **Respect `robots.txt`:** Set `check_robots_txt=True` in your `CrawlerRunConfig`. Crawl4ai's `RobotsParser` will then automatically check `robots.txt` for each domain.
    *   **Implement Politeness Delays:**
        *   Crawl4ai's default dispatcher strategies often include rate limiting and backoff mechanisms.
        *   You can configure `mean_delay` and `max_range` in `CrawlerRunConfig` if using `arun_many` to introduce delays between individual `arun` calls managed by the dispatcher.
        *   Avoid hitting any single server too frequently.
    *   **Identify and Handle Sensitive Data Responsibly:** If your crawl might encounter personally identifiable information (PII) or other sensitive data, ensure you have mechanisms to either avoid it (via filters) or handle it according to privacy regulations and ethical guidelines.
    *   **Avoid Overwhelming Servers:** Monitor your crawl's impact. If you notice server errors (5xx status codes) or very slow responses, reduce your crawl rate or concurrency.
    *   **User-Agent:** While Crawl4ai provides a default User-Agent, consider setting a custom one that identifies your bot and provides a way to contact you if site administrators have questions (e.g., `MyCoolBot/1.0 (+http://mybotinfo.example.com)`).

*   **9.4. Handling Common Challenges**
    *   **Crawler Traps:**
        *   **Solution:** Use a sensible `max_depth`. Employ `URLPatternFilter` to exclude patterns that lead to traps (e.g., infinitely deep calendar links, search facets creating unique URLs for every combination).
        *   **Example:** A filter like `URLPatternFilter(patterns=[r"/calendar/\d{4}/\d{2}/\d{2}/.*"], reverse=True)` could block deep calendar paths.
    *   **Session-Dependent Content:**
        *   **Challenge:** If deep pages require a login session established on an earlier page.
        *   **Solution:** Use Crawl4ai's session persistence features.
            1.  Perform an initial crawl/interaction to log in, then save the `storage_state` from the browser context.
            2.  For subsequent deep crawls, load this `storage_state` into `BrowserConfig` or `CrawlerRunConfig` to reuse the session.
            *   Refer to the [Session Management](./session-management.md) and [Advanced Features](./advanced-features.md#5-session-persistence--local-storage) guides for details.
    *   **AJAX-Loaded Content / JavaScript-Generated Links:**
        *   **Challenge:** If links are not present in the initial HTML but are loaded or generated by JavaScript.
        *   **Solution:** Ensure your base crawling strategy (e.g., `AsyncPlaywrightCrawlerStrategy`, which is default) is used, as it executes JavaScript. You might need to use `wait_for` in `CrawlerRunConfig` to allow time for JS to execute and render links before link discovery happens.
    *   **Large-Scale Crawls:**
        *   **Challenge:** In-memory `visited` sets and URL frontiers can become bottlenecks for very large crawls (millions of pages).
        *   **Solution:** For enterprise-scale crawls, consider:
            *   Distributed crawling architecture (breaking the crawl into smaller, manageable parts).
            *   Using a persistent, disk-based queue (e.g., Redis, RabbitMQ) for the URL frontier.
            *   Using a distributed database or bloom filter service for the `visited` set.
            *   Crawl4ai's current built-in strategies are primarily designed for single-instance operation with in-memory tracking.

## 10. Troubleshooting Common Deep Crawling Issues

Even with careful planning, deep crawls can sometimes behave unexpectedly. Here's how to diagnose common problems.

*   **10.1. Crawl Not Going Deep Enough / Stopping Prematurely**
    *   **Check `max_depth` and `max_pages`:** Are these limits set too low for your target?
        *   `print(f"Config: max_depth={my_strategy.max_depth}, max_pages={my_strategy.max_pages}")`
    *   **Inspect Filters:**
        *   Are your filters (`DomainFilter`, `URLPatternFilter`, `ContentTypeFilter`, etc.) too aggressive?
        *   **Debugging Tip:** Temporarily disable filters one by one or simplify them to see if they are the cause. Add logging within custom filters or enable verbose logging in Crawl4ai to see filter decisions.
        *   `* Code Example: [Temporarily disabling a filter chain for debugging]`
            ```python
            # original_filter_chain = my_strategy.filter_chain
            # my_strategy.filter_chain = None # Temporarily disable for a test run
            # ... run crawl ...
            # my_strategy.filter_chain = original_filter_chain # Restore
            ```
    *   **Examine Link Discovery:**
        *   Are links being correctly extracted from the initial pages? After an `arun` call on a seed URL, inspect `result.links`.
        *   If links are JavaScript-generated, ensure your `wait_for` or other JS execution settings are adequate.
    *   **`include_external` Behavior:** If you *intend* to crawl subdomains but they are treated as external (and `include_external=False`), they won't be followed. Ensure your `DomainFilter` correctly specifies all allowed (sub)domains if `include_external` is `False`.

*   **10.2. Crawling Too Many Irrelevant Pages**
    *   **Tighten Filters:** This is the most common solution.
        *   Make `DomainFilter` more specific.
        *   Refine `URLPatternFilter` to exclude unwanted paths.
        *   Add a `ContentTypeFilter` if you're getting many non-HTML pages.
    *   **Refine Scoring (for Best-First):** If using `BestFirstCrawlingStrategy`, improve your `URLScorer` to give lower scores to irrelevant URL patterns or domains.
    *   **Verify `include_external`:** Ensure it's `False` (default for most strategies) if you don't intend to leave your primary domain(s).

*   **10.3. Performance Bottlenecks**
    *   **Network-Intensive Filters:** `ContentRelevanceFilter` and `SEOFilter` make HEAD requests for each URL they evaluate. If your `FilterChain` applies these to many URLs, it will significantly slow down the link processing phase.
        *   **Solution:** Place these filters *after* faster filters that can eliminate many URLs without network calls.
    *   **Complex Regex:** Very complex or inefficient regular expressions in `URLPatternFilter` can be slow.
        *   **Solution:** Simplify regex where possible. Test regex performance independently.
    *   **Complex Scoring Logic:** If your custom `URLScorer` or `CompositeScorer` performs heavy computations or external API calls for every URL, it will become a bottleneck for `BestFirstCrawlingStrategy`.
        *   **Solution:** Optimize scorer logic. Cache external API results if possible.
    *   **BFS Memory Usage:** As mentioned, BFS on very wide sites can lead to high memory usage.
        *   **Solution:** Limit `max_depth`, or consider DFS/Best-First for parts of the crawl.
    *   **Logging Overhead:** Extremely verbose logging to the console or file can add overhead. Reduce verbosity for production runs once debugging is complete.

*   **10.4. Using Logs for Diagnosis**
    *   **Enable Verbose Logging:** Set `verbose=True` in `CrawlerRunConfig` and/or `BrowserConfig`.
    *   **Look for Key Log Messages:**
        *   Messages indicating a URL is being added to the queue/stack.
        *   Filter actions: "URL [url] rejected by [FilterName]" or "URL [url] passed [FilterName]".
        *   Scorer outputs: "URL [url] scored [score] by [ScorerName]" (if scorers log verbosely).
        *   Link discovery: "Discovered [N] links on [page_url]".
        *   Errors: Any exceptions or error messages during fetching, processing, or strategy execution.
    *   **Custom Logging:** Add `self.logger.debug(...)` or `self.logger.info(...)` statements within your custom filters or scorers to trace their specific behavior.

## 11. Advanced Deep Crawling: Customization and Integration

When built-in components aren't enough, Crawl4ai's modular design allows you to create custom strategies, filters, and scorers.

*   **11.1. Why and When to Create Custom Components**
    *   **Unique Filtering Logic:** You might need to filter URLs based on criteria not covered by existing filters, e.g., checking against a dynamic blocklist from an API, or complex domain-specific path rules.
    *   **Domain-Specific Scoring Heuristics:** Your definition of a "valuable" URL might involve proprietary business logic, data from your own databases, or very specific content cues that standard scorers don't address.
    *   **Novel Traversal Strategies:** While BFS, DFS, and Best-First cover many cases, you might envision a hybrid approach or a strategy tailored to a very unusual site structure.
    *   **Integration with External Systems:** Custom components can interact with external APIs or databases during the filtering or scoring process.

*   **11.2. Implementing a Custom `DeepCrawlStrategy`**
    *   **Key methods to override (from `DeepCrawlStrategy` base class):**
        *   `async def _arun_batch(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> List[CrawlResult]:` Implement the core non-streaming traversal logic here. You'll manage the frontier (queue/stack/priority queue), call `crawler.arun_many()` for batches of URLs, and use `self.link_discovery()` and `self.can_process_url()`.
        *   `async def _arun_stream(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> AsyncGenerator[CrawlResult, None]:` Implement the streaming version of the traversal logic. Yield `CrawlResult` objects as they become available.
        *   `async def can_process_url(self, url: str, depth: int) -> bool:` (Often relies on `self.filter_chain`) This method determines if a given URL should be processed based on depth and filters.
        *   `async def link_discovery(self, result: CrawlResult, source_url: str, current_depth: int, visited: Set[str], next_level: List[Tuple], depths: Dict[str, int]) -> None:` (Helper method) Extracts links from a `CrawlResult`, applies `can_process_url`, and adds valid URLs to `next_level` and updates `depths`.
    *   **Managing state:** Your custom strategy will need to manage:
        *   A **frontier** of URLs to visit (e.g., `asyncio.Queue` for BFS, `list` for DFS stack, `asyncio.PriorityQueue` for Best-First).
        *   A **visited set** to avoid re-processing URLs.
        *   **URL depths** to respect `max_depth`.
        *   Counters for `max_pages`.
    *   `* Code Example: [Skeleton for a custom strategy that crawls based on page title length (longer titles first - a simplistic example)]`
        ```python
        from crawl4ai import DeepCrawlStrategy, CrawlResult, AsyncWebCrawler, CrawlerRunConfig
        import asyncio
        from typing import List, AsyncGenerator, Set, Dict, Tuple

        class TitleLengthPriorityStrategy(DeepCrawlStrategy):
            def __init__(self, max_depth: int = 3, max_pages: int = 100, **kwargs):
                super().__init__(max_depth=max_depth, max_pages=max_pages, **kwargs)
                self.priority_queue = asyncio.PriorityQueue() # (score, url, depth, parent_url)
                # Note: Lower numbers = higher priority for asyncio.PriorityQueue

            async def _process_page_and_discover_links(
                self, url: str, depth: int, parent_url: str,
                crawler: AsyncWebCrawler, config: CrawlerRunConfig,
                visited: Set[str]
            ) -> AsyncGenerator[CrawlResult, None]:
                if url in visited or depth > self.max_depth or self._pages_crawled >= self.max_pages:
                    return

                visited.add(url)
                # Create a config for fetching a single page
                page_config = config.clone(deep_crawl_strategy=None) # Ensure no recursive deep crawl
                
                # arun returns a CrawlResultContainer, access the first (and only) result
                crawl_result_container = await crawler.arun(url=url, config=page_config)
                page_result = crawl_result_container.results[0] if crawl_result_container.results else None

                if page_result and page_result.success:
                    self._pages_crawled += 1
                    page_result.metadata = page_result.metadata or {}
                    page_result.metadata["depth"] = depth
                    page_result.metadata["parent_url"] = parent_url
                    yield page_result

                    # Discover links
                    new_links_to_score = []
                    # Simplified link discovery for example
                    if page_result.links:
                        for link_type in ["internal", "external"]: # Or just internal
                            for link_info in page_result.links.get(link_type, []):
                                next_url = link_info.get("href")
                                if next_url and await self.can_process_url(next_url, depth + 1):
                                     if next_url not in visited: # Check visited again before adding to score
                                        new_links_to_score.append(next_url)
                    
                    for new_url in set(new_links_to_score): # Process unique new links
                        # Fetch title (simplified, real scorer would be more robust)
                        # This is inefficient here, a real scorer would be separate
                        temp_page_config = config.clone(deep_crawl_strategy=None, only_text=True, word_count_threshold=0) # very light fetch
                        try:
                            temp_result_container = await crawler.arun(url=new_url, config=temp_page_config)
                            temp_result = temp_result_container.results[0] if temp_result_container.results else None
                            title_len = len(temp_result.metadata.get("title", "")) if temp_result and temp_result.metadata else 0
                            score = -title_len # Negative because lower number = higher priority
                            if new_url not in visited: # Final check before putting in queue
                                await self.priority_queue.put((score, new_url, depth + 1, url))
                        except Exception as e:
                            if self.logger: self.logger.warning(f"Scoring error for {new_url}: {e}")


            async def _arun_stream(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> AsyncGenerator[CrawlResult, None]:
                self.reset_stats() # Important!
                visited: Set[str] = set()
                await self.priority_queue.put((0, start_url, 0, None)) # Initial score 0 for seed

                while not self.priority_queue.empty() and self._pages_crawled < self.max_pages:
                    _score, current_url, current_depth, parent_url = await self.priority_queue.get()
                    
                    if current_url in visited:
                        continue

                    async for page_result in self._process_page_and_discover_links(
                        current_url, current_depth, parent_url, crawler, config, visited
                    ):
                        yield page_result
                self.log_stats()
            
            # _arun_batch would collect all yields from _arun_stream
            async def _arun_batch(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> List[CrawlResult]:
                results = []
                async for result in self._arun_stream(start_url, crawler, config):
                    results.append(result)
                return results

        # Usage:
        # title_strategy = TitleLengthPriorityStrategy(max_depth=3)
        # run_config_custom = CrawlerRunConfig(deep_crawl_strategy=title_strategy)
        ```

*   **11.3. Developing a Custom `URLFilter`**
    *   **Inheriting from `URLFilter`:** Your custom filter class must inherit from `crawl4ai.deep_crawling.filters.URLFilter`.
    *   **Implementing `apply(self, url: str) -> bool`:** This is the core method. It takes a URL string and must return `True` if the URL should pass the filter, or `False` if it should be rejected.
        *   You can also make `apply` an `async def` if it needs to perform asynchronous operations (e.g., an API call to check a dynamic blocklist).
    *   **Leveraging `FilterStats`:**
        *   Call `self._update_stats(passed=True/False)` at the end of your `apply` method to correctly update the filter's statistics (`total_urls`, `passed_urls`, `rejected_urls`).
    *   `* Code Example: [A filter that blocks URLs with more than 5 path segments or URLs containing a specific query parameter 'sessionid']`
        ```python
        from crawl4ai import URLFilter, FilterStats
        from urllib.parse import urlparse, parse_qs

        class PathAndQueryParamFilter(URLFilter):
            def __init__(self, max_segments=5, forbidden_param="sessionid", **kwargs):
                super().__init__(**kwargs) # Pass name if desired
                self.max_segments = max_segments
                self.forbidden_param = forbidden_param

            # This can be async if needed: async def apply(self, url: str) -> bool:
            def apply(self, url: str) -> bool:
                parsed_url = urlparse(url)
                path_segments = parsed_url.path.strip('/').split('/')
                
                # Check path depth
                if len(path_segments) > self.max_segments:
                    self._update_stats(passed=False)
                    return False

                # Check for forbidden query parameter
                query_params = parse_qs(parsed_url.query)
                if self.forbidden_param in query_params:
                    self._update_stats(passed=False)
                    return False
                
                self._update_stats(passed=True)
                return True

        # Usage:
        # custom_filter = PathAndQueryParamFilter(max_segments=4, forbidden_param="tracking_id")
        # filter_chain = FilterChain(filters=[custom_filter])
        ```

*   **11.4. Designing a Custom `URLScorer`**
    *   **Inheriting from `URLScorer`:** Your custom scorer class must inherit from `crawl4ai.deep_crawling.scorers.URLScorer`.
    *   **Implementing `_calculate_score(self, url: str) -> float`:** This method takes a URL string and must return a float representing its "raw" score (before the scorer's `weight` is applied).
        *   This method can also be `async def` if it needs to perform asynchronous operations (e.g., fetching external data to inform the score).
    *   **Score Range:** It's good practice to design your `_calculate_score` to return values in a somewhat consistent range (e.g., 0.0 to 1.0) to make it easier to combine with other scorers in a `CompositeScorer`. The final score returned by the public `score()` method will be `_calculate_score(url) * self.weight`.
    *   `* Code Example: [A scorer that assigns higher scores to URLs ending with '.html' or '.php' and containing the word 'article']`
        ```python
        from crawl4ai import URLScorer

        class ArticlePageScorer(URLScorer):
            def __init__(self, weight: float = 1.0, **kwargs):
                super().__init__(weight=weight, **kwargs) # Pass name if desired

            # Can be async: async def _calculate_score(self, url: str) -> float:
            def _calculate_score(self, url: str) -> float:
                score = 0.0
                if url.lower().endswith(('.html', '.htm', '.php')):
                    score += 0.5
                if 'article' in url.lower():
                    score += 0.5
                return min(score, 1.0) # Cap score at 1.0

        # Usage:
        # article_scorer = ArticlePageScorer(weight=0.8)
        # composite_scorer = CompositeScorer(scorers=[article_scorer, ...])
        ```

*   **11.5. Integrating Deep Crawling with Other Crawl4ai Features**
    *   **Combining with Extraction Strategies:**
        *   **How it works:** The `DeepCrawlStrategy` (BFS, DFS, Best-First) is responsible for discovering and fetching pages. Each `CrawlResult` object it yields (in stream mode) or returns (in batch mode) contains the HTML content. This `CrawlResult` is then passed to the extraction pipeline defined in your `CrawlerRunConfig` (e.g., `LLMExtractionStrategy`, `JsonCssExtractionStrategy`).
        *   **Data Flow:** `DeepCrawlStrategy` produces `CrawlResult` -> `AsyncWebCrawler`'s main loop -> `ExtractionStrategy` (if defined) consumes `CrawlResult.html` or `CrawlResult.markdown` -> Populates `CrawlResult.extracted_content`.
        *   **Ensuring Compatibility:** Built-in deep crawl strategies yield standard `CrawlResult` objects, which are directly usable by extraction strategies. If you build a very custom strategy, ensure it also yields or returns `CrawlResult` instances.
    *   **Authenticated Deep Crawls:**
        *   **Challenge:** Many websites require login to access deeper content. A deep crawl needs to maintain this session.
        *   **Solution:**
            1.  **Initial Login:** Perform a separate, initial `crawler.arun()` call to the login page. Use `js_code` to fill in login forms and submit.
            2.  **Save Session State:** After successful login, save the browser's `storage_state` (cookies, localStorage):
                ```python
                # In the login part of your script
                # login_page_result = await crawler.arun(...)
                # await page.context.storage_state(path="my_session_state.json")
                ```
                (Assuming `page` is accessible, or via a hook that gets the context). A more robust way is to use a dedicated `BrowserConfig` with `user_data_dir` for persistence across crawler instances, or use the `session_id` feature if you keep the same crawler instance.
            3.  **Deep Crawl with Session:** For the subsequent deep crawl, configure `BrowserConfig` to use this saved state or `CrawlerRunConfig` to reuse a session via `session_id`:
                ```python
                # Option A: Persistent context via user_data_dir (for multiple crawler instances)
                # browser_config_authed = BrowserConfig(user_data_dir="path/to/my_profile_with_login")
                # async with AsyncWebCrawler(config=browser_config_authed) as authed_crawler:
                #    await authed_crawler.arun(..., config=deep_crawl_run_config)

                # Option B: Reusing a session within the same crawler instance
                # deep_crawl_run_config.session_id = "my_authed_session"
                # (after initial login that established this session)
                # await crawler.arun(..., config=deep_crawl_run_config)
                ```
        *   **Considerations:**
            *   **Token Refresh/Session Expiry:** Long crawls might encounter session expiry. More advanced solutions might need hooks or custom logic to detect expired sessions and re-authenticate.
            *   **AJAX/SPA Logins:** Ensure login interactions are fully completed (e.g., using `wait_for` for redirection or dashboard elements) before saving state or proceeding.
        *   `* Scenario Walkthrough: [Conceptual steps for deep crawling a members-only forum]`
            1.  Create `CrawlerRunConfig` for login: `js_code` to fill login form, `wait_for` a dashboard element.
            2.  `crawler.arun()` to login page with this config. Save `session_id` (e.g., "forum_session").
            3.  Create `CrawlerRunConfig` for deep crawl:
                *   `deep_crawl_strategy` (e.g., BFS to find all threads).
                *   `session_id="forum_session"` to reuse the logged-in state.
                *   Filters to stay within forum sections.
            4.  `crawler.arun()` with the forum's starting URL and deep crawl config.

## 12. Conclusion and Further Exploration

Crawl4ai's `deep_crawling` component offers a powerful and flexible toolkit for exploring websites beyond a single page. By understanding and combining strategies, filters, and scorers, you can tailor your crawls to a wide variety of tasks, from comprehensive site indexing to highly targeted data extraction.

*   **Recap:**
    *   Choose the right **strategy** (BFS, DFS, Best-First) based on your exploration goals.
    *   Use **filters** (`DomainFilter`, `ContentTypeFilter`, `URLPatternFilter`, etc.) to precisely define the scope of your crawl and improve efficiency.
    *   Leverage **scorers** (especially with `BestFirstCrawlingStrategy`) to prioritize URLs and focus on the most relevant content.
    *   Configure everything through `CrawlerRunConfig` and its `deep_crawl_strategy` parameter.
    *   Monitor your crawls using `TraversalStats` and logs to optimize performance.
*   **Encouragement:** The best way to master deep crawling is to experiment!
    *   Start with simple configurations and gradually add complexity.
    *   Test different filter combinations and scorer weightings.
    *   Observe how your changes affect the crawl path and results.
*   **Pointers to Other Relevant Documentation:**
    *   **Basic Crawling:** [Simple Crawling Guide](../core/simple-crawling.md)
    *   **Configuration:** [Browser, Crawler & LLM Configuration](../core/browser-crawler-config.md)
    *   **Specific Filters/Scorers API:** (Refer to API documentation if available, or source code comments)
    *   **Extraction Strategies:** [No-LLM Extraction Strategies](../extraction/no-llm-strategies.md), [LLM-based Extraction](../extraction/llm-extraction.md)
    *   **Session Management & Authentication:** [Session Management](./session-management.md), [Hooks & Auth](./hooks-auth.md)
    *   **Advanced Page Interaction:** [Page Interaction](./page-interaction.md)

Happy deep crawling with Crawl4ai!
```