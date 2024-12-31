cache_system: Crawl4AI v0.5.0 introduces CacheMode enum to replace boolean cache flags | caching system, cache control, cache configuration | CacheMode.ENABLED
cache_modes: CacheMode enum supports five states: ENABLED, DISABLED, READ_ONLY, WRITE_ONLY, and BYPASS | cache states, caching options, cache settings | CacheMode.ENABLED, CacheMode.DISABLED, CacheMode.READ_ONLY, CacheMode.WRITE_ONLY, CacheMode.BYPASS
cache_migration_bypass: Replace bypass_cache=True with cache_mode=CacheMode.BYPASS | skip cache, bypass caching | cache_mode=CacheMode.BYPASS
cache_migration_disable: Replace disable_cache=True with cache_mode=CacheMode.DISABLED | disable caching, turn off cache | cache_mode=CacheMode.DISABLED
cache_migration_read: Replace no_cache_read=True with cache_mode=CacheMode.WRITE_ONLY | write-only cache, disable read | cache_mode=CacheMode.WRITE_ONLY
cache_migration_write: Replace no_cache_write=True with cache_mode=CacheMode.READ_ONLY | read-only cache, disable write | cache_mode=CacheMode.READ_ONLY
crawler_config: Use CrawlerRunConfig to set cache mode in AsyncWebCrawler | crawler settings, configuration object | CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
deprecation_warnings: Suppress cache deprecation warnings by setting SHOW_DEPRECATION_WARNINGS to False | warning suppression, legacy support | SHOW_DEPRECATION_WARNINGS = False
async_crawler_usage: AsyncWebCrawler requires async/await syntax and supports configuration via CrawlerRunConfig | async crawler, web crawler setup | async with AsyncWebCrawler(verbose=True) as crawler
crawler_execution: Run AsyncWebCrawler using asyncio.run() in main script | crawler execution, async main | asyncio.run(main())