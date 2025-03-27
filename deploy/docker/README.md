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
cd crawl4ai/deploy

# Build the Docker image
docker build --platform=linux/amd64 --no-cache -t crawl4ai .

# Or build for arm64
docker build --platform=linux/arm64 --no-cache -t crawl4ai .
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
docker run -d -p 8000:8000 --name crawl4ai crawl4ai
```

With LLM support:
```bash
docker run -d -p 8000:8000 \
  --env-file .llm.env \
  --name crawl4ai \
  crawl4ai
```

Using host environment variables (Not a good practice, but works for local testing):
```bash
docker run -d -p 8000:8000 \
  --env-file .llm.env \
  --env "$(env)" \
  --name crawl4ai \
  crawl4ai
```

#### Multi-Platform Build
For distributing your image across different architectures, use `buildx`:

```bash
# Set up buildx builder
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t crawl4ai \
  --push \
  .
```

> 💡 **Note**: Multi-platform builds require Docker Buildx and need to be pushed to a registry.

#### Development Build
For development, you might want to enable all features:

```bash
docker build -t crawl4ai
  --build-arg INSTALL_TYPE=all \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg ENABLE_GPU=true \
  .
```

#### GPU-Enabled Build
If you plan to use GPU acceleration:

```bash
docker build -t crawl4ai
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

3. **Performance Optimization**
   - The image automatically includes platform-specific optimizations
   - AMD64 gets OpenMP optimizations
   - ARM64 gets OpenBLAS optimizations

### Docker Hub

> 🚧 Coming soon! The image will be available at `crawl4ai`. Stay tuned!

## Using the API

In the following sections, we discuss two ways to communicate with the Docker server. One option is to use the client SDK that I developed for Python, and I will soon develop one for Node.js. I highly recommend this approach to avoid mistakes. Alternatively, you can take a more technical route by using the JSON structure and passing it to all the URLs, which I will explain in detail.

### Python SDK

The SDK makes things easier! Here's how to use it:

```python
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import BrowserConfig, CrawlerRunConfig

async def main():
    async with Crawl4aiDockerClient(base_url="http://localhost:8000", verbose=True) as client:
      # If JWT is enabled, you can authenticate like this: (more on this later)
        # await client.authenticate("test@example.com")
        
        # Non-streaming crawl
        results = await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig()
        )
        print(f"Non-streaming results: {results}")
        
        # Streaming crawl
        crawler_config = CrawlerRunConfig(stream=True)
        async for result in await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=crawler_config
        ):
            print(f"Streamed result: {result}")
        
        # Get schema
        schema = await client.get_schema()
        print(f"Schema: {schema}")

if __name__ == "__main__":
    asyncio.run(main())
```

`Crawl4aiDockerClient` is an async context manager that handles the connection for you. You can pass in optional parameters for more control:

- `base_url` (str): Base URL of the Crawl4AI Docker server
- `timeout` (float): Default timeout for requests in seconds
- `verify_ssl` (bool): Whether to verify SSL certificates
- `verbose` (bool): Whether to show logging output
- `log_file` (str, optional): Path to log file if file logging is desired

This client SDK generates a properly structured JSON request for the server's HTTP API.

## Second Approach: Direct API Calls

This is super important! The API expects a specific structure that matches our Python classes. Let me show you how it works.

### Understanding Configuration Structure

Let's dive deep into how configurations work in Crawl4AI. Every configuration object follows a consistent pattern of `type` and `params`. This structure enables complex, nested configurations while maintaining clarity.

#### The Basic Pattern

Try this in Python to understand the structure:
```python
from crawl4ai import BrowserConfig

# Create a config and see its structure
config = BrowserConfig(headless=True)
print(config.dump())
```

This outputs:
```json
{
    "type": "BrowserConfig",
    "params": {
        "headless": true
    }
}
```

#### Simple vs Complex Values

The structure follows these rules:
- Simple values (strings, numbers, booleans, lists) are passed directly
- Complex values (classes, dictionaries) use the type-params pattern

For example, with dictionaries:
```json
{
    "browser_config": {
        "type": "BrowserConfig",
        "params": {
            "headless": true,           // Simple boolean - direct value
            "viewport": {               // Complex dictionary - needs type-params
                "type": "dict",
                "value": {
                    "width": 1200,
                    "height": 800
                }
            }
        }
    }
}
```

#### Strategy Pattern and Nesting

Strategies (like chunking or content filtering) demonstrate why we need this structure. Consider this chunking configuration:

```json
{
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "chunking_strategy": {
                "type": "RegexChunking",      // Strategy implementation
                "params": {
                    "patterns": ["\n\n", "\\.\\s+"]
                }
            }
        }
    }
}
```

Here, `chunking_strategy` accepts any chunking implementation. The `type` field tells the system which strategy to use, and `params` configures that specific strategy.

#### Complex Nested Example

Let's look at a more complex example with content filtering:

```json
{
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "markdown_generator": {
                "type": "DefaultMarkdownGenerator",
                "params": {
                    "content_filter": {
                        "type": "PruningContentFilter",
                        "params": {
                            "threshold": 0.48,
                            "threshold_type": "fixed"
                        }
                    }
                }
            }
        }
    }
}
```

This shows how deeply configurations can nest while maintaining a consistent structure.

#### Quick Grammar Overview
```
config := {
    "type": string,
    "params": {
        key: simple_value | complex_value
    }
}

simple_value := string | number | boolean | [simple_value]
complex_value := config | dict_value

dict_value := {
    "type": "dict",
    "value": object
}
```

#### Important Rules 🚨

- Always use the type-params pattern for class instances
- Use direct values for primitives (numbers, strings, booleans)
- Wrap dictionaries with {"type": "dict", "value": {...}}
- Arrays/lists are passed directly without type-params
- All parameters are optional unless specifically required

#### Pro Tip 💡

The easiest way to get the correct structure is to:
1. Create configuration objects in Python
2. Use the `dump()` method to see their JSON representation
3. Use that JSON in your API calls

Example:
```python
from crawl4ai import CrawlerRunConfig, PruningContentFilter

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed")
    ),
    cache_mode= CacheMode.BYPASS
)
print(config.dump())  # Use this JSON in your API calls
```


#### More Examples

**Advanced Crawler Configuration**

```json
{
    "urls": ["https://example.com"],
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

**Extraction Strategy**:

```json
{
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "extraction_strategy": {
                "type": "JsonCssExtractionStrategy",
                "params": {
                    "schema": {
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
```

**LLM Extraction Strategy**

```json
{
  "crawler_config": {
    "type": "CrawlerRunConfig",
    "params": {
      "extraction_strategy": {
        "type": "LLMExtractionStrategy",
        "params": {
          "instruction": "Extract article title, author, publication date and main content",
          "provider": "openai/gpt-4",
          "api_token": "your-api-token",
          "schema": {
            "type": "dict",
            "value": {
              "title": "Article Schema",
              "type": "object",
              "properties": {
                "title": {
                  "type": "string",
                  "description": "The article's headline"
                },
                "author": {
                  "type": "string",
                  "description": "The author's name"
                },
                "published_date": {
                  "type": "string",
                  "format": "date-time",
                  "description": "Publication date and time"
                },
                "content": {
                  "type": "string",
                  "description": "The main article content"
                }
              },
              "required": ["title", "content"]
            }
          }
        }
      }
    }
  }
}
```

**Deep Crawler Example**

```json
{
  "crawler_config": {
    "type": "CrawlerRunConfig",
    "params": {
      "deep_crawl_strategy": {
        "type": "BFSDeepCrawlStrategy",
        "params": {
          "max_depth": 3,
          "filter_chain": {
            "type": "FilterChain",
            "params": {
              "filters": [
                {
                  "type": "ContentTypeFilter",
                  "params": {
                    "allowed_types": ["text/html", "application/xhtml+xml"]
                  }
                },
                {
                  "type": "DomainFilter",
                  "params": {
                    "allowed_domains": ["blog.*", "docs.*"],
                  }
                }
              ]
            }
          },
          "url_scorer": {
            "type": "CompositeScorer",
            "params": {
              "scorers": [
                {
                  "type": "KeywordRelevanceScorer",
                  "params": {
                    "keywords": ["tutorial", "guide", "documentation"],
                  }
                },
                {
                  "type": "PathDepthScorer",
                  "params": {
                    "weight": 0.5,
                    "optimal_depth": 3  
                  }
                }
              ]
            }
          }
        }
      }
    }
  }
}
```

### REST API Examples

Let's look at some practical examples:

#### Simple Crawl

```python
import requests

crawl_payload = {
    "urls": ["https://example.com"],
    "browser_config": {"headless": True},
    "crawler_config": {"stream": False}
}
response = requests.post(
    "http://localhost:8000/crawl",
    # headers={"Authorization": f"Bearer {token}"},  # If JWT is enabled, more on this later
    json=crawl_payload
)
print(response.json())  # Print the response for debugging
```

#### Streaming Results

```python
async def test_stream_crawl(session, token: str):
    """Test the /crawl/stream endpoint with multiple URLs."""
    url = "http://localhost:8000/crawl/stream"
    payload = {
        "urls": [
            "https://example.com",
            "https://example.com/page1",  
            "https://example.com/page2",  
            "https://example.com/page3",  
        ],
        "browser_config": {"headless": True, "viewport": {"width": 1200}},
        "crawler_config": {"stream": True, "cache_mode": "bypass"}
    }

    # headers = {"Authorization": f"Bearer {token}"} # If JWT is enabled, more on this later
    
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            status = response.status
            print(f"Status: {status} (Expected: 200)")
            assert status == 200, f"Expected 200, got {status}"
            
            # Read streaming response line-by-line (NDJSON)
            async for line in response.content:
                if line:
                    data = json.loads(line.decode('utf-8').strip())
                    print(f"Streamed Result: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error in streaming crawl test: {str(e)}")
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

Check out the `examples` folder in our repository for full working examples! Here are two to get you started:
[Using Client SDK](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_python_sdk.py)
[Using REST API](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_python_rest_api.py)

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
  jwt_enabled: true            # Enable JWT authentication
  https_redirect: True         # Force HTTPS
  trusted_hosts: ["*"]         # Allowed hosts (use specific domains in production)
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

### JWT Authentication

When `security.jwt_enabled` is set to `true` in your config.yml, all endpoints require JWT authentication via bearer tokens. Here's how it works:

#### Getting a Token
```python
POST /token
Content-Type: application/json

{
    "email": "user@example.com"
}
```

The endpoint returns:
```json
{
    "email": "user@example.com",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
    "token_type": "bearer"
}
```

#### Using the Token
Add the token to your requests:
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci..." http://localhost:8000/crawl
```

Using the Python SDK:
```python
from crawl4ai.docker_client import Crawl4aiDockerClient

async with Crawl4aiDockerClient() as client:
    # Authenticate first
    await client.authenticate("user@example.com")
    
    # Now all requests will include the token automatically
    result = await client.crawl(urls=["https://example.com"])
```

#### Production Considerations 💡
The default implementation uses a simple email verification. For production use, consider:
- Email verification via OTP/magic links
- OAuth2 integration
- Rate limiting token generation
- Token expiration and refresh mechanisms
- IP-based restrictions

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
cd crawl4ai/deploy
vim custom-config.yml # Or use any editor

# Build with custom config
docker build --platform=linux/amd64 --no-cache -t crawl4ai:latest .
```

#### Method 2: Build-time Configuration

Use a custom config during build:

```bash
# Build with custom config
docker build --platform=linux/amd64 --no-cache \
  --build-arg CONFIG_PATH=/path/to/custom-config.yml \ 
  -t crawl4ai:latest .
```

#### Method 3: Runtime Configuration
```bash
# Mount custom config at runtime
docker run -d -p 8000:8000 \
  -v $(pwd)/custom-config.yml:/app/config.yml \
  crawl4ai-server:prod
```

> 💡 Note: When using Method 2, `/path/to/custom-config.yml` is relative to deploy directory.
> 💡 Note: When using Method 3, ensure your custom config file has all required fields as the container will use this instead of the built-in config.

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