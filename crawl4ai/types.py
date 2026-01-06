from typing import TYPE_CHECKING, Union

# Logger types
AsyncLoggerBase = Union['AsyncLoggerBaseType']
AsyncLogger = Union['AsyncLoggerType']

# Crawler core types
AsyncWebCrawler = Union['AsyncWebCrawlerType']
CacheMode = Union['CacheModeType']
CrawlResult = Union['CrawlResultType']
BrowserProfiler = Union['BrowserProfilerType']
# NEW: Add AsyncUrlSeederType
AsyncUrlSeeder = Union['AsyncUrlSeederType']

# Configuration types
BrowserConfig = Union['BrowserConfigType']
CrawlerRunConfig = Union['CrawlerRunConfigType']
HTTPCrawlerConfig = Union['HTTPCrawlerConfigType']
LLMConfig = Union['LLMConfigType']
# NEW: Add SeedingConfigType
SeedingConfig = Union['SeedingConfigType']

# Content scraping types
ContentScrapingStrategy = Union['ContentScrapingStrategyType']
LXMLWebScrapingStrategy = Union['LXMLWebScrapingStrategyType']
# Backward compatibility alias
WebScrapingStrategy = Union['LXMLWebScrapingStrategyType']

# Proxy types
ProxyRotationStrategy = Union['ProxyRotationStrategyType']
RoundRobinProxyStrategy = Union['RoundRobinProxyStrategyType']

# Extraction types
ExtractionStrategy = Union['ExtractionStrategyType']
LLMExtractionStrategy = Union['LLMExtractionStrategyType']
CosineStrategy = Union['CosineStrategyType']
JsonCssExtractionStrategy = Union['JsonCssExtractionStrategyType']
JsonXPathExtractionStrategy = Union['JsonXPathExtractionStrategyType']

# Chunking types
ChunkingStrategy = Union['ChunkingStrategyType']
RegexChunking = Union['RegexChunkingType']

# Markdown generation types
DefaultMarkdownGenerator = Union['DefaultMarkdownGeneratorType']
MarkdownGenerationResult = Union['MarkdownGenerationResultType']

# Content filter types
RelevantContentFilter = Union['RelevantContentFilterType']
PruningContentFilter = Union['PruningContentFilterType']
BM25ContentFilter = Union['BM25ContentFilterType']
LLMContentFilter = Union['LLMContentFilterType']

# Dispatcher types
BaseDispatcher = Union['BaseDispatcherType']
MemoryAdaptiveDispatcher = Union['MemoryAdaptiveDispatcherType']
SemaphoreDispatcher = Union['SemaphoreDispatcherType']
RateLimiter = Union['RateLimiterType']
CrawlerMonitor = Union['CrawlerMonitorType']
DisplayMode = Union['DisplayModeType']
RunManyReturn = Union['RunManyReturnType']

# Docker client
Crawl4aiDockerClient = Union['Crawl4aiDockerClientType']

# Deep crawling types
DeepCrawlStrategy = Union['DeepCrawlStrategyType']
BFSDeepCrawlStrategy = Union['BFSDeepCrawlStrategyType']
FilterChain = Union['FilterChainType']
ContentTypeFilter = Union['ContentTypeFilterType']
DomainFilter = Union['DomainFilterType']
URLFilter = Union['URLFilterType']
FilterStats = Union['FilterStatsType']
SEOFilter = Union['SEOFilterType']
KeywordRelevanceScorer = Union['KeywordRelevanceScorerType']
URLScorer = Union['URLScorerType']
CompositeScorer = Union['CompositeScorerType']
DomainAuthorityScorer = Union['DomainAuthorityScorerType']
FreshnessScorer = Union['FreshnessScorerType']
PathDepthScorer = Union['PathDepthScorerType']
BestFirstCrawlingStrategy = Union['BestFirstCrawlingStrategyType']
DFSDeepCrawlStrategy = Union['DFSDeepCrawlStrategyType']
DeepCrawlDecorator = Union['DeepCrawlDecoratorType']

# Only import types during type checking to avoid circular imports
if TYPE_CHECKING:
    # Logger imports
    # Configuration imports
    from .async_configs import (
        BrowserConfig as BrowserConfigType,
    )
    from .async_configs import (
        CrawlerRunConfig as CrawlerRunConfigType,
    )
    from .async_configs import (
        HTTPCrawlerConfig as HTTPCrawlerConfigType,
    )
    from .async_configs import (
        LLMConfig as LLMConfigType,
    )
    from .async_configs import (
        # NEW: Import SeedingConfig for type checking
        SeedingConfig as SeedingConfigType,
    )

    # Dispatcher imports
    from .async_dispatcher import (
        BaseDispatcher as BaseDispatcherType,
    )
    from .async_dispatcher import (
        CrawlerMonitor as CrawlerMonitorType,
    )
    from .async_dispatcher import (
        DisplayMode as DisplayModeType,
    )
    from .async_dispatcher import (
        MemoryAdaptiveDispatcher as MemoryAdaptiveDispatcherType,
    )
    from .async_dispatcher import (
        RateLimiter as RateLimiterType,
    )
    from .async_dispatcher import (
        RunManyReturn as RunManyReturnType,
    )
    from .async_dispatcher import (
        SemaphoreDispatcher as SemaphoreDispatcherType,
    )
    from .async_logger import (
        AsyncLogger as AsyncLoggerType,
    )
    from .async_logger import (
        AsyncLoggerBase as AsyncLoggerBaseType,
    )

    # NEW: Import AsyncUrlSeeder for type checking
    from .async_url_seeder import AsyncUrlSeeder as AsyncUrlSeederType

    # Crawler core imports
    from .async_webcrawler import (
        AsyncWebCrawler as AsyncWebCrawlerType,
    )
    from .async_webcrawler import (
        CacheMode as CacheModeType,
    )
    from .browser_profiler import BrowserProfiler as BrowserProfilerType

    # Chunking imports
    from .chunking_strategy import (
        ChunkingStrategy as ChunkingStrategyType,
    )
    from .chunking_strategy import (
        RegexChunking as RegexChunkingType,
    )
    from .content_filter_strategy import (
        BM25ContentFilter as BM25ContentFilterType,
    )
    from .content_filter_strategy import (
        LLMContentFilter as LLMContentFilterType,
    )
    from .content_filter_strategy import (
        PruningContentFilter as PruningContentFilterType,
    )

    # Content filter imports
    from .content_filter_strategy import (
        RelevantContentFilter as RelevantContentFilterType,
    )

    # Content scraping imports
    from .content_scraping_strategy import (
        ContentScrapingStrategy as ContentScrapingStrategyType,
    )
    from .content_scraping_strategy import (
        LXMLWebScrapingStrategy as LXMLWebScrapingStrategyType,
    )
    from .deep_crawling import (
        BestFirstCrawlingStrategy as BestFirstCrawlingStrategyType,
    )
    from .deep_crawling import (
        BFSDeepCrawlStrategy as BFSDeepCrawlStrategyType,
    )
    from .deep_crawling import (
        CompositeScorer as CompositeScorerType,
    )
    from .deep_crawling import (
        ContentTypeFilter as ContentTypeFilterType,
    )
    from .deep_crawling import (
        DeepCrawlDecorator as DeepCrawlDecoratorType,
    )

    # Deep crawling imports
    from .deep_crawling import (
        DeepCrawlStrategy as DeepCrawlStrategyType,
    )
    from .deep_crawling import (
        DFSDeepCrawlStrategy as DFSDeepCrawlStrategyType,
    )
    from .deep_crawling import (
        DomainAuthorityScorer as DomainAuthorityScorerType,
    )
    from .deep_crawling import (
        DomainFilter as DomainFilterType,
    )
    from .deep_crawling import (
        FilterChain as FilterChainType,
    )
    from .deep_crawling import (
        FilterStats as FilterStatsType,
    )
    from .deep_crawling import (
        FreshnessScorer as FreshnessScorerType,
    )
    from .deep_crawling import (
        KeywordRelevanceScorer as KeywordRelevanceScorerType,
    )
    from .deep_crawling import (
        PathDepthScorer as PathDepthScorerType,
    )
    from .deep_crawling import (
        SEOFilter as SEOFilterType,
    )
    from .deep_crawling import (
        URLFilter as URLFilterType,
    )
    from .deep_crawling import (
        URLScorer as URLScorerType,
    )

    # Docker client
    from .docker_client import Crawl4aiDockerClient as Crawl4aiDockerClientType
    from .extraction_strategy import (
        CosineStrategy as CosineStrategyType,
    )

    # Extraction imports
    from .extraction_strategy import (
        ExtractionStrategy as ExtractionStrategyType,
    )
    from .extraction_strategy import (
        JsonCssExtractionStrategy as JsonCssExtractionStrategyType,
    )
    from .extraction_strategy import (
        JsonXPathExtractionStrategy as JsonXPathExtractionStrategyType,
    )
    from .extraction_strategy import (
        LLMExtractionStrategy as LLMExtractionStrategyType,
    )

    # Markdown generation imports
    from .markdown_generation_strategy import (
        DefaultMarkdownGenerator as DefaultMarkdownGeneratorType,
    )
    from .models import CrawlResult as CrawlResultType
    from .models import MarkdownGenerationResult as MarkdownGenerationResultType

    # Proxy imports
    from .proxy_strategy import (
        ProxyRotationStrategy as ProxyRotationStrategyType,
    )
    from .proxy_strategy import (
        RoundRobinProxyStrategy as RoundRobinProxyStrategyType,
    )


