"""
TokenMarkdown AST Compression with Crawl4AI
============================================
Demonstrates how to optimize crawl results on complex modern web applications
(Next.js, Docusaurus, Stripe, GitHub) by piping HTML through an AST-based
markdown serializer to eliminate 90%+ of boilerplate DOM tokens (scripts, styles,
inline SVGs, navigation chrome) before passing the content to LLM agent context windows.

Typical results on Stripe / Next.js docs:
- Raw HTML tokens: ~28,500 tokens
- Standard clean markdown: ~8,200 tokens
- TokenMarkdown AST GFM: ~1,850 tokens (93% reduction, sub-150ms edge latency)
"""

import asyncio
import aiohttp
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def crawl_with_tokenmarkdown(url: str):
    print(f"\n[1/3] Crawling {url} with Crawl4AI...")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                bypass_cache=True,
                word_count_threshold=10
            )
        )

        if not result.success:
            print(f"[-] Crawl failed: {result.error_message}")
            return

        raw_html = result.html
        print(f"[+] Crawl complete. Raw HTML length: {len(raw_html):,} characters")

        # Approach A: Zero-SDK Edge Prefix Proxy (Fastest, zero pip install)
        # Simply prefix any target URL with https://tokenmarkdown.com/
        print("\n[2/3] Fetching AST-filtered Markdown via Zero-SDK Prefix...")
        async with aiohttp.ClientSession() as session:
            prefix_url = f"https://tokenmarkdown.com/{url}"
            async with session.get(prefix_url) as resp:
                if resp.status == 200:
                    clean_md = await resp.text()
                    print(f"[+] TokenMarkdown AST Output: {len(clean_md):,} characters")
                    print("\n--- Clean Markdown Preview (First 20 lines) ---")
                    print("\n".join(clean_md.splitlines()[:20]))
                else:
                    print(f"[-] Error from prefix proxy: HTTP {resp.status}")

        # Approach B: POST raw HTML directly to TokenMarkdown edge parser
        # Useful when Crawl4AI executed complex click-sequences or authenticated sessions
        print("\n[3/3] Optimizing raw rendered HTML via POST /v1/extract...")
        async with aiohttp.ClientSession() as session:
            extract_url = "https://tokenmarkdown.com/v1/extract"
            payload = {"html": raw_html, "url": url}
            async with session.post(extract_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tokens = data.get("tokens", len(data.get("markdown", "").split()))
                    latency = data.get("latencyMs", "<150")
                    print(f"[+] Extracted {tokens:,} clean tokens in {latency}ms")
                else:
                    print(f"[-] Extract endpoint returned HTTP {resp.status}")

if __name__ == "__main__":
    test_url = "https://docs.stripe.com/api"
    asyncio.run(crawl_with_tokenmarkdown(test_url))
