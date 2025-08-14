Crawl4AI Docker Guide 🐳
=======================

Table of Contents
-----------------

* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Option 1: Using Pre-built Docker Hub Images (Recommended)](#option-1-using-pre-built-docker-hub-images-recommended)
* [Option 2: Using Docker Compose](#option-2-using-docker-compose)
* [Option 3: Manual Local Build & Run](#option-3-manual-local-build--run)
* [Dockerfile Parameters](#dockerfile-parameters)
* [Using the API](#using-the-api)
* [Playground Interface](#playground-interface)
* [Python SDK](#python-sdk)
* [Understanding Request Schema](#understanding-request-schema)
* [REST API Examples](#rest-api-examples)
* [Additional API Endpoints](#additional-api-endpoints)
* [HTML Extraction Endpoint](#html-extraction-endpoint)
* [Screenshot Endpoint](#screenshot-endpoint)
* [PDF Export Endpoint](#pdf-export-endpoint)
* [JavaScript Execution Endpoint](#javascript-execution-endpoint)
* [Library Context Endpoint](#library-context-endpoint)
* [MCP (Model Context Protocol) Support](#mcp-model-context-protocol-support)
* [What is MCP?](#what-is-mcp)
* [Connecting via MCP](#connecting-via-mcp)
* [Using with Claude Code](#using-with-claude-code)
* [Available MCP Tools](#available-mcp-tools)
* [Testing MCP Connections](#testing-mcp-connections)
* [MCP Schemas](#mcp-schemas)
* [Metrics & Monitoring](#metrics--monitoring)
* [Deployment Scenarios](#deployment-scenarios)
* [Complete Examples](#complete-examples)
* [Server Configuration](#server-configuration)
* [Understanding config.yml](#understanding-configyml)
* [JWT Authentication](#jwt-authentication)
* [Configuration Tips and Best Practices](#configuration-tips-and-best-practices)
* [Customizing Your Configuration](#customizing-your-configuration)
* [Configuration Recommendations](#configuration-recommendations)
* [Getting Help](#getting-help)
* [Summary](#summary)

Prerequisites
-------------

Before we dive in, make sure you have:
- Docker installed and running (version 20.10.0 or higher), including `docker compose` (usually bundled with Docker Desktop).
- `git` for cloning the repository.
- At least 4GB of RAM available for the container (more recommended for heavy use).
- Python 3.10+ (if using the Python SDK).
- Node.js 16+ (if using the Node.js examples).

> 💡 **Pro tip**: Run `docker info` to check your Docker installation and available resources.

Installation
------------

We offer several ways to get the Crawl4AI server running. The quickest way is to use our pre-built Docker Hub images.

### Option 1: Using Pre-built Docker Hub Images (Recommended)

Pull and run images directly from Docker Hub without building locally.

#### 1. Pull the Image

Our latest release is `0.7.3`. Images are built with multi-arch manifests, so Docker automatically pulls the correct version for your system.

> 💡 **Note**: The `latest` tag points to the stable `0.7.3` version.

```
# Pull the latest version
docker pull unclecode/crawl4ai:0.7.3

# Or pull using the latest tag
docker pull unclecode/crawl4ai:latest
```

#### 2. Setup Environment (API Keys)

If you plan to use LLMs, create a `.llm.env` file in your working directory:

```
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

* **Basic run:**

  ```
  docker run -d \
    -p 11235:11235 \
    --name crawl4ai \
    --shm-size=1g \
    unclecode/crawl4ai:latest
  ```
* **With LLM support:**

  ```
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

```
docker stop crawl4ai && docker rm crawl4ai
```

#### Docker Hub Versioning Explained

* **Image Name:** `unclecode/crawl4ai`
* **Tag Format:** `LIBRARY_VERSION[-SUFFIX]` (e.g., `0.7.3`)
  + `LIBRARY_VERSION`: The semantic version of the core `crawl4ai` Python library
  + `SUFFIX`: Optional tag for release candidates (`` `) and revisions ( ``r1`)
* **`latest` Tag:** Points to the most recent stable version
* **Multi-Architecture Support:** All images support both `linux/amd64` and `linux/arm64` architectures through a single tag

### Option 2: Using Docker Compose

Docker Compose simplifies building and running the service, especially for local development and testing.

#### 1. Clone Repository

```
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
```

#### 2. Environment Setup (API Keys)

If you plan to use LLMs, copy the example environment file and add your API keys. This file should be in the **project root directory**.

```
# Make sure you are in the 'crawl4ai' root directory
cp deploy/docker/.llm.env.example .llm.env

# Now edit .llm.env and add your API keys
```

**Flexible LLM Provider Configuration:**

The Docker setup now supports flexible LLM provider configuration through three methods:

1. **Environment Variable** (Highest Priority): Set `LLM_PROVIDER` to override the default

   ```
   export LLM_PROVIDER="anthropic/claude-3-opus"
   # Or in your .llm.env file:
   # LLM_PROVIDER=anthropic/claude-3-opus
   ```
2. **API Request Parameter**: Specify provider per request

   ```
   {
     "url": "https://example.com",
     "f": "llm",
     "provider": "groq/mixtral-8x7b"
   }
   ```
3. **Config File Default**: Falls back to `config.yml` (default: `openai/gpt-4o-mini`)

The system automatically selects the appropriate API key based on the configured `api_key_env` in the config file.

#### 3. Build and Run with Compose

The `docker-compose.yml` file in the project root provides a simplified approach that automatically handles architecture detection using buildx.

* **Run Pre-built Image from Docker Hub:**

  ```
  # Pulls and runs the release candidate from Docker Hub
  # Automatically selects the correct architecture
  IMAGE=unclecode/crawl4ai:latest docker compose up -d
  ```
* **Build and Run Locally:**

  ```
  # Builds the image locally using Dockerfile and runs it
  # Automatically uses the correct architecture for your machine
  docker compose up --build -d
  ```
* **Customize the Build:**

  ```
  # Build with all features (includes torch and transformers)
  INSTALL_TYPE=all docker compose up --build -d

  # Build with GPU support (for AMD64 platforms)
  ENABLE_GPU=true docker compose up --build -d
  ```

> The server will be available at `http://localhost:11235`.

#### 4. Stopping the Service

```
# Stop the service
docker compose down
```

### Option 3: Manual Local Build & Run

If you prefer not to use Docker Compose for direct control over the build and run process.

#### 1. Clone Repository & Setup Environment

Follow steps 1 and 2 from the Docker Compose section above (clone repo, `cd crawl4ai`, create `.llm.env` in the root).

#### 2. Build the Image (Multi-Arch)

Use `docker buildx` to build the image. Crawl4AI now uses buildx to handle multi-architecture builds automatically.

```
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

* **Basic run (no LLM support):**

  ```
  docker run -d \
    -p 11235:11235 \
    --name crawl4ai-standalone \
    --shm-size=1g \
    crawl4ai-local:latest
  ```
* **With LLM support:**

  ```
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

```
docker stop crawl4ai-standalone && docker rm crawl4ai-standalone
```

---

MCP (Model Context Protocol) Support
------------------------------------

Crawl4AI server includes support for the Model Context Protocol (MCP), allowing you to connect the server's capabilities directly to MCP-compatible clients like Claude Code.

### What is MCP?

MCP is an open protocol that standardizes how applications provide context to LLMs. It allows AI models to access external tools, data sources, and services through a standardized interface.

### Connecting via MCP

The Crawl4AI server exposes two MCP endpoints:

* **Server-Sent Events (SSE)**: `http://localhost:11235/mcp/sse`
* **WebSocket**: `ws://localhost:11235/mcp/ws`

### Using with Claude Code

You can add Crawl4AI as an MCP tool provider in Claude Code with a simple command:

```
# Add the Crawl4AI server as an MCP provider
claude mcp add --transport sse c4ai-sse http://localhost:11235/mcp/sse

# List all MCP providers to verify it was added
claude mcp list
```

Once connected, Claude Code can directly use Crawl4AI's capabilities like screenshot capture, PDF generation, and HTML processing without having to make separate API calls.

### Available MCP Tools

When connected via MCP, the following tools are available:

* `md` - Generate markdown from web content
* `html` - Extract preprocessed HTML
* `screenshot` - Capture webpage screenshots
* `pdf` - Generate PDF documents
* `execute_js` - Run JavaScript on web pages
* `crawl` - Perform multi-URL crawling
* `ask` - Query the Crawl4AI library context

### Testing MCP Connections

You can test the MCP WebSocket connection using the test file included in the repository:

```
# From the repository root
python tests/mcp/test_mcp_socket.py
```

### MCP Schemas

Access the MCP tool schemas at `http://localhost:11235/mcp/schema` for detailed information on each tool's parameters and capabilities.

---