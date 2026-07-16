import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext

async def test_reuse_context_by_config():
    # We will store each context ID in these maps to confirm reuse
    context_ids_for_A = []
    context_ids_for_B = []

    # Create a small hook to track context creation
    async def on_page_context_created(page: Page, context: BrowserContext, config: CrawlerRunConfig, **kwargs):
        c_id = id(context)
        print(f"[HOOK] on_page_context_created - Context ID: {c_id}")
        # Distinguish which config we used by checking a custom hook param
        config_label = config.shared_data.get("config_label", "unknown")
        if config_label == "A":
            context_ids_for_A.append(c_id)
        elif config_label == "B":
            context_ids_for_B.append(c_id)
        return page

    # Browser config - Headless, verbose so we see logs
    browser_config = BrowserConfig(headless=True, verbose=True)

    # Two crawler run configs that differ (for example, text_mode):
    configA = CrawlerRunConfig(
        only_text=True,
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded",
        shared_data = {
            "config_label" : "A"
        }
    )
    configB = CrawlerRunConfig(
        only_text=False,
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded",
        shared_data = {
            "config_label" : "B"
        }
    )

    # Create the crawler
    crawler = AsyncWebCrawler(config=browser_config)

    # Attach our custom hook
    # Note: "on_page_context_created" will be called each time a new context+page is generated
    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)

    # Start the crawler (launches the browser)
    await crawler.start()

    # For demonstration, we’ll crawl a benign site multiple times with each config
    test_url = "https://example.com"
    print("\n--- Crawling with config A (text_mode=True) ---")
    for _ in range(2):
        # Pass an extra kwarg to the hook so we know which config is being used
        await crawler.arun(test_url, config=configA)

    print("\n--- Crawling with config B (text_mode=False) ---")
    for _ in range(2):
        await crawler.arun(test_url, config=configB)

    # Close the crawler (shuts down the browser, closes contexts)
    await crawler.close()

    # Validate and show the results
    print("\n=== RESULTS ===")
    print(f"Config A context IDs: {context_ids_for_A}")
    print(f"Config B context IDs: {context_ids_for_B}")
    if len(set(context_ids_for_A)) == 1:
        print("✅ All config A crawls used the SAME BrowserContext.")
    else:
        print("❌ Config A crawls created multiple contexts unexpectedly.")
    if len(set(context_ids_for_B)) == 1:
        print("✅ All config B crawls used the SAME BrowserContext.")
    else:
        print("❌ Config B crawls created multiple contexts unexpectedly.")
    if set(context_ids_for_A).isdisjoint(context_ids_for_B):
        print("✅ Config A context is different from Config B context.")
    else:
        print("❌ A and B ended up sharing the same context somehow!")

if __name__ == "__main__":
    asyncio.run(test_reuse_context_by_config())
