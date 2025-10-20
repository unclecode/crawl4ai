#!/bin/bash
# Master Test Runner for Crawl4AI CLI E2E Tests
# Usage: ./run_tests.sh [category] [test_number]
#   category: basic|advanced|resource|dashboard|edge|all (default: all)
#   test_number: specific test number to run (optional)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Print header
print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Print test result
print_result() {
    local test_name=$1
    local result=$2

    if [[ "$result" == "PASS" ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    elif [[ "$result" == "FAIL" ]]; then
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    elif [[ "$result" == "SKIP" ]]; then
        echo -e "${YELLOW}⏭️  SKIP${NC}: $test_name"
        SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    fi
}

# Run a single test
run_test() {
    local test_path=$1
    local test_name=$(basename "$test_path")

    echo ""
    echo -e "${BLUE}Running:${NC} $test_name"
    echo "----------------------------------------"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if bash "$test_path"; then
        print_result "$test_name" "PASS"
        return 0
    else
        print_result "$test_name" "FAIL"
        return 1
    fi
}

# Run Python test
run_python_test() {
    local test_path=$1
    local test_name=$(basename "$test_path")

    echo ""
    echo -e "${BLUE}Running:${NC} $test_name"
    echo "----------------------------------------"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if python "$test_path"; then
        print_result "$test_name" "PASS"
        return 0
    else
        print_result "$test_name" "FAIL"
        return 1
    fi
}

# Run tests in a category
run_category() {
    local category=$1
    local test_number=$2
    local category_dir="$SCRIPT_DIR/$category"

    if [[ ! -d "$category_dir" ]]; then
        echo -e "${RED}Error:${NC} Category '$category' not found"
        return 1
    fi

    print_header "Running $category tests"

    if [[ -n "$test_number" ]]; then
        # Run specific test
        local test_file=$(find "$category_dir" -name "*${test_number}*.sh" | head -n 1)
        if [[ -z "$test_file" ]]; then
            echo -e "${RED}Error:${NC} Test $test_number not found in $category"
            return 1
        fi
        run_test "$test_file"
    else
        # Run all tests in category
        if [[ "$category" == "dashboard" ]]; then
            # Dashboard tests are Python
            for test_file in "$category_dir"/*.py; do
                [[ -f "$test_file" ]] || continue
                run_python_test "$test_file" || true
            done
        else
            # Shell script tests
            for test_file in "$category_dir"/*.sh; do
                [[ -f "$test_file" ]] || continue
                run_test "$test_file" || true
            done
        fi
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo -e "Total:   $TOTAL_TESTS"
    echo -e "${GREEN}Passed:  $PASSED_TESTS${NC}"
    echo -e "${RED}Failed:  $FAILED_TESTS${NC}"
    echo -e "${YELLOW}Skipped: $SKIPPED_TESTS${NC}"
    echo ""

    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    local category=${1:-all}
    local test_number=$2

    # Activate virtual environment
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    else
        echo -e "${YELLOW}Warning:${NC} venv not found, some tests may fail"
    fi

    print_header "Crawl4AI CLI E2E Test Suite"

    if [[ "$category" == "all" ]]; then
        # Run all categories
        for cat in basic advanced resource edge; do
            run_category "$cat" || true
        done
        # Dashboard tests separately (can be slow)
        echo ""
        echo -e "${YELLOW}Note:${NC} Dashboard tests can be run separately with: ./run_tests.sh dashboard"
    else
        run_category "$category" "$test_number"
    fi

    print_summary
}

# Show usage
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $0 [category] [test_number]"
    echo ""
    echo "Categories:"
    echo "  basic      - Basic CLI operations (8 tests)"
    echo "  advanced   - Advanced features (8 tests)"
    echo "  resource   - Resource monitoring and stress tests (5 tests)"
    echo "  dashboard  - Dashboard UI tests with Playwright (1 test)"
    echo "  edge       - Edge cases and error handling (10 tests)"
    echo "  all        - Run all tests except dashboard (default)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 basic              # Run all basic tests"
    echo "  $0 basic 01           # Run test_01 from basic"
    echo "  $0 dashboard          # Run dashboard UI test"
    exit 0
fi

main "$@"
