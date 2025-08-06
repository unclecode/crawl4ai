# Docker Testing Guidelines for Elisp Projects

## Overview

Docker provides a consistent, reproducible environment for testing Elisp code across different Emacs versions and configurations. This guide covers both Docker and Apptainer (formerly Singularity) approaches for containerized testing.

## Why Use Container-Based Testing?

1. **Reproducibility**: Ensures tests run in identical environments
2. **Cross-Version Testing**: Test against multiple Emacs versions easily
3. **Clean Environment**: No interference from local Emacs configuration
4. **CI/CD Integration**: Seamless integration with continuous integration pipelines
5. **Dependency Isolation**: Manage package dependencies without affecting local setup

## Using elisp-ci with Docker

The `elisp-ci` tool provides built-in Docker support for Elisp testing:

### Basic Docker Commands

```bash
# Build Docker image for testing
elisp-ci docker-build

# Run tests in Docker container
elisp-ci docker-test

# Test with specific Emacs version
elisp-ci docker-test --emacs-version 28.2

# Test with multiple versions
elisp-ci docker-test --emacs-version 27.2,28.2,29.1
```

### Creating a Dockerfile for Elisp Testing

```dockerfile
# Basic Dockerfile for Elisp testing
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    emacs \
    git \
    make \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Cask or other package managers if needed
RUN curl -fsSL https://raw.githubusercontent.com/cask/cask/master/go | python

# Run tests
CMD ["make", "test"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml for multi-version testing
version: '3.8'

services:
  emacs-27:
    build:
      context: .
      dockerfile: Dockerfile.emacs27
    command: make test
    
  emacs-28:
    build:
      context: .
      dockerfile: Dockerfile.emacs28
    command: make test
    
  emacs-29:
    build:
      context: .
      dockerfile: Dockerfile.emacs29
    command: make test
```

## Apptainer (Singularity) Workaround

Apptainer is often preferred in HPC environments where Docker requires root privileges. Here's how to use Apptainer for Elisp testing:

### Converting Docker Images to Apptainer

```bash
# Pull Docker image and convert to Apptainer
apptainer pull docker://ubuntu:22.04

# Build from Docker image
apptainer build emacs-test.sif docker://silex/emacs:28.2
```

### Apptainer Definition File

```singularity
# emacs-test.def
Bootstrap: docker
From: ubuntu:22.04

%post
    apt-get update && apt-get install -y \
        emacs \
        git \
        make \
        curl \
        ca-certificates
    
    # Install Cask
    curl -fsSL https://raw.githubusercontent.com/cask/cask/master/go | python
    
    # Clean up
    apt-get clean
    rm -rf /var/lib/apt/lists/*

%environment
    export PATH=/root/.cask/bin:$PATH

%runscript
    cd /app
    make test

%labels
    Author your-name
    Version 1.0
```

### Using Apptainer for Testing

```bash
# Build the container
apptainer build emacs-test.sif emacs-test.def

# Run tests with bind mount
apptainer run --bind $(pwd):/app emacs-test.sif

# Interactive shell for debugging
apptainer shell --bind $(pwd):/app emacs-test.sif
```

### Apptainer with elisp-ci

Since elisp-ci doesn't natively support Apptainer, create a wrapper script:

```bash
#!/bin/bash
# apptainer-elisp-test.sh

# Convert Docker image name to Apptainer
EMACS_VERSION=${1:-28.2}
IMAGE_NAME="emacs-${EMACS_VERSION}.sif"

# Build if not exists
if [ ! -f "$IMAGE_NAME" ]; then
    apptainer build "$IMAGE_NAME" "docker://silex/emacs:${EMACS_VERSION}"
fi

# Run tests
apptainer exec --bind $(pwd):/workspace "$IMAGE_NAME" \
    bash -c "cd /workspace && make test"
```

## Best Practices

1. **Version Matrix Testing**: Always test against multiple Emacs versions
2. **Minimal Images**: Use alpine-based images when possible for faster builds
3. **Layer Caching**: Structure Dockerfiles to maximize layer reuse
4. **CI Integration**: Use container testing in GitHub Actions/GitLab CI
5. **Local Development**: Provide both Docker and native testing options

## Example Integration

### Makefile Integration

```makefile
# Test targets
.PHONY: test test-docker test-apptainer

test:
	./run_tests.sh

test-docker:
	elisp-ci docker-test

test-apptainer:
	./apptainer-elisp-test.sh 28.2
	./apptainer-elisp-test.sh 29.1

test-all: test test-docker test-apptainer
```

### GitHub Actions with Containers

```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        emacs-version: [27.2, 28.2, 29.1]
    
    container:
      image: silex/emacs:${{ matrix.emacs-version }}
    
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: make test
```

## Troubleshooting

### Docker Issues
- **Permission Denied**: Use `--user $(id -u):$(id -g)` flag
- **Network Issues**: Use `--network host` for package downloads
- **Volume Mounting**: Ensure proper bind mount permissions

### Apptainer Issues
- **Bind Mount Failures**: Check directory permissions and SELinux context
- **Image Build Failures**: Ensure sufficient disk space in `/tmp`
- **Environment Variables**: Use `--env` or `%environment` section

## Summary

Container-based testing ensures reproducible, cross-version testing for Elisp projects. While Docker is more common, Apptainer provides a rootless alternative suitable for HPC environments. Choose based on your infrastructure constraints and security requirements.

Key commands:
- Docker: `elisp-ci docker-test`
- Apptainer: `apptainer run --bind $(pwd):/app emacs-test.sif`

Both approaches achieve the same goal: consistent, isolated testing environments for Elisp code.