# Use Debian 12 (Bookworm) slim for a small, stable base image
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install Chromium, socat, and basic fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    wget \
    curl \
    socat \
    fonts-freefont-ttf \
    fonts-noto-color-emoji && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy start.sh and make it executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose socat port (use host mapping, e.g. -p 9225:9223)
EXPOSE 9223

ENTRYPOINT ["/start.sh"]
