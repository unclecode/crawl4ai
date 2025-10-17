#!/usr/bin/env python
"""
Automated multi-turn chat scenario tests for Crawl4AI Agent.

Tests agent's ability to handle complex conversations, maintain state,
plan and execute tasks without human interaction.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from claude_agent_sdk import AssistantMessage, TextBlock, ResultMessage, ToolUseBlock

from .c4ai_tools import CRAWL_TOOLS
from .c4ai_prompts import SYSTEM_PROMPT
from .browser_manager import BrowserManager


class TurnResult(Enum):
    """Result of a single conversation turn."""
    PASS = "PASS"
    FAIL = "FAIL"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


@dataclass
class TurnExpectation:
    """Expectations for a single conversation turn."""
    user_message: str
    expect_tools: Optional[List[str]] = None  # Tools that should be called
    expect_keywords: Optional[List[str]] = None  # Keywords in response
    expect_files_created: Optional[List[str]] = None  # File patterns created
    expect_success: bool = True  # Should complete without error
    expect_min_turns: int = 1  # Minimum agent turns to complete
    timeout_seconds: int = 60


@dataclass
class Scenario:
    """A complete multi-turn conversation scenario."""
    name: str
    category: str  # "simple", "medium", "complex"
    description: str
    turns: List[TurnExpectation]
    cleanup_files: Optional[List[str]] = None  # Files to cleanup after test


# =============================================================================
# TEST SCENARIOS - Categorized from Simple to Complex
# =============================================================================

SIMPLE_SCENARIOS = [
    Scenario(
        name="Single quick crawl",
        category="simple",
        description="Basic one-shot crawl with markdown extraction",
        turns=[
            TurnExpectation(
                user_message="Use quick_crawl to get the title from example.com",
                expect_tools=["mcp__crawler__quick_crawl"],
                expect_keywords=["Example Domain", "title"],
                timeout_seconds=30
            )
        ]
    ),

    Scenario(
        name="Session lifecycle",
        category="simple",
        description="Start session, navigate, close - basic session management",
        turns=[
            TurnExpectation(
                user_message="Start a session named 'simple_test'",
                expect_tools=["mcp__crawler__start_session"],
                expect_keywords=["session", "started"],
                timeout_seconds=20
            ),
            TurnExpectation(
                user_message="Navigate to example.com",
                expect_tools=["mcp__crawler__navigate"],
                expect_keywords=["navigated", "example.com"],
                timeout_seconds=25
            ),
            TurnExpectation(
                user_message="Close the session",
                expect_tools=["mcp__crawler__close_session"],
                expect_keywords=["closed"],
                timeout_seconds=15
            )
        ]
    ),
]


MEDIUM_SCENARIOS = [
    Scenario(
        name="Multi-page crawl with file output",
        category="medium",
        description="Crawl multiple pages and save results to file",
        turns=[
            TurnExpectation(
                user_message="Crawl example.com and example.org, extract titles from both",
                expect_tools=["mcp__crawler__quick_crawl"],
                expect_min_turns=2,  # Should make 2 separate crawls
                timeout_seconds=45
            ),
            TurnExpectation(
                user_message="Save the results to a JSON file called crawl_results.json",
                expect_tools=["Write"],
                expect_files_created=["crawl_results.json"],
                timeout_seconds=20
            )
        ],
        cleanup_files=["crawl_results.json"]
    ),

    Scenario(
        name="Session-based data extraction",
        category="medium",
        description="Use session to navigate and extract data in steps",
        turns=[
            TurnExpectation(
                user_message="Start session 'extract_test', navigate to example.com, and extract the markdown",
                expect_tools=["mcp__crawler__start_session", "mcp__crawler__navigate", "mcp__crawler__extract_data"],
                expect_keywords=["Example Domain"],
                timeout_seconds=50
            ),
            TurnExpectation(
                user_message="Now save that markdown to example_content.md",
                expect_tools=["Write"],
                expect_files_created=["example_content.md"],
                timeout_seconds=20
            ),
            TurnExpectation(
                user_message="Close the session",
                expect_tools=["mcp__crawler__close_session"],
                timeout_seconds=15
            )
        ],
        cleanup_files=["example_content.md"]
    ),

    Scenario(
        name="Context retention across turns",
        category="medium",
        description="Agent should remember previous context",
        turns=[
            TurnExpectation(
                user_message="Crawl example.com and tell me the title",
                expect_tools=["mcp__crawler__quick_crawl"],
                expect_keywords=["Example Domain"],
                timeout_seconds=30
            ),
            TurnExpectation(
                user_message="What was the URL I just asked you to crawl?",
                expect_keywords=["example.com"],
                expect_tools=[],  # Should answer from memory, no tools needed
                timeout_seconds=15
            )
        ]
    ),
]


COMPLEX_SCENARIOS = [
    Scenario(
        name="Multi-step task with planning",
        category="complex",
        description="Complex task requiring agent to plan, execute, and verify",
        turns=[
            TurnExpectation(
                user_message="Crawl example.com and example.org, compare their content, and create a markdown report with: 1) titles of both, 2) word count comparison, 3) save to comparison_report.md",
                expect_tools=["mcp__crawler__quick_crawl", "Write"],
                expect_files_created=["comparison_report.md"],
                expect_min_turns=3,  # Plan, crawl both, write report
                timeout_seconds=90
            ),
            TurnExpectation(
                user_message="Read back the report you just created",
                expect_tools=["Read"],
                expect_keywords=["Example Domain"],
                timeout_seconds=20
            )
        ],
        cleanup_files=["comparison_report.md"]
    ),

    Scenario(
        name="Session with state manipulation",
        category="complex",
        description="Complex session workflow with multiple operations",
        turns=[
            TurnExpectation(
                user_message="Start session 'complex_session' and navigate to example.com",
                expect_tools=["mcp__crawler__start_session", "mcp__crawler__navigate"],
                timeout_seconds=30
            ),
            TurnExpectation(
                user_message="Extract the page content and count how many times the word 'example' appears (case insensitive)",
                expect_tools=["mcp__crawler__extract_data"],
                expect_keywords=["example"],
                timeout_seconds=30
            ),
            TurnExpectation(
                user_message="Take a screenshot of the current page",
                expect_tools=["mcp__crawler__screenshot"],
                expect_keywords=["screenshot"],
                timeout_seconds=25
            ),
            TurnExpectation(
                user_message="Close the session",
                expect_tools=["mcp__crawler__close_session"],
                timeout_seconds=15
            )
        ]
    ),

    Scenario(
        name="Error recovery and continuation",
        category="complex",
        description="Agent should handle errors gracefully and continue",
        turns=[
            TurnExpectation(
                user_message="Crawl https://this-site-definitely-does-not-exist-12345.com",
                expect_success=False,  # Should fail gracefully
                expect_keywords=["error", "fail"],
                timeout_seconds=30
            ),
            TurnExpectation(
                user_message="That's okay, crawl example.com instead",
                expect_tools=["mcp__crawler__quick_crawl"],
                expect_keywords=["Example Domain"],
                timeout_seconds=30
            )
        ]
    ),
]


# Combine all scenarios
ALL_SCENARIOS = SIMPLE_SCENARIOS + MEDIUM_SCENARIOS + COMPLEX_SCENARIOS


# =============================================================================
# TEST RUNNER
# =============================================================================

class ScenarioRunner:
    """Runs automated chat scenarios without human interaction."""

    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.results = []

    async def run_scenario(self, scenario: Scenario) -> Dict[str, Any]:
        """Run a single scenario and return results."""
        print(f"\n{'='*70}")
        print(f"[{scenario.category.upper()}] {scenario.name}")
        print(f"{'='*70}")
        print(f"Description: {scenario.description}\n")

        start_time = time.time()
        turn_results = []

        try:
            # Setup agent options
            crawler_server = create_sdk_mcp_server(
                name="crawl4ai",
                version="1.0.0",
                tools=CRAWL_TOOLS
            )

            options = ClaudeAgentOptions(
                mcp_servers={"crawler": crawler_server},
                allowed_tools=[
                    "mcp__crawler__quick_crawl",
                    "mcp__crawler__start_session",
                    "mcp__crawler__navigate",
                    "mcp__crawler__extract_data",
                    "mcp__crawler__execute_js",
                    "mcp__crawler__screenshot",
                    "mcp__crawler__close_session",
                    "Read", "Write", "Edit", "Glob", "Grep", "Bash"
                ],
                system_prompt=SYSTEM_PROMPT,
                permission_mode="acceptEdits",
                cwd=str(self.working_dir)
            )

            # Run conversation
            async with ClaudeSDKClient(options=options) as client:
                for turn_idx, expectation in enumerate(scenario.turns, 1):
                    print(f"\nTurn {turn_idx}: {expectation.user_message}")

                    turn_result = await self._run_turn(
                        client, expectation, turn_idx
                    )
                    turn_results.append(turn_result)

                    if turn_result["status"] != TurnResult.PASS:
                        print(f"  ✗ FAILED: {turn_result['reason']}")
                        break
                    else:
                        print(f"  ✓ PASSED")

            # Cleanup
            if scenario.cleanup_files:
                self._cleanup_files(scenario.cleanup_files)

            # Overall result
            all_passed = all(r["status"] == TurnResult.PASS for r in turn_results)
            duration = time.time() - start_time

            result = {
                "scenario": scenario.name,
                "category": scenario.category,
                "status": "PASS" if all_passed else "FAIL",
                "duration_seconds": duration,
                "turns": turn_results
            }

            return result

        except Exception as e:
            print(f"\n✗ SCENARIO ERROR: {e}")
            return {
                "scenario": scenario.name,
                "category": scenario.category,
                "status": "ERROR",
                "error": str(e),
                "duration_seconds": time.time() - start_time,
                "turns": turn_results
            }
        finally:
            # Ensure browser cleanup
            await BrowserManager.close_browser()

    async def _run_turn(
        self,
        client: ClaudeSDKClient,
        expectation: TurnExpectation,
        turn_number: int
    ) -> Dict[str, Any]:
        """Execute a single conversation turn and validate."""

        tools_used = []
        response_text = ""
        agent_turns = 0

        try:
            # Send user message
            await client.query(expectation.user_message)

            # Collect response
            start_time = time.time()
            async for message in client.receive_messages():
                if time.time() - start_time > expectation.timeout_seconds:
                    return {
                        "turn": turn_number,
                        "status": TurnResult.TIMEOUT,
                        "reason": f"Exceeded {expectation.timeout_seconds}s timeout"
                    }

                if isinstance(message, AssistantMessage):
                    agent_turns += 1
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text + " "
                        elif isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)

                elif isinstance(message, ResultMessage):
                    # Check if error when expecting success
                    if expectation.expect_success and message.is_error:
                        return {
                            "turn": turn_number,
                            "status": TurnResult.FAIL,
                            "reason": f"Agent returned error: {message.result}"
                        }
                    break

            # Validate expectations
            validation = self._validate_turn(
                expectation, tools_used, response_text, agent_turns
            )

            return {
                "turn": turn_number,
                "status": validation["status"],
                "reason": validation.get("reason", "All checks passed"),
                "tools_used": tools_used,
                "agent_turns": agent_turns
            }

        except Exception as e:
            return {
                "turn": turn_number,
                "status": TurnResult.ERROR,
                "reason": f"Exception: {str(e)}"
            }

    def _validate_turn(
        self,
        expectation: TurnExpectation,
        tools_used: List[str],
        response_text: str,
        agent_turns: int
    ) -> Dict[str, Any]:
        """Validate turn results against expectations."""

        # Check expected tools
        if expectation.expect_tools:
            for tool in expectation.expect_tools:
                if tool not in tools_used:
                    return {
                        "status": TurnResult.FAIL,
                        "reason": f"Expected tool '{tool}' was not used"
                    }

        # Check keywords
        if expectation.expect_keywords:
            response_lower = response_text.lower()
            for keyword in expectation.expect_keywords:
                if keyword.lower() not in response_lower:
                    return {
                        "status": TurnResult.FAIL,
                        "reason": f"Expected keyword '{keyword}' not found in response"
                    }

        # Check files created
        if expectation.expect_files_created:
            for pattern in expectation.expect_files_created:
                matches = list(self.working_dir.glob(pattern))
                if not matches:
                    return {
                        "status": TurnResult.FAIL,
                        "reason": f"Expected file matching '{pattern}' was not created"
                    }

        # Check minimum turns
        if agent_turns < expectation.expect_min_turns:
            return {
                "status": TurnResult.FAIL,
                "reason": f"Expected at least {expectation.expect_min_turns} agent turns, got {agent_turns}"
            }

        return {"status": TurnResult.PASS}

    def _cleanup_files(self, patterns: List[str]):
        """Remove files created during test."""
        for pattern in patterns:
            for file_path in self.working_dir.glob(pattern):
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"  Warning: Could not delete {file_path}: {e}")


async def run_all_scenarios(working_dir: Optional[Path] = None):
    """Run all test scenarios and report results."""

    if working_dir is None:
        working_dir = Path.cwd() / "test_agent_output"
        working_dir.mkdir(exist_ok=True)

    runner = ScenarioRunner(working_dir)

    print("\n" + "="*70)
    print("CRAWL4AI AGENT SCENARIO TESTS")
    print("="*70)
    print(f"Working directory: {working_dir}")
    print(f"Total scenarios: {len(ALL_SCENARIOS)}")
    print(f"  Simple: {len(SIMPLE_SCENARIOS)}")
    print(f"  Medium: {len(MEDIUM_SCENARIOS)}")
    print(f"  Complex: {len(COMPLEX_SCENARIOS)}")

    results = []
    for scenario in ALL_SCENARIOS:
        result = await runner.run_scenario(scenario)
        results.append(result)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    by_category = {"simple": [], "medium": [], "complex": []}
    for result in results:
        by_category[result["category"]].append(result)

    for category in ["simple", "medium", "complex"]:
        cat_results = by_category[category]
        passed = sum(1 for r in cat_results if r["status"] == "PASS")
        total = len(cat_results)
        print(f"\n{category.upper()}: {passed}/{total} passed")
        for r in cat_results:
            status_icon = "✓" if r["status"] == "PASS" else "✗"
            print(f"  {status_icon} {r['scenario']} ({r['duration_seconds']:.1f}s)")

    total_passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)

    print(f"\nOVERALL: {total_passed}/{total} scenarios passed ({total_passed/total*100:.1f}%)")

    # Save detailed results
    results_file = working_dir / "test_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")

    return total_passed == total


if __name__ == "__main__":
    import sys
    success = asyncio.run(run_all_scenarios())
    sys.exit(0 if success else 1)
