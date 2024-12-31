# Deploying with Docker (Quickstart)

> **⚠️ WARNING: Experimental & Legacy**  
> Our current Docker solution for Crawl4AI is **not stable** and **will be discontinued** soon. A more robust Docker/Orchestration strategy is in development, with a planned stable release in **2025**. If you choose to use this Docker approach, please proceed cautiously and avoid production deployment without thorough testing.

Crawl4AI is **open-source** and under **active development**. We appreciate your interest, but strongly recommend you make **informed decisions** if you need a production environment. Expect breaking changes in future versions.

---

## 1. Installation & Environment Setup (Outside Docker)

Before we jump into Docker usage, here’s a quick reminder of how to install Crawl4AI locally (legacy doc). For **non-Docker** deployments or local dev:

```bash
# 1. Install the package
pip install crawl4ai
crawl4ai-setup

# 2. Install playwright dependencies (all browsers or specific ones)
playwright install --with-deps
# or
playwright install --with-deps chromium
# or
playwright install --with-deps chrome
```

**Testing** your installation:

```bash
# Visible browser test
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=False); page = browser.new_page(); page.goto('https://example.com'); input('Press Enter to close...')"
```

---

## 2. Docker Overview

This Docker approach allows you to run a **Crawl4AI** service via REST API. You can:

1. **POST** a request (e.g., URLs, extraction config)  
2. **Retrieve** your results from a task-based endpoint  

> **Note**: This Docker solution is **temporary**. We plan a more robust, stable Docker approach in the near future. For now, you can experiment, but do not rely on it for mission-critical production.

---

## 3. Pulling and Running the Image

### Basic Run

```bash
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
```

This starts a container on port `11235`. You can `POST` requests to `http://localhost:11235/crawl`.

### Using an API Token

```bash
docker run -p 11235:11235 \
  -e CRAWL4AI_API_TOKEN=your_secret_token \
  unclecode/crawl4ai:basic
```

If **`CRAWL4AI_API_TOKEN`** is set, you must include `Authorization: Bearer <token>` in your requests. Otherwise, the service is open to anyone.

---

## 4. Docker Compose for Multi-Container Workflows

You can also use **Docker Compose** to manage multiple services. Below is an **experimental** snippet:

```yaml
version: '3.8'

services:
  crawl4ai:
    image: unclecode/crawl4ai:basic
    ports:
      - "11235:11235"
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_API_TOKEN:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
    # Additional env variables as needed
    volumes:
      - /dev/shm:/dev/shm
```

To run:

```bash
docker-compose up -d
```

And to stop:

```bash
docker-compose down
```

**Troubleshooting**:

- **Check logs**: `docker-compose logs -f crawl4ai`
- **Remove orphan containers**: `docker-compose down --remove-orphans`
- **Remove networks**: `docker network rm <network_name>`

---

## 5. Making Requests to the Container

**Base URL**: `http://localhost:11235`

### Example: Basic Crawl

```python
import requests

task_request = {
    "urls": "https://example.com",
    "priority": 10
}

response = requests.post("http://localhost:11235/crawl", json=task_request)
task_id = response.json()["task_id"]

# Poll for status
status_url = f"http://localhost:11235/task/{task_id}"
status = requests.get(status_url).json()
print(status)
```

If you used an API token, do:

```python
headers = {"Authorization": "Bearer your_secret_token"}
response = requests.post(
    "http://localhost:11235/crawl",
    headers=headers,
    json=task_request
)
```

---

## 6. Docker + New Crawler Config Approach

### Using `BrowserConfig` & `CrawlerRunConfig` in Requests

The Docker-based solution can accept **crawler configurations** in the request JSON (legacy doc might show direct parameters, but we want to embed them in `crawler_params` or `extra` to align with the new approach). For example:

```python
import requests

request_data = {
    "urls": "https://www.nbcnews.com/business",
    "crawler_params": {
        "headless": True,
        "browser_type": "chromium",
        "verbose": True,
        "page_timeout": 30000,
        # ... any other BrowserConfig-like fields
    },
    "extra": {
        "word_count_threshold": 50,
        "bypass_cache": True
    }
}

response = requests.post("http://localhost:11235/crawl", json=request_data)
task_id = response.json()["task_id"]
```

This is the recommended style if you want to replicate `BrowserConfig` and `CrawlerRunConfig` settings in Docker mode.

---

## 7. Example: JSON Extraction in Docker

```python
import requests
import json

# Define a schema for CSS extraction
schema = {
    "name": "Coinbase Crypto Prices",
    "baseSelector": ".cds-tableRow-t45thuk",
    "fields": [
        {
            "name": "crypto",
            "selector": "td:nth-child(1) h2",
            "type": "text"
        },
        {
            "name": "symbol",
            "selector": "td:nth-child(1) p",
            "type": "text"
        },
        {
            "name": "price",
            "selector": "td:nth-child(2)",
            "type": "text"
        }
    ]
}

request_data = {
    "urls": "https://www.coinbase.com/explore",
    "extraction_config": {
        "type": "json_css",
        "params": {"schema": schema}
    },
    "crawler_params": {
        "headless": True,
        "verbose": True
    }
}

resp = requests.post("http://localhost:11235/crawl", json=request_data)
task_id = resp.json()["task_id"]

# Poll for status
status = requests.get(f"http://localhost:11235/task/{task_id}").json()
if status["status"] == "completed":
    extracted_content = status["result"]["extracted_content"]
    data = json.loads(extracted_content)
    print("Extracted:", len(data), "entries")
else:
    print("Task still in progress or failed.")
```

---

## 8. Why This Docker Is Temporary

**We are building a new, stable approach**:

- The current Docker container is **experimental** and might break with future releases.  
- We plan a stable release in **2025** with a more robust API, versioning, and orchestration.  
- If you use this Docker in production, do so at your own risk and be prepared for **breaking changes**.

**Community**: Because Crawl4AI is open-source, you can track progress or contribute to the new Docker approach. Check the [GitHub repository](https://github.com/unclecode/crawl4ai) for roadmaps and updates.

---

## 9. Known Limitations & Next Steps

1. **Not Production-Ready**: This Docker approach lacks extensive security, logging, or advanced config for large-scale usage.  
2. **Ongoing Changes**: Expect API changes. The official stable version is targeted for **2025**.  
3. **LLM Integrations**: Docker images are big if you want GPU or multiple model providers. We might unify these in a future build.  
4. **Performance**: For concurrency or large crawls, you may need to tune resources (memory, CPU) and watch out for ephemeral storage.  
5. **Version Pinning**: If you must deploy, pin your Docker tag to a specific version (e.g., `:basic-0.3.7`) to avoid surprise updates.

### Next Steps

- **Watch the Repository**: For announcements on the new Docker architecture.  
- **Experiment**: Use this Docker for test or dev environments, but keep an eye out for breakage.  
- **Contribute**: If you have ideas or improvements, open a PR or discussion.  
- **Check Roadmaps**: See our [GitHub issues](https://github.com/unclecode/crawl4ai/issues) or [Roadmap doc](https://github.com/unclecode/crawl4ai/blob/main/ROADMAP.md) to find upcoming releases.

---

## 10. Summary

**Deploying with Docker** can simplify running Crawl4AI as a service. However:

- **This Docker** approach is **legacy** and subject to removal/overhaul.  
- For production, please weigh the risks carefully.  
- Detailed “new Docker approach” is coming in **2025**.

We hope this guide helps you do a quick spin-up of Crawl4AI in Docker for **experimental** usage. Stay tuned for the fully-supported version!