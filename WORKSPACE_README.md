# Crawl4AI Microservices Workspace

This workspace contains the microservices architecture for Crawl4AI, built with **uv workspaces** for ultra-fast dependency management.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) installed

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
cd /path/to/crawl4ai

# Create virtual environment
uv venv

# Install all workspace dependencies
uv sync --all-packages

# Or install with dev dependencies
uv sync --all-packages --group dev
```

## 📁 Workspace Structure

```
crawl4ai-workspace/
├── workspace-pyproject.toml    # Workspace root configuration
├── uv.lock                      # Unified lockfile
│
├── services/                    # Microservices
│   ├── browser-service/         # Browser management
│   └── content-scraping-service/# Content scraping
│
├── packages/                    # CLI packages
│   ├── crawl4ai-basic/         # Basic CLI (pending)
│   └── crawl4ai-advanced/      # Advanced CLI (pending)
│
├── shared/                      # Shared libraries
│   ├── core/                   # Core models and utilities
│   ├── client/                 # Service client SDK
│   └── schemas/                # API schemas
│
└── docker/                      # Docker configurations
    └── services/               # Service Dockerfiles
```

## 🛠️ Development Workflow

### Running Services Locally

```bash
# Run browser service
uv run --package crawl4ai-browser-service uvicorn browser_service.main:create_app --factory --reload --port 8001

# Run content scraping service
uv run --package crawl4ai-content-scraping-service uvicorn content_scraping_service.main:create_app --factory --reload --port 8002
```

### Using Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.workspace.yml up

# Start specific service
docker-compose -f docker-compose.workspace.yml up browser-service

# View logs
docker-compose -f docker-compose.workspace.yml logs -f browser-service

# Stop services
docker-compose -f docker-compose.workspace.yml down
```

### Adding Dependencies

```bash
# Add dependency to specific service
cd services/browser-service
uv add <package-name>

# Add dev dependency to workspace
uv add --dev <package-name>

# Update lockfile
uv lock
```

### Building Packages

```bash
# Build specific package
uv build --package crawl4ai-browser-service

# Build all packages
uv build --all-packages
```

## 📚 Available Services

### Browser Service (Port 8001)

Manages headless browser instances using Playwright.

**Endpoints:**
- `POST /api/v1/navigate` - Navigate to URL and perform actions
- `GET /api/v1/status` - Service status
- `GET /health` - Health check

**Example:**
```python
from crawl4ai_client import BrowserClient
from crawl4ai_schemas import BrowserRequest

async with BrowserClient() as client:
    request = BrowserRequest(url="https://example.com")
    response = await client.navigate(request)
    print(response.html)
```

### Content Scraping Service (Port 8002)

Extracts content from HTML using lxml and BeautifulSoup.

**Endpoints:**
- `POST /api/v1/scrape` - Scrape content from HTML
- `GET /api/v1/status` - Service status
- `GET /health` - Health check

**Example:**
```python
from crawl4ai_client import ScrapingClient
from crawl4ai_schemas import ScrapingRequest

async with ScrapingClient() as client:
    request = ScrapingRequest(
        html="<html>...</html>",
        extract_links=True,
        extract_images=True,
    )
    response = await client.scrape(request)
    print(response.links)
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run tests for specific service
uv run pytest services/browser-service/tests/

# Run with coverage
uv run pytest --cov=services --cov-report=html
```

## 📝 Code Quality

```bash
# Format code
uv run black .
uv run isort .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .
```

## 🐳 Docker Commands

```bash
# Build specific service
docker build -f docker/services/browser.Dockerfile -t crawl4ai-browser-service .

# Run service container
docker run -p 8001:8000 crawl4ai-browser-service

# Build all services
docker-compose -f docker-compose.workspace.yml build
```

## 🔧 Environment Variables

Create a `.env` file in the workspace root:

```env
# Service configuration
DEBUG=false
LOG_LEVEL=INFO

# Redis
REDIS_URL=redis://localhost:6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Service URLs
BROWSER_SERVICE_URL=http://localhost:8001
SCRAPING_SERVICE_URL=http://localhost:8002
```

## 📖 Shared Libraries

### crawl4ai-core

Core models, utilities, and configuration.

```python
from crawl4ai_core import CrawlRequest, CrawlResult, Settings
from crawl4ai_core.utils import generate_id, sanitize_url
```

### crawl4ai-schemas

API request/response models for all services.

```python
from crawl4ai_schemas import (
    BrowserRequest,
    BrowserResponse,
    ScrapingRequest,
    ScrapingResponse,
)
```

### crawl4ai-client

HTTP clients for all microservices.

```python
from crawl4ai_client import (
    BrowserClient,
    ScrapingClient,
    ExtractionClient,
    FilteringClient,
)
```

## 🚢 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guides.

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

**Built with ❤️ using [uv](https://github.com/astral-sh/uv) - The fastest Python package manager**
