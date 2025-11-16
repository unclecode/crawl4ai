# Self-Hosting Crawl4AI 🚀

**Take Control of Your Web Crawling Infrastructure**

Self-hosting Crawl4AI gives you complete control over your web crawling and data extraction pipeline. Unlike cloud-based solutions, you own your data, infrastructure, and destiny.

## Why Self-Host?

- **🔒 Data Privacy**: Your crawled data never leaves your infrastructure
- **💰 Cost Control**: No per-request pricing - scale within your own resources
- **🎯 Customization**: Full control over browser configurations, extraction strategies, and performance tuning
- **📊 Transparency**: Real-time monitoring dashboard shows exactly what's happening
- **⚡ Performance**: Direct access without API rate limits or geographic restrictions
- **🛡️ Security**: Keep sensitive data extraction workflows behind your firewall
- **🔧 Flexibility**: Customize, extend, and integrate with your existing infrastructure

When you self-host, you can scale from a single container to a full browser infrastructure, all while maintaining complete control and visibility.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Option 1: Using Pre-built Docker Hub Images (Recommended)](#option-1-using-pre-built-docker-hub-images-recommended)
  - [Option 2: Using Docker Compose](#option-2-using-docker-compose)
  - [Option 3: Manual Local Build & Run](#option-3-manual-local-build--run)
- [MCP (Model Context Protocol) Support](#mcp-model-context-protocol-support)
  - [What is MCP?](#what-is-mcp)
  - [Connecting via MCP](#connecting-via-mcp)
  - [Using with Claude Code](#using-with-claude-code)
  - [Available MCP Tools](#available-mcp-tools)
  - [Testing MCP Connections](#testing-mcp-connections)
  - [MCP Schemas](#mcp-schemas)
- [Real-time Monitoring & Operations](#real-time-monitoring--operations)
  - [Monitoring Dashboard](#monitoring-dashboard)
  - [Monitor API Endpoints](#monitor-api-endpoints)
  - [WebSocket Streaming](#websocket-streaming)
  - [Control Actions](#control-actions)
  - [Production Integration](#production-integration)
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

Our latest release is `0.7.6`. Images are built with multi-arch manifests, so Docker automatically pulls the correct version for your system.

> 💡 **Note**: The `latest` tag points to the stable `0.7.6` version.

```bash
# Pull the latest version
docker pull unclecode/crawl4ai:0.7.6

# Or pull using the latest tag
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

# Optional: Global LLM settings
# LLM_PROVIDER=openai/gpt-4o-mini
# LLM_TEMPERATURE=0.7
# LLM_BASE_URL=https://api.custom.com/v1

# Optional: Provider-specific overrides
# OPENAI_TEMPERATURE=0.5
# OPENAI_BASE_URL=https://custom-openai.com/v1
# ANTHROPIC_TEMPERATURE=0.3
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
      unclecode/crawl4ai:latest
    ```

*   **With LLM support:**
    ```bash
    # Make sure .llm.env is in the current directory
    docker run -d \
      -p 11235:11235 \
      --name crawl4ai \
      --env-file .llm.env \
      --shm-size=1g \
      unclecode/crawl4ai:latest
    ```

> The server will be available at `http://localhost:11235`. Visit `/playground` to access the interactive testing interface.

#### 4. Stopping the Container

```bash
docker stop crawl4ai && docker rm crawl4ai
```

#### Docker Hub Versioning Explained

*   **Image Name:** `unclecode/crawl4ai`
*   **Tag Format:** `LIBRARY_VERSION[-SUFFIX]` (e.g., `0.7.6`)
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

The Docker setup now supports flexible LLM provider configuration through a hierarchical system:

1. **API Request Parameters** (Highest Priority): Specify per request
   ```json
   {
     "url": "https://example.com",
     "f": "llm",
     "provider": "groq/mixtral-8x7b",
     "temperature": 0.7,
     "base_url": "https://api.custom.com/v1"
   }
   ```

2. **Provider-Specific Environment Variables**: Override for specific providers
   ```bash
   # In your .llm.env file:
   OPENAI_TEMPERATURE=0.5
   OPENAI_BASE_URL=https://custom-openai.com/v1
   ANTHROPIC_TEMPERATURE=0.3
   ```

3. **Global Environment Variables**: Set defaults for all providers
   ```bash
   # In your .llm.env file:
   LLM_PROVIDER=anthropic/claude-3-opus
   LLM_TEMPERATURE=0.7
   LLM_BASE_URL=https://api.proxy.com/v1
   ```

4. **Config File Default**: Falls back to `config.yml` (default: `openai/gpt-4o-mini`)

The system automatically selects the appropriate API key based on the provider. LiteLLM handles finding the correct environment variable for each provider (e.g., OPENAI_API_KEY for OpenAI, GEMINI_API_TOKEN for Google Gemini, etc.).

**Supported LLM Parameters:**
- `provider`: LLM provider and model (e.g., "openai/gpt-4", "anthropic/claude-3-opus")
- `temperature`: Controls randomness (0.0-2.0, lower = more focused, higher = more creative)
- `base_url`: Custom API endpoint for proxy servers or alternative endpoints

#### 3. Build and Run with Compose

The `docker-compose.yml` file in the project root provides a simplified approach that automatically handles architecture detection using buildx.

*   **Run Pre-built Image from Docker Hub:**
    ```bash
    # Pulls and runs the release candidate from Docker Hub
    # Automatically selects the correct architecture
    IMAGE=unclecode/crawl4ai:latest docker compose up -d
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

## User-Provided Hooks API

The Docker API supports user-provided hook functions, allowing you to customize the crawling behavior by injecting your own Python code at specific points in the crawling pipeline. This powerful feature enables authentication, performance optimization, and custom content extraction without modifying the server code.

> ⚠️ **IMPORTANT SECURITY WARNING**: 
> - **Never use hooks with untrusted code or on untrusted websites**
> - **Be extremely careful when crawling sites that might be phishing or malicious**
> - **Hook code has access to page context and can interact with the website**
> - **Always validate and sanitize any data extracted through hooks**
> - **Never expose credentials or sensitive data in hook code**
> - **Consider running the Docker container in an isolated network when testing**

### Hook Information Endpoint

```
GET /hooks/info
```

Returns information about available hook points and their signatures:

```bash
curl http://localhost:11235/hooks/info
```

### Available Hook Points

The API supports 8 hook points that match the local SDK:

| Hook Point | Parameters | Description | Best Use Cases |
|------------|------------|-------------|----------------|
| `on_browser_created` | `browser` | After browser instance creation | Light setup tasks |
| `on_page_context_created` | `page, context` | After page/context creation | **Authentication, cookies, route blocking** |
| `before_goto` | `page, context, url` | Before navigating to URL | Custom headers, logging |
| `after_goto` | `page, context, url, response` | After navigation completes | Verification, waiting for elements |
| `on_user_agent_updated` | `page, context, user_agent` | When user agent changes | UA-specific logic |
| `on_execution_started` | `page, context` | When JS execution begins | JS-related setup |
| `before_retrieve_html` | `page, context` | Before getting final HTML | **Scrolling, lazy loading** |
| `before_return_html` | `page, context, html` | Before returning HTML | Final modifications, metrics |

### Using Hooks in Requests

Add hooks to any crawl request by including the `hooks` parameter:

```json
{
  "urls": ["https://httpbin.org/html"],
  "hooks": {
    "code": {
      "hook_point_name": "async def hook(...): ...",
      "another_hook": "async def hook(...): ..."
    },
    "timeout": 30  // Optional, default 30 seconds (max 120)
  }
}
```

### Hook Examples with Real URLs

#### 1. Authentication with Cookies (GitHub)

```python
import requests

# Example: Setting GitHub session cookie (use your actual session)
hooks_code = {
    "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Add authentication cookies for GitHub
    # WARNING: Never hardcode real credentials!
    await context.add_cookies([
        {
            'name': 'user_session',
            'value': 'your_github_session_token',  # Replace with actual token
            'domain': '.github.com',
            'path': '/',
            'httpOnly': True,
            'secure': True,
            'sameSite': 'Lax'
        }
    ])
    return page
"""
}

response = requests.post("http://localhost:11235/crawl", json={
    "urls": ["https://github.com/settings/profile"],  # Protected page
    "hooks": {"code": hooks_code, "timeout": 30}
})
```

#### 2. Basic Authentication (httpbin.org for testing)

```python
# Safe testing with httpbin.org (a service designed for HTTP testing)
hooks_code = {
    "before_goto": """
async def hook(page, context, url, **kwargs):
    import base64
    # httpbin.org/basic-auth expects username="user" and password="passwd"
    credentials = base64.b64encode(b"user:passwd").decode('ascii')
    
    await page.set_extra_http_headers({
        'Authorization': f'Basic {credentials}'
    })
    return page
"""
}

response = requests.post("http://localhost:11235/crawl", json={
    "urls": ["https://httpbin.org/basic-auth/user/passwd"],
    "hooks": {"code": hooks_code, "timeout": 15}
})
```

#### 3. Performance Optimization (News Sites)

```python
# Example: Optimizing crawling of news sites like CNN or BBC
hooks_code = {
    "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Block images, fonts, and media to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
    await context.route("**/*.{woff,woff2,ttf,otf,eot}", lambda route: route.abort())
    await context.route("**/*.{mp4,webm,ogg,mp3,wav,flac}", lambda route: route.abort())
    
    # Block common tracking and ad domains
    await context.route("**/googletagmanager.com/*", lambda route: route.abort())
    await context.route("**/google-analytics.com/*", lambda route: route.abort())
    await context.route("**/doubleclick.net/*", lambda route: route.abort())
    await context.route("**/facebook.com/tr/*", lambda route: route.abort())
    await context.route("**/amazon-adsystem.com/*", lambda route: route.abort())
    
    # Disable CSS animations for faster rendering
    await page.add_style_tag(content='''
        *, *::before, *::after {
            animation-duration: 0s !important;
            transition-duration: 0s !important;
        }
    ''')
    
    return page
"""
}

response = requests.post("http://localhost:11235/crawl", json={
    "urls": ["https://www.bbc.com/news"],  # Heavy news site
    "hooks": {"code": hooks_code, "timeout": 30}
})
```

#### 4. Handling Infinite Scroll (Twitter/X)

```python
# Example: Scrolling on Twitter/X (requires authentication)
hooks_code = {
    "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # Scroll to load more tweets
    previous_height = 0
    for i in range(5):  # Limit scrolls to avoid infinite loop
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break  # No more content to load
            
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)  # Wait for content to load
        previous_height = current_height
    
    return page
"""
}

# Note: Twitter requires authentication for most content
response = requests.post("http://localhost:11235/crawl", json={
    "urls": ["https://twitter.com/nasa"],  # Public profile
    "hooks": {"code": hooks_code, "timeout": 30}
})
```

#### 5. E-commerce Login (Example Pattern)

```python
# SECURITY WARNING: This is a pattern example. 
# Never use real credentials in code!
# Always use environment variables or secure vaults.

hooks_code = {
    "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Example pattern for e-commerce sites
    # DO NOT use real credentials here!
    
    # Navigate to login page first
    await page.goto("https://example-shop.com/login")
    
    # Wait for login form to load
    await page.wait_for_selector("#email", timeout=5000)
    
    # Fill login form (use environment variables in production!)
    await page.fill("#email", "test@example.com")  # Never use real email
    await page.fill("#password", "test_password")   # Never use real password
    
    # Handle "Remember Me" checkbox if present
    try:
        await page.uncheck("#remember_me")  # Don't remember on shared systems
    except:
        pass
    
    # Submit form
    await page.click("button[type='submit']")
    
    # Wait for redirect after login
    await page.wait_for_url("**/account/**", timeout=10000)
    
    return page
"""
}
```

#### 6. Extracting Structured Data (Wikipedia)

```python
# Safe example using Wikipedia
hooks_code = {
    "after_goto": """
async def hook(page, context, url, response, **kwargs):
    # Wait for Wikipedia content to load
    await page.wait_for_selector("#content", timeout=5000)
    return page
""",
    
    "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # Extract structured data from Wikipedia infobox
    metadata = await page.evaluate('''() => {
        const infobox = document.querySelector('.infobox');
        if (!infobox) return null;
        
        const data = {};
        const rows = infobox.querySelectorAll('tr');
        
        rows.forEach(row => {
            const header = row.querySelector('th');
            const value = row.querySelector('td');
            if (header && value) {
                data[header.innerText.trim()] = value.innerText.trim();
            }
        });
        
        return data;
    }''')
    
    if metadata:
        print("Extracted metadata:", metadata)
    
    return page
"""
}

response = requests.post("http://localhost:11235/crawl", json={
    "urls": ["https://en.wikipedia.org/wiki/Python_(programming_language)"],
    "hooks": {"code": hooks_code, "timeout": 20}
})
```

### Security Best Practices

> 🔒 **Critical Security Guidelines**:

1. **Never Trust User Input**: If accepting hook code from users, always validate and sandbox it
2. **Avoid Phishing Sites**: Never use hooks on suspicious or unverified websites
3. **Protect Credentials**: 
   - Never hardcode passwords, tokens, or API keys in hook code
   - Use environment variables or secure secret management
   - Rotate credentials regularly
4. **Network Isolation**: Run the Docker container in an isolated network when testing
5. **Audit Hook Code**: Always review hook code before execution
6. **Limit Permissions**: Use the least privileged access needed
7. **Monitor Execution**: Check hook execution logs for suspicious behavior
8. **Timeout Protection**: Always set reasonable timeouts (default 30s)

### Hook Response Information

When hooks are used, the response includes detailed execution information:

```json
{
  "success": true,
  "results": [...],
  "hooks": {
    "status": {
      "status": "success",  // or "partial" or "failed"
      "attached_hooks": ["on_page_context_created", "before_retrieve_html"],
      "validation_errors": [],
      "successfully_attached": 2,
      "failed_validation": 0
    },
    "execution_log": [
      {
        "hook_point": "on_page_context_created",
        "status": "success",
        "execution_time": 0.523,
        "timestamp": 1234567890.123
      }
    ],
    "errors": [],  // Any runtime errors
    "summary": {
      "total_executions": 2,
      "successful": 2,
      "failed": 0,
      "timed_out": 0,
      "success_rate": 100.0
    }
  }
}
```

### Error Handling

The hooks system is designed to be resilient:

1. **Validation Errors**: Caught before execution (syntax errors, wrong parameters)
2. **Runtime Errors**: Handled gracefully - crawl continues with original page object
3. **Timeout Protection**: Hooks automatically terminated after timeout (configurable 1-120s)

### Complete Example: Safe Multi-Hook Crawling

```python
import requests
import json
import os

# Safe example using httpbin.org for testing
hooks_code = {
    "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Set viewport and test cookies
    await page.set_viewport_size({"width": 1920, "height": 1080})
    await context.add_cookies([
        {"name": "test_cookie", "value": "test_value", "domain": ".httpbin.org", "path": "/"}
    ])
    
    # Block unnecessary resources for httpbin
    await context.route("**/*.{png,jpg,jpeg}", lambda route: route.abort())
    return page
""",
    
    "before_goto": """
async def hook(page, context, url, **kwargs):
    # Add custom headers for testing
    await page.set_extra_http_headers({
        "X-Test-Header": "crawl4ai-test",
        "Accept-Language": "en-US,en;q=0.9"
    })
    print(f"[HOOK] Navigating to: {url}")
    return page
""",
    
    "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # Simple scroll for any lazy-loaded content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    return page
"""
}

# Make the request to safe testing endpoints
response = requests.post("http://localhost:11235/crawl", json={
    "urls": [
        "https://httpbin.org/html",
        "https://httpbin.org/json"
    ],
    "hooks": {
        "code": hooks_code,
        "timeout": 30
    },
    "crawler_config": {
        "cache_mode": "bypass"
    }
})

# Check results
if response.status_code == 200:
    data = response.json()
    
    # Check hook execution
    if data['hooks']['status']['status'] == 'success':
        print(f"✅ All {len(data['hooks']['status']['attached_hooks'])} hooks executed successfully")
        print(f"Execution stats: {data['hooks']['summary']}")
    
    # Process crawl results
    for result in data['results']:
        print(f"Crawled: {result['url']} - Success: {result['success']}")
else:
    print(f"Error: {response.status_code}")
```

> 💡 **Remember**: Always test your hooks on safe, known websites first before using them on production sites. Never crawl sites that you don't have permission to access or that might be malicious.

### Hooks Utility: Function-Based Approach (Python)

For Python developers, Crawl4AI provides a more convenient way to work with hooks using the `hooks_to_string()` utility function and Docker client integration.

#### Why Use Function-Based Hooks?

**String-Based Approach (shown above)**:
```python
hooks_code = {
    "on_page_context_created": """
async def hook(page, context, **kwargs):
    await page.set_viewport_size({"width": 1920, "height": 1080})
    return page
"""
}
```

**Function-Based Approach (recommended for Python)**:
```python
from crawl4ai import Crawl4aiDockerClient

async def my_hook(page, context, **kwargs):
    await page.set_viewport_size({"width": 1920, "height": 1080})
    return page

async with Crawl4aiDockerClient(base_url="http://localhost:11235") as client:
    result = await client.crawl(
        ["https://example.com"],
        hooks={"on_page_context_created": my_hook}
    )
```

**Benefits**:
- ✅ Write hooks as regular Python functions
- ✅ Full IDE support (autocomplete, syntax highlighting, type checking)
- ✅ Easy to test and debug
- ✅ Reusable hook libraries
- ✅ Automatic conversion to API format

#### Using the Hooks Utility

The `hooks_to_string()` utility converts Python function objects to the string format required by the API:

```python
from crawl4ai import hooks_to_string

# Define your hooks as functions
async def setup_hook(page, context, **kwargs):
    await page.set_viewport_size({"width": 1920, "height": 1080})
    await context.add_cookies([{
        "name": "session",
        "value": "token",
        "domain": ".example.com"
    }])
    return page

async def scroll_hook(page, context, **kwargs):
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    return page

# Convert to string format
hooks_dict = {
    "on_page_context_created": setup_hook,
    "before_retrieve_html": scroll_hook
}
hooks_string = hooks_to_string(hooks_dict)

# Now use with REST API or Docker client
# hooks_string contains the string representations
```

#### Docker Client with Automatic Conversion

The Docker client automatically detects and converts function objects:

```python
from crawl4ai import Crawl4aiDockerClient

async def auth_hook(page, context, **kwargs):
    """Add authentication cookies"""
    await context.add_cookies([{
        "name": "auth_token",
        "value": "your_token",
        "domain": ".example.com"
    }])
    return page

async def performance_hook(page, context, **kwargs):
    """Block unnecessary resources"""
    await context.route("**/*.{png,jpg,gif}", lambda r: r.abort())
    await context.route("**/analytics/*", lambda r: r.abort())
    return page

async with Crawl4aiDockerClient(base_url="http://localhost:11235") as client:
    # Pass functions directly - automatic conversion!
    result = await client.crawl(
        ["https://example.com"],
        hooks={
            "on_page_context_created": performance_hook,
            "before_goto": auth_hook
        },
        hooks_timeout=30  # Optional timeout in seconds (1-120)
    )

    print(f"Success: {result.success}")
    print(f"HTML: {len(result.html)} chars")
```

#### Creating Reusable Hook Libraries

Build collections of reusable hooks:

```python
# hooks_library.py
class CrawlHooks:
    """Reusable hook collection for common crawling tasks"""

    @staticmethod
    async def block_images(page, context, **kwargs):
        """Block all images to speed up crawling"""
        await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda r: r.abort())
        return page

    @staticmethod
    async def block_analytics(page, context, **kwargs):
        """Block analytics and tracking scripts"""
        tracking_domains = [
            "**/google-analytics.com/*",
            "**/googletagmanager.com/*",
            "**/facebook.com/tr/*",
            "**/doubleclick.net/*"
        ]
        for domain in tracking_domains:
            await context.route(domain, lambda r: r.abort())
        return page

    @staticmethod
    async def scroll_infinite(page, context, **kwargs):
        """Handle infinite scroll to load more content"""
        previous_height = 0
        for i in range(5):  # Max 5 scrolls
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            previous_height = current_height
        return page

    @staticmethod
    async def wait_for_dynamic_content(page, context, url, response, **kwargs):
        """Wait for dynamic content to load"""
        await page.wait_for_timeout(2000)
        try:
            # Click "Load More" if present
            load_more = await page.query_selector('[class*="load-more"]')
            if load_more:
                await load_more.click()
                await page.wait_for_timeout(1000)
        except:
            pass
        return page

# Use in your application
from hooks_library import CrawlHooks
from crawl4ai import Crawl4aiDockerClient

async def crawl_with_optimizations(url):
    async with Crawl4aiDockerClient() as client:
        result = await client.crawl(
            [url],
            hooks={
                "on_page_context_created": CrawlHooks.block_images,
                "before_retrieve_html": CrawlHooks.scroll_infinite
            }
        )
        return result
```

#### Choosing the Right Approach

| Approach | Best For | IDE Support | Language |
|----------|----------|-------------|----------|
| **String-based** | Non-Python clients, REST APIs, other languages | ❌ None | Any |
| **Function-based** | Python applications, local development | ✅ Full | Python only |
| **Docker Client** | Python apps with automatic conversion | ✅ Full | Python only |

**Recommendation**:
- **Python applications**: Use Docker client with function objects (easiest)
- **Non-Python or REST API**: Use string-based hooks (most flexible)
- **Manual control**: Use `hooks_to_string()` utility (middle ground)

#### Complete Example with Function Hooks

```python
from crawl4ai import Crawl4aiDockerClient, BrowserConfig, CrawlerRunConfig, CacheMode

# Define hooks as regular Python functions
async def setup_environment(page, context, **kwargs):
    """Setup crawling environment"""
    # Set viewport
    await page.set_viewport_size({"width": 1920, "height": 1080})

    # Block resources for speed
    await context.route("**/*.{png,jpg,gif}", lambda r: r.abort())

    # Add custom headers
    await page.set_extra_http_headers({
        "Accept-Language": "en-US",
        "X-Custom-Header": "Crawl4AI"
    })

    print("[HOOK] Environment configured")
    return page

async def extract_content(page, context, **kwargs):
    """Extract and prepare content"""
    # Scroll to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)

    # Extract metadata
    metadata = await page.evaluate('''() => ({
        title: document.title,
        links: document.links.length,
        images: document.images.length
    })''')

    print(f"[HOOK] Page metadata: {metadata}")
    return page

async def main():
    async with Crawl4aiDockerClient(base_url="http://localhost:11235", verbose=True) as client:
        # Configure crawl
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

        # Crawl with hooks
        result = await client.crawl(
            ["https://httpbin.org/html"],
            browser_config=browser_config,
            crawler_config=crawler_config,
            hooks={
                "on_page_context_created": setup_environment,
                "before_retrieve_html": extract_content
            },
            hooks_timeout=30
        )

        if result.success:
            print(f"✅ Crawl successful!")
            print(f"   URL: {result.url}")
            print(f"   HTML: {len(result.html)} chars")
            print(f"   Markdown: {len(result.markdown)} chars")
        else:
            print(f"❌ Crawl failed: {result.error_message}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### Additional Resources

- **Comprehensive Examples**: See `/docs/examples/hooks_docker_client_example.py` for Python function-based examples
- **REST API Examples**: See `/docs/examples/hooks_rest_api_example.py` for string-based examples
- **Comparison Guide**: See `/docs/examples/README_HOOKS.md` for detailed comparison
- **Utility Documentation**: See `/docs/hooks-utility-guide.md` for complete guide

---

## Job Queue & Webhook API

The Docker deployment includes a powerful asynchronous job queue system with webhook support for both crawling and LLM extraction tasks. Instead of waiting for long-running operations to complete, submit jobs and receive real-time notifications via webhooks when they finish.

### Why Use the Job Queue API?

**Traditional Synchronous API (`/crawl`):**
- Client waits for entire crawl to complete
- Timeout issues with long-running crawls
- Resource blocking during execution
- Constant polling required for status updates

**Asynchronous Job Queue API (`/crawl/job`, `/llm/job`):**
- ✅ Submit job and continue immediately
- ✅ No timeout concerns for long operations
- ✅ Real-time webhook notifications on completion
- ✅ Better resource utilization
- ✅ Perfect for batch processing
- ✅ Ideal for microservice architectures

### Available Endpoints

#### 1. Crawl Job Endpoint

```
POST /crawl/job
```

Submit an asynchronous crawl job with optional webhook notification.

**Request Body:**
```json
{
  "urls": ["https://example.com"],
  "cache_mode": "bypass",
  "extraction_strategy": {
    "type": "JsonCssExtractionStrategy",
    "schema": {
      "title": "h1",
      "content": ".article-body"
    }
  },
  "webhook_config": {
    "webhook_url": "https://your-app.com/webhook/crawl-complete",
    "webhook_data_in_payload": true,
    "webhook_headers": {
      "X-Webhook-Secret": "your-secret-token",
      "X-Custom-Header": "value"
    }
  }
}
```

**Response:**
```json
{
  "task_id": "crawl_1698765432",
  "message": "Crawl job submitted"
}
```

#### 2. LLM Extraction Job Endpoint

```
POST /llm/job
```

Submit an asynchronous LLM extraction job with optional webhook notification.

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "q": "Extract the article title, author, publication date, and main points",
  "provider": "openai/gpt-4o-mini",
  "schema": "{\"title\": \"string\", \"author\": \"string\", \"date\": \"string\", \"points\": [\"string\"]}",
  "cache": false,
  "webhook_config": {
    "webhook_url": "https://your-app.com/webhook/llm-complete",
    "webhook_data_in_payload": true,
    "webhook_headers": {
      "X-Webhook-Secret": "your-secret-token"
    }
  }
}
```

**Response:**
```json
{
  "task_id": "llm_1698765432",
  "message": "LLM job submitted"
}
```

#### 3. Job Status Endpoint

```
GET /job/{task_id}
```

Check the status and retrieve results of a submitted job.

**Response (In Progress):**
```json
{
  "task_id": "crawl_1698765432",
  "status": "processing",
  "message": "Job is being processed"
}
```

**Response (Completed):**
```json
{
  "task_id": "crawl_1698765432",
  "status": "completed",
  "result": {
    "markdown": "# Page Title\n\nContent...",
    "extracted_content": {...},
    "links": {...}
  }
}
```

### Webhook Configuration

Webhooks provide real-time notifications when your jobs complete, eliminating the need for constant polling.

#### Webhook Config Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | Yes | Your HTTP(S) endpoint to receive notifications |
| `webhook_data_in_payload` | boolean | No | Include full result data in webhook payload (default: false) |
| `webhook_headers` | object | No | Custom headers for authentication/identification |

#### Webhook Payload Format

**Success Notification (Crawl Job):**
```json
{
  "task_id": "crawl_1698765432",
  "task_type": "crawl",
  "status": "completed",
  "timestamp": "2025-10-22T12:30:00.000000+00:00",
  "urls": ["https://example.com"],
  "data": {
    "markdown": "# Page content...",
    "extracted_content": {...},
    "links": {...}
  }
}
```

**Success Notification (LLM Job):**
```json
{
  "task_id": "llm_1698765432",
  "task_type": "llm_extraction",
  "status": "completed",
  "timestamp": "2025-10-22T12:30:00.000000+00:00",
  "urls": ["https://example.com/article"],
  "data": {
    "extracted_content": {
      "title": "Understanding Web Scraping",
      "author": "John Doe",
      "date": "2025-10-22",
      "points": ["Point 1", "Point 2"]
    }
  }
}
```

**Failure Notification:**
```json
{
  "task_id": "crawl_1698765432",
  "task_type": "crawl",
  "status": "failed",
  "timestamp": "2025-10-22T12:30:00.000000+00:00",
  "urls": ["https://example.com"],
  "error": "Connection timeout after 30 seconds"
}
```

#### Webhook Delivery & Retry

- **Delivery Method:** HTTP POST to your `webhook_url`
- **Content-Type:** `application/json`
- **Retry Policy:** Exponential backoff with 5 attempts
  - Attempt 1: Immediate
  - Attempt 2: 1 second delay
  - Attempt 3: 2 seconds delay
  - Attempt 4: 4 seconds delay
  - Attempt 5: 8 seconds delay
- **Success Status Codes:** 200-299
- **Custom Headers:** Your `webhook_headers` are included in every request

### Usage Examples

#### Example 1: Python with Webhook Handler (Flask)

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Webhook handler
@app.route('/webhook/crawl-complete', methods=['POST'])
def handle_crawl_webhook():
    payload = request.json

    if payload['status'] == 'completed':
        print(f"✅ Job {payload['task_id']} completed!")
        print(f"Task type: {payload['task_type']}")

        # Access the crawl results
        if 'data' in payload:
            markdown = payload['data'].get('markdown', '')
            extracted = payload['data'].get('extracted_content', {})
            print(f"Extracted {len(markdown)} characters")
            print(f"Structured data: {extracted}")
    else:
        print(f"❌ Job {payload['task_id']} failed: {payload.get('error')}")

    return jsonify({"status": "received"}), 200

# Submit a crawl job with webhook
def submit_crawl_job():
    response = requests.post(
        "http://localhost:11235/crawl/job",
        json={
            "urls": ["https://example.com"],
            "extraction_strategy": {
                "type": "JsonCssExtractionStrategy",
                "schema": {
                    "name": "Example Schema",
                    "baseSelector": "body",
                    "fields": [
                        {"name": "title", "selector": "h1", "type": "text"},
                        {"name": "description", "selector": "meta[name='description']", "type": "attribute", "attribute": "content"}
                    ]
                }
            },
            "webhook_config": {
                "webhook_url": "https://your-app.com/webhook/crawl-complete",
                "webhook_data_in_payload": True,
                "webhook_headers": {
                    "X-Webhook-Secret": "your-secret-token"
                }
            }
        }
    )

    task_id = response.json()['task_id']
    print(f"Job submitted: {task_id}")
    return task_id

if __name__ == '__main__':
    app.run(port=5000)
```

#### Example 2: LLM Extraction with Webhooks

```python
import requests

def submit_llm_job_with_webhook():
    response = requests.post(
        "http://localhost:11235/llm/job",
        json={
            "url": "https://example.com/article",
            "q": "Extract the article title, author, and main points",
            "provider": "openai/gpt-4o-mini",
            "webhook_config": {
                "webhook_url": "https://your-app.com/webhook/llm-complete",
                "webhook_data_in_payload": True,
                "webhook_headers": {
                    "X-Webhook-Secret": "your-secret-token"
                }
            }
        }
    )

    task_id = response.json()['task_id']
    print(f"LLM job submitted: {task_id}")
    return task_id

# Webhook handler for LLM jobs
@app.route('/webhook/llm-complete', methods=['POST'])
def handle_llm_webhook():
    payload = request.json

    if payload['status'] == 'completed':
        extracted = payload['data']['extracted_content']
        print(f"✅ LLM extraction completed!")
        print(f"Results: {extracted}")
    else:
        print(f"❌ LLM extraction failed: {payload.get('error')}")

    return jsonify({"status": "received"}), 200
```

#### Example 3: Without Webhooks (Polling)

If you don't use webhooks, you can poll for results:

```python
import requests
import time

# Submit job
response = requests.post(
    "http://localhost:11235/crawl/job",
    json={"urls": ["https://example.com"]}
)
task_id = response.json()['task_id']

# Poll for results
while True:
    result = requests.get(f"http://localhost:11235/job/{task_id}")
    data = result.json()

    if data['status'] == 'completed':
        print("Job completed!")
        print(data['result'])
        break
    elif data['status'] == 'failed':
        print(f"Job failed: {data.get('error')}")
        break

    print("Still processing...")
    time.sleep(2)
```

#### Example 4: Global Webhook Configuration

Set a default webhook URL in your `config.yml` to avoid repeating it in every request:

```yaml
# config.yml
api:
  crawler:
    # ... other settings ...
    webhook:
      default_url: "https://your-app.com/webhook/default"
      default_headers:
        X-Webhook-Secret: "your-secret-token"
```

Then submit jobs without webhook config:

```python
# Uses the global webhook configuration
response = requests.post(
    "http://localhost:11235/crawl/job",
    json={"urls": ["https://example.com"]}
)
```

### Webhook Best Practices

1. **Authentication:** Always use custom headers for webhook authentication
   ```json
   "webhook_headers": {
     "X-Webhook-Secret": "your-secret-token"
   }
   ```

2. **Idempotency:** Design your webhook handler to be idempotent (safe to receive duplicate notifications)

3. **Fast Response:** Return HTTP 200 quickly; process data asynchronously if needed
   ```python
   @app.route('/webhook', methods=['POST'])
   def webhook():
       payload = request.json
       # Queue for background processing
       queue.enqueue(process_webhook, payload)
       return jsonify({"status": "received"}), 200
   ```

4. **Error Handling:** Handle both success and failure notifications
   ```python
   if payload['status'] == 'completed':
       # Process success
   elif payload['status'] == 'failed':
       # Log error, retry, or alert
   ```

5. **Validation:** Verify webhook authenticity using custom headers
   ```python
   secret = request.headers.get('X-Webhook-Secret')
   if secret != os.environ['EXPECTED_SECRET']:
       return jsonify({"error": "Unauthorized"}), 401
   ```

6. **Logging:** Log webhook deliveries for debugging
   ```python
   logger.info(f"Webhook received: {payload['task_id']} - {payload['status']}")
   ```

### Use Cases

**1. Batch Processing**
Submit hundreds of URLs and get notified as each completes:
```python
urls = ["https://site1.com", "https://site2.com", ...]
for url in urls:
    submit_crawl_job(url, webhook_url="https://app.com/webhook")
```

**2. Microservice Integration**
Integrate with event-driven architectures:
```python
# Service A submits job
task_id = submit_crawl_job(url)

# Service B receives webhook and triggers next step
@app.route('/webhook')
def webhook():
    process_result(request.json)
    trigger_next_service()
    return "OK", 200
```

**3. Long-Running Extractions**
Handle complex LLM extractions without timeouts:
```python
submit_llm_job(
    url="https://long-article.com",
    q="Comprehensive summary with key points and analysis",
    webhook_url="https://app.com/webhook/llm"
)
```

### Troubleshooting

**Webhook not receiving notifications?**
- Check your webhook URL is publicly accessible
- Verify firewall/security group settings
- Use webhook testing tools like webhook.site for debugging
- Check server logs for delivery attempts
- Ensure your handler returns 200-299 status code

**Job stuck in processing?**
- Check Redis connection: `docker logs <container_name> | grep redis`
- Verify worker processes: `docker exec <container_name> ps aux | grep worker`
- Check server logs: `docker logs <container_name>`

**Need to cancel a job?**
Jobs are processed asynchronously. If you need to cancel:
- Delete the task from Redis (requires Redis CLI access)
- Or implement a cancellation endpoint in your webhook handler

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

The Python SDK provides a convenient way to interact with the Docker API, including **automatic hook conversion** when using function objects.

```python
import asyncio
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    # Point to the correct server port
    async with Crawl4aiDockerClient(base_url="http://localhost:11235", verbose=True) as client:
        # If JWT is enabled on the server, authenticate first:
        # await client.authenticate("user@example.com") # See Server Configuration section

        # Example Non-streaming crawl
        print("--- Running Non-Streaming Crawl ---")
        results = await client.crawl(
            ["https://httpbin.org/html"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        if results:
            print(f"Non-streaming results success: {results.success}")
            if results.success:
                for result in results:
                    print(f"URL: {result.url}, Success: {result.success}")
        else:
            print("Non-streaming crawl failed.")

        # Example Streaming crawl
        print("\n--- Running Streaming Crawl ---")
        stream_config = CrawlerRunConfig(stream=True, cache_mode=CacheMode.BYPASS)
        try:
            async for result in await client.crawl(
                ["https://httpbin.org/html", "https://httpbin.org/links/5/0"],
                browser_config=BrowserConfig(headless=True),
                crawler_config=stream_config
            ):
                print(f"Streamed result: URL: {result.url}, Success: {result.success}")
        except Exception as e:
            print(f"Streaming crawl failed: {e}")

        # Example with hooks (Python function objects)
        print("\n--- Crawl with Hooks ---")

        async def my_hook(page, context, **kwargs):
            """Custom hook to optimize performance"""
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await context.route("**/*.{png,jpg}", lambda r: r.abort())
            print("[HOOK] Page optimized")
            return page

        result = await client.crawl(
            ["https://httpbin.org/html"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
            hooks={"on_page_context_created": my_hook},  # Pass function directly!
            hooks_timeout=30
        )
        print(f"Crawl with hooks success: {result.success}")

        # Example Get schema
        print("\n--- Getting Schema ---")
        schema = await client.get_schema()
        print(f"Schema received: {bool(schema)}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### SDK Parameters

The Docker client supports the following parameters:

**Client Initialization**:
- `base_url` (str): URL of the Docker server (default: `http://localhost:8000`)
- `timeout` (float): Request timeout in seconds (default: 30.0)
- `verify_ssl` (bool): Verify SSL certificates (default: True)
- `verbose` (bool): Enable verbose logging (default: True)
- `log_file` (Optional[str]): Path to log file (default: None)

**crawl() Method**:
- `urls` (List[str]): List of URLs to crawl
- `browser_config` (Optional[BrowserConfig]): Browser configuration
- `crawler_config` (Optional[CrawlerRunConfig]): Crawler configuration
- `hooks` (Optional[Dict]): Hook functions or strings - **automatically converts function objects!**
- `hooks_timeout` (int): Timeout for each hook execution in seconds (default: 30)

**Returns**:
- Single URL: `CrawlResult` object
- Multiple URLs: `List[CrawlResult]`
- Streaming: `AsyncGenerator[CrawlResult]`

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

### LLM Configuration Examples

The Docker API supports dynamic LLM configuration through multiple levels:

#### Temperature Control

Temperature affects the randomness of LLM responses (0.0 = deterministic, 2.0 = very creative):

```python
import requests

# Low temperature for factual extraction
response = requests.post(
    "http://localhost:11235/md",
    json={
        "url": "https://example.com",
        "f": "llm",
        "q": "Extract all dates and numbers from this page",
        "temperature": 0.2  # Very focused, deterministic
    }
)

# High temperature for creative tasks
response = requests.post(
    "http://localhost:11235/md",
    json={
        "url": "https://example.com", 
        "f": "llm",
        "q": "Write a creative summary of this content",
        "temperature": 1.2  # More creative, varied responses
    }
)
```

#### Custom API Endpoints

Use custom base URLs for proxy servers or alternative API endpoints:

```python

# Using a local LLM server
response = requests.post(
    "http://localhost:11235/md",
    json={
        "url": "https://example.com",
        "f": "llm",
        "q": "Extract key information",
        "provider": "ollama/llama2",
        "base_url": "http://localhost:11434/v1"
    }
)
```

#### Dynamic Provider Selection

Switch between providers based on task requirements:

```python
async def smart_extraction(url: str, content_type: str):
    """Select provider and temperature based on content type"""
    
    configs = {
        "technical": {
            "provider": "openai/gpt-4",
            "temperature": 0.3,
            "query": "Extract technical specifications and code examples"
        },
        "creative": {
            "provider": "anthropic/claude-3-opus",
            "temperature": 0.9,
            "query": "Create an engaging narrative summary"
        },
        "quick": {
            "provider": "groq/mixtral-8x7b",
            "temperature": 0.5,
            "query": "Quick summary in bullet points"
        }
    }
    
    config = configs.get(content_type, configs["quick"])
    
    response = await httpx.post(
        "http://localhost:11235/md",
        json={
            "url": url,
            "f": "llm",
            "q": config["query"],
            "provider": config["provider"],
            "temperature": config["temperature"]
        }
    )
    
    return response.json()
```

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

## Real-time Monitoring & Operations

One of the key advantages of self-hosting is complete visibility into your infrastructure. Crawl4AI includes a comprehensive real-time monitoring system that gives you full transparency and control.

### Monitoring Dashboard

Access the **built-in real-time monitoring dashboard** for complete operational visibility:

```
http://localhost:11235/monitor
```

![Monitoring Dashboard](https://via.placeholder.com/800x400?text=Crawl4AI+Monitoring+Dashboard)

**Dashboard Features:**

#### 1. System Health Overview
- **CPU & Memory**: Live usage with progress bars and percentage indicators
- **Network I/O**: Total bytes sent/received since startup
- **Server Uptime**: How long your server has been running
- **Browser Pool Status**:
  - 🔥 Permanent browser (always-on default config, ~270MB)
  - ♨️ Hot pool (frequently used configs, ~180MB each)
  - ❄️ Cold pool (idle browsers awaiting cleanup, ~180MB each)
- **Memory Pressure**: LOW/MEDIUM/HIGH indicator for janitor behavior

#### 2. Live Request Tracking
- **Active Requests**: Currently running crawls with:
  - Request ID for tracking
  - Target URL (truncated for display)
  - Endpoint being used
  - Elapsed time (updates in real-time)
  - Memory usage from start
- **Completed Requests**: Last 10 finished requests showing:
  - Success/failure status (color-coded)
  - Total execution time
  - Memory delta (how much memory changed)
  - Pool hit (was browser reused?)
  - HTTP status code
- **Filtering**: View all, success only, or errors only

#### 3. Browser Pool Management
Interactive table showing all active browsers:

| Type | Signature | Age | Last Used | Hits | Actions |
|------|-----------|-----|-----------|------|---------|
| permanent | abc12345 | 2h | 5s ago | 1,247 | Restart |
| hot | def67890 | 45m | 2m ago | 89 | Kill / Restart |
| cold | ghi11213 | 30m | 15m ago | 3 | Kill / Restart |

- **Reuse Rate**: Percentage of requests that reused existing browsers
- **Memory Estimates**: Total memory used by browser pool
- **Manual Control**: Kill or restart individual browsers

#### 4. Janitor Events Log
Real-time log of browser pool cleanup events:
- When cold browsers are closed due to memory pressure
- When browsers are promoted from cold to hot pool
- Forced cleanups triggered manually
- Detailed cleanup reasons and browser signatures

#### 5. Error Monitoring
Recent errors with full context:
- Timestamp
- Endpoint where error occurred
- Target URL
- Error message
- Request ID for correlation

**Live Updates:**
The dashboard connects via WebSocket and refreshes every **2 seconds** with the latest data. Connection status indicator shows when you're connected/disconnected.

---

### Monitor API Endpoints

For programmatic monitoring, automation, and integration with your existing infrastructure:

#### Health & Statistics

**Get System Health**
```bash
GET /monitor/health
```

Returns current system snapshot:
```json
{
  "container": {
    "memory_percent": 45.2,
    "cpu_percent": 23.1,
    "network_sent_mb": 1250.45,
    "network_recv_mb": 3421.12,
    "uptime_seconds": 7234
  },
  "pool": {
    "permanent": {"active": true, "memory_mb": 270},
    "hot": {"count": 3, "memory_mb": 540},
    "cold": {"count": 1, "memory_mb": 180},
    "total_memory_mb": 990
  },
  "janitor": {
    "next_cleanup_estimate": "adaptive",
    "memory_pressure": "MEDIUM"
  }
}
```

**Get Request Statistics**
```bash
GET /monitor/requests?status=all&limit=50
```

Query parameters:
- `status`: Filter by `all`, `active`, `completed`, `success`, or `error`
- `limit`: Number of completed requests to return (1-1000)

**Get Browser Pool Details**
```bash
GET /monitor/browsers
```

Returns detailed information about all active browsers:
```json
{
  "browsers": [
    {
      "type": "permanent",
      "sig": "abc12345",
      "age_seconds": 7234,
      "last_used_seconds": 5,
      "memory_mb": 270,
      "hits": 1247,
      "killable": false
    },
    {
      "type": "hot",
      "sig": "def67890",
      "age_seconds": 2701,
      "last_used_seconds": 120,
      "memory_mb": 180,
      "hits": 89,
      "killable": true
    }
  ],
  "summary": {
    "total_count": 5,
    "total_memory_mb": 990,
    "reuse_rate_percent": 87.3
  }
}
```

**Get Endpoint Performance Statistics**
```bash
GET /monitor/endpoints/stats
```

Returns aggregated metrics per endpoint:
```json
{
  "/crawl": {
    "count": 1523,
    "avg_latency_ms": 2341.5,
    "success_rate_percent": 98.2,
    "pool_hit_rate_percent": 89.1,
    "errors": 27
  },
  "/md": {
    "count": 891,
    "avg_latency_ms": 1823.7,
    "success_rate_percent": 99.4,
    "pool_hit_rate_percent": 92.3,
    "errors": 5
  }
}
```

**Get Timeline Data**
```bash
GET /monitor/timeline?metric=memory&window=5m
```

Parameters:
- `metric`: `memory`, `requests`, or `browsers`
- `window`: Currently only `5m` (5-minute window, 5-second resolution)

Returns time-series data for charts:
```json
{
  "timestamps": [1699564800, 1699564805, 1699564810, ...],
  "values": [42.1, 43.5, 41.8, ...]
}
```

#### Logs

**Get Janitor Events**
```bash
GET /monitor/logs/janitor?limit=100
```

**Get Error Log**
```bash
GET /monitor/logs/errors?limit=100
```

---

### WebSocket Streaming

For real-time monitoring in your own dashboards or applications:

```bash
WS /monitor/ws
```

**Connection Example (Python):**
```python
import asyncio
import websockets
import json

async def monitor_server():
    uri = "ws://localhost:11235/monitor/ws"

    async with websockets.connect(uri) as websocket:
        print("Connected to Crawl4AI monitor")

        while True:
            # Receive update every 2 seconds
            data = await websocket.recv()
            update = json.loads(data)

            # Extract key metrics
            health = update['health']
            active_requests = len(update['requests']['active'])
            browsers = len(update['browsers'])

            print(f"Memory: {health['container']['memory_percent']:.1f}% | "
                  f"Active: {active_requests} | "
                  f"Browsers: {browsers}")

            # Check for high memory pressure
            if health['janitor']['memory_pressure'] == 'HIGH':
                print("⚠️  HIGH MEMORY PRESSURE - Consider cleanup")

asyncio.run(monitor_server())
```

**Update Payload Structure:**
```json
{
  "timestamp": 1699564823.456,
  "health": { /* System health snapshot */ },
  "requests": {
    "active": [ /* Currently running */ ],
    "completed": [ /* Last 10 completed */ ]
  },
  "browsers": [ /* All active browsers */ ],
  "timeline": {
    "memory": { /* Last 5 minutes */ },
    "requests": { /* Request rate */ },
    "browsers": { /* Pool composition */ }
  },
  "janitor": [ /* Last 10 cleanup events */ ],
  "errors": [ /* Last 10 errors */ ]
}
```

---

### Control Actions

Take manual control when needed:

**Force Immediate Cleanup**
```bash
POST /monitor/actions/cleanup
```

Kills all cold pool browsers immediately (useful when memory is tight):
```json
{
  "success": true,
  "killed_browsers": 3
}
```

**Kill Specific Browser**
```bash
POST /monitor/actions/kill_browser
Content-Type: application/json

{
  "sig": "abc12345"  // First 8 chars of browser signature
}
```

Response:
```json
{
  "success": true,
  "killed_sig": "abc12345",
  "pool_type": "hot"
}
```

**Restart Browser**
```bash
POST /monitor/actions/restart_browser
Content-Type: application/json

{
  "sig": "permanent"  // Or first 8 chars of signature
}
```

For permanent browser, this will close and reinitialize it. For hot/cold browsers, it kills them and lets new requests create fresh ones.

**Reset Statistics**
```bash
POST /monitor/stats/reset
```

Clears endpoint counters (useful for starting fresh after testing).

---

### Production Integration

#### Integration with Existing Monitoring Systems

**Prometheus Integration:**
```bash
# Scrape metrics endpoint
curl http://localhost:11235/metrics
```

**Custom Dashboard Integration:**
```python
# Example: Push metrics to your monitoring system
import asyncio
import websockets
import json
from your_monitoring import push_metric

async def integrate_monitoring():
    async with websockets.connect("ws://localhost:11235/monitor/ws") as ws:
        while True:
            data = json.loads(await ws.recv())

            # Push to your monitoring system
            push_metric("crawl4ai.memory.percent",
                       data['health']['container']['memory_percent'])
            push_metric("crawl4ai.active_requests",
                       len(data['requests']['active']))
            push_metric("crawl4ai.browser_count",
                       len(data['browsers']))
```

**Alerting Example:**
```python
import requests
import time

def check_health():
    """Poll health endpoint and alert on issues"""
    response = requests.get("http://localhost:11235/monitor/health")
    health = response.json()

    # Alert on high memory
    if health['container']['memory_percent'] > 85:
        send_alert(f"High memory: {health['container']['memory_percent']}%")

    # Alert on high error rate
    stats = requests.get("http://localhost:11235/monitor/endpoints/stats").json()
    for endpoint, metrics in stats.items():
        if metrics['success_rate_percent'] < 95:
            send_alert(f"{endpoint} success rate: {metrics['success_rate_percent']}%")

# Run every minute
while True:
    check_health()
    time.sleep(60)
```

**Log Aggregation:**
```python
import requests
from datetime import datetime

def aggregate_errors():
    """Fetch and aggregate errors for logging system"""
    response = requests.get("http://localhost:11235/monitor/logs/errors?limit=100")
    errors = response.json()['errors']

    for error in errors:
        log_to_system({
            'timestamp': datetime.fromtimestamp(error['timestamp']),
            'service': 'crawl4ai',
            'endpoint': error['endpoint'],
            'url': error['url'],
            'message': error['error'],
            'request_id': error['request_id']
        })
```

#### Key Metrics to Track

For production self-hosted deployments, monitor these metrics:

1. **Memory Usage Trends**
   - Track `container.memory_percent` over time
   - Alert when consistently above 80%
   - Prevents OOM kills

2. **Request Success Rates**
   - Monitor per-endpoint success rates
   - Alert when below 95%
   - Indicates crawling issues

3. **Average Latency**
   - Track `avg_latency_ms` per endpoint
   - Detect performance degradation
   - Optimize slow endpoints

4. **Browser Pool Efficiency**
   - Monitor `reuse_rate_percent`
   - Should be >80% for good efficiency
   - Low rates indicate pool churn

5. **Error Frequency**
   - Count errors per time window
   - Alert on sudden spikes
   - Track error patterns

6. **Janitor Activity**
   - Monitor cleanup frequency
   - Excessive cleanup indicates memory pressure
   - Adjust pool settings if needed

---

### Quick Health Check

For simple uptime monitoring:

```bash
curl http://localhost:11235/health
```

Returns:
```json
{
  "status": "healthy",
  "version": "0.7.4"
}
```

Other useful endpoints:
- `/metrics` - Prometheus metrics
- `/schema` - Full API schema

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
  # api_key: sk-...  # If you pass the API key directly (not recommended)
  # temperature and base_url are controlled via environment variables or request parameters

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

Congratulations! You now have everything you need to self-host your own Crawl4AI infrastructure with complete control and visibility.

**What You've Learned:**
- ✅ Multiple deployment options (Docker Hub, Docker Compose, manual builds)
- ✅ Environment configuration and LLM integration
- ✅ Using the interactive playground for testing
- ✅ Making API requests with proper typing (SDK and REST)
- ✅ Specialized endpoints (screenshots, PDFs, JavaScript execution)
- ✅ MCP integration for AI-assisted development
- ✅ **Real-time monitoring dashboard** for operational transparency
- ✅ **Monitor API** for programmatic control and integration
- ✅ Production deployment best practices

**Why This Matters:**

By self-hosting Crawl4AI, you:
- 🔒 **Own Your Data**: Everything stays in your infrastructure
- 📊 **See Everything**: Real-time dashboard shows exactly what's happening
- 💰 **Control Costs**: Scale within your resources, no per-request fees
- ⚡ **Maximize Performance**: Direct access with smart browser pooling (10x memory efficiency)
- 🛡️ **Stay Secure**: Keep sensitive workflows behind your firewall
- 🔧 **Customize Freely**: Full control over configs, strategies, and optimizations

**Next Steps:**

1. **Start Simple**: Deploy with Docker Hub image and test with the playground
2. **Monitor Everything**: Open `http://localhost:11235/monitor` to watch your server
3. **Integrate**: Connect your applications using the Python SDK or REST API
4. **Scale Smart**: Use the monitoring data to optimize your deployment
5. **Go Production**: Set up alerting, log aggregation, and automated cleanup

**Key Resources:**
- 🎮 **Playground**: `http://localhost:11235/playground` - Interactive testing
- 📊 **Monitor Dashboard**: `http://localhost:11235/monitor` - Real-time visibility
- 📖 **Architecture Docs**: `deploy/docker/ARCHITECTURE.md` - Deep technical dive
- 💬 **Discord Community**: Get help and share experiences
- ⭐ **GitHub**: Report issues, contribute, show support

Remember: The monitoring dashboard is your window into your infrastructure. Use it to understand performance, troubleshoot issues, and optimize your deployment. The examples in the `examples` folder show real-world usage patterns you can adapt.

**You're now in control of your web crawling destiny!** 🚀

Happy crawling! 🕷️
