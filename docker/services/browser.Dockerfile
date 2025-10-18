FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy workspace files
COPY workspace-pyproject.toml pyproject.toml
COPY uv.lock* ./

# Copy service and shared libraries
COPY services/browser-service ./services/browser-service
COPY shared ./shared

# Install dependencies using uv
RUN uv sync --frozen --no-dev --package crawl4ai-browser-service

# Install playwright browsers
RUN uv run --package crawl4ai-browser-service playwright install chromium --with-deps

# Expose service port
EXPOSE 8000

# Run service
CMD ["uv", "run", "--package", "crawl4ai-browser-service", "uvicorn", "browser_service.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
