# First stage: Build and install dependencies
FROM python:3.10-slim-bookworm

# Set the working directory in the container
WORKDIR /usr/src/app

# Define build arguments
ARG INSTALL_OPTION=default

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    git \
    curl \
    unzip \
    gnupg \
    xvfb \
    ca-certificates \
    apt-transport-https \
    software-properties-common && \
    rm -rf /var/lib/apt/lists/*    

# Copy the application code
COPY . .

# Install Crawl4AI using the local setup.py with the specified option
# and download models only for torch, transformer, or all options
RUN if [ "$INSTALL_OPTION" = "all" ]; then \
        pip install --no-cache-dir .[all] && \
        crawl4ai-download-models; \
    elif [ "$INSTALL_OPTION" = "torch" ]; then \
        pip install --no-cache-dir .[torch] && \
        crawl4ai-download-models; \
    elif [ "$INSTALL_OPTION" = "transformer" ]; then \
        pip install --no-cache-dir .[transformer] && \
        crawl4ai-download-models; \
    else \
        pip install --no-cache-dir .; \
    fi

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# Set environment to use Chrome properly
ENV CHROME_BIN=/usr/bin/google-chrome \
    DISPLAY=:99 \
    DBUS_SESSION_BUS_ADDRESS=/dev/null \
    PYTHONUNBUFFERED=1

# Ensure the PATH environment variable includes the location of the installed packages
ENV PATH=/opt/conda/bin:$PATH   

# Make port 80 available to the world outside this container
EXPOSE 80

# Install mkdocs
RUN pip install mkdocs mkdocs-terminal

# Call mkdocs to build the documentation
RUN mkdocs build

# Run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4"]