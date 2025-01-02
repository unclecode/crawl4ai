FROM python:3.10-slim

# System dependencies for Playwright/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
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
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Install crawl4ai and setup
RUN pip install crawl4ai
RUN crawl4ai-setup

# Add startup script
RUN echo '#!/bin/bash\n\
/root/.cache/ms-playwright/chromium-1148/chrome-linux/chrome \
  --remote-debugging-port=9222 \
  --no-sandbox \
  --headless=new \
  --disable-gpu &\n\
sleep 2\n\
socat TCP-LISTEN:9223,fork,reuseaddr TCP:127.0.0.1:9222\n' > /start.sh && \
    chmod +x /start.sh

EXPOSE 9223
CMD ["/start.sh"]
