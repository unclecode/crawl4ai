# Crawl4AI Docker Guide 🐳

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Local Build](#local-build)
  - [Docker Hub](#docker-hub)
- [Dockerfile Parameters](#dockerfile-parameters)
- [Using the API](#using-the-api)
  - [Understanding Request Schema](#understanding-request-schema)
  - [REST API Examples](#rest-api-examples)
  - [Python SDK](#python-sdk)
- [Metrics & Monitoring](#metrics--monitoring)
- [Deployment Scenarios](#deployment-scenarios)
- [Complete Examples](#complete-examples)
- [Getting Help](#getting-help)

## Prerequisites

Before we dive in, make sure you have:
- Docker installed and running (version 20.10.0 or higher)
- At least 4GB of RAM available for the container
- Python 3.10+ (if using the Python SDK)
- Node.js 16+ (if using the Node.js examples)

> 💡 **Pro tip**: Run `docker info` to check your Docker installation and available resources.

## Installation

### Local Build

Let's get your local environment set up step by step!

#### 1. Building the Image

First, clone the repository and build the Docker image:

```bash
# Clone the repository
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai

# Build the Docker image
docker build -t crawl4ai-server:prod \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg INSTALL_TYPE=all \
  --build-arg ENABLE_GPU=false \
  deploy/docker/
```

#### 2. Environment Setup

If you plan to use LLMs (Language Models), you'll need to set up your API keys. Create a `.llm.env` file:

```env
# OpenAI
OPENAI_API_KEY=sk-your-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-key

# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-key

# Check out https://docs.litellm.ai/docs/providers for more providers!
```

> 🔑 **Note**: Keep your API keys secure! Never commit them to version control.

#### 3. Running the Container

You have several options for running the container:

Basic run (no LLM support):
```bash
docker run -d -p 8000:8000 --name crawl4ai crawl4ai-server:prod
```

With LLM support:
```bash
docker run -d -p 8000:8000 \
  --env-file .llm.env \
  --name crawl4ai \
  crawl4ai-server:prod
```

Using host environment variables (Not a good practice, but works for local testing):
```bash
docker run -d -p 8000:8000 \
  --env-file .llm.env \
  --env-from "$(env)" \
  --name crawl4ai \
  crawl4ai-server:prod
```

### More on Building

You have several options for building the Docker image based on your needs:

#### Basic Build
```bash
# Clone the repository
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai

# Simple build with defaults
docker build -t crawl4ai-server:prod deploy/docker/
```

#### Advanced Build Options
```bash
# Build with custom parameters
docker build -t crawl4ai-server:prod \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg INSTALL_TYPE=all \
  --build-arg ENABLE_GPU=false \
  deploy/docker/
```

#### Platform-Specific Builds
The Dockerfile includes optimizations for different architectures (ARM64 and AMD64). Docker automatically detects your platform, but you can specify it explicitly:

```bash
# Build for ARM64
docker build --platform linux/arm64 -t crawl4ai-server:arm64 deploy/docker/

# Build for AMD64
docker build --platform linux/amd64 -t crawl4ai-server:amd64 deploy/docker/
```

#### Multi-Platform Build
For distributing your image across different architectures, use `buildx`:

```bash
# Set up buildx builder
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/crawl4ai-server:multi \
  --push \
  deploy/docker/
```

> 💡 **Note**: Multi-platform builds require Docker Buildx and need to be pushed to a registry.

#### Development Build
For development, you might want to enable all features:

```bash
docker build -t crawl4ai-server:dev \
  --build-arg INSTALL_TYPE=all \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg ENABLE_GPU=true \
  deploy/docker/
```

#### GPU-Enabled Build
If you plan to use GPU acceleration:

```bash
docker build -t crawl4ai-server:gpu \
  --build-arg ENABLE_GPU=true \
  deploy/docker/
```

### Build Arguments Explained

| Argument | Description | Default | Options |
|----------|-------------|---------|----------|
| PYTHON_VERSION | Python version | 3.10 | 3.8, 3.9, 3.10 |
| INSTALL_TYPE | Feature set | default | default, all, torch, transformer |
| ENABLE_GPU | GPU support | false | true, false |
| APP_HOME | Install path | /app | any valid path |

### Build Best Practices

1. **Choose the Right Install Type**
   - `default`: Basic installation, smallest image, to be honest, I use this most of the time.
   - `all`: Full features, larger image (include transformer, and nltk, make sure you really need them)

2. **Platform Considerations**
   - Let Docker auto-detect platform unless you need cross-compilation
   - Use --platform for specific architecture requirements
   - Consider buildx for multi-architecture distribution

3. **Development vs Production**
   - Use `INSTALL_TYPE=all` for development
   - Stick to `default` for production if you don't need extra features
   - Enable GPU only if you have compatible hardware

4. **Performance Optimization**
   - The image automatically includes platform-specific optimizations
   - AMD64 gets OpenMP optimizations
   - ARM64 gets OpenBLAS optimizations

### Docker Hub

> 🚧 Coming soon! The image will be available at `crawl4ai/server`. Stay tuned!

## Dockerfile Parameters

Configure your build with these parameters:

| Parameter | Description | Default | Options |
|-----------|-------------|---------|----------|
| PYTHON_VERSION | Python version to use | 3.10 | 3.8, 3.9, 3.10 |
| INSTALL_TYPE | Installation profile | default | default, all, torch, transformer |
| ENABLE_GPU | Enable GPU support | false | true, false |
| APP_HOME | Application directory | /app | any valid path |
| TARGETARCH | Target architecture | auto-detected | amd64, arm64 |

## Using the API

### Understanding Request Schema

This is super important! The API expects a specific structure that matches our Python classes. Let me show you how it works.

#### The Magic of Type Matching

When you send a request, each configuration object needs a "type" field that matches the exact class name from the library. Here's an example:

```python
# First, let's create objects the normal way
from crawl4ai import BrowserConfig, CrawlerRunConfig, PruningContentFilter

# Create some config objects
browser_config = BrowserConfig(headless=True, viewport={"width": 1200, "height": 800})
content_filter = PruningContentFilter(threshold=0.48, threshold_type="fixed")

# Use dump() to see the serialized format
print(browser_config.dump())
```

This will output something like:
```json
{
    "type": "BrowserConfig",
    "params": {
        "headless": true,
        "viewport": {
            "width": 1200,
            "height": 800
        }
    }
}
```

#### Making API Requests

So when making a request, your JSON should look like this:

```json
{
    "urls": ["https://example.com"],
    "browser_config": {
        "type": "BrowserConfig",
        "params": {
            "headless": true,
            "viewport": {"width": 1200, "height": 800}
        }
    },
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "cache_mode": "bypass",
            "markdown_generator": {
                "type": "DefaultMarkdownGenerator",
                "params": {
                    "content_filter": {
                        "type": "PruningContentFilter",
                        "params": {
                            "threshold": 0.48,
                            "threshold_type": "fixed",
                            "min_word_threshold": 0
                        }
                    }
                }
            }
        }
    }
}
```

> 💡 **Pro tip**: Look at the class names in the library documentation - they map directly to the "type" fields in your requests!

### REST API Examples

Let's look at some practical examples:

#### Simple Crawl

```python
import requests

response = requests.post(
    "http://localhost:8000/crawl",
    json={
        "urls": ["https://example.com"],
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True}
        }
    }
)
print(response.json())
```

#### Streaming Results

```python
import requests

response = requests.post(
    "http://localhost:8000/crawl",
    json={
        "urls": ["https://example.com"],
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"stream": True}
        }
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode())
```

### Python SDK

The SDK makes things even easier! Here's how to use it:

```python
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import BrowserConfig, CrawlerRunConfig

async with Crawl4aiDockerClient() as client:
    # The SDK handles serialization for you!
    result = await client.crawl(
        urls=["https://example.com"],
        browser_config=BrowserConfig(headless=True),
        crawler_config=CrawlerRunConfig(stream=False)
    )
    print(result.markdown)
```

## Metrics & Monitoring

Keep an eye on your crawler with these endpoints:

- `/health` - Quick health check
- `/metrics` - Detailed Prometheus metrics
- `/schema` - Full API schema

Example health check:
```bash
curl http://localhost:8000/health
```

## Deployment Scenarios

> 🚧 Coming soon! We'll cover:
> - Kubernetes deployment
> - Cloud provider setups (AWS, GCP, Azure)
> - High-availability configurations
> - Load balancing strategies

## Complete Examples

Check out the `examples` folder in our repository for full working examples! Here's one to get you started:

```python
import requests
import time
import httpx
import asyncio
from typing import Dict, Any
from crawl4ai import (
    BrowserConfig, CrawlerRunConfig, DefaultMarkdownGenerator,
    PruningContentFilter, JsonCssExtractionStrategy, LLMContentFilter, CacheMode
)
from crawl4ai.docker_client import Crawl4aiDockerClient

class Crawl4AiTester:
    def __init__(self, base_url: str = "http://localhost:11235"):
        self.base_url = base_url

    def submit_and_wait(
        self, request_data: Dict[str, Any], timeout: int = 300
    ) -> Dict[str, Any]:
        # Submit crawl job
        response = requests.post(f"{self.base_url}/crawl", json=request_data)
        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")

        # Poll for result
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {timeout} seconds"
                )

            result = requests.get(f"{self.base_url}/task/{task_id}")
            status = result.json()

            if status["status"] == "failed":
                print("Task failed:", status.get("error"))
                raise Exception(f"Task failed: {status.get('error')}")

            if status["status"] == "completed":
                return status

            time.sleep(2)

async def test_direct_api():
    """Test direct API endpoints without using the client SDK"""
    print("\n=== Testing Direct API Calls ===")
    
    # Test 1: Basic crawl with content filtering
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1200,
        viewport_height=800
    )
    
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=0
            ),
            options={"ignore_links": True}
        )
    )

    request_data = {
        "urls": ["https://example.com"],
        "browser_config": browser_config.dump(),
        "crawler_config": crawler_config.dump()
    }

    # Make direct API call
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/crawl",
            json=request_data,
            timeout=300
        )
        assert response.status_code == 200
        result = response.json()
        print("Basic crawl result:", result["success"])

    # Test 2: Structured extraction with JSON CSS
    schema = {
        "baseSelector": "article.post",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".content", "type": "html"}
        ]
    }

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema=schema)
    )

    request_data["crawler_config"] = crawler_config.dump()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/crawl",
            json=request_data
        )
        assert response.status_code == 200
        result = response.json()
        print("Structured extraction result:", result["success"])

    # Test 3: Get schema
    # async with httpx.AsyncClient() as client:
    #     response = await client.get("http://localhost:8000/schema")
    #     assert response.status_code == 200
    #     schemas = response.json()
    #     print("Retrieved schemas for:", list(schemas.keys()))

async def test_with_client():
    """Test using the Crawl4AI Docker client SDK"""
    print("\n=== Testing Client SDK ===")
    
    async with Crawl4aiDockerClient(verbose=True) as client:
        # Test 1: Basic crawl
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48,
                    threshold_type="fixed"
                )
            )
        )

        result = await client.crawl(
            urls=["https://example.com"],
            browser_config=browser_config,
            crawler_config=crawler_config
        )
        print("Client SDK basic crawl:", result.success)

        # Test 2: LLM extraction with streaming
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=LLMContentFilter(
                    provider="openai/gpt-40",
                    instruction="Extract key technical concepts"
                )
            ),
            stream=True
        )

        async for result in await client.crawl(
            urls=["https://example.com"],
            browser_config=browser_config,
            crawler_config=crawler_config
        ):
            print(f"Streaming result for: {result.url}")

        # # Test 3: Get schema
        # schemas = await client.get_schema()
        # print("Retrieved client schemas for:", list(schemas.keys()))

async def main():
    """Run all tests"""
    # Test direct API
    print("Testing direct API calls...")
    await test_direct_api()

    # Test client SDK
    print("\nTesting client SDK...")
    await test_with_client()

if __name__ == "__main__":
    asyncio.run(main())
```

## Server Configuration

The server's behavior can be customized through the `config.yml` file. Let's explore how to configure your Crawl4AI server for optimal performance and security.

### Understanding config.yml

The configuration file is located at `deploy/docker/config.yml`. You can either modify this file before building the image or mount a custom configuration when running the container.

Here's a detailed breakdown of the configuration options:

```yaml
# Application Configuration
app:
  title: "Crawl4AI API"           # Server title in OpenAPI docs
  version: "1.0.0"               # API version
  host: "0.0.0.0"               # Listen on all interfaces
  port: 8000                    # Server port
  reload: True                  # Enable hot reloading (development only)
  timeout_keep_alive: 300       # Keep-alive timeout in seconds

# Rate Limiting Configuration
rate_limiting:
  enabled: True                 # Enable/disable rate limiting
  default_limit: "100/minute"   # Rate limit format: "number/timeunit"
  trusted_proxies: []          # List of trusted proxy IPs
  storage_uri: "memory://"     # Use "redis://localhost:6379" for production

# Security Configuration
security:
  enabled: false               # Master toggle for security features
  https_redirect: True         # Force HTTPS
  trusted_hosts: ["*"]        # Allowed hosts (use specific domains in production)
  headers:                     # Security headers
    x_content_type_options: "nosniff"
    x_frame_options: "DENY"
    content_security_policy: "default-src 'self'"
    strict_transport_security: "max-age=63072000; includeSubDomains"

# Crawler Configuration
crawler:
  memory_threshold_percent: 95.0  # Memory usage threshold
  rate_limiter:
    base_delay: [1.0, 2.0]      # Min and max delay between requests
  timeouts:
    stream_init: 30.0           # Stream initialization timeout
    batch_process: 300.0        # Batch processing timeout

# Logging Configuration
logging:
  level: "INFO"                 # Log level (DEBUG, INFO, WARNING, ERROR)
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Observability Configuration
observability:
  prometheus:
    enabled: True              # Enable Prometheus metrics
    endpoint: "/metrics"       # Metrics endpoint
  health_check:
    endpoint: "/health"        # Health check endpoint
```

### Configuration Tips and Best Practices

1. **Production Settings** 🏭
   ```yaml
   app:
     reload: False              # Disable reload in production
     timeout_keep_alive: 120    # Lower timeout for better resource management
   
   rate_limiting:
     storage_uri: "redis://redis:6379"  # Use Redis for distributed rate limiting
     default_limit: "50/minute"         # More conservative rate limit
   
   security:
     enabled: true                      # Enable all security features
     trusted_hosts: ["your-domain.com"] # Restrict to your domain
   ```

2. **Development Settings** 🛠️
   ```yaml
   app:
     reload: True               # Enable hot reloading
     timeout_keep_alive: 300    # Longer timeout for debugging
   
   logging:
     level: "DEBUG"            # More verbose logging
   ```

3. **High-Traffic Settings** 🚦
   ```yaml
   crawler:
     memory_threshold_percent: 85.0  # More conservative memory limit
     rate_limiter:
       base_delay: [2.0, 4.0]       # More aggressive rate limiting
   ```

### Customizing Your Configuration

#### Method 1: Pre-build Configuration
```bash
# Copy and modify config before building
cp deploy/docker/config.yml custom-config.yml
vim custom-config.yml

# Build with custom config
docker build -t crawl4ai-server:prod \
  --build-arg CONFIG_PATH=custom-config.yml .
```

#### Method 2: Runtime Configuration
```bash
# Mount custom config at runtime
docker run -d -p 8000:8000 \
  -v $(pwd)/custom-config.yml:/app/config.yml \
  crawl4ai-server:prod
```

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

### Configuration Migration

When upgrading Crawl4AI, follow these steps:

1. Back up your current config:
   ```bash
   cp /app/config.yml /app/config.yml.backup
   ```

2. Use version control:
   ```bash
   git add config.yml
   git commit -m "Save current server configuration"
   ```

3. Test in staging first:
   ```bash
   docker run -d -p 8001:8000 \  # Use different port
     -v $(pwd)/new-config.yml:/app/config.yml \
     crawl4ai-server:prod
   ```

### Common Configuration Scenarios

1. **Basic Development Setup**
   ```yaml
   security:
     enabled: false
   logging:
     level: "DEBUG"
   ```

2. **Production API Server**
   ```yaml
   security:
     enabled: true
     trusted_hosts: ["api.yourdomain.com"]
   rate_limiting:
     enabled: true
     default_limit: "50/minute"
   ```

3. **High-Performance Crawler**
   ```yaml
   crawler:
     memory_threshold_percent: 90.0
     timeouts:
       batch_process: 600.0
   ```

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