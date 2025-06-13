```markdown
# Examples for `crawl4ai` - Deployment Component

**Target Document Type:** Examples Collection
**Target Output Filename Suggestion:** `llm_examples_deployment.md`
**Library Version Context:** 0.5.1-d1
**Outline Generation Date:** 2025-05-24
---

This document provides runnable code examples showcasing the diverse usage patterns and configurations of the `crawl4ai` deployment component. The examples primarily focus on interacting with the API provided by a deployed Crawl4ai instance.

## I. Introduction to Crawl4ai Deployment Examples

### 1.1. Overview of the API and common interaction patterns (e.g., using `requests` library).
The Crawl4ai deployment exposes a FastAPI backend. Most examples will use the `requests` library for synchronous calls and `httpx` for asynchronous calls to interact with these API endpoints. The base URL for a local deployment is typically `http://localhost:11235`.

```python
import requests
import httpx # For async examples later
import asyncio
import json
import time
import os
import base64

# Assume the Crawl4ai API is running locally
BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
API_TOKEN = os.environ.get("CRAWL4AI_API_TOKEN") # Set if your API requires auth

def get_headers():
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}"}
    return {}

print(f"Crawl4AI API Base URL: {BASE_URL}")
if API_TOKEN:
    print("API Token will be used for authenticated requests.")
else:
    print("No API Token found in env; assuming API does not require authentication for these examples.")

# A simple synchronous GET request
try:
    response = requests.get(f"{BASE_URL}/health")
    response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)
    print(f"Health check successful: {response.json()}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to Crawl4AI API: {e}")
    print("Please ensure the Crawl4AI Docker container or server is running.")
```

### 1.2. Note on Authentication: Brief explanation of when and how to use API tokens.
If JWT authentication is enabled in `config.yml` (via `security.jwt_enabled: true`), most API endpoints will require an `Authorization: Bearer <YOUR_TOKEN>` header. You can obtain a token from the `/token` endpoint using a whitelisted email address. The `get_headers()` helper function in the examples will attempt to use `CRAWL4AI_API_TOKEN` if set.

---
## II. Docker and Docker-Compose

### 2.1. Building the Docker Image

#### 2.1.1. Example: Basic `docker build` command.
This command builds the default Docker image from the root of the `crawl4ai` repository.
```bash
# Navigate to the root of the crawl4ai repository
# cd /path/to/crawl4ai
docker build -t crawl4ai:latest .
```

#### 2.1.2. Example: Building with `INSTALL_TYPE=all` build argument.
This installs all optional dependencies, including those for advanced AI/ML features.
```bash
# Navigate to the root of the crawl4ai repository
# cd /path/to/crawl4ai
docker build --build-arg INSTALL_TYPE=all -t crawl4ai:all-features .
```

#### 2.1.3. Example: Building with `ENABLE_GPU=true` build argument (conceptual, as GPU usage is complex).
This attempts to include GPU support (e.g., CUDA toolkits) if the base image and host support it.
```bash
# Navigate to the root of the crawl4ai repository
# cd /path/to/crawl4ai
# Ensure your Docker daemon and host are configured for GPU passthrough
docker build --build-arg ENABLE_GPU=true --build-arg TARGETARCH=amd64 -t crawl4ai:gpu-amd64 .
# For ARM64 with GPU (e.g., NVIDIA Jetson), you might need specific base images or configurations.
# docker build --build-arg ENABLE_GPU=true --build-arg TARGETARCH=arm64 -t crawl4ai:gpu-arm64 .
```
**Note:** Full GPU support in Docker can be complex and depends on your host system, NVIDIA drivers, and Docker version. The `Dockerfile` provides a basic attempt.

---
### 2.2. Running with Docker Compose

#### 2.2.1. Example: Basic `docker-compose up` using the provided `docker-compose.yml`.
This starts the Crawl4ai service as defined in the `docker-compose.yml` file.
```bash
# Navigate to the directory containing docker-compose.yml
# cd /path/to/crawl4ai
docker-compose up -d
```

#### 2.2.2. Example: Overriding image tag in `docker-compose` via environment variable `TAG`.
You can specify a different image tag for the `crawl4ai` service.
```bash
# Example: Using a specific version tag
TAG=0.6.0 docker-compose up -d

# Example: Using a custom built tag
# TAG=my-custom-crawl4ai-build docker-compose up -d
```

#### 2.2.3. Example: Overriding `INSTALL_TYPE` in `docker-compose` via environment variable.
If your `docker-compose.yml` is set up to use build arguments from environment variables, you can override `INSTALL_TYPE`.
```bash
# Assuming docker-compose.yml uses INSTALL_TYPE from env for the build context:
# (The provided docker-compose.yml directly passes it as a build arg)
# If you modify docker-compose.yml to pick up an env var for INSTALL_TYPE:
# INSTALL_TYPE=all docker-compose up -d --build
```
**Note:** The provided `docker-compose.yml` directly sets `INSTALL_TYPE` in the `args` section. To make it environment-variable driven like `TAG`, you would modify the `docker-compose.yml`'s `build.args` section.

---
### 2.3. Configuration via Environment Variables & `.llm.env`

#### 2.3.1. Example: Setting `OPENAI_API_KEY` using an `.llm.env` file.
Create a `.llm.env` file in the same directory as `docker-compose.yml` or where you run the server.
```text
# Contents of .llm.env
OPENAI_API_KEY="sk-your_openai_api_key_here"
```
The `docker-compose.yml` (or server if run directly) will load this file.

#### 2.3.2. Example: Showing how to pass multiple LLM API keys via `.llm.env`.
You can add keys for various supported LLM providers.
```text
# Contents of .llm.env
OPENAI_API_KEY="sk-your_openai_api_key_here"
ANTHROPIC_API_KEY="sk-ant-your_anthropic_api_key_here"
GROQ_API_KEY="gsk_your_groq_api_key_here"
# ...and other keys supported by LiteLLM
```

---
### 2.4. Accessing the Deployed Service

#### 2.4.1. Example: Python script to perform a basic health check (`/health`) on the locally deployed service.
```python
import requests
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")

try:
    response = requests.get(f"{BASE_URL}/health")
    response.raise_for_status()
    data = response.json()
    print(f"Service is healthy. Version: {data.get('version')}, Timestamp: {data.get('timestamp')}")
except requests.exceptions.RequestException as e:
    print(f"Failed to connect or health check failed: {e}")
```

#### 2.4.2. Example: Accessing the API playground at `/playground`.
Open your web browser and navigate to `http://localhost:11235/playground` (or your deployed URL + `/playground`). This will show the FastAPI interactive API documentation.

---
### 2.5. Understanding Shared Memory

#### 2.5.1. Explanation: Importance of `/dev/shm` for Chromium performance and how it's configured in `docker-compose.yml`.
Chromium-based browsers (like Chrome, Edge) use `/dev/shm` (shared memory) extensively. If the default Docker limit for `/dev/shm` (often 64MB) is too small, browser instances can crash or perform poorly. The `docker-compose.yml` provided with Crawl4ai typically increases this:
```yaml
# Snippet from a typical docker-compose.yml for crawl4ai
# services:
#   crawl4ai:
#     # ... other configurations ...
#     shm_size: '1g' # Or '2g', depending on expected load
#     # Alternatively, for more flexibility but less security:
#     # volumes:
#     #   - /dev/shm:/dev/shm
```
Setting `shm_size` or mounting `/dev/shm` directly from the host provides more shared memory, preventing common browser crashes within Docker. The `Dockerfile` also sets `ENV DEBIAN_FRONTEND=noninteractive` and browser flags like `--disable-dev-shm-usage` to mitigate some issues, but adequate shared memory is still crucial.

---
## III. Interacting with the Crawl4ai API Endpoints

### A. Authentication (`/token`)

#### A.1. Example: Python script to obtain an API token using a valid email.
This example assumes JWT authentication is enabled and "user@example.com" is whitelisted (this is illustrative, actual whitelisting is not part of the default config).
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")

# This email domain would need to be configured as allowed in your security settings
# if verify_email_domain is used.
email_to_test = "user@example.com" # Replace with a valid email if your server uses domain verification

payload = {"email": email_to_test}
try:
    response = requests.post(f"{BASE_URL}/token", json=payload)
    if response.status_code == 200:
        token_data = response.json()
        print(f"Successfully obtained token for {email_to_test}:")
        print(json.dumps(token_data, indent=2))
        # Store this token for subsequent authenticated requests
        # API_TOKEN = token_data["access_token"]
    else:
        print(f"Failed to obtain token for {email_to_test}. Status: {response.status_code}, Response: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to /token endpoint: {e}")
```
**Note:** The default `config.yml` has `security.jwt_enabled: false`. For this example to fully work, you would need to enable JWT and potentially configure allowed email domains.

#### A.2. Example: Python script attempting to obtain a token with an invalid email domain and handling the error.
```python
import requests
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")

# Assuming "invalid-domain.com" is not whitelisted.
# The default Crawl4AI config doesn't whitelist specific domains for /token,
# but if `verify_email_domain` were true in auth.py, this would be relevant.
# For now, this will likely succeed if jwt_enabled is false, or fail if jwt_enabled is true
# and no user exists, or pass if jwt_enabled is true and any email can get a token.
payload = {"email": "test@invalid-domain.com"}
try:
    response = requests.post(f"{BASE_URL}/token", json=payload)
    if response.status_code == 400 and "Invalid email domain" in response.text:
        print(f"Correctly failed to obtain token for invalid domain: {response.text}")
    elif response.status_code == 200:
        print(f"Obtained token (unexpected if domain verification is strict): {response.json()}")
    else:
        print(f"Token request status: {response.status_code}, Response: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to /token endpoint: {e}")
```

#### A.3. Example: Python script making an authenticated request to a protected endpoint.
This example assumes an endpoint like `/md` is protected and requires a token.
```python
import requests
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
# First, obtain a token (replace with actual token for a real protected setup)
# For this example, we'll use a placeholder. If API_TOKEN is set in env, it will be used.
# If not, and the endpoint is truly protected, this will fail.
# API_TOKEN = "your_manually_obtained_token_or_from_previous_step"

headers = get_headers() # Uses API_TOKEN from environment if set

md_payload = {"url": "https://example.com"}
try:
    response = requests.post(f"{BASE_URL}/md", json=md_payload, headers=headers)
    if response.status_code == 200:
        print("Successfully accessed protected /md endpoint.")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:500] + "...")
    elif response.status_code == 401 or response.status_code == 403:
        print(f"Authentication/Authorization failed for /md: {response.status_code} - {response.text}")
        print("Ensure JWT is enabled and you have a valid token if this endpoint is protected.")
    else:
        print(f"Request to /md failed: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to /md endpoint: {e}")
```
**Note:** By default, most Crawl4ai endpoints are not protected by JWT even if `jwt_enabled` is true, unless explicitly decorated with `Depends(token_dep)`.

---
### B. Core Crawling Endpoints

#### B.1. `/crawl` (Asynchronous Job-based Crawling via Redis)

The `/crawl` endpoint submits a job to a Redis queue. You then poll the `/task/{task_id}` endpoint to get the status and results.

##### B.1.1. Example: Submitting a single URL crawl job and getting a `task_id`.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "urls": ["https://example.com"],
    # browser_config and crawler_config are optional, defaults will be used
}

try:
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
    response.raise_for_status()
    job_data = response.json()
    task_id = job_data.get("task_id")
    if task_id:
        print(f"Crawl job submitted successfully. Task ID: {task_id}")
        print(f"Poll status at: {BASE_URL}/task/{task_id}")
    else:
        print(f"Failed to submit job or get task_id: {job_data}")
except requests.exceptions.RequestException as e:
    print(f"Error submitting crawl job: {e}")
```

##### B.1.2. Example: Submitting multiple URLs as a single crawl job.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "urls": ["https://example.com", "https://www.python.org"],
}

try:
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
    response.raise_for_status()
    job_data = response.json()
    task_id = job_data.get("task_id")
    if task_id:
        print(f"Multi-URL crawl job submitted. Task ID: {task_id}")
    else:
        print(f"Failed to submit job: {job_data}")
except requests.exceptions.RequestException as e:
    print(f"Error submitting multi-URL crawl job: {e}")

```

##### B.1.3. Example: Submitting a crawl job with a custom `browser_config` (e.g., headless false).
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "urls": ["https://example.com"],
    "browser_config": {
        "headless": False, # Run browser in visible mode (if server environment supports UI)
        "viewport_width": 800,
        "viewport_height": 600
    }
}

try:
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
    response.raise_for_status()
    job_data = response.json()
    task_id = job_data.get("task_id")
    if task_id:
        print(f"Crawl job with custom browser_config submitted. Task ID: {task_id}")
    else:
        print(f"Failed to submit job: {job_data}")
except requests.exceptions.RequestException as e:
    print(f"Error submitting crawl job with custom browser_config: {e}")
```

##### B.1.4. Example: Submitting a crawl job with a custom `crawler_config` (e.g., specific `word_count_threshold`).
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "urls": ["https://example.com"],
    "crawler_config": {
        "word_count_threshold": 50, # Only process content blocks with more than 50 words
        "screenshot": True # Also take a screenshot
    }
}

try:
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
    response.raise_for_status()
    job_data = response.json()
    task_id = job_data.get("task_id")
    if task_id:
        print(f"Crawl job with custom crawler_config submitted. Task ID: {task_id}")
    else:
        print(f"Failed to submit job: {job_data}")
except requests.exceptions.RequestException as e:
    print(f"Error submitting crawl job with custom crawler_config: {e}")
```

##### B.1.5. Example: Submitting a job that uses a specific `CacheMode` (e.g., `BYPASS`).
`CacheMode` values are typically: "DISABLED", "ENABLED", "BYPASS", "READ_ONLY", "WRITE_ONLY".
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "urls": ["https://example.com"],
    "crawler_config": {
        "cache_mode": "BYPASS" # Force a fresh crawl, ignore existing cache, don't write to cache
    }
}

try:
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
    response.raise_for_status()
    job_data = response.json()
    task_id = job_data.get("task_id")
    if task_id:
        print(f"Crawl job with CacheMode.BYPASS submitted. Task ID: {task_id}")
    else:
        print(f"Failed to submit job: {job_data}")
except requests.exceptions.RequestException as e:
    print(f"Error submitting crawl job with CacheMode.BYPASS: {e}")
```

##### B.1.6. Example: Submitting a job to extract PDF content from a URL.
(This assumes the URL points directly to a PDF or the page leads to a PDF download that the crawler handles).
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

# URL of a sample PDF file
pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

payload = {
    "urls": [pdf_url],
    "crawler_config": {
        # Crawl4ai should auto-detect PDF content type and use appropriate processor
        "pdf": True # Explicitly enabling PDF processing, though often auto-detected
    }
}

try:
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
    response.raise_for_status()
    job_data = response.json()
    task_id = job_data.get("task_id")
    if task_id:
        print(f"PDF crawl job submitted for {pdf_url}. Task ID: {task_id}")
        print(f"Poll status at: {BASE_URL}/task/{task_id}")
    else:
        print(f"Failed to submit PDF crawl job: {job_data}")
except requests.exceptions.RequestException as e:
    print(f"Error submitting PDF crawl job: {e}")
```

##### B.1.7. Example: Submitting a job to take a screenshot from a URL.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "urls": ["https://example.com"],
    "crawler_config": {
        "screenshot": True,
        "screenshot_wait_for": 2 # wait 2 seconds after page load before screenshot
    }
}

try:
    response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
    response.raise_for_status()
    job_data = response.json()
    task_id = job_data.get("task_id")
    if task_id:
        print(f"Screenshot job submitted for example.com. Task ID: {task_id}")
        print(f"Poll status at: {BASE_URL}/task/{task_id}")
    else:
        print(f"Failed to submit screenshot job: {job_data}")
except requests.exceptions.RequestException as e:
    print(f"Error submitting screenshot job: {e}")
```

---
#### B.2. `/task/{task_id}` (Job Status and Results)

##### B.2.1. Example: Python script to poll the `/task/{task_id}` endpoint for PENDING status.
```python
import requests
import time
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

# Assume task_id is obtained from a previous /crawl request
# For this example, we'll submit a quick job first
submit_payload = {"urls": ["http://example.com/nonexistent-page-for-quick-fail-or-processing"]}
task_id = None
try:
    submit_response = requests.post(f"{BASE_URL}/crawl", json=submit_payload, headers=headers)
    submit_response.raise_for_status()
    task_id = submit_response.json().get("task_id")
except requests.exceptions.RequestException as e:
    print(f"Failed to submit initial job for polling example: {e}")

if task_id:
    print(f"Polling for task: {task_id}")
    for _ in range(5): # Poll a few times
        try:
            status_response = requests.get(f"{BASE_URL}/task/{task_id}", headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            print(f"Current status: {status_data.get('status')}")
            if status_data.get('status') in ["COMPLETED", "FAILED"]:
                break
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"Error polling task status: {e}")
            break
else:
    print("No task ID to poll.")
```

##### B.2.2. Example: Python script to retrieve results for a COMPLETED job.
```python
import requests
import time
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

# Submit a job that should complete successfully
submit_payload = {"urls": ["https://example.com"]}
task_id = None
try:
    submit_response = requests.post(f"{BASE_URL}/crawl", json=submit_payload, headers=headers)
    submit_response.raise_for_status()
    task_id = submit_response.json().get("task_id")
except requests.exceptions.RequestException as e:
    print(f"Failed to submit job for result retrieval example: {e}")


if task_id:
    print(f"Waiting for task {task_id} to complete...")
    while True:
        try:
            status_response = requests.get(f"{BASE_URL}/task/{task_id}", headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            current_status = status_data.get('status')
            print(f"Task status: {current_status}")

            if current_status == "COMPLETED":
                print("\nJob COMPLETED. Results:")
                # The 'result' field contains the JSON string of the CrawlResult model(s)
                # For a single URL job, it's typically a dict. For multiple, a list of dicts.
                # The structure from api.py suggests `result` field in Redis is a JSON string
                # of a dictionary which itself contains a 'results' key (list of CrawlResult dicts).
                
                # This is based on how handle_crawl_job in api.py stores results
                # and how the /task/{task_id} endpoint decodes it.
                # The 'result' from /task/{task_id} should already be a parsed dict.
                
                crawl_results_wrapper = status_data.get("result")
                if crawl_results_wrapper and "results" in crawl_results_wrapper:
                    actual_results = crawl_results_wrapper["results"]
                    for i, res_item in enumerate(actual_results):
                        print(f"\n--- Result for URL {i+1} ({res_item.get('url', 'N/A')}) ---")
                        print(f"  Success: {res_item.get('success')}")
                        print(f"  Markdown (first 100 chars): {res_item.get('markdown', {}).get('raw_markdown', '')[:100]}...")
                        if res_item.get('screenshot'):
                             print("  Screenshot captured (base64 data not printed).")
                else:
                     print(f"Unexpected result structure: {crawl_results_wrapper}")
                break
            elif current_status == "FAILED":
                print(f"\nJob FAILED. Error: {status_data.get('error')}")
                break
            
            time.sleep(3) # Poll every 3 seconds
        except requests.exceptions.RequestException as e:
            print(f"Error polling task status: {e}")
            break
        except KeyboardInterrupt:
            print("\nPolling interrupted.")
            break
else:
    print("No task ID to retrieve results for.")

```

##### B.2.3. Example: Python script to get error details for a FAILED job.
```python
import requests
import time
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

# Submit a job that is likely to fail (e.g., invalid URL or one that times out quickly)
submit_payload = {"urls": ["http://nonexistentdomain1234567890.com"]}
task_id = None
try:
    submit_response = requests.post(f"{BASE_URL}/crawl", json=submit_payload, headers=headers)
    submit_response.raise_for_status()
    task_id = submit_response.json().get("task_id")
except requests.exceptions.RequestException as e:
    print(f"Failed to submit job for failure example: {e}")

if task_id:
    print(f"Waiting for task {task_id} (expected to fail)...")
    while True:
        try:
            status_response = requests.get(f"{BASE_URL}/task/{task_id}", headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            current_status = status_data.get('status')
            print(f"Task status: {current_status}")

            if current_status == "FAILED":
                print("\nJob FAILED as expected.")
                error_message = status_data.get('error', 'No error message provided.')
                print(f"Error details: {error_message}")
                break
            elif current_status == "COMPLETED":
                print("\nJob COMPLETED unexpectedly.")
                break
            
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"Error polling task status: {e}")
            break
        except KeyboardInterrupt:
            print("\nPolling interrupted.")
            break
else:
    print("No task ID to check for failure.")
```

##### B.2.4. Example: Full workflow - submit job, poll status, retrieve results or error.
This combines the above examples into a more complete client script.
```python
import requests
import time
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

def submit_and_poll(payload, timeout_seconds=60):
    task_id = None
    try:
        # Submit the job
        print(f"Submitting job with payload: {payload}")
        submit_response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
        submit_response.raise_for_status()
        task_id = submit_response.json().get("task_id")
        if not task_id:
            print("Error: No task_id received.")
            return None
        print(f"Job submitted. Task ID: {task_id}. Polling for completion...")

        # Poll for status
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            status_response = requests.get(f"{BASE_URL}/task/{task_id}", headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            current_status = status_data.get('status')
            print(f"  Task {task_id} status: {current_status} (elapsed: {time.time() - start_time:.1f}s)")

            if current_status == "COMPLETED":
                print(f"Task {task_id} COMPLETED.")
                return status_data.get("result") # This should be the parsed JSON result
            elif current_status == "FAILED":
                print(f"Task {task_id} FAILED.")
                print(f"Error: {status_data.get('error')}")
                return None
            time.sleep(5) # Poll interval
        
        print(f"Task {task_id} timed out after {timeout_seconds} seconds.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    crawl_payload = {
        "urls": ["https://www.python.org/about/"],
        "crawler_config": {"screenshot": False}
    }
    results_data = submit_and_poll(crawl_payload)

    if results_data and "results" in results_data:
        for i, res_item in enumerate(results_data["results"]):
            print(f"\n--- Result for URL {res_item.get('url', 'N/A')} ---")
            print(f"  Success: {res_item.get('success')}")
            print(f"  Markdown (first 200 chars): {res_item.get('markdown', {}).get('raw_markdown', '')[:200]}...")
    elif results_data: # If result isn't in the expected wrapper structure
        print(f"\nReceived result data (unexpected structure):")
        print(json.dumps(results_data, indent=2, ensure_ascii=False))

```

---
#### B.3. `/crawl/stream` (Streaming Crawl Results)

##### B.3.1. Example: Python script to stream crawl results for a single URL and process NDJSON.
```python
import requests
import json
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()
headers['Accept'] = 'application/x-ndjson' # Important for streaming

payload = {
    "urls": ["https://example.com"],
    "crawler_config": {"stream": True} # Ensure stream is True in config
}

print(f"Streaming results for {payload['urls'][0]}...")
try:
    with requests.post(f"{BASE_URL}/crawl/stream", json=payload, headers=headers, stream=True) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    result_chunk = json.loads(line.decode('utf-8'))
                    if "status" in result_chunk and result_chunk["status"] == "completed":
                        print("\nStream finished.")
                        break
                    print("\nReceived chunk:")
                    # Print some key info from the chunk
                    print(f"  URL: {result_chunk.get('url', 'N/A')}")
                    print(f"  Success: {result_chunk.get('success')}")
                    if 'markdown' in result_chunk and isinstance(result_chunk['markdown'], dict):
                         print(f"  Markdown (snippet): {result_chunk['markdown'].get('raw_markdown', '')[:100]}...")
                    else:
                         print(f"  Markdown (snippet): {str(result_chunk.get('markdown', ''))[:100]}...")
                    if result_chunk.get('error_message'):
                        print(f"  Error: {result_chunk.get('error_message')}")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON line: {e} - Line: {line.decode('utf-8')}")
except requests.exceptions.RequestException as e:
    print(f"Error during streaming request: {e}")

```

##### B.3.2. Example: Python script to stream crawl results for multiple URLs.
```python
import requests
import json
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()
headers['Accept'] = 'application/x-ndjson'

payload = {
    "urls": ["https://example.com", "https://www.python.org/doc/"],
    "crawler_config": {"stream": True}
}

print(f"Streaming results for multiple URLs...")
try:
    with requests.post(f"{BASE_URL}/crawl/stream", json=payload, headers=headers, stream=True) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    result_chunk = json.loads(line.decode('utf-8'))
                    if "status" in result_chunk and result_chunk["status"] == "completed":
                        print("\nStream finished for all URLs.")
                        break
                    print(f"\nChunk for URL: {result_chunk.get('url', 'N/A')}")
                    # Process or display part of the result
                    print(f"  Success: {result_chunk.get('success')}")
                    if 'markdown' in result_chunk and isinstance(result_chunk['markdown'], dict):
                         print(f"  Markdown (snippet): {result_chunk['markdown'].get('raw_markdown', '')[:70]}...")
                    else:
                         print(f"  Markdown (snippet): {str(result_chunk.get('markdown', ''))[:70]}...")

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON line: {e} - Line: {line.decode('utf-8')}")
except requests.exceptions.RequestException as e:
    print(f"Error during streaming request: {e}")
```

##### B.3.3. Example: Streaming crawl results with custom `browser_config` and `crawler_config`.
```python
import requests
import json
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()
headers['Accept'] = 'application/x-ndjson'

payload = {
    "urls": ["https://example.com"],
    "browser_config": {
        "headless": True,
        "user_agent": "Crawl4AI-Stream-Tester/1.0"
    },
    "crawler_config": {
        "stream": True,
        "word_count_threshold": 10 # Lower threshold for this example
    }
}

print(f"Streaming results with custom configs for {payload['urls'][0]}...")
try:
    with requests.post(f"{BASE_URL}/crawl/stream", json=payload, headers=headers, stream=True) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                result_chunk = json.loads(line.decode('utf-8'))
                if "status" in result_chunk and result_chunk["status"] == "completed":
                    print("\nStream finished.")
                    break
                print("\nReceived chunk with custom config:")
                print(f"  URL: {result_chunk.get('url')}")
                print(f"  Word count threshold was: {payload['crawler_config']['word_count_threshold']}")
                if 'markdown' in result_chunk and isinstance(result_chunk['markdown'], dict):
                     print(f"  Markdown (snippet): {result_chunk['markdown'].get('raw_markdown', '')[:70]}...")
                else:
                     print(f"  Markdown (snippet): {str(result_chunk.get('markdown', ''))[:70]}...")
except requests.exceptions.RequestException as e:
    print(f"Error during streaming request: {e}")
```

##### B.3.4. Example: Handling connection closure or errors during streaming.
```python
import requests
import json
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()
headers['Accept'] = 'application/x-ndjson'

payload = {
    "urls": ["https://thissitedoesnotexist12345.com", "https://example.com"], # First URL will fail
    "crawler_config": {"stream": True}
}

print(f"Streaming with a URL expected to fail...")
try:
    with requests.post(f"{BASE_URL}/crawl/stream", json=payload, headers=headers, stream=True) as response:
        # We might not get a non-200 status code immediately if the connection itself is established
        # Errors for individual URLs will be part of the NDJSON stream
        for line in response.iter_lines():
            if line:
                try:
                    result_chunk = json.loads(line.decode('utf-8'))
                    print(f"\nReceived data: {result_chunk.get('url', 'N/A')}")
                    if "status" in result_chunk and result_chunk["status"] == "completed":
                        print("Stream finished.")
                        break
                    if result_chunk.get('error_message'):
                        print(f"  ERROR for {result_chunk.get('url')}: {result_chunk.get('error_message')}")
                    elif result_chunk.get('success'):
                        print(f"  SUCCESS for {result_chunk.get('url')}")
                except json.JSONDecodeError as e:
                    print(f"  Error decoding JSON line: {e}")
except requests.exceptions.ChunkedEncodingError:
    print("Connection closed unexpectedly by server during streaming (ChunkedEncodingError).")
except requests.exceptions.RequestException as e:
    print(f"General error during streaming request: {e}")
```

---
### C. Content Transformation & Utility Endpoints

#### C.1. `/md` (Markdown Generation)

##### C.1.1. Example: Getting raw Markdown for a URL (default filter).
The default filter is `FIT` if no filter is specified.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {"url": "https://example.com", "f": "RAW"} # 'f' is for filter_type
try:
    response = requests.post(f"{BASE_URL}/md", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Markdown (RAW filter - first 300 chars):")
    print(data.get("markdown", "")[:300] + "...")
except requests.exceptions.RequestException as e:
    print(f"Error fetching Markdown: {e}")
```

##### C.1.2. Example: Getting Markdown using the `FIT` filter type.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {"url": "https://example.com", "f": "FIT"}
try:
    response = requests.post(f"{BASE_URL}/md", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Markdown (FIT filter - first 300 chars):")
    print(data.get("markdown", "")[:300] + "...")
except requests.exceptions.RequestException as e:
    print(f"Error fetching Markdown: {e}")
```

##### C.1.3. Example: Getting Markdown using the `BM25` filter type with a specific query.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)", 
    "f": "BM25",
    "q": "What are the key features of Python?" # Query for BM25 filtering
}
try:
    response = requests.post(f"{BASE_URL}/md", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    print(f"Markdown (BM25 filter, query='{payload['q']}' - first 300 chars):")
    print(data.get("markdown", "")[:300] + "...")
except requests.exceptions.RequestException as e:
    print(f"Error fetching Markdown: {e}")
```

##### C.1.4. Example: Getting Markdown using the `LLM` filter type with a query (conceptual, requires LLM setup).
This requires an LLM provider (like OpenAI) to be configured in `config.yml` or via environment variables loaded by the server.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "f": "LLM",
    "q": "Summarize the history of Python" # Query for LLM to focus on
}
print("Attempting LLM-filtered Markdown (this may take a moment and requires LLM config)...")
try:
    # LLM requests can take longer
    response = requests.post(f"{BASE_URL}/md", json=payload, headers=headers, timeout=120) 
    response.raise_for_status()
    data = response.json()
    print(f"Markdown (LLM filter, query='{payload['q']}' - first 300 chars):")
    print(data.get("markdown", "")[:300] + "...")
except requests.exceptions.RequestException as e:
    print(f"Error fetching LLM-filtered Markdown: {e}")
    print("Ensure your LLM provider (e.g., OPENAI_API_KEY) is configured for the server.")
```

##### C.1.5. Example: Demonstrating cache usage with the `/md` endpoint (`c` parameter).
The `c` parameter can be "0" (bypass write, read if available - effectively WRITE_ONLY for this endpoint if no cache exists), "1" (force refresh, write - effectively ENABLED for this endpoint), or other numbers for revision control (not shown here).
```python
import requests
import os
import json
import time

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()
test_url = "https://example.com"

# First call: cache miss, should fetch and write to cache
print("First call (cache_mode=ENABLED implied by 'c=1', or default if 'c' omitted)")
payload1 = {"url": test_url, "f": "RAW", "c": "1"} # c="1" forces refresh and writes
start_time = time.time()
response1 = requests.post(f"{BASE_URL}/md", json=payload1, headers=headers)
duration1 = time.time() - start_time
response1.raise_for_status()
print(f"First call duration: {duration1:.2f}s. Markdown length: {len(response1.json().get('markdown', ''))}")

# Second call: should be a cache hit if c="0" or c is omitted and cache is fresh
print("\nSecond call (cache_mode=READ_ONLY implied by 'c=0', or default if 'c' omitted and cache fresh)")
payload2 = {"url": test_url, "f": "RAW", "c": "0"} # c="0" attempts to read from cache
start_time = time.time()
response2 = requests.post(f"{BASE_URL}/md", json=payload2, headers=headers)
duration2 = time.time() - start_time
response2.raise_for_status()
print(f"Second call duration: {duration2:.2f}s. Markdown length: {len(response2.json().get('markdown', ''))}")

if duration2 < duration1 / 2 and duration1 > 0.1 : # Heuristic for cache hit
    print("Second call was significantly faster, likely a cache hit.")
else:
    print("Cache behavior inconclusive or first call was very fast.")
```

---
#### C.2. `/html` (Preprocessed HTML)

##### C.2.1. Example: Fetching preprocessed HTML for a URL suitable for schema extraction.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {"url": "https://example.com"}
try:
    response = requests.post(f"{BASE_URL}/html", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Preprocessed HTML (first 500 chars):")
    print(data.get("html", "")[:500] + "...")
    print(f"\nOriginal URL: {data.get('url')}")
except requests.exceptions.RequestException as e:
    print(f"Error fetching preprocessed HTML: {e}")
```

---
#### C.3. `/screenshot`

##### C.3.1. Example: Generating a PNG screenshot for a URL and receiving base64 data.
```python
import requests
import os
import base64
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {"url": "https://example.com"}
try:
    response = requests.post(f"{BASE_URL}/screenshot", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data.get("screenshot"):
        print("Screenshot received (base64 data).")
        # To save the image:
        # image_data = base64.b64decode(data["screenshot"])
        # with open("example_screenshot.png", "wb") as f:
        #     f.write(image_data)
        # print("Screenshot saved as example_screenshot.png")
    else:
        print(f"Screenshot generation failed or no data returned: {data}")
except requests.exceptions.RequestException as e:
    print(f"Error generating screenshot: {e}")
```

##### C.3.2. Example: Generating a screenshot with a custom `screenshot_wait_for` delay.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "url": "https://example.com",
    "screenshot_wait_for": 3  # Wait 3 seconds after page load
}
try:
    response = requests.post(f"{BASE_URL}/screenshot", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data.get("screenshot"):
        print(f"Screenshot with {payload['screenshot_wait_for']}s delay received.")
    else:
        print(f"Screenshot generation failed: {data}")
except requests.exceptions.RequestException as e:
    print(f"Error generating screenshot with delay: {e}")
```

##### C.3.3. Example: Saving screenshot to server-side path via `output_path`.
**Note:** This requires `output_path` to be a path accessible and writable by the server process. For Docker, this usually means a mounted volume.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

# This path needs to be valid from the server's perspective
# e.g., if running in Docker, it might be a path inside the container
# that is mapped to a host volume.
server_side_path = "/app/screenshots/example_com.png" # Example path

payload = {
    "url": "https://example.com",
    "output_path": server_side_path
}
try:
    response = requests.post(f"{BASE_URL}/screenshot", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data.get("success") and data.get("path"):
        print(f"Screenshot successfully saved to server path: {data.get('path')}")
        print("Note: This file is on the server, not the client machine unless paths are mapped.")
    else:
        print(f"Failed to save screenshot to server: {data}")
except requests.exceptions.RequestException as e:
    print(f"Error saving screenshot to server: {e}")
```

---
#### C.4. `/pdf`

##### C.4.1. Example: Generating a PDF for a URL and receiving base64 data.
```python
import requests
import os
import base64
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {"url": "https://example.com"}
try:
    response = requests.post(f"{BASE_URL}/pdf", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data.get("pdf"):
        print("PDF received (base64 data).")
        # To save the PDF:
        # pdf_data = base64.b64decode(data["pdf"])
        # with open("example_page.pdf", "wb") as f:
        #     f.write(pdf_data)
        # print("PDF saved as example_page.pdf")
    else:
        print(f"PDF generation failed or no data returned: {data}")
except requests.exceptions.RequestException as e:
    print(f"Error generating PDF: {e}")
```

##### C.4.2. Example: Saving PDF to server-side path via `output_path`.
**Note:** Similar to screenshots, `output_path` must be server-accessible.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

server_side_path = "/app/pdfs/example_com.pdf" # Example path

payload = {
    "url": "https://example.com",
    "output_path": server_side_path
}
try:
    response = requests.post(f"{BASE_URL}/pdf", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if data.get("success") and data.get("path"):
        print(f"PDF successfully saved to server path: {data.get('path')}")
    else:
        print(f"Failed to save PDF to server: {data}")
except requests.exceptions.RequestException as e:
    print(f"Error saving PDF to server: {e}")

```

---
#### C.5. `/execute_js`

##### C.5.1. Example: Executing a simple JavaScript snippet (e.g., `return document.title;`) on a page.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "url": "https://example.com",
    "scripts": ["return document.title;"]
}
try:
    response = requests.post(f"{BASE_URL}/execute_js", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json() # This is the full CrawlResult model as JSON
    print("Full CrawlResult from /execute_js:")
    # print(json.dumps(data, indent=2, ensure_ascii=False)) # Can be very long
    
    js_results = data.get("js_execution_result")
    if js_results and js_results.get("script_0"):
        print(f"\nResult of script 0 (document.title): {js_results['script_0']}")
    else:
        print(f"\nCould not find JS execution result: {js_results}")

except requests.exceptions.RequestException as e:
    print(f"Error executing JS: {e}")
```

##### C.5.2. Example: Executing multiple JavaScript snippets sequentially.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "url": "https://example.com",
    "scripts": [
        "return document.title;",
        "return document.querySelectorAll('p').length;",
        "() => { const h1 = document.querySelector('h1'); return h1 ? h1.innerText : 'No H1'; }()"
    ]
}
try:
    response = requests.post(f"{BASE_URL}/execute_js", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    js_results = data.get("js_execution_result")
    if js_results:
        print("\nResults of JS snippets:")
        print(f"  Script 0 (Title): {js_results.get('script_0')}")
        print(f"  Script 1 (Paragraph count): {js_results.get('script_1')}")
        print(f"  Script 2 (H1 text): {js_results.get('script_2')}")
    else:
        print(f"\nCould not find JS execution results: {js_results}")

except requests.exceptions.RequestException as e:
    print(f"Error executing multiple JS snippets: {e}")
```

##### C.5.3. Example: Demonstrating how the full `CrawlResult` (JSON of model) is returned.
The `/execute_js` endpoint returns the entire `CrawlResult` object, serialized to JSON. This includes HTML, Markdown, links, etc., in addition to the `js_execution_result`.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

payload = {
    "url": "https://example.com",
    "scripts": ["return window.location.href;"]
}
try:
    response = requests.post(f"{BASE_URL}/execute_js", json=payload, headers=headers)
    response.raise_for_status()
    crawl_result_data = response.json()
    
    print("Demonstrating full CrawlResult structure from /execute_js:")
    print(f"  URL crawled: {crawl_result_data.get('url')}")
    print(f"  Success: {crawl_result_data.get('success')}")
    print(f"  HTML (snippet): {crawl_result_data.get('html', '')[:100]}...")
    if isinstance(crawl_result_data.get('markdown'), dict):
        print(f"  Markdown (snippet): {crawl_result_data['markdown'].get('raw_markdown', '')[:100]}...")
    else:
        print(f"  Markdown (snippet): {str(crawl_result_data.get('markdown', ''))[:100]}...")

    js_result = crawl_result_data.get("js_execution_result", {}).get("script_0")
    print(f"  Result of JS (window.location.href): {js_result}")

except requests.exceptions.RequestException as e:
    print(f"Error demonstrating full CrawlResult: {e}")
```

---
### D. Contextual Endpoints

#### D.1. `/ask` (RAG-like Context Retrieval)
The `/ask` endpoint uses local Markdown files (`c4ai-code-context.md` and `c4ai-doc-context.md`, which should be in the same directory as `server.py`) for retrieval.

##### D.1.1. Example: Asking a general question to retrieve "code" context.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

params = {
    "context_type": "code",
    "query": "How to handle Playwright installation?" # General query
}
try:
    response = requests.get(f"{BASE_URL}/ask", params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Retrieved 'code' context for 'How to handle Playwright installation?':")
    if "code_results" in data:
        for i, item in enumerate(data["code_results"][:2]): # Show first 2 results
            print(f"\n--- Code Result {i+1} (Score: {item.get('score', 'N/A'):.2f}) ---")
            print(item.get("text", "")[:300] + "...")
    else:
        print(json.dumps(data, indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error asking for code context: {e}")
```

##### D.1.2. Example: Asking a general question to retrieve "doc" context.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

params = {
    "context_type": "doc",
    "query": "Explain Crawl4ai API endpoints"
}
try:
    response = requests.get(f"{BASE_URL}/ask", params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Retrieved 'doc' context for 'Explain Crawl4ai API endpoints':")
    if "doc_results" in data:
        for i, item in enumerate(data["doc_results"][:2]):
            print(f"\n--- Doc Result {i+1} (Score: {item.get('score', 'N/A'):.2f}) ---")
            print(item.get("text", "")[:300] + "...")
    else:
        print(json.dumps(data, indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error asking for doc context: {e}")
```

##### D.1.3. Example: Using the `query` parameter to filter context related to a specific function.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

params = {
    "context_type": "all", # Search both code and docs
    "query": "AsyncWebCrawler arun method"
}
try:
    response = requests.get(f"{BASE_URL}/ask", params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    print(f"Retrieved 'all' context for query: '{params['query']}'")
    if "code_results" in data:
        print(f"\nFound {len(data['code_results'])} code results.")
        # Optionally print snippets
    if "doc_results" in data:
        print(f"Found {len(data['doc_results'])} doc results.")
        # Optionally print snippets
    # print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "...")
except requests.exceptions.RequestException as e:
    print(f"Error asking with specific query: {e}")

```

##### D.1.4. Example: Adjusting `score_ratio` to change result sensitivity.
A lower `score_ratio` (e.g., 0.1) will return more, less relevant results. A higher one (e.g., 0.8) will be more strict. Default is 0.5.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

params_strict = {
    "context_type": "code",
    "query": "Playwright browser installation",
    "score_ratio": 0.8 # Higher, more strict
}
params_loose = {
    "context_type": "code",
    "query": "Playwright browser installation",
    "score_ratio": 0.2 # Lower, less strict
}

try:
    response_strict = requests.get(f"{BASE_URL}/ask", params=params_strict, headers=headers)
    response_strict.raise_for_status()
    data_strict = response_strict.json()
    print(f"Results with score_ratio=0.8: {len(data_strict.get('code_results', []))}")

    response_loose = requests.get(f"{BASE_URL}/ask", params=params_loose, headers=headers)
    response_loose.raise_for_status()
    data_loose = response_loose.json()
    print(f"Results with score_ratio=0.2: {len(data_loose.get('code_results', []))}")

except requests.exceptions.RequestException as e:
    print(f"Error adjusting score_ratio: {e}")
```

##### D.1.5. Example: Limiting results with `max_results`.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

params = {
    "context_type": "doc",
    "query": "crawl4ai features",
    "max_results": 3 # Limit to top 3 results
}
try:
    response = requests.get(f"{BASE_URL}/ask", params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    print(f"Retrieved max {params['max_results']} doc_results for 'crawl4ai features':")
    if "doc_results" in data:
        print(f"Actual results returned: {len(data['doc_results'])}")
        for item in data["doc_results"]:
            print(f"  - Score: {item.get('score', 0):.2f}, Text (snippet): {item.get('text', '')[:50]}...")
    else:
        print("No doc_results found.")
except requests.exceptions.RequestException as e:
    print(f"Error limiting results: {e}")
```

---
### E. Server & Configuration Information

#### E.1. `/config/dump`

##### E.1.1. Example: Dumping a `CrawlerRunConfig` Python object representation to its JSON equivalent via the API.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

# This is a Python-style string representation of a CrawlerRunConfig
# that the server's _safe_eval_config can parse.
config_string = "CrawlerRunConfig(word_count_threshold=50, screenshot=True, cache_mode=CacheMode.BYPASS)"

payload = {"code": config_string}
try:
    response = requests.post(f"{BASE_URL}/config/dump", json=payload, headers=headers)
    response.raise_for_status()
    dumped_json = response.json()
    print("Dumped CrawlerRunConfig JSON:")
    print(json.dumps(dumped_json, indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error dumping CrawlerRunConfig: {e}")
```

##### E.1.2. Example: Dumping a `BrowserConfig` Python object representation to its JSON equivalent via the API.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

config_string = "BrowserConfig(headless=False, user_agent='MyTestAgent/1.0')"
payload = {"code": config_string}
try:
    response = requests.post(f"{BASE_URL}/config/dump", json=payload, headers=headers)
    response.raise_for_status()
    dumped_json = response.json()
    print("Dumped BrowserConfig JSON:")
    print(json.dumps(dumped_json, indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error dumping BrowserConfig: {e}")
```

##### E.1.3. Example: Attempting to dump an invalid or non-serializable configuration string.
```python
import requests
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

# Invalid: not a recognized Crawl4AI config class
invalid_config_string = "MyCustomClass(param=1)"
payload = {"code": invalid_config_string}
try:
    response = requests.post(f"{BASE_URL}/config/dump", json=payload, headers=headers)
    if response.status_code == 400:
        print(f"Correctly failed to dump invalid config string. Server response: {response.json()}")
    else:
        print(f"Unexpected response for invalid config: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error attempting to dump invalid config: {e}")

# Invalid: nested function call (security restriction)
unsafe_config_string = "CrawlerRunConfig(word_count_threshold=__import__('os').system('echo unsafe'))"
payload_unsafe = {"code": unsafe_config_string}
try:
    response_unsafe = requests.post(f"{BASE_URL}/config/dump", json=payload_unsafe, headers=headers)
    if response_unsafe.status_code == 400:
        print(f"Correctly failed to dump unsafe config string. Server response: {response_unsafe.json()}")
    else:
        print(f"Unexpected response for unsafe config: {response_unsafe.status_code} - {response_unsafe.text}")
except requests.exceptions.RequestException as e:
    print(f"Error attempting to dump unsafe config: {e}")
```

---
#### E.2. `/schema`

##### E.2.1. Example: Fetching the default JSON schemas for `BrowserConfig` and `CrawlerRunConfig`.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

try:
    response = requests.get(f"{BASE_URL}/schema", headers=headers)
    response.raise_for_status()
    schemas = response.json()
    
    print("BrowserConfig Schema (sample):")
    # print(json.dumps(schemas.get("browser"), indent=2)) # Full schema can be long
    if "browser" in schemas and "properties" in schemas["browser"]:
        print(f"  BrowserConfig has {len(schemas['browser']['properties'])} properties.")
        print(f"  Example property 'headless': {schemas['browser']['properties'].get('headless')}")

    print("\nCrawlerRunConfig Schema (sample):")
    # print(json.dumps(schemas.get("crawler"), indent=2))
    if "crawler" in schemas and "properties" in schemas["crawler"]:
        print(f"  CrawlerRunConfig has {len(schemas['crawler']['properties'])} properties.")
        print(f"  Example property 'word_count_threshold': {schemas['crawler']['properties'].get('word_count_threshold')}")

except requests.exceptions.RequestException as e:
    print(f"Error fetching schemas: {e}")
```

---
#### E.3. `/health` & `/metrics`

##### E.3.1. Example: Python script to programmatically check the `/health` endpoint.
(Similar to example 2.4.1, but reiterated here for completeness of this section)
```python
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

try:
    response = requests.get(f"{BASE_URL}/health", headers=headers)
    response.raise_for_status()
    health_data = response.json()
    print("Health Check:")
    print(f"  Status: {health_data.get('status')}")
    print(f"  Version: {health_data.get('version')}")
    ts = health_data.get('timestamp')
    if ts:
        print(f"  Timestamp: {ts} (UTC: {datetime.utcfromtimestamp(ts).isoformat()})")
except requests.exceptions.RequestException as e:
    print(f"Error checking health: {e}")
```

##### E.3.2. Example: Accessing Prometheus metrics at `/metrics` (assuming Prometheus is enabled in `config.yml`).
This typically involves pointing a Prometheus scraper at the endpoint or manually fetching.
```python
import requests
import os

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
# Prometheus metrics are usually at /metrics, but the server.py config uses
# config["observability"]["prometheus"]["endpoint"] which defaults to "/metrics"
METRICS_ENDPOINT = "/metrics" # As per default config.yml
headers = get_headers()

try:
    # First, check if Prometheus is enabled in the server's config
    # This is a conceptual check, real check depends on your setup
    config_response = requests.get(f"{BASE_URL}/health", headers=headers) # Health often includes version
    # In a real scenario, you might have an endpoint to get active config or infer from behavior

    print(f"Attempting to fetch metrics from {BASE_URL}{METRICS_ENDPOINT}")
    response = requests.get(f"{BASE_URL}{METRICS_ENDPOINT}", headers=headers)
    if response.status_code == 200:
        print("Prometheus metrics response (first 500 chars):")
        print(response.text[:500] + "...")
    elif response.status_code == 404:
        print(f"Metrics endpoint {METRICS_ENDPOINT} not found. Ensure Prometheus is enabled in config.yml.")
    else:
        print(f"Error fetching metrics: {response.status_code} - {response.text}")

except requests.exceptions.RequestException as e:
    print(f"Error connecting to metrics endpoint: {e}")
```
**Note:** For this to work, `observability.prometheus.enabled` must be `true` in the server's `config.yml`.

---
## IV. Configuring the Deployment (via `config.yml`)

### 4.1. Note: These examples primarily show snippets of `config.yml` and describe their effect, rather than Python code to modify the live configuration.
The `config.yml` file is read by the server on startup. Changes typically require a server restart.

### 4.2. Rate Limiting Configuration

#### 4.2.1. Example `config.yml` snippet: Enabling rate limiting with a custom limit (e.g., "10/second").
```yaml
# In your config.yml
rate_limiting:
  enabled: true
  default_limit: "10/second" # Allows 10 requests per second per client IP
  # trusted_proxies: ["127.0.0.1"] # If behind a reverse proxy
```

#### 4.2.2. Example `config.yml` snippet: Using Redis as a storage backend for rate limiting.
This is recommended for production if you have multiple server instances.
```yaml
# In your config.yml
rate_limiting:
  enabled: true
  default_limit: "1000/minute"
  storage_uri: "redis://localhost:6379" # Or your Redis server URI
  # Ensure your Redis server is running and accessible
```

---
### 4.3. Security Settings Configuration

#### 4.3.1. Example `config.yml` snippet: Enabling JWT authentication.
```yaml
# In your config.yml
security:
  enabled: true
  jwt_enabled: true
  # jwt_secret_key: "YOUR_VERY_SECRET_KEY" # Auto-generated if not set
  # jwt_algorithm: "HS256"
  # jwt_access_token_expire_minutes: 30
  # jwt_allowed_email_domains: ["example.com", "another.org"] # Optional: Restrict token issuance
```
**Note:** Enabling `jwt_enabled` means endpoints decorated with the token dependency will require authentication.

#### 4.3.2. Example `config.yml` snippet: Enabling HTTPS redirect.
This is useful if your server is behind a reverse proxy that handles TLS termination.
```yaml
# In your config.yml
security:
  enabled: true
  https_redirect: true # Adds middleware to redirect HTTP to HTTPS
```

#### 4.3.3. Example `config.yml` snippet: Setting custom trusted hosts.
Restricts which `Host` headers are accepted. Use `["*"]` to allow all (less secure).
```yaml
# In your config.yml
security:
  enabled: true
  trusted_hosts: ["api.example.com", "localhost", "127.0.0.1"]
```

#### 4.3.4. Example `config.yml` snippet: Configuring custom HTTP security headers (CSP, X-Frame-Options).
```yaml
# In your config.yml
security:
  enabled: true
  headers:
    x_content_type_options: "nosniff"
    x_frame_options: "DENY"
    content_security_policy: "default-src 'self'; script-src 'self' 'unsafe-inline'; object-src 'none';"
    strict_transport_security: "max-age=31536000; includeSubDomains"
```

---
### 4.4. LLM Provider Configuration

#### 4.4.1. Example `config.yml` snippet: Setting the default LLM provider and API key env variable.
```yaml
# In your config.yml
llm:
  provider: "openai/gpt-4o-mini" # Default provider/model
  api_key_env: "OPENAI_API_KEY"  # Environment variable to read the API key from
```
The server will then expect the `OPENAI_API_KEY` environment variable to be set.

#### 4.4.2. Example `config.yml` snippet: Overriding the API key directly in the config (for testing/specific cases).
**Warning:** Not recommended for production due to security risks of hardcoding keys.
```yaml
# In your config.yml
llm:
  provider: "openai/gpt-3.5-turbo"
  api_key: "sk-this_is_a_test_key_do_not_use_in_prod" # Key directly in config
```

#### 4.4.3. Example `config.yml` snippet: Configuring for a different LiteLLM-supported provider (e.g., Groq).
```yaml
# In your config.yml
llm:
  provider: "groq/llama3-8b-8192"
  api_key_env: "GROQ_API_KEY" # Server will look for this env var
```

---
### 4.5. Default Crawler Settings
These settings in `config.yml` under the `crawler` key affect the default behavior if not overridden by specific `BrowserConfig` or `CrawlerRunConfig` in API requests.

#### 4.5.1. Example `config.yml` snippet: Modifying `crawler.base_config.simulate_user`.
```yaml
# In your config.yml
crawler:
  base_config:
    simulate_user: true # Enable user simulation features by default
```

#### 4.5.2. Example `config.yml` snippet: Adjusting `crawler.memory_threshold_percent`.
This is for the `MemoryAdaptiveDispatcher`.
```yaml
# In your config.yml
crawler:
  memory_threshold_percent: 85.0 # Pause new tasks if system memory usage exceeds 85%
```

#### 4.5.3. Example `config.yml` snippet: Configuring default `crawler.rate_limiter` parameters.
```yaml
# In your config.yml
crawler:
  rate_limiter:
    enabled: true
    base_delay: [0.5, 1.5] # Default delay between 0.5 and 1.5 seconds
```

#### 4.5.4. Example `config.yml` snippet: Adding default browser arguments to `crawler.browser.extra_args`.
```yaml
# In your config.yml
crawler:
  browser:
    # Default kwargs for BrowserConfig
    # headless: true
    # text_mode: false # etc.
    extra_args:
      - "--disable-gpu" # Already default, but shown for example
      - "--window-size=1920,1080"
      # Add other chromium flags as needed
```

#### 4.5.5. Example `config.yml` snippet: Changing `crawler.pool.max_pages` (global semaphore).
This controls the maximum number of concurrent browser pages globally for the server.
```yaml
# In your config.yml
crawler:
  pool:
    max_pages: 20 # Allow up to 20 concurrent browser pages
```

#### 4.5.6. Example `config.yml` snippet: Changing `crawler.pool.idle_ttl_sec` (janitor GC timeout).
This controls how long an idle browser instance in the pool will live before being closed.
```yaml
# In your config.yml
crawler:
  pool:
    idle_ttl_sec: 600 # Close idle browsers after 10 minutes (default is 30 min)
```

---
## V. Model-Controller-Presenter (MCP) Bridge Integration

### 5.1. Overview of MCP and its purpose with Crawl4ai.
The Model-Controller-Presenter (MCP) bridge allows AI tools and agents (like Claude Code, potentially others in the future) to interact with Crawl4ai's capabilities as "tools." Crawl4ai endpoints decorated with `@mcp_tool` become callable functions for these AI agents. This enables AIs to leverage web crawling and data extraction within their reasoning and task execution processes.

### 5.2. Accessing MCP Endpoints

#### 5.2.1. Example: Conceptual connection to the MCP WebSocket endpoint (`/mcp/ws`).
Connecting to `/mcp/ws` would typically be done by an MCP-compatible client library.
```python
# This is a conceptual Python example using a hypothetical MCP client library
# For actual MCP client usage, refer to the specific MCP tool's documentation.
# from mcp_client_library import MCPClient # Hypothetical library

# async def connect_mcp_ws():
#     mcp_url = f"{BASE_URL.replace('http', 'ws')}/mcp/ws"
#     async with MCPClient(mcp_url) as client:
#         print(f"Connected to MCP WebSocket at {mcp_url}")
#         # ... send/receive MCP messages ...
#         # e.g., await client.list_tools()
#         # e.g., await client.call_tool(tool_name="crawl", arguments={"urls": ["https://example.com"]})

# if __name__ == "__main__":
#     # asyncio.run(connect_mcp_ws()) # Uncomment if you have a client library
    print("MCP WebSocket conceptual connection. Real client library needed.")
```

#### 5.2.2. Example: Conceptual connection to the MCP SSE endpoint (`/mcp/sse`).
Server-Sent Events (SSE) is another transport for MCP.
```python
# Similar to WebSocket, an MCP-compatible SSE client would be used.
# from sseclient import SSEClient # A possible library for SSE

# def connect_mcp_sse():
#     mcp_sse_url = f"{BASE_URL}/mcp/sse"
#     print(f"Attempting to connect to MCP SSE at {mcp_sse_url} (conceptual)")
    # try:
    #     messages = SSEClient(mcp_sse_url) # This is synchronous, an async version would be better
    #     for msg in messages:
    #         print(f"MCP SSE Message: {msg.data}")
    #         if "some_condition_to_stop": # e.g. after init message
    #             break
    # except Exception as e:
    #     print(f"Error with MCP SSE: {e}")
    print("MCP SSE conceptual connection. Real client library needed.")

# if __name__ == "__main__":
    # connect_mcp_sse() # Uncomment if you have a client library
```

#### 5.2.3. Example: Fetching the MCP schema from `/mcp/schema` using `requests`.
This endpoint provides information about available MCP tools and resources.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

try:
    response = requests.get(f"{BASE_URL}/mcp/schema", headers=headers)
    response.raise_for_status()
    mcp_schema = response.json()
    print("MCP Schema:")
    # print(json.dumps(mcp_schema, indent=2)) # Can be verbose

    if "tools" in mcp_schema:
        print(f"\nAvailable MCP Tools ({len(mcp_schema['tools'])}):")
        for tool in mcp_schema["tools"][:3]: # Show first 3 tools
            print(f"  - Name: {tool.get('name')}, Description: {tool.get('description', '')[:50]}...")
    
    if "resources" in mcp_schema:
        print(f"\nAvailable MCP Resources ({len(mcp_schema['resources'])}):")
        for resource in mcp_schema["resources"][:3]: # Show first 3 resources
            print(f"  - Name: {resource.get('name')}, Description: {resource.get('description', '')[:50]}...")

except requests.exceptions.RequestException as e:
    print(f"Error fetching MCP schema: {e}")
```

### 5.3. Understanding MCP Tool Exposure

#### 5.3.1. Explanation: How endpoints decorated with `@mcp_tool` become available through the MCP bridge.
In `server.py`, FastAPI endpoints decorated with `@mcp_tool("tool_name")` are automatically registered with the MCP bridge. The MCP bridge then exposes these tools (like `/crawl`, `/md`, `/screenshot`, etc.) to connected MCP clients (e.g., AI agents). The arguments of the FastAPI endpoint function become the expected arguments for the MCP tool call.

#### 5.3.2. Example: Invoking a Crawl4ai tool (e.g., `/md`) through a simulated MCP client request structure (if simple enough to demonstrate with `requests`).
This is a conceptual illustration. A real MCP client would handle the JSON-RPC formatting for calls via WebSocket or SSE. The `/mcp/messages` endpoint is used by the SSE client to POST messages.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
# This requires a client_id which is usually established during SSE handshake
# For a simple test, if the server allows it, you might be able to send.
# However, this is highly dependent on the MCP server's transport implementation.

# This is a simplified, conceptual example of what an MCP call might look like
# if sent via a direct POST (which is how SSE clients send requests).
# A proper MCP client would handle session IDs and JSON-RPC framing.
mcp_tool_call_payload = {
    "jsonrpc": "2.0",
    "method": "call_tool",
    "params": {
        "name": "md", # The tool name, matches @mcp_tool("md")
        "arguments": { # These map to the FastAPI endpoint's Pydantic model or parameters
            "body": { # Matches the 'body: MarkdownRequest' in the get_markdown endpoint
                "url": "https://example.com",
                "f": "RAW"
            }
        }
    },
    "id": "some_unique_request_id"
}

# The SSE transport uses a client-specific POST endpoint, e.g., /mcp/messages/<client_id>
# This example cannot fully replicate that without a client_id.
# We'll try to hit a hypothetical endpoint or illustrate the payload.
print("Conceptual MCP tool call payload (actual call needs proper client/transport):")
print(json.dumps(mcp_tool_call_payload, indent=2))

# If you had a direct POST endpoint for tools (not standard MCP for SSE/WS):
# try:
#     # This is NOT how MCP typically works for SSE/WS, but for a hypothetical direct tool POST:
#     # response = requests.post(f"{BASE_URL}/mcp/call_tool_directly", json=mcp_tool_call_payload, headers=get_headers())
#     # response.raise_for_status()
#     # tool_result = response.json()
#     # print("\nResult from conceptual direct tool call:")
#     # print(json.dumps(tool_result, indent=2))
#     pass
# except requests.exceptions.RequestException as e:
#     print(f"Error in conceptual direct tool call: {e}")
```

---
## VI. Advanced Scenarios & Client-Side Best Practices

### 6.1. Chaining API Calls for Complex Workflows

#### 6.1.1. Example: Fetch preprocessed HTML using `/html`, then use this HTML as input to a local `crawl4ai` instance or another tool (conceptual).
```python
import requests
import os
import json
import asyncio
# Assuming crawl4ai is also installed as a library for local processing
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DefaultMarkdownGenerator

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

async def chained_workflow():
    target_url = "https://example.com/article"
    
    # Step 1: Fetch preprocessed HTML from the API
    print(f"Step 1: Fetching preprocessed HTML for {target_url} via API...")
    html_payload = {"url": target_url}
    preprocessed_html = None
    try:
        response = requests.post(f"{BASE_URL}/html", json=html_payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        preprocessed_html = data.get("html")
        if preprocessed_html:
            print(f"Successfully fetched preprocessed HTML (length: {len(preprocessed_html)}).")
        else:
            print("Failed to get preprocessed HTML from API.")
            return
    except requests.exceptions.RequestException as e:
        print(f"Error fetching preprocessed HTML: {e}")
        return

    # Step 2: Use this HTML with a local Crawl4AI instance for further processing
    # (e.g., applying a very specific local Markdown generator or extraction)
    if preprocessed_html:
        print("\nStep 2: Processing fetched HTML with a local Crawl4AI instance...")
        # Example: Generate Markdown using a specific local configuration
        custom_md_generator = DefaultMarkdownGenerator(
            # content_source="raw_html" because we are feeding it raw HTML
            content_source="raw_html", 
            options={"body_width": 0} # No line wrapping
        )
        local_run_config = CrawlerRunConfig(markdown_generator=custom_md_generator)
        
        async with AsyncWebCrawler() as local_crawler:
            # Use "raw:" prefix to tell the local crawler this is direct HTML content
            result = await local_crawler.arun(url=f"raw:{preprocessed_html}", config=local_run_config)
            if result.success and result.markdown:
                print("Markdown generated locally from API-fetched HTML (first 300 chars):")
                print(result.markdown.raw_markdown[:300] + "...")
            else:
                print(f"Local processing failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(chained_workflow())
```

---
### 6.2. API Error Handling

#### 6.2.1. Example: Python script showing robust error handling for common HTTP status codes (400, 401, 403, 404, 422, 500) when calling Crawl4ai API.
```python
import requests
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
# Use a token known to be invalid or expired if testing 401/403 with auth enabled
# invalid_headers = {"Authorization": "Bearer invalidtoken123"}
# For this example, we'll use the standard get_headers()
headers = get_headers()


def make_api_call(endpoint, method="GET", payload=None):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=payload, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=payload, headers=headers, timeout=10)
        else:
            print(f"Unsupported method: {method}")
            return

        print(f"\n--- Testing {method} {url} with payload {payload} ---")
        print(f"Status Code: {response.status_code}")
        
        if response.ok: # status_code < 400
            print("Response JSON:")
            try:
                print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:500] + "...")
            except json.JSONDecodeError:
                print("Response is not valid JSON.")
                print(f"Response Text (snippet): {response.text[:200]}...")
        else:
            print(f"Error Response Text: {response.text}")
            # Specific error handling based on status code
            if response.status_code == 400:
                print("Handling Bad Request (400)... Possible malformed payload.")
            elif response.status_code == 401:
                print("Handling Unauthorized (401)... API token might be missing or invalid.")
            elif response.status_code == 403:
                print("Handling Forbidden (403)... API token might lack permissions or IP restricted.")
            elif response.status_code == 404:
                print("Handling Not Found (404)... Endpoint or resource does not exist.")
            elif response.status_code == 422:
                print("Handling Unprocessable Entity (422)... Validation error with request data.")
                print(f"Details: {response.json().get('detail')}")
            elif response.status_code >= 500:
                print("Handling Server Error (5xx)... Problem on the server side.")
            
    except requests.exceptions.Timeout:
        print(f"Request to {url} timed out.")
    except requests.exceptions.ConnectionError:
        print(f"Could not connect to {url}. Is the server running?")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred for {url}: {e}")

if __name__ == "__main__":
    # Test a valid endpoint
    make_api_call("/health")
    
    # Test a non-existent endpoint (expected 404)
    make_api_call("/nonexistent_endpoint")

    # Test /md with missing URL (expected 422)
    make_api_call("/md", method="POST", payload={"f": "RAW"}) 

    # Test /token with invalid payload (expected 422 if email is missing)
    make_api_call("/token", method="POST", payload={"not_email": "test"})

    # If JWT is enabled, an unauthenticated call to a protected endpoint would give 401/403.
    # For this example, assume /admin is a hypothetical protected endpoint.
    # print("\nAttempting access to hypothetical protected /admin endpoint...")
    # make_api_call("/admin", headers={}) # No auth header
```

---
### 6.3. Client-Side Script for Long-Running Jobs

#### 6.3.1. Example: A Python client that submits a job to `/crawl`, polls `/task/{task_id}` with backoff, and retrieves results.
This is a more robust version of the polling mechanism shown earlier.
```python
import requests
import time
import os
import json

BASE_URL = os.environ.get("CRAWL4AI_BASE_URL", "http://localhost:11235")
headers = get_headers()

def submit_job_and_wait_with_backoff(payload, max_poll_time=300, initial_poll_interval=2, max_poll_interval=30, backoff_factor=1.5):
    try:
        # 1. Submit Job
        submit_response = requests.post(f"{BASE_URL}/crawl", json=payload, headers=headers)
        submit_response.raise_for_status()
        task_id = submit_response.json().get("task_id")
        if not task_id:
            print("Failed to get task_id from submission.")
            return None
        print(f"Job submitted. Task ID: {task_id}. Polling with backoff...")

        # 2. Poll with Exponential Backoff
        poll_interval = initial_poll_interval
        start_time = time.time()
        
        while time.time() - start_time < max_poll_time:
            status_response = requests.get(f"{BASE_URL}/task/{task_id}", headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            current_status = status_data.get("status")
            
            print(f"  Task {task_id} status: {current_status} (next poll in {poll_interval:.1f}s)")

            if current_status == "COMPLETED":
                print(f"Task {task_id} COMPLETED.")
                return status_data.get("result")
            elif current_status == "FAILED":
                print(f"Task {task_id} FAILED. Error: {status_data.get('error')}")
                return None
            
            time.sleep(poll_interval)
            poll_interval = min(poll_interval * backoff_factor, max_poll_interval)
            
        print(f"Task {task_id} polling timed out after {max_poll_time} seconds.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Example of a potentially longer job (crawling a site known for being slow or large)
    long_job_payload = {
        "urls": ["https://archive.org/web/"], # A site that might take a bit longer
        "crawler_config": {"word_count_threshold": 500} # Higher threshold
    }
    
    print("\n--- Testing Long-Running Job Client ---")
    job_result = submit_job_and_wait_with_backoff(long_job_payload, max_poll_time=120) # 2 min timeout

    if job_result and "results" in job_result:
        for i, res_item in enumerate(job_result["results"]):
            print(f"\nResult for {res_item.get('url')}:")
            print(f"  Success: {res_item.get('success')}")
            if res_item.get('success'):
                 md_length = len(res_item.get('markdown', {}).get('raw_markdown', ''))
                 print(f"  Markdown Length: {md_length}")
    elif job_result:
         print(f"\nReceived result data (unexpected structure):")
         print(json.dumps(job_result, indent=2, ensure_ascii=False))
    else:
        print("\nJob did not complete successfully or timed out.")
```

---
### 6.4. Batching Requests to `/crawl/stream` vs. `/crawl`

#### 6.4.1. Discussion: When to use streaming for many URLs vs. submitting a single job with multiple URLs.

*   **`/crawl` (Job-based, polling):**
    *   **Pros:**
        *   Better for very large numbers of URLs where you don't need immediate feedback for each.
        *   Robust to client disconnections (job continues on server).
        *   Redis queue handles load and persistence of jobs.
        *   Server manages concurrency and resources more globally.
    *   **Cons:**
        *   Requires a polling mechanism on the client side.
        *   Results are only available once the entire batch (or individual URL within a multi-URL job if server processes them somewhat independently before final aggregation) is complete.
    *   **Use when:** You have hundreds or thousands of URLs, can tolerate some delay for results, and need a fire-and-forget submission style.

*   **`/crawl/stream` (Streaming):**
    *   **Pros:**
        *   Real-time feedback: results for each URL are streamed back as soon as they are processed.
        *   Simpler client logic if immediate processing of individual results is needed.
        *   Good for interactive applications or dashboards.
    *   **Cons:**
        *   Client must maintain an open connection. If it drops, the stream is lost.
        *   Can be less efficient for very large numbers of URLs if each URL is processed sequentially within the stream handler on the server (though `handle_stream_crawl_request` does process them concurrently up to server limits).
        *   The client needs to handle NDJSON parsing.
    *   **Use when:** You need results for URLs as they come in, are processing a moderate number of URLs, or building an interactive tool.

**General Guideline:**
*   For a few to a few dozen URLs where you want results quickly and can process them one-by-one: `/crawl/stream`.
*   For hundreds or thousands of URLs, or when you prefer to submit a batch and check back later: `/crawl` with polling.
*   If using `/crawl/stream` for many URLs, ensure your client-side processing of each streamed result is fast to avoid becoming a bottleneck. The server-side uses an `AsyncGenerator` which processes URLs concurrently up to its internal limits, so the client should be ready to consume these results efficiently.

```