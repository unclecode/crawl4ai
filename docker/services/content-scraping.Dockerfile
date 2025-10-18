FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy workspace files
COPY workspace-pyproject.toml pyproject.toml
COPY uv.lock* ./

# Copy service and shared libraries
COPY services/content-scraping-service ./services/content-scraping-service
COPY shared ./shared

# Install dependencies using uv
RUN uv sync --frozen --no-dev --package crawl4ai-content-scraping-service

# Expose service port
EXPOSE 8002

# Run service
CMD ["uv", "run", "--package", "crawl4ai-content-scraping-service", "uvicorn", "content_scraping_service.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8002"]
