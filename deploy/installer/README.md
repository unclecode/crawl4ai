# Crawl4AI Node Manager (cnode) - Installation & Distribution

This directory contains the standalone `cnode` package and installation scripts for managing Crawl4AI Docker server instances.

## Overview

`cnode` is a fast, lightweight CLI tool for managing Crawl4AI Docker servers. It provides:
- One-command deployment with automatic scaling
- Single container for development (N=1)
- Docker Swarm for production with built-in load balancing (N>1)
- Docker Compose + Nginx as fallback (N>1)

## Directory Structure

```
deploy/installer/
├── README.md                 # This file
├── cnode_pkg/                # Standalone Python package
│   ├── __init__.py           # Package marker
│   ├── cli.py                # CLI interface (commands)
│   ├── server_manager.py     # Docker orchestration logic
│   └── requirements.txt      # Python dependencies
├── install-cnode.sh          # Local installation script
├── deploy.sh                 # Remote installation script (for users)
└── releases/                 # Release artifacts for distribution
```

## Installation

### For Users (Remote Installation)

Users can install `cnode` directly from the web:

```bash
# Install from GitHub/website
curl -sSL https://crawl4ai.com/install-cnode.sh | bash

# Or with wget
wget -qO- https://crawl4ai.com/install-cnode.sh | bash
```

### For Local Testing

Test the installation locally:

```bash
cd deploy/installer
./install-cnode.sh
```

## Package Contents

### `cnode_pkg/` - Python Package

This is a self-contained Python package with:

- **`cli.py`**: Click-based CLI with all commands (start, stop, status, scale, logs, cleanup, restart)
- **`server_manager.py`**: Core Docker orchestration logic
- **`requirements.txt`**: Dependencies (click, rich, anyio, pyyaml)
- **`__init__.py`**: Package initialization

### Installation Script

**`install-cnode.sh`** does the following:
1. Checks for Python 3.8+ and pip
2. Checks for Docker (warns if not found)
3. Installs Python dependencies
4. Copies `cnode_pkg/` to `/usr/local/lib/cnode/`
5. Creates wrapper script at `/usr/local/bin/cnode`
6. Verifies installation

### Wrapper Script

Created at `/usr/local/bin/cnode`:

```bash
#!/usr/bin/env bash
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

# Run cnode
export PYTHONPATH="/usr/local/lib/cnode:$PYTHONPATH"
exec $PYTHON_CMD -m cnode_pkg.cli "$@"
```

## Performance

**Blazing Fast Startup:**
- **~0.1 seconds** to launch
- 49x faster than compiled binary alternatives
- Minimal overhead, maximum responsiveness

## Requirements

### User Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Docker (for running servers)

### Dependencies (Auto-installed)
- click >= 8.0.0 (CLI framework)
- rich >= 13.0.0 (Terminal formatting)
- anyio >= 3.0.0 (Async I/O)
- pyyaml >= 6.0.0 (YAML parsing)

## Usage

After installation:

```bash
# Quick start
cnode start                    # Single container on port 11235
cnode start --replicas 5       # 5-replica cluster
cnode status                   # Check server status
cnode logs -f                  # Follow logs
cnode scale 10                 # Scale to 10 replicas
cnode stop                     # Stop server

# Get help
cnode --help
cnode start --help
```

## Development Workflow

### Making Changes

1. **Edit source code** in `deploy/docker/`:
   ```bash
   vim deploy/docker/cnode_cli.py
   vim deploy/docker/server_manager.py
   ```

2. **Update package** by copying to installer:
   ```bash
   # Copy CLI
   cp deploy/docker/cnode_cli.py deploy/installer/cnode_pkg/cli.py

   # Fix imports (deploy.docker → cnode_pkg)
   sed -i 's/from deploy\.docker\./from cnode_pkg./g' deploy/installer/cnode_pkg/cli.py

   # Copy server manager
   cp deploy/docker/server_manager.py deploy/installer/cnode_pkg/server_manager.py
   ```

3. **Test locally**:
   ```bash
   cd deploy/installer
   ./install-cnode.sh
   cnode --help
   ```

4. **Commit both**:
   ```bash
   git add deploy/docker/cnode_cli.py
   git add deploy/installer/cnode_pkg/cli.py
   git commit -m "Update cnode: [description]"
   ```

### Creating a Release

1. **Tag the release**:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Package for distribution**:
   ```bash
   cd deploy/installer
   tar -czf releases/cnode-v1.0.0.tar.gz cnode_pkg/ install-cnode.sh
   ```

3. **Create GitHub release**:
   ```bash
   gh release create v1.0.0 \
     releases/cnode-v1.0.0.tar.gz \
     --title "cnode v1.0.0" \
     --notes "Release notes here"
   ```

4. **Update deployment script** (if needed):
   - Update `deploy.sh` with new version/URL
   - Upload to hosting (e.g., `https://crawl4ai.com/install-cnode.sh`)

## Deployment

### Remote Installation Script

The `deploy.sh` script is meant to be hosted at a public URL for user installation:

```bash
# Upload to your server
scp deploy.sh user@crawl4ai.com:/var/www/html/install-cnode.sh

# Or use GitHub raw URL
https://raw.githubusercontent.com/unclecode/crawl4ai/main/deploy/installer/deploy.sh
```

Users can then install with:
```bash
curl -sSL https://crawl4ai.com/install-cnode.sh | bash
```

## Backward Compatibility

The main Crawl4AI CLI (`crwl`) includes a redirect for backward compatibility:

```bash
# These work identically:
crwl server start --replicas 3
cnode start --replicas 3

# All subcommands redirect:
crwl server status  → cnode status
crwl server stop    → cnode stop
crwl server scale 5 → cnode scale 5
crwl server logs -f → cnode logs -f
```

This ensures existing scripts continue working while users migrate to `cnode`.

## Uninstallation

To remove cnode:

```bash
# Remove command
sudo rm /usr/local/bin/cnode

# Remove package
sudo rm -rf /usr/local/lib/cnode

# (Optional) Uninstall dependencies
pip uninstall click rich anyio pyyaml
```

## Troubleshooting

### Python Not Found
```bash
# Install Python 3.8+
# macOS: brew install python3
# Ubuntu: sudo apt install python3 python3-pip
# RHEL/CentOS: sudo yum install python3 python3-pip
```

### Permission Denied
```bash
# Run installer with sudo
sudo ./install-cnode.sh

# Or change install location
INSTALL_DIR=$HOME/.local/bin ./install-cnode.sh
```

### Command Not Found After Install
```bash
# Add to PATH in ~/.bashrc or ~/.zshrc
export PATH="/usr/local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

### Dependencies Install Failed
```bash
# Install manually
pip install --user click rich anyio pyyaml

# Or with break-system-packages (if needed)
pip install --user --break-system-packages click rich anyio pyyaml
```

### Docker Not Running
```bash
# macOS: Start Docker Desktop
# Linux: sudo systemctl start docker

# Check Docker
docker --version
docker ps
```

## Architecture

### Component Flow

```
User runs: cnode start
         ↓
/usr/local/bin/cnode (wrapper script)
         ↓
Finds python3 executable
         ↓
Sets PYTHONPATH=/usr/local/lib/cnode
         ↓
python3 -m cnode_pkg.cli start
         ↓
cli.py → start_cmd()
         ↓
server_manager.py → ServerManager.start()
         ↓
Docker orchestration (single/swarm/compose)
         ↓
Server running!
```

### Why Python Wrapper vs Binary?

We chose a Python wrapper over compiled binaries (PyInstaller) because:

| Metric | Python Wrapper | PyInstaller Binary |
|--------|---------------|-------------------|
| Startup time | **0.1s** | 4.7s |
| Size | ~50KB wrapper | 8.8MB |
| Updates | Easy (just copy files) | Rebuild required |
| Dependencies | Python 3.8+ | None |
| Platform | Any with Python | OS-specific builds |

Since users running Crawl4AI already have Python, the wrapper is the clear winner.

## Support

For issues or questions:
- GitHub Issues: https://github.com/unclecode/crawl4ai/issues
- Documentation: https://docs.crawl4ai.com
- Discord: https://discord.gg/crawl4ai

## Version History

- **v1.0.0**: Initial release with Python wrapper approach
  - Fast startup (~0.1s)
  - Supports single container, Docker Swarm, and Compose modes
  - Auto-scaling and load balancing
  - Real-time monitoring and logs
