# Crawl4AI Docker Guide 🐳

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Option 1: Using Docker Compose (Recommended)](#option-1-using-docker-compose-recommended)
  - [Option 2: Manual Local Build & Run](#option-2-manual-local-build--run)
  - [Option 3: Using Pre-built Docker Hub Images](#option-3-using-pre-built-docker-hub-images)
- [Dockerfile Parameters](#dockerfile-parameters)
- [Using the API](#using-the-api)
  - [Understanding Request Schema](#understanding-request-schema)
  - [REST API Examples](#rest-api-examples)
  - [Python SDK](#python-sdk)
- [Metrics & Monitoring](#metrics--monitoring)
- [Deployment Scenarios](#deployment-scenarios)
- [Complete Examples](#complete-examples)
- [Server Configuration](#server-configuration)
  - [Understanding config.yml](#understanding-configyml)
  - [JWT Authentication](#jwt-authentication)
  - [Configuration Tips and Best Practices](#configuration-tips-and-best-practices)
  - [Customizing Your Configuration](#customizing-your-configuration)
  - [Configuration Recommendations](#configuration-recommendations)
- [Getting Help](#getting-help)

## Prerequisites

Before we dive in, make sure you have:
- Docker installed and running (version 20.10.0 or higher), including `docker compose` (usually bundled with Docker Desktop).
- `git` for cloning the repository.
- At least 4GB of RAM available for the container (more recommended for heavy use).
- Python 3.10+ (if using the Python SDK).
- Node.js 16+ (if using the Node.js examples).

> 💡 **Pro tip**: Run `docker info` to check your Docker installation and available resources.

## Installation

We offer several ways to get the Crawl4AI server running. Docker Compose is the easiest way to manage local builds and runs.

### Option 1: Using Docker Compose (Recommended)

Docker Compose simplifies building and running the service, especially for local development and testing across different platforms.

#### 1. Clone Repository

```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
```

#### 2. Environment Setup (API Keys)

If you plan to use LLMs, copy the example environment file and add your API keys. This file should be in the **project root directory**.

```bash
# Make sure you are in the 'crawl4ai' root directory
cp deploy/docker/.llm.env.example .llm.env

# Now edit .llm.env and add your API keys
# Example content:
# OPENAI_API_KEY=sk-your-key
# ANTHROPIC_API_KEY=your-anthropic-key
# ...
```
> 🔑 **Note**: Keep your API keys secure! Never commit `.llm.env` to version control.

#### 3. Build and Run with Compose

The `docker-compose.yml` file in the project root defines services for different scenarios using **profiles**.

*   **Build and Run Locally (AMD64):**
    ```bash
    # Builds the image locally using Dockerfile and runs it
    docker compose --profile local-amd64 up --build -d
    ```

*   **Build and Run Locally (ARM64):**
    ```bash
    # Builds the image locally using Dockerfile and runs it
    docker compose --profile local-arm64 up --build -d
    ```

*   **Run Pre-built Image from Docker Hub (AMD64):**
    ```bash
    # Pulls and runs the specified AMD64 image from Docker Hub
    # (Set VERSION env var for specific tags, e.g., VERSION=0.5.1-d1)
    docker compose --profile hub-amd64 up -d
    ```

*   **Run Pre-built Image from Docker Hub (ARM64):**
    ```bash
    # Pulls and runs the specified ARM64 image from Docker Hub
    docker compose --profile hub-arm64 up -d
    ```

> The server will be available at `http://localhost:11235`.

#### 4. Stopping Compose Services

```bash
# Stop the service(s) associated with a profile (e.g., local-amd64)
docker compose --profile local-amd64 down
```

### Option 2: Manual Local Build & Run

If you prefer not to use Docker Compose for local builds.

#### 1. Clone Repository & Setup Environment

Follow steps 1 and 2 from the Docker Compose section above (clone repo, `cd crawl4ai`, create `.llm.env` in the root).

#### 2. Build the Image (Multi-Arch)

Use `docker buildx` to build the image. This example builds for multiple platforms and loads the image matching your host architecture into the local Docker daemon.

```bash
# Make sure you are in the 'crawl4ai' root directory
docker buildx build --platform linux/amd64,linux/arm64 -t crawl4ai-local:latest --load .
```

#### 3. Run the Container

*   **Basic run (no LLM support):**
    ```bash
    # Replace --platform if your host is ARM64
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai-standalone \
      --shm-size=1g \
      --platform linux/amd64 \
      crawl4ai-local:latest
    ```

*   **With LLM support:**
    ```bash
    # Make sure .llm.env is in the current directory (project root)
    # Replace --platform if your host is ARM64
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai-standalone \
      --env-file .llm.env \
      --shm-size=1g \
      --platform linux/amd64 \
      crawl4ai-local:latest
    ```

> The server will be available at `http://localhost:11235`.

#### 4. Stopping the Manual Container

```bash
docker stop crawl4ai-standalone && docker rm crawl4ai-standalone
```

### Option 3: Using Pre-built Docker Hub Images

Pull and run images directly from Docker Hub without building locally.

#### 1. Pull the Image

We use a versioning scheme like `LIBRARY_VERSION-dREVISION` (e.g., `0.5.1-d1`). The `latest` tag points to the most recent stable release. Images are built with multi-arch manifests, so Docker usually pulls the correct version for your system automatically.

```bash
# Pull a specific version (recommended for stability)
docker pull unclecode/crawl4ai:0.5.1-d1

# Or pull the latest stable version
docker pull unclecode/crawl4ai:latest
```

#### 2. Setup Environment (API Keys)

If using LLMs, create the `.llm.env` file in a directory of your choice, similar to Step 2 in the Compose section.

#### 3. Run the Container

*   **Basic run:**
    ```bash
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai-hub \
      --shm-size=1g \
      unclecode/crawl4ai:0.5.1-d1 # Or use :latest
    ```

*   **With LLM support:**
    ```bash
    # Make sure .llm.env is in the current directory you are running docker from
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai-hub \
      --env-file .llm.env \
      --shm-size=1g \
      unclecode/crawl4ai:0.5.1-d1 # Or use :latest
    ```

> The server will be available at `http://localhost:11235`.

#### 4. Stopping the Hub Container

```bash
docker stop crawl4ai-hub && docker rm crawl4ai-hub
```

#### Docker Hub Versioning Explained

*   **Image Name:** `unclecode/crawl4ai`
*   **Tag Format:** `LIBRARY_VERSION-dREVISION`
    *   `LIBRARY_VERSION`: The Semantic Version of the core `crawl4ai` Python library included (e.g., `0.5.1`).
    *   `dREVISION`: An incrementing number (starting at `d1`) for Docker build changes made *without* changing the library version (e.g., base image updates, dependency fixes). Resets to `d1` for each new `LIBRARY_VERSION`.
*   **Example:** `unclecode/crawl4ai:0.5.1-d1`
*   **`latest` Tag:** Points to the most recent stable `LIBRARY_VERSION-dREVISION`.
*   **Multi-Arch:** Images support `linux/amd64` and `linux/arm64`. Docker automatically selects the correct architecture.

---

*(Rest of the document remains largely the same, but with key updates below)*

---

## Dockerfile Parameters

You can customize the image build process using build arguments (`--build-arg`). These are typically used via `docker buildx build` or within the `docker-compose.yml` file.

```bash
# Example: Build with 'all' features using buildx
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg INSTALL_TYPE=all \
  -t yourname/crawl4ai-all:latest \
  --load \
  . # Build from root context
```

### Build Arguments Explained

| Argument     | Description                              | Default   | Options                            |
| :----------- | :--------------------------------------- | :-------- | :--------------------------------- |
| INSTALL_TYPE | Feature set                              | `default` | `default`, `all`, `torch`, `transformer` |
| ENABLE_GPU   | GPU support (CUDA for AMD64)           | `false`   | `true`, `false`                    |
| APP_HOME     | Install path inside container (advanced) | `/app`    | any valid path                   |
| USE_LOCAL    | Install library from local source        | `true`    | `true`, `false`                    |
| GITHUB_REPO  | Git repo to clone if USE_LOCAL=false   | *(see Dockerfile)* | any git URL                  |
| GITHUB_BRANCH| Git branch to clone if USE_LOCAL=false   | `main`    | any branch name                  |

*(Note: PYTHON_VERSION is fixed by the `FROM` instruction in the Dockerfile)*

### Build Best Practices

1.  **Choose the Right Install Type**
    *   `default`: Basic installation, smallest image size. Suitable for most standard web scraping and markdown generation.
    *   `all`: Full features including `torch` and `transformers` for advanced extraction strategies (e.g., CosineStrategy, certain LLM filters). Significantly larger image. Ensure you need these extras.
2.  **Platform Considerations**
    *   Use `buildx` for building multi-architecture images, especially for pushing to registries.
    *   Use `docker compose` profiles (`local-amd64`, `local-arm64`) for easy platform-specific local builds.
3.  **Performance Optimization**
    *   The image automatically includes platform-specific optimizations (OpenMP for AMD64, OpenBLAS for ARM64).

---

## Using the API

Communicate with the running Docker server via its REST API (defaulting to `http://localhost:11235`). You can use the Python SDK or make direct HTTP requests.

### Python SDK

Install the SDK: `pip install crawl4ai`

```python
import asyncio
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode # Assuming you have crawl4ai installed

async def main():
    # Point to the correct server port
    async with Crawl4aiDockerClient(base_url="http://localhost:11235", verbose=True) as client:
        # If JWT is enabled on the server, authenticate first:
        # await client.authenticate("user@example.com") # See Server Configuration section

        # Example Non-streaming crawl
        print("--- Running Non-Streaming Crawl ---")
        results = await client.crawl(
            ["https://httpbin.org/html"],
            browser_config=BrowserConfig(headless=True), # Use library classes for config aid
            crawler_config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        if results: # client.crawl returns None on failure
          print(f"Non-streaming results success: {results.success}")
          if results.success:
              for result in results: # Iterate through the CrawlResultContainer
                  print(f"URL: {result.url}, Success: {result.success}")
        else:
            print("Non-streaming crawl failed.")


        # Example Streaming crawl
        print("\n--- Running Streaming Crawl ---")
        stream_config = CrawlerRunConfig(stream=True, cache_mode=CacheMode.BYPASS)
        try:
            async for result in await client.crawl( # client.crawl returns an async generator for streaming
                ["https://httpbin.org/html", "https://httpbin.org/links/5/0"],
                browser_config=BrowserConfig(headless=True),
                crawler_config=stream_config
            ):
                print(f"Streamed result: URL: {result.url}, Success: {result.success}")
        except Exception as e:
            print(f"Streaming crawl failed: {e}")


        # Example Get schema
        print("\n--- Getting Schema ---")
        schema = await client.get_schema()
        print(f"Schema received: {bool(schema)}") # Print whether schema was received

if __name__ == "__main__":
    asyncio.run(main())
```

*(SDK parameters like timeout, verify_ssl etc. remain the same)*

### Second Approach: Direct API Calls

Crucially, when sending configurations directly via JSON, they **must** follow the `{"type": "ClassName", "params": {...}}` structure for any non-primitive value (like config objects or strategies). Dictionaries must be wrapped as `{"type": "dict", "value": {...}}`.

*(Keep the detailed explanation of Configuration Structure, Basic Pattern, Simple vs Complex, Strategy Pattern, Complex Nested Example, Quick Grammar Overview, Important Rules, Pro Tip)*

#### More Examples *(Ensure Schema example uses type/value wrapper)*

**Advanced Crawler Configuration**
*(Keep example, ensure cache_mode uses valid enum value like "bypass")*

**Extraction Strategy**
```json
{
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "extraction_strategy": {
                "type": "JsonCssExtractionStrategy",
                "params": {
                    "schema": {
                        "type": "dict",
                        "value": {
                           "baseSelector": "article.post",
                           "fields": [
                               {"name": "title", "selector": "h1", "type": "text"},
                               {"name": "content", "selector": ".content", "type": "html"}
                           ]
                         }
                    }
                }
            }
        }
    }
}
```

**LLM Extraction Strategy** *(Keep example, ensure schema uses type/value wrapper)*
*(Keep Deep Crawler Example)*

### REST API Examples

Update URLs to use port `11235`.

#### Simple Crawl

```python
import requests

# Configuration objects converted to the required JSON structure
browser_config_payload = {
    "type": "BrowserConfig",
    "params": {"headless": True}
}
crawler_config_payload = {
    "type": "CrawlerRunConfig",
    "params": {"stream": False, "cache_mode": "bypass"} # Use string value of enum
}

crawl_payload = {
    "urls": ["https://httpbin.org/html"],
    "browser_config": browser_config_payload,
    "crawler_config": crawler_config_payload
}
response = requests.post(
    "http://localhost:11235/crawl", # Updated port
    # headers={"Authorization": f"Bearer {token}"},  # If JWT is enabled
    json=crawl_payload
)
print(f"Status Code: {response.status_code}")
if response.ok:
    print(response.json())
else:
    print(f"Error: {response.text}")

```

#### Streaming Results

```python
import json
import httpx # Use httpx for async streaming example

async def test_stream_crawl(token: str = None): # Made token optional
    """Test the /crawl/stream endpoint with multiple URLs."""
    url = "http://localhost:11235/crawl/stream" # Updated port
    payload = {
        "urls": [
            "https://httpbin.org/html",
            "https://httpbin.org/links/5/0",
        ],
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True, "viewport": {"type": "dict", "value": {"width": 1200, "height": 800}}} # Viewport needs type:dict
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"stream": True, "cache_mode": "bypass"}
        }
    }

    headers = {}
    # if token:
    #    headers = {"Authorization": f"Bearer {token}"} # If JWT is enabled

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, headers=headers, timeout=120.0) as response:
                print(f"Status: {response.status_code} (Expected: 200)")
                response.raise_for_status() # Raise exception for bad status codes

                # Read streaming response line-by-line (NDJSON)
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            # Check for completion marker
                            if data.get("status") == "completed":
                                print("Stream completed.")
                                break
                            print(f"Streamed Result: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode JSON line: {line}")

    except httpx.HTTPStatusError as e:
         print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Error in streaming crawl test: {str(e)}")

# To run this example:
# import asyncio
# asyncio.run(test_stream_crawl())
```

---

## Metrics & Monitoring

Keep an eye on your crawler with these endpoints:

- `/health` - Quick health check
- `/metrics` - Detailed Prometheus metrics
- `/schema` - Full API schema

Example health check:
```bash
curl http://localhost:11235/health
```

---

*(Deployment Scenarios and Complete Examples sections remain the same, maybe update links if examples moved)*

---

## Server Configuration

The server's behavior can be customized through the `config.yml` file.

### Understanding config.yml

The configuration file is loaded from `/app/config.yml` inside the container. By default, the file from `deploy/docker/config.yml` in the repository is copied there during the build.

Here's a detailed breakdown of the configuration options (using defaults from `deploy/docker/config.yml`):

```yaml
# Application Configuration
app:
  title: "Crawl4AI API"
  version: "1.0.0" # Consider setting this to match library version, e.g., "0.5.1"
  host: "0.0.0.0"
  port: 8020 # NOTE: This port is used ONLY when running server.py directly. Gunicorn overrides this (see supervisord.conf).
  reload: False # Default set to False - suitable for production
  timeout_keep_alive: 300

# Default LLM Configuration
llm:
  provider: "openai/gpt-4o-mini"
  api_key_env: "OPENAI_API_KEY"
  # api_key: sk-...  # If you pass the API key directly then api_key_env will be ignored

# Redis Configuration (Used by internal Redis server managed by supervisord)
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: ""
  # ... other redis options ...

# Rate Limiting Configuration
rate_limiting:
  enabled: True
  default_limit: "1000/minute"
  trusted_proxies: []
  storage_uri: "memory://"  # Use "redis://localhost:6379" if you need persistent/shared limits

# Security Configuration
security:
  enabled: false # Master toggle for security features
  jwt_enabled: false # Enable JWT authentication (requires security.enabled=true)
  https_redirect: false # Force HTTPS (requires security.enabled=true)
  trusted_hosts: ["*"] # Allowed hosts (use specific domains in production)
  headers: # Security headers (applied if security.enabled=true)
    x_content_type_options: "nosniff"
    x_frame_options: "DENY"
    content_security_policy: "default-src 'self'"
    strict_transport_security: "max-age=63072000; includeSubDomains"

# Crawler Configuration
crawler:
  memory_threshold_percent: 95.0
  rate_limiter:
    base_delay: [1.0, 2.0] # Min/max delay between requests in seconds for dispatcher
  timeouts:
    stream_init: 30.0  # Timeout for stream initialization
    batch_process: 300.0 # Timeout for non-streaming /crawl processing

# Logging Configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Observability Configuration
observability:
  prometheus:
    enabled: True
    endpoint: "/metrics"
  health_check:
    endpoint: "/health"
```

*(JWT Authentication section remains the same, just note the default port is now 11235 for requests)*

*(Configuration Tips and Best Practices remain the same)*

### Customizing Your Configuration

You can override the default `config.yml`.

#### Method 1: Modify Before Build

1.  Edit the `deploy/docker/config.yml` file in your local repository clone.
2.  Build the image using `docker buildx` or `docker compose --profile local-... up --build`. The modified file will be copied into the image.

#### Method 2: Runtime Mount (Recommended for Custom Deploys)

1.  Create your custom configuration file, e.g., `my-custom-config.yml` locally. Ensure it contains all necessary sections.
2.  Mount it when running the container:

    *   **Using `docker run`:**
        ```bash
        # Assumes my-custom-config.yml is in the current directory
        docker run -d -p 11235:11235 \
          --name crawl4ai-custom-config \
          --env-file .llm.env \
          --shm-size=1g \
          -v $(pwd)/my-custom-config.yml:/app/config.yml \
          unclecode/crawl4ai:latest # Or your specific tag
        ```

    *   **Using `docker-compose.yml`:** Add a `volumes` section to the service definition:
        ```yaml
        services:
          crawl4ai-hub-amd64: # Or your chosen service
            image: unclecode/crawl4ai:latest
            profiles: ["hub-amd64"]
            <<: *base-config
            volumes:
              # Mount local custom config over the default one in the container
              - ./my-custom-config.yml:/app/config.yml
              # Keep the shared memory volume from base-config
              - /dev/shm:/dev/shm
        ```
        *(Note: Ensure `my-custom-config.yml` is in the same directory as `docker-compose.yml`)*

> 💡 When mounting, your custom file *completely replaces* the default one. Ensure it's a valid and complete configuration.

### Configuration Recommendations

1. **Security First** 🔒
   - Always enable security in production
   - Use specific trusted_hosts instead of wildcards
   - Set up proper rate limiting to protect your server
   - Consider your environment before enabling HTTPS redirect

2. **Resource Management** 💻
   - Adjust memory_threshold_percent based on available RAM
   - Set timeouts according to your content size and network conditions
   - Use Redis for rate limiting in multi-container setups

3. **Monitoring** 📊
   - Enable Prometheus if you need metrics
   - Set DEBUG logging in development, INFO in production
   - Regular health check monitoring is crucial

4. **Performance Tuning** ⚡
   - Start with conservative rate limiter delays
   - Increase batch_process timeout for large content
   - Adjust stream_init timeout based on initial response times

## Getting Help

We're here to help you succeed with Crawl4AI! Here's how to get support:

- 📖 Check our [full documentation](https://docs.crawl4ai.com)
- 🐛 Found a bug? [Open an issue](https://github.com/unclecode/crawl4ai/issues)
- 💬 Join our [Discord community](https://discord.gg/crawl4ai)
- ⭐ Star us on GitHub to show support!

## Summary

In this guide, we've covered everything you need to get started with Crawl4AI's Docker deployment:
- Building and running the Docker container
- Configuring the environment
- Making API requests with proper typing
- Using the Python SDK
- Monitoring your deployment

Remember, the examples in the `examples` folder are your friends - they show real-world usage patterns that you can adapt for your needs.

Keep exploring, and don't hesitate to reach out if you need help! We're building something amazing together. 🚀

Happy crawling! 🕷️
