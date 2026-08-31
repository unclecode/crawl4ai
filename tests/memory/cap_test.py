#!/usr/bin/env python3
"""
Hammer /crawl with many concurrent requests to prove GLOBAL_SEM works.
"""

import asyncio, httpx, json, uuid, argparse

API = "http://localhost:8020/crawl"
URLS_PER_CALL = 1          # keep it minimal so each arun() == 1 page
CONCURRENT_CALLS = 20      # way above your cap

payload_template = {
    "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {"cache_mode": "BYPASS", "verbose": False},
    }
}

async def one_call(client):
    payload = payload_template.copy()
    payload["urls"] = [f"https://httpbin.org/anything/{uuid.uuid4()}"]
    r = await client.post(API, json=payload)
    r.raise_for_status()
    return r.json()["server_peak_memory_mb"]

async def main():
    async with httpx.AsyncClient(timeout=60) as client:
        tasks = [asyncio.create_task(one_call(client)) for _ in range(CONCURRENT_CALLS)]
        mem_usages = await asyncio.gather(*tasks)
        print("Calls finished OK, server peaks reported:", mem_usages)

if __name__ == "__main__":
    asyncio.run(main())
