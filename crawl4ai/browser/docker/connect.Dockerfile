FROM ubuntu:22.04

# Install dependencies with comprehensive Chromium support
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    # Core dependencies
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libx11-6 \
    libxcb1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libnss3 \
    libnspr4 \
    libglib2.0-0 \
    # Utilities
    xdg-utils \
    socat \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Install Chromium with codecs
RUN apt-get update && \
    apt-get install -y \
    chromium-browser \
    chromium-codecs-ffmpeg-extra \
    && rm -rf /var/lib/apt/lists/*

# Create Chrome alias for compatibility
RUN ln -s /usr/bin/chromium-browser /usr/bin/google-chrome

# Create data directory
RUN mkdir -p /data && chmod 777 /data

# Add startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]