#!/usr/bin/env bash
set -euo pipefail

# Generate CycloneDX JSON SBOM using Syft
# Output: sbom.cdx.json in project root

cd "$(dirname "$0")/.."

if ! command -v syft &> /dev/null; then
    echo "Error: syft is not installed. Install from https://github.com/anchore/syft" >&2
    exit 1
fi

syft . -o cyclonedx-json=sbom/sbom.cdx.json

echo "SBOM generated: sbom/sbom.cdx.json"
