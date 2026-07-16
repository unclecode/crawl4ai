# GitHub Actions Workflows Documentation

## Table of Contents

1. [Overview](#overview)
2. [Workflow Architecture](#workflow-architecture)
3. [Workflows](#workflows)
   - [Release Pipeline](#release-pipeline)
   - [Docker Release](#docker-release)
4. [Usage Guide](#usage-guide)
5. [Secrets Configuration](#secrets-configuration)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Topics](#advanced-topics)

---

## Overview

This repository uses a **split release pipeline** architecture to optimize release times and provide flexibility. The release process is divided into two independent workflows:

1. **Release Pipeline** (`release.yml`) - Fast PyPI and GitHub release publication
2. **Docker Release** (`docker-release.yml`) - Multi-architecture Docker image builds with caching

### Why Split Workflows?

**Problem**: Docker multi-architecture builds take 10-15 minutes, blocking quick package releases.

**Solution**: Separate Docker builds into an independent workflow that runs in parallel.

**Benefits**:
- ✅ PyPI package available in ~2-3 minutes
- ✅ GitHub release published immediately
- ✅ Docker images build in parallel (non-blocking)
- ✅ Can rebuild Docker images independently
- ✅ Faster subsequent builds with layer caching

---

## Workflow Architecture

```
Tag Push (v1.2.3)
    │
    ├─► Release Pipeline (release.yml)
    │   ├─ Version validation
    │   ├─ Build Python package
    │   ├─ Upload to PyPI ✓
    │   └─ Create GitHub Release ✓
    │       │
    │       └─► Triggers Docker Release (docker-release.yml)
    │           ├─ Build multi-arch images
    │           ├─ Use GitHub Actions cache
    │           └─ Push to Docker Hub ✓
    │
    └─► Total Time:
        - PyPI/GitHub: 2-3 minutes
        - Docker: 1-15 minutes (parallel)
```

### Event Flow

```mermaid
graph TD
    A[Push tag v1.2.3] --> B[release.yml triggered]
    B --> C{Version Check}
    C -->|Match| D[Build Package]
    C -->|Mismatch| E[❌ Fail - Update __version__.py]
    D --> F[Upload to PyPI]
    F --> G[Create GitHub Release]
    G --> H[docker-release.yml triggered]
    H --> I[Build Docker Images]
    I --> J[Push to Docker Hub]

    K[Push tag docker-rebuild-v1.2.3] --> H
```

---

## Workflows

### Release Pipeline

**File**: `.github/workflows/release.yml`

#### Trigger

```yaml
on:
  push:
    tags:
      - 'v*'           # Matches: v1.2.3, v2.0.0, etc.
      - '!test-v*'     # Excludes: test-v1.2.3
```

#### Jobs & Steps

##### 1. Version Extraction
```bash
# Extracts version from tag
v1.2.3 → 1.2.3
```

##### 2. Version Consistency Check
Validates that the git tag matches `crawl4ai/__version__.py`:

```python
# crawl4ai/__version__.py must contain:
__version__ = "1.2.3"  # Must match tag v1.2.3
```

**Failure Example**:
```
Tag version: 1.2.3
Package version: 1.2.2
❌ Version mismatch! Please update crawl4ai/__version__.py
```

##### 3. Package Build
- Installs build dependencies (`build`, `twine`)
- Builds source distribution and wheel: `python -m build`
- Validates package: `twine check dist/*`

##### 4. PyPI Upload
```bash
twine upload dist/*
# Uploads to: https://pypi.org/project/crawl4ai/
```

**Environment Variables**:
- `TWINE_USERNAME`: `__token__` (PyPI API token authentication)
- `TWINE_PASSWORD`: `${{ secrets.PYPI_TOKEN }}`

##### 5. GitHub Release Creation
Creates a release with:
- Tag: `v1.2.3`
- Title: `Release v1.2.3`
- Body: Installation instructions + changelog link
- Status: Published (not draft)

**Note**: The release body includes a link to the Docker workflow status, informing users that Docker images are building.

##### 6. Summary Report
Generates a GitHub Actions summary with:
- PyPI package URL and version
- GitHub release URL
- Link to Docker workflow status

#### Output Artifacts

| Artifact | Location | Time |
|----------|----------|------|
| PyPI Package | https://pypi.org/project/crawl4ai/ | ~2-3 min |
| GitHub Release | Repository releases page | ~2-3 min |

---

### Docker Release

**File**: `.github/workflows/docker-release.yml`

#### Triggers

This workflow has **two independent triggers**:

##### 1. Automatic Trigger (Release Event)
```yaml
on:
  release:
    types: [published]
```

Triggers when `release.yml` publishes a GitHub release.

##### 2. Manual Trigger (Docker Rebuild Tag)
```yaml
on:
  push:
    tags:
      - 'docker-rebuild-v*'
```

Allows rebuilding Docker images without creating a new release.

**Use case**: Fix Dockerfile, rebuild images for existing version.

#### Jobs & Steps

##### 1. Version Detection
Intelligently detects version from either trigger:

```bash
# From release event:
github.event.release.tag_name → v1.2.3 → 1.2.3

# From docker-rebuild tag:
docker-rebuild-v1.2.3 → 1.2.3
```

##### 2. Semantic Version Extraction
```bash
VERSION=1.2.3
MAJOR=1         # First component
MINOR=1.2       # First two components
```

Used for Docker tag variations.

##### 3. Docker Buildx Setup
Configures multi-architecture build support:
- Platform: linux/amd64, linux/arm64
- Builder: Buildx with QEMU emulation

##### 4. Docker Hub Authentication
```yaml
username: ${{ secrets.DOCKER_USERNAME }}
password: ${{ secrets.DOCKER_TOKEN }}
```

##### 5. Multi-Architecture Build & Push

**Docker Tags Created**:
```
unclecode/crawl4ai:1.2.3    # Exact version
unclecode/crawl4ai:1.2      # Minor version
unclecode/crawl4ai:1        # Major version
unclecode/crawl4ai:latest   # Latest stable
```

**Platforms**:
- `linux/amd64` (x86_64 - Intel/AMD processors)
- `linux/arm64` (ARM processors - Apple Silicon, AWS Graviton)

**Caching Configuration**:
```yaml
cache-from: type=gha          # Read from GitHub Actions cache
cache-to: type=gha,mode=max   # Write all layers to cache
```

##### 6. Summary Report
Generates a summary with:
- Published image tags
- Supported platforms
- Pull command example

#### Docker Layer Caching

**How It Works**:

Docker builds images in layers:
```dockerfile
FROM python:3.12           # Layer 1 (base image)
RUN apt-get update         # Layer 2 (system packages)
COPY requirements.txt .    # Layer 3 (dependency file)
RUN pip install -r ...     # Layer 4 (Python packages)
COPY . .                   # Layer 5 (application code)
```

**Cache Behavior**:

| Change Type | Cached Layers | Rebuild Time |
|-------------|---------------|--------------|
| No changes | 1-5 | ~30-60 sec |
| Code only | 1-4 | ~1-2 min |
| Dependencies | 1-3 | ~3-5 min |
| Dockerfile | None | ~10-15 min |

**Cache Storage**:
- Location: GitHub Actions cache
- Limit: 10GB per repository
- Retention: 7 days for unused cache
- Cleanup: Automatic (LRU eviction)

**Cache Efficiency Example**:

```bash
# First build (v1.0.0)
Build time: 12m 34s
Cache: 0% (cold start)

# Second build (v1.0.1 - code change only)
Build time: 1m 47s
Cache: 85% hit rate
Cached: Base image, system packages, Python dependencies

# Third build (v1.0.2 - dependency update)
Build time: 4m 12s
Cache: 60% hit rate
Cached: Base image, system packages
```

#### Output Artifacts

| Artifact | Location | Tags | Time |
|----------|----------|------|------|
| Docker Images | Docker Hub | 4 tags | 1-15 min |

**Docker Hub URL**: https://hub.docker.com/r/unclecode/crawl4ai

---

## Usage Guide

### Standard Release Process

#### Step 1: Update Version

Edit `crawl4ai/__version__.py`:
```python
__version__ = "1.2.3"
```

#### Step 2: Commit and Tag

```bash
git add crawl4ai/__version__.py
git commit -m "chore: bump version to 1.2.3"
git tag v1.2.3
git push origin main
git push origin v1.2.3
```

#### Step 3: Monitor Workflows

**Release Pipeline** (~2-3 minutes):
```
✓ Version check passed
✓ Package built
✓ Uploaded to PyPI
✓ GitHub release created
```

**Docker Release** (~1-15 minutes, runs in parallel):
```
✓ Images built for amd64, arm64
✓ Pushed 4 tags to Docker Hub
✓ Cache updated
```

#### Step 4: Verify Deployment

```bash
# Check PyPI
pip install crawl4ai==1.2.3

# Check Docker
docker pull unclecode/crawl4ai:1.2.3
docker run unclecode/crawl4ai:1.2.3 --version
```

### Manual Docker Rebuild

**When to Use**:
- Dockerfile fixed after release
- Security patch in base image
- Rebuild needed without new version

**Process**:

```bash
# Rebuild Docker images for existing version 1.2.3
git tag docker-rebuild-v1.2.3
git push origin docker-rebuild-v1.2.3
```

This triggers **only** `docker-release.yml`, not `release.yml`.

**Result**:
- Docker images rebuilt with same version tag
- PyPI package unchanged
- GitHub release unchanged

### Rollback Procedure

#### Rollback PyPI Package
PyPI does not allow re-uploading the same version. Instead:

```bash
# Publish a patch version
git tag v1.2.4
git push origin v1.2.4
```

Then update documentation to recommend the new version.

#### Rollback Docker Images

```bash
# Option 1: Rebuild with fixed code
git tag docker-rebuild-v1.2.3
git push origin docker-rebuild-v1.2.3

# Option 2: Manually retag in Docker Hub (advanced)
# Not recommended - use git tags for traceability
```

---

## Secrets Configuration

### Required Secrets

Configure these in: **Repository Settings → Secrets and variables → Actions**

#### 1. PYPI_TOKEN

**Purpose**: Authenticate with PyPI for package uploads

**How to Create**:
1. Go to https://pypi.org/manage/account/token/
2. Create token with scope: "Entire account" or "Project: crawl4ai"
3. Copy token (starts with `pypi-`)
4. Add to GitHub secrets as `PYPI_TOKEN`

**Format**:
```
pypi-AgEIcHlwaS5vcmcCJGQ4M2Y5YTM5LWRjMzUtNGY3MS04ZmMwLWVhNzA5MjkzMjk5YQACKl...
```

#### 2. DOCKER_USERNAME

**Purpose**: Docker Hub username for authentication

**Value**: Your Docker Hub username (e.g., `unclecode`)

#### 3. DOCKER_TOKEN

**Purpose**: Docker Hub access token for authentication

**How to Create**:
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name: `github-actions-crawl4ai`
4. Permissions: Read, Write, Delete
5. Copy token
6. Add to GitHub secrets as `DOCKER_TOKEN`

**Format**:
```
dckr_pat_1a2b3c4d5e6f7g8h9i0j
```

### Built-in Secrets

#### GITHUB_TOKEN

**Purpose**: Create GitHub releases

**Note**: Automatically provided by GitHub Actions. No configuration needed.

**Permissions**: Configured in workflow file:
```yaml
permissions:
  contents: write  # Required for creating releases
```

---

## Troubleshooting

### Version Mismatch Error

**Error**:
```
❌ Version mismatch! Tag: 1.2.3, Package: 1.2.2
Please update crawl4ai/__version__.py to match the tag version
```

**Cause**: Git tag doesn't match `__version__` in `crawl4ai/__version__.py`

**Fix**:
```bash
# Option 1: Update __version__.py and re-tag
vim crawl4ai/__version__.py  # Change to 1.2.3
git add crawl4ai/__version__.py
git commit -m "fix: update version to 1.2.3"
git tag -d v1.2.3                    # Delete local tag
git push --delete origin v1.2.3      # Delete remote tag
git tag v1.2.3                       # Create new tag
git push origin main
git push origin v1.2.3

# Option 2: Use correct tag
git tag v1.2.2  # Match existing __version__
git push origin v1.2.2
```

### PyPI Upload Failure

**Error**:
```
HTTPError: 403 Forbidden
```

**Causes & Fixes**:

1. **Invalid Token**:
   - Verify `PYPI_TOKEN` in GitHub secrets
   - Ensure token hasn't expired
   - Regenerate token on PyPI

2. **Version Already Exists**:
   ```
   HTTPError: 400 File already exists
   ```
   - PyPI doesn't allow re-uploading same version
   - Increment version number and retry

3. **Package Name Conflict**:
   - Ensure you own the `crawl4ai` package on PyPI
   - Check token scope includes this project

### Docker Build Failure

**Error**:
```
failed to solve: process "/bin/sh -c ..." did not complete successfully
```

**Debug Steps**:

1. **Check Build Logs**:
   - Go to Actions tab → Docker Release workflow
   - Expand "Build and push Docker images" step
   - Look for specific error

2. **Test Locally**:
   ```bash
   docker build -t crawl4ai:test .
   ```

3. **Common Issues**:

   **Dependency installation fails**:
   ```dockerfile
   # Check requirements.txt is valid
   # Ensure all packages are available
   ```

   **Architecture-specific issues**:
   ```bash
   # Test both platforms locally (if on Mac with Apple Silicon)
   docker buildx build --platform linux/amd64,linux/arm64 -t test .
   ```

4. **Cache Issues**:
   ```bash
   # Clear cache by pushing a tag with different content
   # Or wait 7 days for automatic cache eviction
   ```

### Docker Authentication Failure

**Error**:
```
Error: Cannot perform an interactive login from a non TTY device
```

**Cause**: Docker Hub credentials invalid

**Fix**:
1. Verify `DOCKER_USERNAME` is correct
2. Regenerate `DOCKER_TOKEN` on Docker Hub
3. Update secret in GitHub

### Docker Release Not Triggering

**Issue**: Pushed tag `v1.2.3`, but `docker-release.yml` didn't run

**Causes**:

1. **Release Not Published**:
   - Check if `release.yml` completed successfully
   - Verify GitHub release is published (not draft)

2. **Workflow File Syntax Error**:
   ```bash
   # Validate YAML syntax
   yamllint .github/workflows/docker-release.yml
   ```

3. **Workflow Not on Default Branch**:
   - Workflow files must be on `main` branch
   - Check if `.github/workflows/docker-release.yml` exists on `main`

**Debug**:
```bash
# Check workflow files
git ls-tree main .github/workflows/

# Check GitHub Actions tab for workflow runs
```

### Cache Not Working

**Issue**: Every build takes 10-15 minutes despite using cache

**Causes**:

1. **Cache Scope**:
   - Cache is per-branch and per-workflow
   - First build on new branch is always cold

2. **Dockerfile Changes**:
   - Any change invalidates subsequent layers
   - Optimize Dockerfile layer order (stable → volatile)

3. **Base Image Updates**:
   - `FROM python:3.12` pulls latest monthly
   - Pin to specific digest for stable cache

**Optimization**:
```dockerfile
# Good: Stable layers first
FROM python:3.12
RUN apt-get update && apt-get install -y ...
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Bad: Volatile layers first (breaks cache often)
FROM python:3.12
COPY . .
RUN pip install -r requirements.txt
```

---

## Advanced Topics

### Multi-Architecture Build Details

#### Platform Support

| Platform | Architecture | Use Cases |
|----------|-------------|-----------|
| linux/amd64 | x86_64 | AWS EC2, GCP, Azure, Traditional servers |
| linux/arm64 | aarch64 | Apple Silicon, AWS Graviton, Raspberry Pi |

#### Build Process

```bash
# Buildx uses QEMU to emulate different architectures
docker buildx create --use                    # Create builder
docker buildx build --platform linux/amd64,linux/arm64 ...
```

**Under the Hood**:
1. For each platform:
   - Spawn QEMU emulator
   - Execute Dockerfile instructions
   - Generate platform-specific image
2. Create manifest list (multi-arch index)
3. Push all variants + manifest to registry

**Pull Behavior**:
```bash
# Docker automatically selects correct platform
docker pull unclecode/crawl4ai:latest

# On M1 Mac: Pulls arm64 variant
# On Intel Linux: Pulls amd64 variant

# Force specific platform
docker pull --platform linux/amd64 unclecode/crawl4ai:latest
```

### Semantic Versioning Strategy

#### Tag Scheme

```
v1.2.3
 │ │ │
 │ │ └─ Patch: Bug fixes, no API changes
 │ └─── Minor: New features, backward compatible
 └───── Major: Breaking changes
```

#### Docker Tag Mapping

| Git Tag | Docker Tags Created | Use Case |
|---------|---------------------|----------|
| v1.2.3 | 1.2.3, 1.2, 1, latest | Full version chain |
| v2.0.0 | 2.0.0, 2.0, 2, latest | Major version bump |

**Example Evolution**:

```bash
# Release v1.0.0
Tags: 1.0.0, 1.0, 1, latest

# Release v1.1.0
Tags: 1.1.0, 1.1, 1, latest
# Note: 1.0 still exists, but 1 and latest now point to 1.1.0

# Release v1.2.0
Tags: 1.2.0, 1.2, 1, latest
# Note: 1.0 and 1.1 still exist, but 1 and latest now point to 1.2.0

# Release v2.0.0
Tags: 2.0.0, 2.0, 2, latest
# Note: All v1.x tags still exist, but latest now points to 2.0.0
```

**User Pinning Strategies**:

```bash
# Maximum stability (never updates)
docker pull unclecode/crawl4ai:1.2.3

# Get patch updates only
docker pull unclecode/crawl4ai:1.2

# Get minor updates (features, bug fixes)
docker pull unclecode/crawl4ai:1

# Always get latest (potentially breaking)
docker pull unclecode/crawl4ai:latest
```

### Cache Optimization Strategies

#### 1. Layer Order Optimization

```dockerfile
# BEFORE (cache breaks often)
FROM python:3.12
COPY . /app              # Changes every commit
RUN pip install -r requirements.txt
RUN apt-get install -y ffmpeg

# AFTER (cache-optimized)
FROM python:3.12
RUN apt-get update && apt-get install -y ffmpeg  # Rarely changes
COPY requirements.txt /app/requirements.txt       # Changes occasionally
RUN pip install -r /app/requirements.txt
COPY . /app                                       # Changes every commit
```

#### 2. Multi-Stage Builds

```dockerfile
# Build stage (cached separately)
FROM python:3.12 as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
ENV PATH=/root/.local/bin:$PATH
```

**Benefits**:
- Builder stage cached independently
- Runtime image smaller
- Faster rebuilds

#### 3. Dependency Caching

```dockerfile
# Cache pip packages
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Cache apt packages
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y ...
```

**Note**: Requires BuildKit (enabled by default in GitHub Actions)

#### 4. Base Image Pinning

```dockerfile
# VOLATILE (updates monthly, breaks cache)
FROM python:3.12

# STABLE (fixed digest, cache preserved)
FROM python:3.12@sha256:8c5e5c77e7b9e44a6f0e3b9e8f5e5c77e7b9e44a6f0e3b9e8f5e5c77e7b9e44a
```

Find digest:
```bash
docker pull python:3.12
docker inspect python:3.12 | grep -A 2 RepoDigests
```

### Workflow Security Best Practices

#### 1. Secret Handling

**Never**:
```yaml
# DON'T: Hardcode secrets
run: echo "my-secret-token" | docker login

# DON'T: Log secrets
run: echo "Token is ${{ secrets.PYPI_TOKEN }}"
```

**Always**:
```yaml
# DO: Use environment variables
env:
  PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
run: twine upload dist/*

# DO: Use action inputs (masked automatically)
uses: docker/login-action@v3
with:
  password: ${{ secrets.DOCKER_TOKEN }}
```

#### 2. Permission Minimization

```yaml
# Specific permissions only
permissions:
  contents: write  # Only what's needed
  # NOT: permissions: write-all
```

#### 3. Dependency Pinning

```yaml
# DON'T: Use floating versions
uses: actions/checkout@v4

# DO: Pin to SHA (immutable)
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
```

#### 4. Token Scoping

**PyPI Token**:
- Scope: Project-specific (`crawl4ai` only)
- Not: Account-wide access

**Docker Token**:
- Permissions: Read, Write (not Delete unless needed)
- Expiration: Set to 1 year, rotate regularly

### Monitoring and Observability

#### GitHub Actions Metrics

**Available in Actions tab**:
- Workflow run duration
- Success/failure rates
- Cache hit rates
- Artifact sizes

#### Custom Metrics

Add to workflow summary:
```yaml
- name: Build Metrics
  run: |
    echo "## Build Metrics" >> $GITHUB_STEP_SUMMARY
    echo "- Duration: $(date -u -d @$SECONDS +%T)" >> $GITHUB_STEP_SUMMARY
    echo "- Cache hit rate: 85%" >> $GITHUB_STEP_SUMMARY
```

#### External Monitoring

**Webhooks**: Configure in Settings → Webhooks
```json
{
  "events": ["workflow_run"],
  "url": "https://your-monitoring-service.com/webhook"
}
```

**Status Badges**:
```markdown
[![Release](https://github.com/user/repo/actions/workflows/release.yml/badge.svg)](https://github.com/user/repo/actions/workflows/release.yml)

[![Docker](https://github.com/user/repo/actions/workflows/docker-release.yml/badge.svg)](https://github.com/user/repo/actions/workflows/docker-release.yml)
```

### Disaster Recovery

#### Backup Workflow Files

**Current Backup**:
- `.github/workflows/release.yml.backup`

**Recommended**:
```bash
# Automatic backup before modifications
cp .github/workflows/release.yml .github/workflows/release.yml.backup-$(date +%Y%m%d)
git add .github/workflows/*.backup*
git commit -m "backup: workflow before modification"
```

#### Recovery from Failed Release

**Scenario**: v1.2.3 release failed mid-way

**Steps**:
1. **Identify what succeeded**:
   - Check PyPI: `pip search crawl4ai`
   - Check Docker Hub: https://hub.docker.com/r/unclecode/crawl4ai/tags
   - Check GitHub Releases

2. **Clean up partial release**:
   ```bash
   # Delete tag
   git tag -d v1.2.3
   git push --delete origin v1.2.3

   # Delete GitHub release (if created)
   gh release delete v1.2.3
   ```

3. **Fix issue and retry**:
   ```bash
   # Fix the issue
   # Re-tag and push
   git tag v1.2.3
   git push origin v1.2.3
   ```

**Note**: Cannot delete PyPI uploads. If PyPI succeeded, increment to v1.2.4.

### CI/CD Best Practices

#### 1. Version Validation

Add pre-commit hook:
```bash
# .git/hooks/pre-commit
#!/bin/bash
VERSION_FILE="crawl4ai/__version__.py"
VERSION=$(python -c "exec(open('$VERSION_FILE').read()); print(__version__)")
echo "Current version: $VERSION"
```

#### 2. Changelog Automation

Use conventional commits:
```bash
git commit -m "feat: add new scraping mode"
git commit -m "fix: handle timeout errors"
git commit -m "docs: update API reference"
```

Generate changelog:
```bash
# Use git-cliff or similar
git cliff --tag v1.2.3 > CHANGELOG.md
```

#### 3. Pre-Release Testing

Add test workflow:
```yaml
# .github/workflows/test.yml
on:
  push:
    tags:
      - 'test-v*'

jobs:
  test-release:
    runs-on: ubuntu-latest
    steps:
      - name: Build package
        run: python -m build
      - name: Upload to TestPyPI
        run: twine upload --repository testpypi dist/*
```

#### 4. Release Checklist

Create issue template:
```markdown
## Release Checklist

- [ ] Update version in `crawl4ai/__version__.py`
- [ ] Update CHANGELOG.md
- [ ] Run tests locally: `pytest`
- [ ] Build package locally: `python -m build`
- [ ] Create and push tag: `git tag v1.2.3 && git push origin v1.2.3`
- [ ] Monitor Release Pipeline workflow
- [ ] Monitor Docker Release workflow
- [ ] Verify PyPI: `pip install crawl4ai==1.2.3`
- [ ] Verify Docker: `docker pull unclecode/crawl4ai:1.2.3`
- [ ] Announce release
```

---

## References

### Official Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

### Related Files

- [`release.yml`](../release.yml) - Main release workflow
- [`docker-release.yml`](../docker-release.yml) - Docker build workflow
- [`release.yml.backup`](../release.yml.backup) - Original combined workflow

### Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-01-XX | 2.0 | Split workflows, added Docker caching |
| 2024-XX-XX | 1.0 | Initial combined workflow |

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [GitHub Actions logs](../../actions)
3. Create issue in repository

---

**Last Updated**: 2025-01-21
**Maintainer**: Crawl4AI Team
