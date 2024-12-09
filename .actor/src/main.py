"""This module defines the main entry point for the Apify Actor.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from base64 import b64decode
from hashlib import sha256
from typing import cast
from urllib.parse import urljoin

from apify import Actor
from apify.storages import RequestList, RequestQueue
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import (
    CosineStrategy,
    JsonCssExtractionStrategy,
    LLMExtractionStrategy,
    NoExtractionStrategy,
)
from crawlee import Request
from crawlee.basic_crawler import BasicCrawler, BasicCrawlingContext
from crawlee.storages import KeyValueStore, RequestSourceTandem

from .input import CosineExtraction, Input, JsonCssExtraction, LLMExtraction


async def create_crawler(input: Input) -> BasicCrawler:
    request_list = await RequestList.open(request_list_sources_input=input.start_urls)
    proxy_configuration = await Actor.create_proxy_configuration(
        actor_proxy_input=input.proxy_configuration
    )

    crawler = BasicCrawler(
        request_provider=RequestSourceTandem(request_list, await RequestQueue.open()),
        proxy_configuration=proxy_configuration,
    )

    if isinstance(input.extraction_strategy, LLMExtraction):
        extraction_strategy = LLMExtractionStrategy(
            provider=input.extraction_strategy.provider,
            api_token=input.extraction_strategy.api_token,
            instruction=cast(str, input.extraction_strategy.instruction),
        )
    elif isinstance(input.extraction_strategy, JsonCssExtraction):
        extraction_strategy = JsonCssExtractionStrategy(
            schema=input.extraction_strategy.extraction_schema
        )
    elif isinstance(input.extraction_strategy, CosineExtraction):
        extraction_strategy = CosineStrategy(
            semantic_filter=input.extraction_strategy.semantic_filter,
            word_count_threshold=input.extraction_strategy.word_count_threshold,
            max_dist=input.extraction_strategy.max_dist,
            linkage_method=input.extraction_strategy.linkage_method,
            top_k=input.extraction_strategy.top_k,
            model_name=input.extraction_strategy.extraction_model_name,
            sim_threshold=input.extraction_strategy.sim_threshold,
        )
    else:
        extraction_strategy = NoExtractionStrategy()

    @crawler.router.default_handler
    async def handler(context: BasicCrawlingContext) -> None:
        context.log.info(f"Processing {context.request.url}...")

        # We're making a new crawler for every page to work around memory leaks
        async with AsyncWebCrawler(
            proxy_config={
                "server": context.proxy_info.url,
                "username": context.proxy_info.username,
                "password": context.proxy_info.password,
            }
            if context.proxy_info
            else None,
        ) as crawl4ai:
            result = await crawl4ai.arun(
                context.request.url,
                magic=input.magic_mode,
                screenshot=input.save_screenshots,
                css_selector=cast(str, input.css_selector),
                extraction_strategy=extraction_strategy,
                js_code=input.js_code,
                wait_for=input.wait_for,
            )

        await context.add_requests(
            [
                Request.from_url(url=urljoin(result.url, href))
                for link in result.links["internal"]
                if (href := link["href"]) and not href.startswith("#")
            ]
        )

        store = await KeyValueStore.open()

        html_key = (
            f"content_{sha256(context.request.unique_key.encode()).hexdigest()}.html"
        )
        await store.set_value(html_key, result.html)

        md_key = f"content_{sha256(context.request.unique_key.encode()).hexdigest()}.md"
        await store.set_value(md_key, result.markdown)

        data = {
            "url": result.url,
            "markdown": await store.get_public_url(md_key),
            "html": await store.get_public_url(html_key),
            "extracted_content": result.extracted_content,
            "metadata": result.metadata,
            "screenshot_url": None,
        }

        if input.save_screenshots and result.screenshot:
            key = f"screenshot_{sha256(context.request.unique_key.encode()).hexdigest()}.jpg"
            await store.set_value(key, b64decode(result.screenshot))

            data["screenshot_url"] = await store.get_public_url(key)

        await context.push_data(data)

    return crawler


async def main() -> None:
    async with Actor:
        input = Input.model_validate(await Actor.get_input())
        crawler = await create_crawler(input)
        await crawler.run()
