#!/usr/bin/env python
"""
Automated Test Suite Runner for Crawl4AI Agent
Runs all tests in sequence: Component → Tools → Scenarios
Generates comprehensive test report with timing and pass/fail metrics.
"""

import sys
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSuiteRunner:
    """Orchestrates all test suites with reporting."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": [],
            "overall_status": "PENDING"
        }

    def print_banner(self, text: str, char: str = "="):
        """Print a formatted banner."""
        width = 70
        print(f"\n{char * width}")
        print(f"{text:^{width}}")
        print(f"{char * width}\n")

    async def run_component_tests(self) -> Dict[str, Any]:
        """Run component tests (test_chat.py)."""
        self.print_banner("TEST SUITE 1/3: COMPONENT TESTS", "=")
        print("Testing: BrowserManager, TerminalUI, MCP Server, ChatMode")
        print("Expected duration: ~5 seconds\n")

        start_time = time.time()
        suite_result = {
            "name": "Component Tests",
            "file": "test_chat.py",
            "status": "PENDING",
            "duration_seconds": 0,
            "tests_run": 4,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": []
        }

        try:
            # Import and run the test
            from crawl4ai.agent import test_chat

            # Capture the result
            success = await test_chat.test_components()

            duration = time.time() - start_time
            suite_result["duration_seconds"] = duration

            if success:
                suite_result["status"] = "PASS"
                suite_result["tests_passed"] = 4
                print(f"\n✓ Component tests PASSED in {duration:.2f}s")
            else:
                suite_result["status"] = "FAIL"
                suite_result["tests_failed"] = 4
                print(f"\n✗ Component tests FAILED in {duration:.2f}s")

        except Exception as e:
            duration = time.time() - start_time
            suite_result["status"] = "ERROR"
            suite_result["error"] = str(e)
            suite_result["duration_seconds"] = duration
            suite_result["tests_failed"] = 4
            print(f"\n✗ Component tests ERROR: {e}")

        return suite_result

    async def run_tool_tests(self) -> Dict[str, Any]:
        """Run tool integration tests (test_tools.py)."""
        self.print_banner("TEST SUITE 2/3: TOOL INTEGRATION TESTS", "=")
        print("Testing: Quick crawl, Session workflow, HTML format")
        print("Expected duration: ~30 seconds (uses browser)\n")

        start_time = time.time()
        suite_result = {
            "name": "Tool Integration Tests",
            "file": "test_tools.py",
            "status": "PENDING",
            "duration_seconds": 0,
            "tests_run": 3,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": []
        }

        try:
            # Import and run the test
            from crawl4ai.agent import test_tools

            # Run the main test function
            success = await test_tools.main()

            duration = time.time() - start_time
            suite_result["duration_seconds"] = duration

            if success:
                suite_result["status"] = "PASS"
                suite_result["tests_passed"] = 3
                print(f"\n✓ Tool tests PASSED in {duration:.2f}s")
            else:
                suite_result["status"] = "FAIL"
                suite_result["tests_failed"] = 3
                print(f"\n✗ Tool tests FAILED in {duration:.2f}s")

        except Exception as e:
            duration = time.time() - start_time
            suite_result["status"] = "ERROR"
            suite_result["error"] = str(e)
            suite_result["duration_seconds"] = duration
            suite_result["tests_failed"] = 3
            print(f"\n✗ Tool tests ERROR: {e}")

        return suite_result

    async def run_scenario_tests(self) -> Dict[str, Any]:
        """Run multi-turn scenario tests (test_scenarios.py)."""
        self.print_banner("TEST SUITE 3/3: MULTI-TURN SCENARIO TESTS", "=")
        print("Testing: 9 scenarios (2 simple, 3 medium, 4 complex)")
        print("Expected duration: ~3-5 minutes\n")

        start_time = time.time()
        suite_result = {
            "name": "Multi-turn Scenario Tests",
            "file": "test_scenarios.py",
            "status": "PENDING",
            "duration_seconds": 0,
            "tests_run": 9,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": [],
            "pass_rate_percent": 0.0
        }

        try:
            # Import and run the test
            from crawl4ai.agent import test_scenarios

            # Run all scenarios
            success = await test_scenarios.run_all_scenarios(self.output_dir)

            duration = time.time() - start_time
            suite_result["duration_seconds"] = duration

            # Load detailed results from the generated file
            results_file = self.output_dir / "test_results.json"
            if results_file.exists():
                with open(results_file) as f:
                    scenario_results = json.load(f)

                passed = sum(1 for r in scenario_results if r["status"] == "PASS")
                total = len(scenario_results)

                suite_result["tests_passed"] = passed
                suite_result["tests_failed"] = total - passed
                suite_result["pass_rate_percent"] = (passed / total * 100) if total > 0 else 0
                suite_result["details"] = scenario_results

                if success:
                    suite_result["status"] = "PASS"
                    print(f"\n✓ Scenario tests PASSED ({passed}/{total}) in {duration:.2f}s")
                else:
                    suite_result["status"] = "FAIL"
                    print(f"\n✗ Scenario tests FAILED ({passed}/{total}) in {duration:.2f}s")
            else:
                suite_result["status"] = "FAIL"
                suite_result["tests_failed"] = 9
                print(f"\n✗ Scenario results file not found")

        except Exception as e:
            duration = time.time() - start_time
            suite_result["status"] = "ERROR"
            suite_result["error"] = str(e)
            suite_result["duration_seconds"] = duration
            suite_result["tests_failed"] = 9
            print(f"\n✗ Scenario tests ERROR: {e}")
            import traceback
            traceback.print_exc()

        return suite_result

    async def run_all(self) -> bool:
        """Run all test suites in sequence."""
        self.print_banner("CRAWL4AI AGENT - AUTOMATED TEST SUITE", "█")
        print("This will run 3 test suites in sequence:")
        print("  1. Component Tests (~5s)")
        print("  2. Tool Integration Tests (~30s)")
        print("  3. Multi-turn Scenario Tests (~3-5 min)")
        print(f"\nOutput directory: {self.output_dir}")
        print(f"Started at: {self.results['timestamp']}\n")

        overall_start = time.time()

        # Run all test suites
        component_result = await self.run_component_tests()
        self.results["test_suites"].append(component_result)

        # Only continue if components pass
        if component_result["status"] != "PASS":
            print("\n⚠️  Component tests failed. Stopping execution.")
            print("Fix component issues before running integration tests.")
            self.results["overall_status"] = "FAILED"
            self._save_report()
            return False

        tool_result = await self.run_tool_tests()
        self.results["test_suites"].append(tool_result)

        # Only continue if tools pass
        if tool_result["status"] != "PASS":
            print("\n⚠️  Tool tests failed. Stopping execution.")
            print("Fix tool integration issues before running scenarios.")
            self.results["overall_status"] = "FAILED"
            self._save_report()
            return False

        scenario_result = await self.run_scenario_tests()
        self.results["test_suites"].append(scenario_result)

        # Calculate overall results
        overall_duration = time.time() - overall_start
        self.results["total_duration_seconds"] = overall_duration

        # Determine overall status
        all_passed = all(s["status"] == "PASS" for s in self.results["test_suites"])

        # For scenarios, we accept ≥80% pass rate
        if scenario_result["status"] == "FAIL" and scenario_result.get("pass_rate_percent", 0) >= 80.0:
            self.results["overall_status"] = "PASS_WITH_WARNINGS"
        elif all_passed:
            self.results["overall_status"] = "PASS"
        else:
            self.results["overall_status"] = "FAIL"

        # Print final summary
        self._print_summary()
        self._save_report()

        return self.results["overall_status"] in ["PASS", "PASS_WITH_WARNINGS"]

    def _print_summary(self):
        """Print final test summary."""
        self.print_banner("FINAL TEST SUMMARY", "█")

        for suite in self.results["test_suites"]:
            status_icon = "✓" if suite["status"] == "PASS" else "✗"
            duration = suite["duration_seconds"]

            if "pass_rate_percent" in suite:
                # Scenario tests
                passed = suite["tests_passed"]
                total = suite["tests_run"]
                pass_rate = suite["pass_rate_percent"]
                print(f"{status_icon} {suite['name']}: {passed}/{total} passed ({pass_rate:.1f}%) in {duration:.2f}s")
            else:
                # Component/Tool tests
                passed = suite["tests_passed"]
                total = suite["tests_run"]
                print(f"{status_icon} {suite['name']}: {passed}/{total} passed in {duration:.2f}s")

        print(f"\nTotal duration: {self.results['total_duration_seconds']:.2f}s")
        print(f"Overall status: {self.results['overall_status']}")

        if self.results["overall_status"] == "PASS":
            print("\n🎉 ALL TESTS PASSED! Ready for evaluation phase.")
        elif self.results["overall_status"] == "PASS_WITH_WARNINGS":
            print("\n⚠️  Tests passed with warnings (≥80% scenario pass rate).")
            print("Consider investigating failed scenarios before evaluation.")
        else:
            print("\n❌ TESTS FAILED. Please fix issues before proceeding to evaluation.")

    def _save_report(self):
        """Save detailed test report to JSON."""
        report_file = self.output_dir / "test_suite_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")


async def main():
    """Main entry point."""
    # Set up output directory
    output_dir = Path.cwd() / "test_agent_output"

    # Run all tests
    runner = TestSuiteRunner(output_dir)
    success = await runner.run_all()

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
