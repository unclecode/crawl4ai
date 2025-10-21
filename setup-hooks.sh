#!/bin/bash
# Setup Git hooks for cnode auto-sync
# Run this once after cloning the repo: ./setup-hooks.sh

set -e

echo "🔧 Setting up Git hooks..."

# Configure Git to use .githooks directory
git config core.hooksPath .githooks

echo "✅ Git hooks configured!"
echo ""
echo "Hooks installed:"
echo "  • pre-commit: Auto-syncs cnode source → package when committing"
echo ""
echo "What this means:"
echo "  ✅ Edit deploy/docker/cnode_cli.py"
echo "  ✅ Run: git add deploy/docker/cnode_cli.py"
echo "  ✅ Run: git commit -m \"update cnode\""
echo "  ✅ Hook automatically syncs to deploy/installer/cnode_pkg/"
echo "  ✅ Synced files are auto-staged in the same commit"
echo ""
echo "You're all set! 🚀"
