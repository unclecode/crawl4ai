# ---------- Dockerfile ----------
    FROM alpine:latest

    # Combine everything in one RUN to keep layers minimal.
    RUN apk update && apk upgrade && \
        apk add --no-cache \
            chromium \
            nss \
            freetype \
            harfbuzz \
            ca-certificates \
            ttf-freefont \
            socat \
            curl && \
        addgroup -S chromium && adduser -S chromium -G chromium && \
        mkdir -p /data && chown chromium:chromium /data && \
        rm -rf /var/cache/apk/*
    
    # Copy start script, then chown/chmod in one step
    COPY start.sh /home/chromium/start.sh
    RUN chown chromium:chromium /home/chromium/start.sh && \
        chmod +x /home/chromium/start.sh
    
    USER chromium
    WORKDIR /home/chromium
    
    # Expose port used by socat (mapping 9222→9223 or whichever you prefer)
    EXPOSE 9223
    
    # Simple healthcheck: is the remote debug endpoint responding?
    HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:9222/json/version || exit 1
    
    CMD ["./start.sh"]
    