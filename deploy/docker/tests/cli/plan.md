E2E CLI Test Suite Plan                                                                                     │ │
│ │                                                                                                             │ │
│ │ Test Structure                                                                                              │ │
│ │                                                                                                             │ │
│ │ Create deploy/docker/tests/cli/ folder with individual test scripts organized by category.                  │ │
│ │                                                                                                             │ │
│ │ Test Categories                                                                                             │ │
│ │                                                                                                             │ │
│ │ 1. Basic Tests (deploy/docker/tests/cli/basic/)                                                             │ │
│ │                                                                                                             │ │
│ │ - test_01_start_default.sh - Start server with defaults (1 replica, port 11235)                             │ │
│ │ - test_02_status.sh - Check server status                                                                   │ │
│ │ - test_03_stop.sh - Stop server cleanly                                                                     │ │
│ │ - test_04_start_custom_port.sh - Start with custom port (8080)                                              │ │
│ │ - test_05_start_replicas.sh - Start with 3 replicas                                                         │ │
│ │ - test_06_logs.sh - View logs (tail and follow)                                                             │ │
│ │ - test_07_restart.sh - Restart server preserving config                                                     │ │
│ │ - test_08_cleanup.sh - Force cleanup all resources                                                          │ │
│ │                                                                                                             │ │
│ │ 2. Advanced Tests (deploy/docker/tests/cli/advanced/)                                                       │ │
│ │                                                                                                             │ │
│ │ - test_01_scale_up.sh - Scale from 3 to 5 replicas                                                          │ │
│ │ - test_02_scale_down.sh - Scale from 5 to 2 replicas                                                        │ │
│ │ - test_03_mode_single.sh - Start in single mode explicitly                                                  │ │
│ │ - test_04_mode_compose.sh - Start in compose mode with 3 replicas                                           │ │
│ │ - test_05_custom_image.sh - Start with custom image tag                                                     │ │
│ │ - test_06_env_file.sh - Start with custom env file                                                          │ │
│ │ - test_07_stop_remove_volumes.sh - Stop and remove volumes                                                  │ │
│ │ - test_08_restart_with_scale.sh - Restart and change replica count                                          │ │
│ │                                                                                                             │ │
│ │ 3. Resource Tests (deploy/docker/tests/cli/resource/)                                                       │ │
│ │                                                                                                             │ │
│ │ - test_01_memory_monitoring.sh - Monitor memory during crawls                                               │ │
│ │ - test_02_cpu_stress.sh - CPU usage under concurrent load                                                   │ │
│ │ - test_03_max_replicas.sh - Start with 10 replicas and stress test                                          │ │
│ │ - test_04_cleanup_verification.sh - Verify all resources cleaned up                                         │ │
│ │ - test_05_long_running.sh - Stability test (30 min runtime)                                                 │ │
│ │                                                                                                             │ │
│ │ 4. Dashboard UI Tests (deploy/docker/tests/cli/dashboard/)                                                  │ │
│ │                                                                                                             │ │
│ │ - test_01_dashboard_ui.py - Playwright test with screenshots                                                │ │
│ │   - Start server with 3 replicas                                                                            │ │
│ │   - Run demo_monitor_dashboard.py script                                                                    │ │
│ │   - Use Playwright to:                                                                                      │ │
│ │       - Take screenshot of main dashboard                                                                   │ │
│ │     - Verify container filter buttons (All, C-1, C-2, C-3)                                                  │ │
│ │     - Test WebSocket connection indicator                                                                   │ │
│ │     - Verify timeline charts render                                                                         │ │
│ │     - Test filtering functionality                                                                          │ │
│ │     - Check all tabs (Requests, Browsers, Janitor, Errors, Stats)                                           │ │
│ │                                                                                                             │ │
│ │ 5. Edge Cases (deploy/docker/tests/cli/edge/)                                                               │ │
│ │                                                                                                             │ │
│ │ - test_01_already_running.sh - Try starting when already running                                            │ │
│ │ - test_02_not_running.sh - Try stop/status when not running                                                 │ │
│ │ - test_03_scale_single_mode.sh - Try scaling single container mode                                          │ │
│ │ - test_04_invalid_port.sh - Invalid port numbers (0, -1, 99999)                                             │ │
│ │ - test_05_invalid_replicas.sh - Invalid replica counts (0, -1, 101)                                         │ │
│ │ - test_06_missing_env_file.sh - Non-existent env file                                                       │ │
│ │ - test_07_port_in_use.sh - Port already occupied                                                            │ │
│ │ - test_08_state_corruption.sh - Manually corrupt state file                                                 │ │
│ │ - test_09_network_conflict.sh - Docker network name collision                                               │ │
│ │ - test_10_rapid_operations.sh - Start/stop/restart in quick succession                                      │ │
│ │                                                                                                             │ │
│ │ Test Execution Plan                                                                                         │ │
│ │                                                                                                             │ │
│ │ Process:                                                                                                    │ │
│ │                                                                                                             │ │
│ │ 1. Create test file                                                                                         │ │
│ │ 2. Run test                                                                                                 │ │
│ │ 3. Verify results                                                                                           │ │
│ │ 4. If fails → fix issue → re-test                                                                           │ │
│ │ 5. Move to next test                                                                                        │ │
│ │ 6. Clean up after each test to ensure clean state                                                           │ │
│ │                                                                                                             │ │
│ │ Common Test Structure:                                                                                      │ │
│ │                                                                                                             │ │
│ │ #!/bin/bash                                                                                                 │ │
│ │ # Test: [Description]                                                                                       │ │
│ │ # Expected: [What should happen]                                                                            │ │
│ │                                                                                                             │ │
│ │ source venv/bin/activate                                                                                    │ │
│ │ set -e  # Exit on error                                                                                     │ │
│ │                                                                                                             │ │
│ │ echo "=== Test: [Name] ==="                                                                                 │ │
│ │                                                                                                             │ │
│ │ # Setup                                                                                                     │ │
│ │ # ... test commands ...                                                                                     │ │
│ │                                                                                                             │ │
│ │ # Verification                                                                                              │ │
│ │ # ... assertions ...                                                                                        │ │
│ │                                                                                                             │ │
│ │ # Cleanup                                                                                                   │ │
│ │ crwl server stop || true                                                                                    │ │
│ │                                                                                                             │ │
│ │ echo "✓ Test passed"                                                                                        │ │
│ │                                                                                                             │ │
│ │ Dashboard Test Structure (Python):                                                                          │ │
│ │                                                                                                             │ │
│ │ # Activate venv first in calling script                                                                     │ │
│ │ import asyncio                                                                                              │ │
│ │ from playwright.async_api import async_playwright                                                           │ │
│ │                                                                                                             │ │
│ │ async def test_dashboard():                                                                                 │ │
│ │     # Start server with 3 replicas                                                                          │ │
│ │     # Run demo script in background                                                                         │ │
│ │     # Launch Playwright                                                                                     │ │
│ │     # Take screenshots                                                                                      │ │
│ │     # Verify elements                                                                                       │ │
│ │     # Cleanup                                                                                               │ │
│ │                                                                                                             │ │
│ │ Success Criteria:                                                                                           │ │
│ │                                                                                                             │ │
│ │ - All basic operations work correctly                                                                       │ │
│ │ - Scaling operations function properly                                                                      │ │
│ │ - Resource limits are respected                                                                             │ │
│ │ - Dashboard UI is functional and responsive                                                                 │ │
│ │ - Edge cases handled gracefully with proper error messages                                                  │ │
│ │ - Clean resource cleanup verified