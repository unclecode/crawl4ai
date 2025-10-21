#!/bin/bash
# Sync cnode source code to installer package
# Run this before committing changes to cnode

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/../docker"
PKG_DIR="$SCRIPT_DIR/cnode_pkg"

echo "🔄 Syncing cnode source to package..."

# Copy CLI
echo "  → Copying cnode_cli.py to cli.py"
cp "$SOURCE_DIR/cnode_cli.py" "$PKG_DIR/cli.py"

# Fix imports
echo "  → Fixing imports (deploy.docker → cnode_pkg)"
sed -i '' 's/from deploy\.docker\./from cnode_pkg./g' "$PKG_DIR/cli.py"

# Copy server manager
echo "  → Copying server_manager.py"
cp "$SOURCE_DIR/server_manager.py" "$PKG_DIR/server_manager.py"

echo "✅ Sync complete!"
echo ""
echo "Files updated:"
echo "  • deploy/installer/cnode_pkg/cli.py"
echo "  • deploy/installer/cnode_pkg/server_manager.py"
echo ""
echo "Next steps:"
echo "  1. Test: cd deploy/installer && ./install-cnode.sh"
echo "  2. Commit both source and package files"
