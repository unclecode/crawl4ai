# Set build arguments
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.6.6 \
    PYTHON_IMAGE=python:3.10-slim \
    BUILD_ENV=local

# Create an alias for the UV image so we can reference it in the base stage.
FROM ${UV_IMAGE} AS uv

FROM ${PYTHON_IMAGE} AS base
COPY --from=uv /uv /uvx /bin/

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

ARG \
    TARGETARCH \
    ENABLE_GPU=false

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

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

COPY --link . /tmp/project/

COPY deploy/docker/requirements.txt deploy/docker/supervisord.conf ./

# Install the docker dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --upgrade pip -r requirements.txt

# Install the dependencies for the specified install type.
ARG INSTALL_TYPE=default
RUN --mount=type=cache,target=/root/.cache/uv \
    GROUP=$([ "$INSTALL_TYPE" = "default" ] && echo "" || echo "[$INSTALL_TYPE]") ; \
    uv pip install "/tmp/project/$GROUP"

# If the install type is all or transformer, download the models.
RUN --mount=type=cache,target=/tmp/.cache/huggingface \
    --mount=type=cache,target=/tmp/.cache/nltk \
if [ "$INSTALL_TYPE" = "all" ] || [ "$INSTALL_TYPE" = "transformer" ] ; then \
    NLTK_DATA=/tmp/.cache/nltk \
    HF_HOME=/tmp/.cache/huggingface \
    python -m crawl4ai.model_loader && \
    mkdir -p /root/.cache && \
    rm -rf /root/.cache/ms-playwright/ /root/nltk_data/ && \
    cp -R /tmp/.cache/nltk/ /root/nltk_data/ && \
    cp -R /tmp/.cache/huggingface/ /root/.cache/huggingface/ ; \
fi

# Install from local source.
FROM base AS local
RUN --mount=type=cache,target=/root/.cache/uv \
    echo "📦 Installing from local source..." ; \
    uv pip install /tmp/project/

# Install from GitHub.
FROM base AS github
ARG \
    GITHUB_REPO=https://github.com/unclecode/crawl4ai.git \
    GITHUB_BRANCH=main
RUN --mount=type=cache,target=/root/.cache/uv \
    echo "🌐 Installing from GitHub..." ; \
    for i in {1..3}; do \
        git clone --depth 1 --branch ${GITHUB_BRANCH} ${GITHUB_REPO} /tmp/crawl4ai && break || \
        { echo "Attempt $i/3 failed! Taking a short break... ☕"; sleep 5; }; \
    done ; \
    uv pip install /tmp/crawl4ai

FROM ${BUILD_ENV} AS final

# Test the installation.
RUN \
    python -c "import crawl4ai; print('✅ crawl4ai is ready to rock!')" && \
    python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright is feeling dramatic!')"

# Install Playwright browsers.
RUN --mount=type=cache,target=/tmp/.cache/ms-playwright \
    PLAYWRIGHT_BROWSERS_PATH=/tmp/.cache/ms-playwright playwright install --no-shell chromium && \
    mkdir -p /root/.cache && \
    rm -rf /root/.cache/ms-playwright/ && \
    cp -R /tmp/.cache/ms-playwright/ /root/.cache/ms-playwright/

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

