FROM python:3.10-slim

# Set build arguments
ARG APP_HOME=/app
ARG GITHUB_REPO=https://github.com/unclecode/crawl4ai.git
ARG GITHUB_BRANCH=next
ARG USE_LOCAL=False
ARG CONFIG_PATH=""

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    DEBIAN_FRONTEND=noninteractive \
    REDIS_HOST=localhost \
    REDIS_PORT=6379

ARG PYTHON_VERSION=3.10
ARG INSTALL_TYPE=default
ARG ENABLE_GPU=false
ARG TARGETARCH

LABEL maintainer="unclecode"
LABEL description="🔥🕷️ Crawl4AI: Open-source LLM Friendly Web Crawler & scraper"
LABEL version="1.0"    

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    gnupg \
    git \
    cmake \
    pkg-config \
    python3-dev \
    libjpeg-dev \
    redis-server \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
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
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$ENABLE_GPU" = "true" ] && [ "$TARGETARCH" = "amd64" ] ; then \
    apt-get update && apt-get install -y --no-install-recommends \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/* ; \
else \
    echo "Skipping NVIDIA CUDA Toolkit installation (unsupported platform or GPU disabled)"; \
fi

RUN if [ "$TARGETARCH" = "arm64" ]; then \
    echo "🦾 Installing ARM-specific optimizations"; \
    apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*; \
elif [ "$TARGETARCH" = "amd64" ]; then \
    echo "🖥️ Installing AMD64-specific optimizations"; \
    apt-get update && apt-get install -y --no-install-recommends \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*; \
else \
    echo "Skipping platform-specific optimizations (unsupported platform)"; \
fi

WORKDIR ${APP_HOME}

RUN git clone --branch ${GITHUB_BRANCH} ${GITHUB_REPO} /tmp/crawl4ai

COPY docker/supervisord.conf .
COPY docker/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN if [ "$INSTALL_TYPE" = "all" ] ; then \
        pip install "/tmp/crawl4ai/[all]" && \
        python -m nltk.downloader punkt stopwords && \
        python -m crawl4ai.model_loader ; \
    elif [ "$INSTALL_TYPE" = "torch" ] ; then \
        pip install "/tmp/crawl4ai/[torch]" ; \
    elif [ "$INSTALL_TYPE" = "transformer" ] ; then \
        pip install "/tmp/crawl4ai/[transformer]" && \
        python -m crawl4ai.model_loader ; \
    else \
        pip install "/tmp/crawl4ai" ; \
    fi
    
RUN pip install --no-cache-dir --upgrade pip && \
    python -c "import crawl4ai; print('✅ crawl4ai is ready to rock!')" && \
    python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright is feeling dramatic!')"
    
RUN playwright install --with-deps chromium

COPY docker/* ${APP_HOME}/
RUN if [ -n "$CONFIG_PATH" ] && [ -f "$CONFIG_PATH" ]; then \
    echo "Using custom config from $CONFIG_PATH" && \
    cp $CONFIG_PATH /app/config.yml; \
fi

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD bash -c '\
    MEM=$(free -m | awk "/^Mem:/{print \$2}"); \
    if [ $MEM -lt 2048 ]; then \
        echo "⚠️ Warning: Less than 2GB RAM available! Your container might need a memory boost! 🚀"; \
        exit 1; \
    fi && \
    redis-cli ping > /dev/null && \
    curl -f http://localhost:8000/health || exit 1'

# EXPOSE 6379

CMD ["supervisord", "-c", "supervisord.conf"]
    
