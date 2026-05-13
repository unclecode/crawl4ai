#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Build a custom Crawl4AI image from your GitHub fork.
# All code comes from GitHub — no local project files needed.
#
# Just put this script + Dockerfile.custom in the same directory:
#   bash build-custom-image.sh
#
# Override defaults with env vars:
#   BASE_IMAGE=my-registry/crawl4ai:latest bash build-custom-image.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

BASE_IMAGE="${BASE_IMAGE:-docker.1ms.run/unclecode/crawl4ai:latest}"
TAG="${TAG:-crawl4ai-custom:latest}"
GITHUB_REPO="${GITHUB_REPO:-https://github.com/wchy1128/crawl4ai.git}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"

echo "========================================="
echo " Building custom Crawl4AI image"
echo "========================================="
echo "  Base image : ${BASE_IMAGE}"
echo "  Output tag : ${TAG}"
echo "  GitHub repo: ${GITHUB_REPO}"
echo "  Branch     : ${GITHUB_BRANCH}"
echo "========================================="

# Make sure the base image exists locally
if ! docker image inspect "${BASE_IMAGE}" >/dev/null 2>&1; then
    echo "==> Pulling base image..."
    docker pull "${BASE_IMAGE}"
fi

# No build context needed — pipe Dockerfile via stdin
docker build \
    --build-arg "BASE_IMAGE=${BASE_IMAGE}" \
    --build-arg "GITHUB_REPO=${GITHUB_REPO}" \
    --build-arg "GITHUB_BRANCH=${GITHUB_BRANCH}" \
    -t "${TAG}" \
    - < "${SCRIPT_DIR}/Dockerfile.custom"

echo ""
echo "========================================="
echo " Build complete: ${TAG}"
echo "========================================="
echo ""
echo "Quick test:"
echo "  docker run --rm -p 11235:11235 ${TAG}"
