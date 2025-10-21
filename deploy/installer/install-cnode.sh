#!/bin/bash
# Crawl4AI Node Manager (cnode) - Fast Installation Script
# This installs cnode as a Python package with a wrapper script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Crawl4AI Node Manager (cnode) - Fast Installer            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
LIB_DIR="${LIB_DIR:-/usr/local/lib/cnode}"

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python 3.8+ is required but not found${NC}"
    echo -e "${YELLOW}Install from: https://www.python.org/downloads/${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

if [ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]; then
    echo -e "${RED}Error: Python 3.8+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi

# Check pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "${RED}Error: pip is required${NC}"
    echo -e "${YELLOW}Install pip: $PYTHON_CMD -m ensurepip${NC}"
    exit 1
fi

echo -e "${GREEN}✓ pip is available${NC}"

# Check Docker
echo -e "\n${BLUE}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found (required for running servers)${NC}"
    echo -e "${YELLOW}Install from: https://docs.docker.com/get-docker/${NC}\n"
else
    echo -e "${GREEN}✓ Docker is installed${NC}"
fi

# Check permissions
USE_SUDO=""
if [ ! -w "$INSTALL_DIR" ] || [ ! -w "/usr/local" ]; then
    echo -e "\n${YELLOW}⚠️  Root permission required for installation${NC}"
    USE_SUDO="sudo"
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install Python dependencies
echo -e "\n${BLUE}Installing Python dependencies...${NC}"
$PYTHON_CMD -m pip install --quiet --user -r "$SCRIPT_DIR/cnode_pkg/requirements.txt" 2>/dev/null || \
$PYTHON_CMD -m pip install --quiet --user --break-system-packages -r "$SCRIPT_DIR/cnode_pkg/requirements.txt" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Could not install dependencies with pip${NC}"
    echo -e "${YELLOW}Trying to continue anyway (dependencies may already be installed)${NC}"
}
echo -e "${GREEN}✓ Dependencies check complete${NC}"

# Create lib directory
echo -e "\n${BLUE}Installing cnode package...${NC}"
$USE_SUDO mkdir -p "$LIB_DIR"
$USE_SUDO cp -r "$SCRIPT_DIR/cnode_pkg" "$LIB_DIR/"
echo -e "${GREEN}✓ Package installed to $LIB_DIR${NC}"

# Create wrapper script
echo -e "\n${BLUE}Creating cnode command...${NC}"
$USE_SUDO tee "$INSTALL_DIR/cnode" > /dev/null << 'EOF'
#!/usr/bin/env bash
# Crawl4AI Node Manager (cnode) wrapper

set -e

# Find Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3.8+ required" >&2
    exit 1
fi

# Add cnode to Python path and run
export PYTHONPATH="/usr/local/lib/cnode:$PYTHONPATH"
exec $PYTHON_CMD -m cnode_pkg.cli "$@"
EOF

$USE_SUDO chmod +x "$INSTALL_DIR/cnode"
echo -e "${GREEN}✓ cnode command created${NC}"

# Verify installation
echo -e "\n${BLUE}Verifying installation...${NC}"
if ! command -v cnode &> /dev/null; then
    echo -e "${RED}Error: cnode not found in PATH${NC}"
    echo -e "${YELLOW}Add $INSTALL_DIR to your PATH${NC}"
    exit 1
fi

if ! cnode --help &> /dev/null; then
    echo -e "${RED}Error: cnode command failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Installation verified${NC}"

# Success message
echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Installation Complete!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}cnode is now installed and ready!${NC}\n"

echo -e "${YELLOW}Quick Start:${NC}"
echo -e "  ${GREEN}cnode start${NC}                    # Start single server"
echo -e "  ${GREEN}cnode start --replicas 5${NC}       # Start 5-replica cluster"
echo -e "  ${GREEN}cnode status${NC}                   # Check status"
echo -e "  ${GREEN}cnode logs -f${NC}                  # Follow logs"
echo -e "  ${GREEN}cnode stop${NC}                     # Stop server"

echo -e "\n${YELLOW}More help:${NC}"
echo -e "  ${BLUE}cnode --help${NC}\n"
