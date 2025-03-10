FROM python:3.12-bookworm AS python-builder

RUN pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry export -f requirements.txt -o requirements.txt

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    python3-pip \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install specific dependencies that have build issues
RUN pip install --no-cache-dir cchardet

FROM python:3.12-bookworm

# Install AWS Lambda Runtime Interface Client
RUN python3 -m pip install --no-cache-dir awslambdaric

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

# Install build essentials for any compilations needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up function directory and browser path
ARG FUNCTION_DIR="/function"
RUN mkdir -p "${FUNCTION_DIR}/pw-browsers"
RUN mkdir -p "/tmp/.crawl4ai"

# Set critical environment variables
ENV PLAYWRIGHT_BROWSERS_PATH="${FUNCTION_DIR}/pw-browsers" \
    HOME="/tmp" \
    CRAWL4_AI_BASE_DIRECTORY="/tmp/.crawl4ai"

# Create Craw4ai base directory
RUN mkdir -p ${CRAWL4_AI_BASE_DIRECTORY}

RUN pip install --no-cache-dir faust-cchardet

# Install Crawl4ai and dependencies
RUN pip install --no-cache-dir git+https://github.com/unclecode/crawl4ai.git@next

# Install Chromium only (no deps flag)
RUN playwright install chromium

# Copy function code
COPY lambda_function.py ${FUNCTION_DIR}/

# Set working directory
WORKDIR ${FUNCTION_DIR}

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "lambda_function.handler" ]