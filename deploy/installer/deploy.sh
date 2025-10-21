#!/bin/bash
# Crawl4AI Node Manager (cnode) Installation Script
# Usage: curl -sSL https://crawl4ai.com/deploy.sh | bash
# Or: wget -qO- https://crawl4ai.com/deploy.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
BINARY_NAME="cnode"
GITHUB_REPO="unclecode/crawl4ai"
RELEASE_TAG="${CNODE_VERSION:-latest}"

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Crawl4AI Node Manager (cnode) Installation Script         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"

# Detect OS and architecture
detect_platform() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"

    case "$OS" in
        Linux*)
            OS_TYPE="linux"
            ;;
        Darwin*)
            OS_TYPE="macos"
            ;;
        *)
            echo -e "${RED}Error: Unsupported operating system: $OS${NC}"
            exit 1
            ;;
    esac

    case "$ARCH" in
        x86_64|amd64)
            ARCH_TYPE="amd64"
            ;;
        aarch64|arm64)
            ARCH_TYPE="arm64"
            ;;
        *)
            echo -e "${RED}Error: Unsupported architecture: $ARCH${NC}"
            exit 1
            ;;
    esac

    echo -e "${BLUE}Detected platform: ${YELLOW}$OS_TYPE-$ARCH_TYPE${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not found. cnode requires Docker to manage server instances.${NC}"
        echo -e "${YELLOW}Install Docker from: https://docs.docker.com/get-docker/${NC}\n"
        read -p "Continue installation anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Docker is installed${NC}"
    fi
}

# Check write permissions
check_permissions() {
    if [ ! -w "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}⚠️  No write permission for $INSTALL_DIR${NC}"
        echo -e "${YELLOW}The script will attempt to use sudo for installation.${NC}\n"
        USE_SUDO="sudo"
    else
        USE_SUDO=""
    fi
}

# Download binary
download_binary() {
    BINARY_URL="https://github.com/$GITHUB_REPO/releases/download/$RELEASE_TAG/cnode-$OS_TYPE-$ARCH_TYPE"

    echo -e "${BLUE}Downloading cnode from GitHub...${NC}"
    echo -e "${YELLOW}URL: $BINARY_URL${NC}\n"

    # Create temp directory
    TMP_DIR="$(mktemp -d)"
    TMP_FILE="$TMP_DIR/$BINARY_NAME"

    # Download with curl or wget
    if command -v curl &> /dev/null; then
        if ! curl -fSL "$BINARY_URL" -o "$TMP_FILE"; then
            echo -e "${RED}Error: Failed to download binary${NC}"
            echo -e "${YELLOW}URL: $BINARY_URL${NC}"
            rm -rf "$TMP_DIR"
            exit 1
        fi
    elif command -v wget &> /dev/null; then
        if ! wget -q "$BINARY_URL" -O "$TMP_FILE"; then
            echo -e "${RED}Error: Failed to download binary${NC}"
            echo -e "${YELLOW}URL: $BINARY_URL${NC}"
            rm -rf "$TMP_DIR"
            exit 1
        fi
    else
        echo -e "${RED}Error: Neither curl nor wget found${NC}"
        echo -e "${YELLOW}Please install curl or wget and try again${NC}"
        rm -rf "$TMP_DIR"
        exit 1
    fi

    # Make executable
    chmod +x "$TMP_FILE"

    echo "$TMP_FILE"
}

# Install binary
install_binary() {
    local tmp_file="$1"
    local install_path="$INSTALL_DIR/$BINARY_NAME"

    echo -e "\n${BLUE}Installing cnode to $install_path...${NC}"

    # Check if already installed
    if [ -f "$install_path" ]; then
        echo -e "${YELLOW}⚠️  cnode is already installed${NC}"
        read -p "Overwrite existing installation? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Installation cancelled${NC}"
            rm -rf "$(dirname "$tmp_file")"
            exit 0
        fi
    fi

    # Install
    if ! $USE_SUDO mv "$tmp_file" "$install_path"; then
        echo -e "${RED}Error: Failed to install binary${NC}"
        rm -rf "$(dirname "$tmp_file")"
        exit 1
    fi

    # Cleanup temp directory
    rm -rf "$(dirname "$tmp_file")"

    echo -e "${GREEN}✓ Installation successful${NC}"
}

# Verify installation
verify_installation() {
    echo -e "\n${BLUE}Verifying installation...${NC}"

    if ! command -v $BINARY_NAME &> /dev/null; then
        echo -e "${RED}Error: $BINARY_NAME not found in PATH${NC}"
        echo -e "${YELLOW}You may need to add $INSTALL_DIR to your PATH${NC}"
        echo -e "${YELLOW}Add this to your ~/.bashrc or ~/.zshrc:${NC}"
        echo -e "${YELLOW}export PATH=\"$INSTALL_DIR:\$PATH\"${NC}\n"
        exit 1
    fi

    # Test version
    if $BINARY_NAME --help &> /dev/null; then
        echo -e "${GREEN}✓ $BINARY_NAME is working correctly${NC}"
    else
        echo -e "${RED}Error: $BINARY_NAME failed to execute${NC}"
        exit 1
    fi
}

# Show completion message
show_completion() {
    local version
    version=$($BINARY_NAME --help | head -1 || echo "unknown")

    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Installation Complete!                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"

    echo -e "${BLUE}cnode is now installed and ready to use!${NC}\n"

    echo -e "${YELLOW}Quick Start:${NC}"
    echo -e "  ${GREEN}cnode start${NC}                    # Start single server instance"
    echo -e "  ${GREEN}cnode start --replicas 5${NC}       # Start 5-replica cluster"
    echo -e "  ${GREEN}cnode status${NC}                   # Check server status"
    echo -e "  ${GREEN}cnode logs -f${NC}                  # Follow server logs"
    echo -e "  ${GREEN}cnode scale 10${NC}                 # Scale to 10 replicas"
    echo -e "  ${GREEN}cnode stop${NC}                     # Stop server"

    echo -e "\n${YELLOW}For more information:${NC}"
    echo -e "  ${BLUE}cnode --help${NC}"
    echo -e "  ${BLUE}https://github.com/$GITHUB_REPO${NC}\n"
}

# Main installation flow
main() {
    detect_platform
    check_docker
    check_permissions

    # Download and install
    TMP_FILE=$(download_binary)
    install_binary "$TMP_FILE"

    # Verify
    verify_installation
    show_completion
}

# Run installation
main
