# Crawl4AI CLI E2E Test Suite

Comprehensive end-to-end tests for the `crwl server` command-line interface.

## Overview

This test suite validates all aspects of the Docker server CLI including:
- Basic operations (start, stop, status, logs)
- Advanced features (scaling, modes, custom configurations)
- Resource management and stress testing
- Dashboard UI functionality
- Edge cases and error handling

**Total Tests:** 32
- Basic: 8 tests
- Advanced: 8 tests
- Resource: 5 tests
- Dashboard: 1 test
- Edge Cases: 10 tests

## Prerequisites

```bash
# Activate virtual environment
source venv/bin/activate

# For dashboard tests, install Playwright
pip install playwright
playwright install chromium

# Ensure Docker is running
docker ps
```

## Quick Start

```bash
# Run all tests (except dashboard)
./run_tests.sh

# Run specific category
./run_tests.sh basic
./run_tests.sh advanced
./run_tests.sh resource
./run_tests.sh edge

# Run dashboard tests (slower, includes UI screenshots)
./run_tests.sh dashboard

# Run specific test
./run_tests.sh basic 01
./run_tests.sh edge 05
```

## Test Categories

### 1. Basic Tests (`basic/`)

Core CLI functionality tests.

| Test | Description | Expected Result |
|------|-------------|----------------|
| `test_01_start_default.sh` | Start server with defaults | 1 replica on port 11235 |
| `test_02_status.sh` | Check server status | Shows running state and details |
| `test_03_stop.sh` | Stop server | Clean shutdown, port freed |
| `test_04_start_custom_port.sh` | Start on port 8080 | Server on custom port |
| `test_05_start_replicas.sh` | Start with 3 replicas | Multi-container deployment |
| `test_06_logs.sh` | View server logs | Logs displayed correctly |
| `test_07_restart.sh` | Restart server | Preserves configuration |
| `test_08_cleanup.sh` | Force cleanup | All resources removed |

### 2. Advanced Tests (`advanced/`)

Advanced features and configurations.

| Test | Description | Expected Result |
|------|-------------|----------------|
| `test_01_scale_up.sh` | Scale 3 → 5 replicas | Live scaling without downtime |
| `test_02_scale_down.sh` | Scale 5 → 2 replicas | Graceful container removal |
| `test_03_mode_single.sh` | Explicit single mode | Single container deployment |
| `test_04_mode_compose.sh` | Compose mode with Nginx | Multi-container with load balancer |
| `test_05_custom_image.sh` | Custom image specification | Uses specified image tag |
| `test_06_env_file.sh` | Environment file loading | Variables loaded correctly |
| `test_07_stop_remove_volumes.sh` | Stop with volume removal | Volumes cleaned up |
| `test_08_restart_with_scale.sh` | Restart with new replica count | Configuration updated |

### 3. Resource Tests (`resource/`)

Resource monitoring and stress testing.

| Test | Description | Expected Result |
|------|-------------|----------------|
| `test_01_memory_monitoring.sh` | Monitor memory usage | Stats accessible and reasonable |
| `test_02_cpu_stress.sh` | Concurrent request load | Handles load without errors |
| `test_03_max_replicas.sh` | 10 replicas stress test | Maximum scale works correctly |
| `test_04_cleanup_verification.sh` | Verify resource cleanup | All Docker resources removed |
| `test_05_long_running.sh` | 5-minute stability test | Server remains stable |

### 4. Dashboard Tests (`dashboard/`)

Dashboard UI functionality with Playwright.

| Test | Description | Expected Result |
|------|-------------|----------------|
| `test_01_dashboard_ui.py` | Full dashboard UI test | All UI elements functional |

**Dashboard Test Details:**
- Starts server with 3 replicas
- Runs demo script to generate activity
- Uses Playwright to:
  - Take screenshots of dashboard
  - Verify container filter buttons
  - Check WebSocket connection
  - Validate timeline charts
  - Test all dashboard sections

**Screenshots saved to:** `dashboard/screenshots/`

### 5. Edge Case Tests (`edge/`)

Error handling and validation.

| Test | Description | Expected Result |
|------|-------------|----------------|
| `test_01_already_running.sh` | Start when already running | Proper error message |
| `test_02_not_running.sh` | Operations when stopped | Appropriate errors |
| `test_03_scale_single_mode.sh` | Scale single container | Error with guidance |
| `test_04_invalid_port.sh` | Invalid port numbers | Validation errors |
| `test_05_invalid_replicas.sh` | Invalid replica counts | Validation errors |
| `test_06_missing_env_file.sh` | Non-existent env file | File not found error |
| `test_07_port_in_use.sh` | Port already occupied | Port conflict error |
| `test_08_state_corruption.sh` | Corrupted state file | Cleanup recovers |
| `test_09_network_conflict.sh` | Docker network collision | Handles gracefully |
| `test_10_rapid_operations.sh` | Rapid start/stop cycles | No corruption |

## Test Execution Workflow

Each test follows this pattern:

1. **Setup:** Clean state, activate venv
2. **Execute:** Run test commands
3. **Verify:** Check results and assertions
4. **Cleanup:** Stop server, remove resources

## Running Individual Tests

```bash
# Make test executable (if needed)
chmod +x deploy/docker/tests/cli/basic/test_01_start_default.sh

# Run directly
./deploy/docker/tests/cli/basic/test_01_start_default.sh

# Or use the test runner
./run_tests.sh basic 01
```

## Interpreting Results

### Success Output
```
✅ Test passed: [description]
```

### Failure Output
```
❌ Test failed: [error message]
```

### Warning Output
```
⚠️  Warning: [issue description]
```

## Common Issues

### Docker Not Running
```
Error: Docker daemon not running
Solution: Start Docker Desktop or Docker daemon
```

### Port Already In Use
```
Error: Port 11235 is already in use
Solution: Stop existing server or use different port
```

### Virtual Environment Not Found
```
Warning: venv not found
Solution: Create venv and activate it
```

### Playwright Not Installed
```
Error: playwright module not found
Solution: pip install playwright && playwright install chromium
```

## Test Development

### Adding New Tests

1. **Choose category:** basic, advanced, resource, dashboard, or edge
2. **Create test file:** Follow naming pattern `test_XX_description.sh`
3. **Use template:**

```bash
#!/bin/bash
# Test: [Description]
# Expected: [What should happen]

set -e

echo "=== Test: [Name] ==="
echo ""

source venv/bin/activate

# Cleanup
crwl server stop 2>/dev/null || true
sleep 2

# Test logic here

# Cleanup
crwl server stop >/dev/null 2>&1

echo ""
echo "✅ Test passed: [success message]"
```

4. **Make executable:** `chmod +x test_XX_description.sh`
5. **Test it:** `./test_XX_description.sh`
6. **Add to runner:** Tests are auto-discovered by `run_tests.sh`

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run CLI Tests
  run: |
    source venv/bin/activate
    cd deploy/docker/tests/cli
    ./run_tests.sh all
```

## Performance Considerations

- **Basic tests:** ~2-5 minutes total
- **Advanced tests:** ~5-10 minutes total
- **Resource tests:** ~10-15 minutes total (including 5-min stability test)
- **Dashboard test:** ~3-5 minutes
- **Edge case tests:** ~5-8 minutes total

**Full suite:** ~30-45 minutes

## Best Practices

1. **Always cleanup:** Each test should cleanup after itself
2. **Wait for readiness:** Add sleep after starting servers
3. **Check health:** Verify health endpoint before assertions
4. **Graceful failures:** Use `|| true` to continue on expected failures
5. **Clear messages:** Output should clearly indicate what's being tested

## Troubleshooting

### Tests Hanging
- Check if Docker containers are stuck
- Look for port conflicts
- Verify network connectivity

### Intermittent Failures
- Increase sleep durations for slower systems
- Check system resources (memory, CPU)
- Verify Docker has enough resources allocated

### All Tests Failing
- Verify Docker is running: `docker ps`
- Check CLI is installed: `which crwl`
- Activate venv: `source venv/bin/activate`
- Check server manager: `crwl server status`

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add comprehensive documentation
3. Test on clean system
4. Update this README
5. Ensure cleanup is robust

## License

Same as Crawl4AI project license.
