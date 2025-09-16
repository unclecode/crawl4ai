# Crawl4AI Docker Guide 🐳

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Option 1: Using Pre-built Docker Hub Images (Recommended)](#option-1-using-pre-built-docker-hub-images-recommended)
  - [Option 2: Using Docker Compose](#option-2-using-docker-compose)
  - [Option 3: Manual Local Build & Run](#option-3-manual-local-build--run)
- [Dockerfile Parameters](#dockerfile-parameters)
- [Using the API](#using-the-api)
  - [Playground Interface](#playground-interface)
  - [Python SDK](#python-sdk)
  - [Understanding Request Schema](#understanding-request-schema)
  - [REST API Examples](#rest-api-examples)
- [Additional API Endpoints](#additional-api-endpoints)
  - [HTML Extraction Endpoint](#html-extraction-endpoint)
  - [Screenshot Endpoint](#screenshot-endpoint)
  - [PDF Export Endpoint](#pdf-export-endpoint)
  - [JavaScript Execution Endpoint](#javascript-execution-endpoint)
  - [Library Context Endpoint](#library-context-endpoint)
- [MCP (Model Context Protocol) Support](#mcp-model-context-protocol-support)
  - [What is MCP?](#what-is-mcp)
  - [Connecting via MCP](#connecting-via-mcp)
  - [Using with Claude Code](#using-with-claude-code)
  - [Available MCP Tools](#available-mcp-tools)
  - [Testing MCP Connections](#testing-mcp-connections)
  - [MCP Schemas](#mcp-schemas)
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
- [Summary](#summary)

## Prerequisites

Before we dive in, make sure you have:
- Docker installed and running (version 20.10.0 or higher), including `docker compose` (usually bundled with Docker Desktop).
- `git` for cloning the repository.
- At least 4GB of RAM available for the container (more recommended for heavy use).
- Python 3.10+ (if using the Python SDK).
- Node.js 16+ (if using the Node.js examples).

> 💡 **Pro tip**: Run `docker info` to check your Docker installation and available resources.

## Installation

We offer several ways to get the Crawl4AI server running. The quickest way is to use our pre-built Docker Hub images.

### Option 1: Using Pre-built Docker Hub Images (Recommended)

Pull and run images directly from Docker Hub without building locally.

#### 1. Pull the Image

Our latest release candidate is `0.7.0-r1`. Images are built with multi-arch manifests, so Docker automatically pulls the correct version for your system.

> ⚠️ **Important Note**: The `latest` tag currently points to the stable `0.6.0` version. After testing and validation, `0.7.0` (without -r1) will be released and `latest` will be updated. For now, please use `0.7.0-r1` to test the new features.

```bash
# Pull the release candidate (for testing new features)
docker pull unclecode/crawl4ai:0.7.0-r1

# Or pull the current stable version (0.6.0)
docker pull unclecode/crawl4ai:latest
```

#### 2. Setup Environment (API Keys)

If you plan to use LLMs, create a `.llm.env` file in your working directory:

```bash
# Create a .llm.env file with your API keys
cat > .llm.env << EOL
# OpenAI
OPENAI_API_KEY=sk-your-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-key

# Other providers as needed
# DEEPSEEK_API_KEY=your-deepseek-key
# GROQ_API_KEY=your-groq-key
# TOGETHER_API_KEY=your-together-key
# MISTRAL_API_KEY=your-mistral-key
# GEMINI_API_TOKEN=your-gemini-token
EOL
```
> 🔑 **Note**: Keep your API keys secure! Never commit `.llm.env` to version control.

#### 3. Run the Container

*   **Basic run:**
    ```bash
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai \
      --shm-size=1g \
      unclecode/crawl4ai:0.7.0-r1
    ```

*   **With LLM support:**
    ```bash
    # Make sure .llm.env is in the current directory
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai \
      --env-file .llm.env \
      --shm-size=1g \
      unclecode/crawl4ai:0.7.0-r1
    ```

> The server will be available at `http://localhost:11235`. Visit `/playground` to access the interactive testing interface.

#### 4. Stopping the Container

```bash
docker stop crawl4ai && docker rm crawl4ai
```

#### Docker Hub Versioning Explained

*   **Image Name:** `unclecode/crawl4ai`
*   **Tag Format:** `LIBRARY_VERSION[-SUFFIX]` (e.g., `0.7.0-r1`)
    *   `LIBRARY_VERSION`: The semantic version of the core `crawl4ai` Python library
    *   `SUFFIX`: Optional tag for release candidates (``) and revisions (`r1`)
*   **`latest` Tag:** Points to the most recent stable version
*   **Multi-Architecture Support:** All images support both `linux/amd64` and `linux/arm64` architectures through a single tag

### Option 2: Using Docker Compose

Docker Compose simplifies building and running the service, especially for local development and testing.

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
```

**Flexible LLM Provider Configuration:**

The Docker setup now supports flexible LLM provider configuration through three methods:

1. **Environment Variable** (Highest Priority): Set `LLM_PROVIDER` to override the default
   ```bash
   export LLM_PROVIDER="anthropic/claude-3-opus"
   # Or in your .llm.env file:
   # LLM_PROVIDER=anthropic/claude-3-opus
   ```

2. **API Request Parameter**: Specify provider per request
   ```json
   {
     "url": "https://example.com",
     "provider": "groq/mixtral-8x7b"
   }
   ```

3. **Config File Default**: Falls back to `config.yml` (default: `openai/gpt-4o-mini`)

The system automatically selects the appropriate API key based on the provider.

#### 3. Build and Run with Compose

The `docker-compose.yml` file in the project root provides a simplified approach that automatically handles architecture detection using buildx.

*   **Run Pre-built Image from Docker Hub:**
    ```bash
    # Pulls and runs the release candidate from Docker Hub
    # Automatically selects the correct architecture
    IMAGE=unclecode/crawl4ai:0.7.0-r1 docker compose up -d
    ```

*   **Build and Run Locally:**
    ```bash
    # Builds the image locally using Dockerfile and runs it
    # Automatically uses the correct architecture for your machine
    docker compose up --build -d
    ```

*   **Customize the Build:**
    ```bash
    # Build with all features (includes torch and transformers)
    INSTALL_TYPE=all docker compose up --build -d
    
    # Build with GPU support (for AMD64 platforms)
    ENABLE_GPU=true docker compose up --build -d
    ```

> The server will be available at `http://localhost:11235`.

#### 4. Stopping the Service

```bash
# Stop the service
docker compose down
```

### Option 3: Manual Local Build & Run

If you prefer not to use Docker Compose for direct control over the build and run process.

#### 1. Clone Repository & Setup Environment

Follow steps 1 and 2 from the Docker Compose section above (clone repo, `cd crawl4ai`, create `.llm.env` in the root).

#### 2. Build the Image (Multi-Arch)

Use `docker buildx` to build the image. Crawl4AI now uses buildx to handle multi-architecture builds automatically.

```bash
# Make sure you are in the 'crawl4ai' root directory
# Build for the current architecture and load it into Docker
docker buildx build -t crawl4ai-local:latest --load .

# Or build for multiple architectures (useful for publishing)
docker buildx build --platform linux/amd64,linux/arm64 -t crawl4ai-local:latest --load .

# Build with additional options
docker buildx build \
  --build-arg INSTALL_TYPE=all \
  --build-arg ENABLE_GPU=false \
  -t crawl4ai-local:latest --load .
```

#### 3. Run the Container

*   **Basic run (no LLM support):**
    ```bash
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai-standalone \
      --shm-size=1g \
      crawl4ai-local:latest
    ```

*   **With LLM support:**
    ```bash
    # Make sure .llm.env is in the current directory (project root)
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai-standalone \
      --env-file .llm.env \
      --shm-size=1g \
      crawl4ai-local:latest
    ```

> The server will be available at `http://localhost:11235`.

#### 4. Stopping the Manual Container

```bash
docker stop crawl4ai-standalone && docker rm crawl4ai-standalone
```

---

## MCP (Model Context Protocol) Support

Crawl4AI server includes support for the Model Context Protocol (MCP), allowing you to connect the server's capabilities directly to MCP-compatible clients like Claude Code.

### What is MCP?

MCP is an open protocol that standardizes how applications provide context to LLMs. It allows AI models to access external tools, data sources, and services through a standardized interface.

### Connecting via MCP

The Crawl4AI server exposes two MCP endpoints:

- **Server-Sent Events (SSE)**: `http://localhost:11235/mcp/sse`
- **WebSocket**: `ws://localhost:11235/mcp/ws`

### Using with Claude Code

You can add Crawl4AI as an MCP tool provider in Claude Code with a simple command:

```bash
# Add the Crawl4AI server as an MCP provider
claude mcp add --transport sse c4ai-sse http://localhost:11235/mcp/sse

# List all MCP providers to verify it was added
claude mcp list
```

Once connected, Claude Code can directly use Crawl4AI's capabilities like screenshot capture, PDF generation, and HTML processing without having to make separate API calls.

### Available MCP Tools

When connected via MCP, the following tools are available:

- `md` - Generate markdown from web content
- `html` - Extract preprocessed HTML
- `screenshot` - Capture webpage screenshots
- `pdf` - Generate PDF documents
- `execute_js` - Run JavaScript on web pages
- `crawl` - Perform multi-URL crawling
- `ask` - Query the Crawl4AI library context

### Testing MCP Connections

You can test the MCP WebSocket connection using the test file included in the repository:

```bash
# From the repository root
python tests/mcp/test_mcp_socket.py
```

### MCP Schemas

Access the MCP tool schemas at `http://localhost:11235/mcp/schema` for detailed information on each tool's parameters and capabilities.

---

## Additional API Endpoints

In addition to the core `/crawl` and `/crawl/stream` endpoints, the server provides several specialized endpoints:

### HTML Extraction Endpoint

```
POST /html
```

Crawls the URL and returns preprocessed HTML optimized for schema extraction.

```json
{
  "url": "https://example.com"
}
```

### Screenshot Endpoint

```
POST /screenshot
```

Captures a full-page PNG screenshot of the specified URL.

```json
{
  "url": "https://example.com",
  "screenshot_wait_for": 2,
  "output_path": "/path/to/save/screenshot.png"
}
```

- `screenshot_wait_for`: Optional delay in seconds before capture (default: 2)
- `output_path`: Optional path to save the screenshot (recommended)

### PDF Export Endpoint

```
POST /pdf
```

Generates a PDF document of the specified URL.

```json
{
  "url": "https://example.com",
  "output_path": "/path/to/save/document.pdf"
}
```

- `output_path`: Optional path to save the PDF (recommended)

### JavaScript Execution Endpoint

```
POST /execute_js
```

Executes JavaScript snippets on the specified URL and returns the full crawl result.

```json
{
  "url": "https://example.com",
  "scripts": [
    "return document.title",
    "return Array.from(document.querySelectorAll('a')).map(a => a.href)"
  ]
}
```

- `scripts`: List of JavaScript snippets to execute sequentially

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

### Playground Interface

A built-in web playground is available at `http://localhost:11235/playground` for testing and generating API requests. The playground allows you to:

1. Configure `CrawlerRunConfig` and `BrowserConfig` using the main library's Python syntax
2. Test crawling operations directly from the interface
3. Generate corresponding JSON for REST API requests based on your configuration

This is the easiest way to translate Python configuration to JSON requests when building integrations.

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
  provider: "openai/gpt-4o-mini"  # Can be overridden by LLM_PROVIDER env var
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
- Using the interactive playground for testing
- Making API requests with proper typing
- Using the Python SDK
- Leveraging specialized endpoints for screenshots, PDFs, and JavaScript execution
- Connecting via the Model Context Protocol (MCP)
- Monitoring your deployment

The new playground interface at `http://localhost:11235/playground` makes it much easier to test configurations and generate the corresponding JSON for API requests.

For AI application developers, the MCP integration allows tools like Claude Code to directly access Crawl4AI's capabilities without complex API handling.

Remember, the examples in the `examples` folder are your friends - they show real-world usage patterns that you can adapt for your needs.

Keep exploring, and don't hesitate to reach out if you need help! We're building something amazing together. 🚀

Happy crawling! 🕷️
