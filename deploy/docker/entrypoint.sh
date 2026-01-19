#!/bin/bash
# Crawl4AI Docker Entrypoint
# Handles conditional embedded Redis startup based on CRAWL4AI_DISABLE_EMBEDDED_REDIS

set -e

# If CRAWL4AI_DISABLE_EMBEDDED_REDIS is set to true, modify supervisord.conf
# to remove the Redis program section
if [ "${CRAWL4AI_DISABLE_EMBEDDED_REDIS}" = "true" ]; then
    echo "External Redis mode: Disabling embedded Redis server"

    # Create a modified supervisord.conf without Redis
    cat > /tmp/supervisord.conf << 'EOF'
[supervisord]
nodaemon=true
logfile=/dev/null
logfile_maxbytes=0

[program:gunicorn]
command=/usr/local/bin/gunicorn --bind 0.0.0.0:11235 --workers 1 --threads 4 --timeout 1800 --graceful-timeout 30 --keep-alive 300 --log-level info --worker-class uvicorn.workers.UvicornWorker server:app
directory=/app
user=appuser
autorestart=true
priority=20
environment=PYTHONUNBUFFERED=1
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
EOF

    exec supervisord -c /tmp/supervisord.conf
else
    # Default: use the original supervisord.conf with embedded Redis
    exec supervisord -c supervisord.conf
fi
