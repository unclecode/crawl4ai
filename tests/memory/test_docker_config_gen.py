#!/usr/bin/env python3
"""
Quick sanity‑check for /config/dump endpoint.

Usage:
    python test_config_dump.py  [http://localhost:8020]

If the server isn’t running, start it first:
    uvicorn deploy.docker.server:app --port 8020
"""

import sys, json, textwrap, requests

# BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8020"
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11235"
URL  = f"{BASE.rstrip('/')}/config/dump"

CASES = [
    # --- CrawlRunConfig variants ---
    "CrawlerRunConfig()",
    "CrawlerRunConfig(stream=True, cache_mode=CacheMode.BYPASS)",
    "CrawlerRunConfig(js_only=True, wait_until='networkidle')",

    # --- BrowserConfig variants ---
    "BrowserConfig()",
    "BrowserConfig(headless=False, extra_args=['--disable-gpu'])",
    "BrowserConfig(browser_mode='builtin', proxy='http://1.2.3.4:8080')",
]

for code in CASES:
    print("\n===  POST:", code)
    resp = requests.post(URL, json={"code": code}, timeout=15)
    if resp.ok:
        print(json.dumps(resp.json(), indent=2)[:400] + "...")
    else:
        print("ERROR", resp.status_code, resp.text[:200])
