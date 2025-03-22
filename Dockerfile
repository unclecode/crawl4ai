ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.6.6
ARG PYTHON_IMAGE=python:3.10-slim

# Create an alias for the UV image so we can reference it in the builder stage.
FROM ${UV_IMAGE} AS uv

ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE} AS builder
COPY --from=uv /uv /uvx /bin/

# Set build arguments
ARG \
    APP_HOME=/app \
    GITHUB_REPO=https://github.com/unclecode/crawl4ai.git \
    GITHUB_BRANCH=main \
    USE_LOCAL=true \
    PYTHON_VERSION=3.10 \
    INSTALL_TYPE=default \
    ENABLE_GPU=false \
    TARGETARCH

# Enable bytecode compilation during build to improve runtime
# performance, set the link mode to copy to avoid warnings
# with the default mode.
ENV \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    DEBIAN_FRONTEND=noninteractive \
    REDIS_HOST=localhost \
    REDIS_PORT=6379 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1 \
    PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=120000

LABEL \
    maintainer="unclecode" \
    description="🔥🕷️ Crawl4AI: Open-source LLM Friendly Web Crawler & scraper" \
    version="1.0"

# Install dependencies with caching to speed up the build process.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    wget \
    gnupg \
    git \
    cmake \
    pkg-config \
    python3-dev \
    libjpeg-dev \
    redis-server \
    supervisor \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
if [ "$ENABLE_GPU" = "true" ] && [ "$TARGETARCH" = "amd64" ] ; then \
    apt-get install -y --no-install-recommends \
    nvidia-cuda-toolkit; \
else \
    echo "Skipping NVIDIA CUDA Toolkit installation (unsupported platform or GPU disabled)"; \
fi

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
if [ "$TARGETARCH" = "arm64" ]; then \
    echo "🦾 Installing ARM-specific optimizations"; \
    apt-get install -y --no-install-recommends \
    libopenblas-dev; \
elif [ "$TARGETARCH" = "amd64" ]; then \
    echo "🖥️ Installing AMD64-specific optimizations"; \
    apt-get install -y --no-install-recommends \
    libomp-dev; \
else \
    echo "Skipping platform-specific optimizations (unsupported platform ${TARGET_ARCH})"; \
fi

WORKDIR ${APP_HOME}

RUN echo '#!/bin/bash\n\
if [ "$USE_LOCAL" = "true" ]; then\n\
    echo "📦 Installing from local source..."\n\
    uv pip install /tmp/project/\n\
else\n\
    echo "🌐 Installing from GitHub..."\n\
    for i in {1..3}; do \n\
        git clone --branch ${GITHUB_BRANCH} ${GITHUB_REPO} /tmp/crawl4ai && break || \n\
        { echo "Attempt $i/3 failed! Taking a short break... ☕"; sleep 5; }; \n\
    done\n\
    uv pip install /tmp/crawl4ai\n\
fi' > /tmp/install.sh && chmod +x /tmp/install.sh

COPY --link . /tmp/project/

COPY deploy/docker/requirements.txt deploy/docker/supervisord.conf ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --upgrade pip -r requirements.txt

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/tmp/.cache/huggingface \
    --mount=type=cache,target=/tmp/.cache/nltk \
if [ "$INSTALL_TYPE" = "all" ] ; then \
    uv pip install --directory /tmp/project .[all] && \
    NLTK_DATA=/tmp/.cache/nltk python -m nltk.downloader punkt stopwords && \
    cp -r /tmp/.cache/nltk /root/nltk_data && \
    HF_HOME=/tmp/.cache/huggingface python -m crawl4ai.model_loader && \
    cp -r /tmp/.cache/huggingface /root/.cache/huggingface ; \
elif [ "$INSTALL_TYPE" = "torch" ] ; then \
    uv pip install --project /tmp/project .[torch] && \
    NLTK_DATA=/tmp/.cache/nltk python -m nltk.downloader punkt stopwords && \
    cp -r /tmp/.cache/nltk /root/nltk_data ; \
elif [ "$INSTALL_TYPE" = "transformer" ] ; then \
    uv pip install --project /tmp/project .[transformer] && \
    HF_HOME=/tmp/.cache/huggingface python -m crawl4ai.model_loader && \
    cp -r /tmp/.cache/huggingface /root/.cache/huggingface ; \
else \
    uv pip install --directory /tmp/project .; \
fi

RUN --mount=type=cache,target=/root/.cache/uv \
    /tmp/install.sh && \
    python -c "import crawl4ai; print('✅ crawl4ai is ready to rock!')" && \
    python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright is feeling dramatic!')"

# Install Playwright browsers with caching to speed up the build process.
RUN --mount=type=cache,target=/tmp/.cache/ms-playwright \
    PLAYWRIGHT_BROWSERS_PATH=/tmp/.cache/ms-playwright playwright install --no-shell chromium && \
    cp -r /tmp/.cache/ms-playwright /root/.cache/ms-playwright

COPY deploy/docker/* ${APP_HOME}/

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD bash -c '\
    MEM=$(free -m | awk "/^Mem:/{print \$2}"); \
    if [ $MEM -lt 2048 ]; then \
        echo "⚠️ Warning: Less than 2GB RAM available! Your container might need a memory boost! 🚀"; \
        exit 1; \
    fi && \
    redis-cli ping > /dev/null && \
    curl -f http://localhost:8000/health || exit 1'

EXPOSE 6379
CMD ["supervisord", "-c", "supervisord.conf"]

