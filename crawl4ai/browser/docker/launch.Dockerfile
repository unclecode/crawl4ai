FROM ubuntu:22.04

# Install dependencies with comprehensive Chromium support
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    # Sound support
    libasound2 \
    # Accessibility support
    libatspi2.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    # Graphics and rendering
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    # X11 and window system
    libx11-6 \
    libxcb1 \
    libxkbcommon0 \
    # Text and internationalization
    libpango-1.0-0 \
    libcairo2 \
    # Printing support
    libcups2 \
    # System libraries
    libdbus-1-3 \
    libnss3 \
    libnspr4 \
    libglib2.0-0 \
    # Utilities
    xdg-utils \
    socat \
    # Process management
    procps \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Create data directory for user data
RUN mkdir -p /data && chmod 777 /data

# Keep container running without starting Chrome
CMD ["tail", "-f", "/dev/null"]