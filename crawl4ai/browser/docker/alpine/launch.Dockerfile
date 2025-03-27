# ---------- Dockerfile (Idle Version) ----------
    FROM alpine:latest

    # Install only Chromium and its dependencies in a single layer
    RUN apk update && apk upgrade && \
        apk add --no-cache \
            chromium \
            nss \
            freetype \
            harfbuzz \
            ca-certificates \
            ttf-freefont && \
        addgroup -S chromium && adduser -S chromium -G chromium && \
        mkdir -p /data && chown chromium:chromium /data && \
        rm -rf /var/cache/apk/*
    
    # Switch to a non-root user for security
    USER chromium
    WORKDIR /home/chromium
    
    # Idle: container does nothing except stay alive
    CMD ["tail", "-f", "/dev/null"]
    