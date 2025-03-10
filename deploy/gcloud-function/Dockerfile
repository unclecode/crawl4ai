FROM --platform=linux/amd64 python:3.10-slim

# Install system dependencies required for Chromium and Git
RUN apt-get update && apt-get install -y \
    python3-dev \
    pkg-config \
    libjpeg-dev \
    gcc \
    build-essential \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    procps \
    git \
    socat \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Make a directory for crawl4ai call it crawl4ai_repo
# RUN mkdir crawl4ai_repo

# # Clone Crawl4ai from the next branch and install it
# RUN git clone --branch next https://github.com/unclecode/crawl4ai.git ./crawl4ai_repo \
#     && cd crawl4ai_repo \
#     && pip install . \
#     && cd .. \
#     && rm -rf crawl4ai_repo

RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
# RUN pip install git+https://github.com/unclecode/crawl4ai.git@next
   
# Copy requirements and install remaining dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY resources /app/resources
COPY main.py .
COPY start.sh .

# Set permissions for Chrome binary and start script
RUN chmod +x /app/resources/chrome/headless_shell && \
    chmod -R 755 /app/resources/chrome && \
    chmod +x start.sh

ENV FUNCTION_TARGET=crawl
EXPOSE 8080 9223

CMD ["/app/start.sh"]