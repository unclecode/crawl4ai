#!/bin/bash
# Wrapper script to run dashboard UI test with proper environment

set -e

echo "=== Dashboard UI Test ==="
echo ""

# Activate virtual environment
source venv/bin/activate

# Make sure playwright is installed
echo "Checking Playwright installation..."
python -c "import playwright" 2>/dev/null || {
    echo "Installing Playwright..."
    pip install playwright
    playwright install chromium
}

# Run the test
echo ""
echo "Running dashboard UI test..."
python deploy/docker/tests/cli/dashboard/test_01_dashboard_ui.py

echo ""
echo "✅ Dashboard test complete"
echo "Check deploy/docker/tests/cli/dashboard/screenshots/ for results"
