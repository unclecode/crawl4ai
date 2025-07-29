from typing import TYPE_CHECKING, Union

# Logger types
AsyncLoggerBase = Union['AsyncLoggerBaseType']
AsyncLogger = Union['AsyncLoggerType']

# Crawler core types
AsyncWebCrawler = Union['AsyncWebCrawlerType']
CacheMode = Union['CacheModeType']
CrawlResult = Union['CrawlResultType']
CrawlerHub = Union['CrawlerHubType']
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
WebScrapingStrategy = Union['WebScrapingStrategyType']
LXMLWebScrapingStrategy = Union['LXMLWebScrapingStrategyType']

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
    from .async_logger import (
        AsyncLoggerBase as AsyncLoggerBaseType,
        AsyncLogger as AsyncLoggerType,
    )
    
    # Crawler core imports
    from .async_webcrawler import (
        AsyncWebCrawler as AsyncWebCrawlerType,
        CacheMode as CacheModeType,
    )
    from .models import CrawlResult as CrawlResultType
    from .hub import CrawlerHub as CrawlerHubType
    from .browser_profiler import BrowserProfiler as BrowserProfilerType
    # NEW: Import AsyncUrlSeeder for type checking
    from .async_url_seeder import AsyncUrlSeeder as AsyncUrlSeederType
    
    # Configuration imports
    from .async_configs import (
        BrowserConfig as BrowserConfigType,
        CrawlerRunConfig as CrawlerRunConfigType,
        HTTPCrawlerConfig as HTTPCrawlerConfigType,
        LLMConfig as LLMConfigType,
        # NEW: Import SeedingConfig for type checking
        SeedingConfig as SeedingConfigType,
    )
    
    # Content scraping imports
    from .content_scraping_strategy import (
        ContentScrapingStrategy as ContentScrapingStrategyType,
        WebScrapingStrategy as WebScrapingStrategyType,
        LXMLWebScrapingStrategy as LXMLWebScrapingStrategyType,
    )
    
    # Proxy imports
    from .proxy_strategy import (
        ProxyRotationStrategy as ProxyRotationStrategyType,
        RoundRobinProxyStrategy as RoundRobinProxyStrategyType,
    )
    
    # Extraction imports
    from .extraction_strategy import (
        ExtractionStrategy as ExtractionStrategyType,
        LLMExtractionStrategy as LLMExtractionStrategyType,
        CosineStrategy as CosineStrategyType,
        JsonCssExtractionStrategy as JsonCssExtractionStrategyType,
        JsonXPathExtractionStrategy as JsonXPathExtractionStrategyType,
    )
    
    # Chunking imports
    from .chunking_strategy import (
        ChunkingStrategy as ChunkingStrategyType,
        RegexChunking as RegexChunkingType,
    )
    
    # Markdown generation imports
    from .markdown_generation_strategy import (
        DefaultMarkdownGenerator as DefaultMarkdownGeneratorType,
    )
    from .models import MarkdownGenerationResult as MarkdownGenerationResultType
    
    # Content filter imports
    from .content_filter_strategy import (
        RelevantContentFilter as RelevantContentFilterType,
        PruningContentFilter as PruningContentFilterType,
        BM25ContentFilter as BM25ContentFilterType,
        LLMContentFilter as LLMContentFilterType,
    )
    
    # Dispatcher imports
    from .async_dispatcher import (
        BaseDispatcher as BaseDispatcherType,
        MemoryAdaptiveDispatcher as MemoryAdaptiveDispatcherType,
        SemaphoreDispatcher as SemaphoreDispatcherType,
        RateLimiter as RateLimiterType,
        CrawlerMonitor as CrawlerMonitorType,
        DisplayMode as DisplayModeType,
        RunManyReturn as RunManyReturnType,
    )
    
    # Docker client
    from .docker_client import Crawl4aiDockerClient as Crawl4aiDockerClientType
    
    # Deep crawling imports
    from .deep_crawling import (
        DeepCrawlStrategy as DeepCrawlStrategyType,
        BFSDeepCrawlStrategy as BFSDeepCrawlStrategyType,
        FilterChain as FilterChainType,
        ContentTypeFilter as ContentTypeFilterType,
        DomainFilter as DomainFilterType,
        URLFilter as URLFilterType,
        FilterStats as FilterStatsType,
        SEOFilter as SEOFilterType,
        KeywordRelevanceScorer as KeywordRelevanceScorerType,
        URLScorer as URLScorerType,
        CompositeScorer as CompositeScorerType,
        DomainAuthorityScorer as DomainAuthorityScorerType,
        FreshnessScorer as FreshnessScorerType,
        PathDepthScorer as PathDepthScorerType,
        BestFirstCrawlingStrategy as BestFirstCrawlingStrategyType,
        DFSDeepCrawlStrategy as DFSDeepCrawlStrategyType,
        DeepCrawlDecorator as DeepCrawlDecoratorType,
    )



def create_llm_config(*args, **kwargs) -> 'LLMConfigType':
    from .async_configs import LLMConfig
    return LLMConfig(*args, **kwargs)