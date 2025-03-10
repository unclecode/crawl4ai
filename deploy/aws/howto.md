# Crawl4AI API Quickstart

This document shows how to generate an API token and use it to call the `/crawl` and `/md` endpoints.

---

## 1. Crawl Example

Send a POST request to `/crawl` with the following JSON payload:

```json
{
  "urls": ["https://example.com"],
  "browser_config": { "headless": true, "verbose": true },
  "crawler_config": { "stream": false, "cache_mode": "enabled" }
}
```

**cURL Command:**

```bash
curl -X POST "https://api.crawl4ai.com/crawl" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "urls": ["https://example.com"],
        "browser_config": {"headless": true, "verbose": true},
        "crawler_config": {"stream": false, "cache_mode": "enabled"}
      }'
```

---

## 2. Markdown Retrieval Example

To retrieve markdown from a given URL (e.g., `https://example.com`), use:

```bash
curl -X GET "https://api.crawl4ai.com/md/example.com" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

---

## 3. Python Code Example (Using `requests`)

Below is a sample Python script that demonstrates using the `requests` library to call the API endpoints:

```python
import requests

BASE_URL = "https://api.crawl4ai.com"
TOKEN = "YOUR_API_TOKEN"  # Replace with your actual token

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Crawl endpoint example
crawl_payload = {
    "urls": ["https://example.com"],
    "browser_config": {"headless": True, "verbose": True},
    "crawler_config": {"stream": False, "cache_mode": "enabled"}
}

crawl_response = requests.post(f"{BASE_URL}/crawl", json=crawl_payload, headers=headers)
print("Crawl Response:", crawl_response.json())

# /md endpoint example
md_response = requests.get(f"{BASE_URL}/md/example.com", headers=headers)
print("Markdown Content:", md_response.text)
```

---

Happy crawling!
