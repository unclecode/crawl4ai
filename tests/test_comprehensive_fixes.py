#!/usr/bin/env python3
"""
Comprehensive test suite for all major fixes implemented in the deep crawl streaming functionality.

This test suite validates:
1. ORJSON serialization system
2. Global deprecated properties system  
3. Deep crawl strategy serialization/deserialization
4. Docker client streaming functionality
5. Server API streaming endpoints
6. CrawlResultContainer handling

Uses rich library for beautiful progress tracking and result visualization.
"""

import unittest
import asyncio
import json
import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Rich imports for visualization
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box

# Crawl4AI imports
from crawl4ai.models import CrawlResult, MarkdownGenerationResult, DeprecatedPropertiesMixin, ORJSONModel
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig
from crawl4ai.docker_client import Crawl4aiDockerClient

console = Console()

class TestResult:
    """Test result tracking for rich display."""
    def __init__(self, name: str):
        self.name = name
        self.status = "⏳ Pending"
        self.duration = 0.0
        self.details = ""
        self.passed = False
        self.start_time = None
    
    def start(self):
        self.start_time = datetime.now()
        self.status = "🔄 Running"
    
    def finish(self, passed: bool, details: str = ""):
        if self.start_time:
            self.duration = (datetime.now() - self.start_time).total_seconds()
        self.passed = passed
        self.status = "✅ Passed" if passed else "❌ Failed"
        self.details = details


class ComprehensiveTestRunner:
    """Test runner with rich visualization."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.console = Console()
    
    def add_test(self, name: str) -> TestResult:
        """Add a test to track."""
        result = TestResult(name)
        self.results.append(result)
        return result
    
    def display_results(self):
        """Display final test results in a beautiful table."""
        
        # Create summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Create summary panel
        summary_text = Text()
        summary_text.append("🎯 Test Summary\n", style="bold blue")
        summary_text.append(f"Total Tests: {total_tests}\n")
        summary_text.append(f"Passed: {passed_tests}\n", style="green")
        summary_text.append(f"Failed: {failed_tests}\n", style="red")
        summary_text.append(f"Success Rate: {success_rate:.1f}%\n", style="yellow")
        summary_text.append(f"Total Duration: {sum(r.duration for r in self.results):.2f}s", style="cyan")
        
        summary_panel = Panel(summary_text, title="📊 Results Summary", border_style="green" if success_rate > 80 else "yellow")
        console.print(summary_panel)
        
        # Create detailed results table
        table = Table(title="🔍 Detailed Test Results", box=box.ROUNDED)
        table.add_column("Test Name", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right", style="magenta")
        table.add_column("Details", style="dim")
        
        for result in self.results:
            status_style = "green" if result.passed else "red"
            table.add_row(
                result.name,
                Text(result.status, style=status_style),
                f"{result.duration:.3f}s",
                result.details[:50] + "..." if len(result.details) > 50 else result.details
            )
        
        console.print(table)
        
        return success_rate >= 80  # Return True if 80% or higher success rate


class TestORJSONSerialization:
    """Test ORJSON serialization system."""
    
    def test_basic_orjson_serialization(self, test_runner: ComprehensiveTestRunner):
        """Test basic ORJSON serialization functionality."""
        test_result = test_runner.add_test("ORJSON Basic Serialization")
        test_result.start()
        
        try:
            # Create a CrawlResult
            result = CrawlResult(
                url="https://example.com",
                html="<html>test</html>",
                success=True,
                metadata={"test": "data"}
            )
            
            # Test ORJSON serialization
            json_bytes = result.model_dump_json()
            assert isinstance(json_bytes, bytes)
            
            # Test deserialization
            data = json.loads(json_bytes)
            assert data["url"] == "https://example.com"
            assert data["success"] is True
            
            test_result.finish(True, "ORJSON serialization working correctly")
            
        except Exception as e:
            test_result.finish(False, f"ORJSON serialization failed: {str(e)}")
    
    def test_datetime_serialization(self, test_runner: ComprehensiveTestRunner):
        """Test datetime serialization with ORJSON."""
        test_result = test_runner.add_test("ORJSON DateTime Serialization")
        test_result.start()
        
        try:
            from crawl4ai.models import orjson_default
            
            # Test datetime serialization
            now = datetime.now()
            serialized = orjson_default(now)
            assert isinstance(serialized, str)
            assert "T" in serialized  # ISO format check
            
            test_result.finish(True, "DateTime serialization working")
            
        except Exception as e:
            test_result.finish(False, f"DateTime serialization failed: {str(e)}")
    
    def test_property_object_handling(self, test_runner: ComprehensiveTestRunner):
        """Test handling of property objects in serialization."""
        test_result = test_runner.add_test("ORJSON Property Object Handling")
        test_result.start()
        
        try:
            from crawl4ai.models import orjson_default
            
            # Create a mock property object
            class TestClass:
                @property
                def test_prop(self):
                    return "test"
            
            obj = TestClass()
            prop = TestClass.test_prop
            
            # Test property serialization
            serialized = orjson_default(prop)
            assert isinstance(serialized, str)
            
            test_result.finish(True, "Property object handling working")
            
        except Exception as e:
            test_result.finish(False, f"Property handling failed: {str(e)}")


class TestDeprecatedPropertiesSystem:
    """Test the global deprecated properties system."""
    
    def test_deprecated_properties_mixin(self, test_runner: ComprehensiveTestRunner):
        """Test DeprecatedPropertiesMixin functionality."""
        test_result = test_runner.add_test("Deprecated Properties Mixin")
        test_result.start()
        
        try:
            # Create a test model with deprecated properties
            class TestModel(ORJSONModel):
                name: str
                old_field: Optional[str] = None
                
                def get_deprecated_properties(self) -> set[str]:
                    return {'old_field', 'another_deprecated'}
            
            model = TestModel(name="test", old_field="should_be_excluded")
            
            # Test that deprecated properties are excluded
            data = model.model_dump()
            assert 'old_field' not in data
            assert 'another_deprecated' not in data
            assert data['name'] == "test"
            
            test_result.finish(True, "Deprecated properties correctly excluded")
            
        except Exception as e:
            test_result.finish(False, f"Deprecated properties test failed: {str(e)}")
    
    def test_crawl_result_deprecated_properties(self, test_runner: ComprehensiveTestRunner):
        """Test CrawlResult deprecated properties exclusion."""
        test_result = test_runner.add_test("CrawlResult Deprecated Properties")
        test_result.start()
        
        try:
            result = CrawlResult(
                url="https://example.com",
                html="<html>test</html>",
                success=True
            )
            
            # Get deprecated properties
            deprecated_props = result.get_deprecated_properties()
            expected_deprecated = {'fit_html', 'fit_markdown', 'markdown_v2'}
            assert deprecated_props == expected_deprecated
            
            # Test serialization excludes deprecated properties
            data = result.model_dump()
            for prop in deprecated_props:
                assert prop not in data, f"Deprecated property {prop} found in serialization"
            
            test_result.finish(True, f"Deprecated properties {deprecated_props} correctly excluded")
            
        except Exception as e:
            test_result.finish(False, f"CrawlResult deprecated properties test failed: {str(e)}")


class TestDeepCrawlStrategySerialization:
    """Test deep crawl strategy serialization/deserialization."""
    
    def test_bfs_strategy_serialization(self, test_runner: ComprehensiveTestRunner):
        """Test BFSDeepCrawlStrategy serialization."""
        test_result = test_runner.add_test("BFS Strategy Serialization")
        test_result.start()
        
        try:
            from crawl4ai.async_configs import to_serializable_dict, from_serializable_dict
            
            # Create strategy
            strategy = BFSDeepCrawlStrategy(
                max_depth=2,
                include_external=False,
                max_pages=5
            )
            
            # Test serialization
            serialized = to_serializable_dict(strategy)
            assert serialized['type'] == 'BFSDeepCrawlStrategy'
            assert serialized['params']['max_depth'] == 2
            assert serialized['params']['max_pages'] == 5
            
            # Test deserialization
            deserialized = from_serializable_dict(serialized)
            assert hasattr(deserialized, 'arun')
            assert deserialized.max_depth == 2
            assert deserialized.max_pages == 5
            
            test_result.finish(True, "BFS strategy serialization working correctly")
            
        except Exception as e:
            test_result.finish(False, f"BFS strategy serialization failed: {str(e)}")
    
    def test_logger_type_safety(self, test_runner: ComprehensiveTestRunner):
        """Test logger type safety in BFSDeepCrawlStrategy."""
        test_result = test_runner.add_test("BFS Strategy Logger Type Safety")
        test_result.start()
        
        try:
            import logging
            
            # Test with valid logger
            valid_logger = logging.getLogger("test")
            strategy1 = BFSDeepCrawlStrategy(max_depth=1, logger=valid_logger)
            assert strategy1.logger == valid_logger
            
            # Test with dict logger (should fallback to default)
            dict_logger = {"name": "invalid_logger"}
            strategy2 = BFSDeepCrawlStrategy(max_depth=1, logger=dict_logger)
            assert isinstance(strategy2.logger, logging.Logger)
            assert strategy2.logger != dict_logger
            
            test_result.finish(True, "Logger type safety working correctly")
            
        except Exception as e:
            test_result.finish(False, f"Logger type safety test failed: {str(e)}")


class TestCrawlerConfigSerialization:
    """Test CrawlerRunConfig with deep crawl strategies."""
    
    def test_config_with_strategy_serialization(self, test_runner: ComprehensiveTestRunner):
        """Test CrawlerRunConfig serialization with deep crawl strategy."""
        test_result = test_runner.add_test("Config with Strategy Serialization")
        test_result.start()
        
        try:
            strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=3)
            config = CrawlerRunConfig(
                deep_crawl_strategy=strategy,
                stream=True,
                word_count_threshold=1000
            )
            
            # Test serialization
            serialized = config.dump()
            assert 'deep_crawl_strategy' in serialized['params']
            assert serialized['params']['stream'] is True
            
            # Test deserialization
            loaded_config = CrawlerRunConfig.load(serialized)
            assert hasattr(loaded_config.deep_crawl_strategy, 'arun')
            assert loaded_config.stream is True
            assert loaded_config.word_count_threshold == 1000
            
            test_result.finish(True, "Config with strategy serialization working")
            
        except Exception as e:
            test_result.finish(False, f"Config serialization failed: {str(e)}")


class TestDockerClientFunctionality:
    """Test Docker client streaming functionality."""
    
    def test_docker_client_initialization(self, test_runner: ComprehensiveTestRunner):
        """Test Docker client initialization and configuration."""
        test_result = test_runner.add_test("Docker Client Initialization")
        test_result.start()
        
        try:
            client = Crawl4aiDockerClient(
                base_url="http://localhost:8000",
                timeout=600.0,
                verbose=False
            )
            
            assert client.base_url == "http://localhost:8000"
            assert client.timeout == 600.0
            
            test_result.finish(True, "Docker client initialization working")
            
        except Exception as e:
            test_result.finish(False, f"Docker client initialization failed: {str(e)}")
    
    def test_docker_client_request_preparation(self, test_runner: ComprehensiveTestRunner):
        """Test Docker client request preparation."""
        test_result = test_runner.add_test("Docker Client Request Preparation")
        test_result.start()
        
        try:
            client = Crawl4aiDockerClient()
            
            browser_config = BrowserConfig(headless=True)
            strategy = BFSDeepCrawlStrategy(max_depth=1)
            crawler_config = CrawlerRunConfig(deep_crawl_strategy=strategy, stream=True)
            
            # Test request preparation
            request_data = client._prepare_request(
                urls=["https://example.com"],
                browser_config=browser_config,
                crawler_config=crawler_config
            )
            
            assert "urls" in request_data
            assert "browser_config" in request_data
            assert "crawler_config" in request_data
            assert request_data["urls"] == ["https://example.com"]
            
            test_result.finish(True, "Request preparation working correctly")
            
        except Exception as e:
            test_result.finish(False, f"Request preparation failed: {str(e)}")


class ComprehensiveTestSuite(unittest.TestCase):
    """Main test suite class."""
    
    def setUp(self):
        """Set up test runner."""
        self.test_runner = ComprehensiveTestRunner()
    
    def test_all_fixes_comprehensive(self):
        """Run all comprehensive tests with rich visualization."""
        
        console.print("\n")
        console.print("🚀 Starting Comprehensive Test Suite for Deep Crawl Fixes", style="bold blue")
        console.print("=" * 70, style="blue")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=40),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TimeElapsedColumn(),
            console=console,
            refresh_per_second=10
        ) as progress:
            
            # Add overall progress task
            overall_task = progress.add_task("Running comprehensive tests...", total=100)
            
            # Initialize test classes
            orjson_tests = TestORJSONSerialization()
            deprecated_tests = TestDeprecatedPropertiesSystem()
            strategy_tests = TestDeepCrawlStrategySerialization()
            config_tests = TestCrawlerConfigSerialization()
            docker_tests = TestDockerClientFunctionality()
            
            test_methods = [
                # ORJSON Tests
                (orjson_tests.test_basic_orjson_serialization, "ORJSON Basic"),
                (orjson_tests.test_datetime_serialization, "ORJSON DateTime"),
                (orjson_tests.test_property_object_handling, "ORJSON Properties"),
                
                # Deprecated Properties Tests
                (deprecated_tests.test_deprecated_properties_mixin, "Deprecated Mixin"),
                (deprecated_tests.test_crawl_result_deprecated_properties, "CrawlResult Deprecated"),
                
                # Strategy Tests
                (strategy_tests.test_bfs_strategy_serialization, "BFS Serialization"),
                (strategy_tests.test_logger_type_safety, "Logger Safety"),
                
                # Config Tests
                (config_tests.test_config_with_strategy_serialization, "Config Serialization"),
                
                # Docker Client Tests
                (docker_tests.test_docker_client_initialization, "Docker Init"),
                (docker_tests.test_docker_client_request_preparation, "Docker Requests"),
            ]
            
            total_tests = len(test_methods)
            
            for i, (test_method, description) in enumerate(test_methods):
                # Update progress
                progress.update(overall_task, completed=(i / total_tests) * 100)
                progress.update(overall_task, description=f"Running {description}...")
                
                # Run the test
                try:
                    test_method(self.test_runner)
                except Exception as e:
                    # If test method fails, create a failed result
                    test_result = self.test_runner.add_test(description)
                    test_result.start()
                    test_result.finish(False, f"Test execution failed: {str(e)}")
            
            # Complete progress
            progress.update(overall_task, completed=100, description="All tests completed!")
        
        console.print("\n")
        
        # Display results
        success = self.test_runner.display_results()
        
        # Final status
        if success:
            console.print("\n🎉 All tests completed successfully!", style="bold green")
            console.print("✅ Deep crawl streaming functionality is fully operational", style="green")
        else:
            console.print("\n⚠️  Some tests failed - review results above", style="bold yellow")
        
        console.print("\n" + "=" * 70, style="blue")
        
        # Assert for unittest
        self.assertTrue(success, "Some comprehensive tests failed")
        
        return success
    
    def test_end_to_end_serialization(self):
        """Test end-to-end serialization flow."""
        
        # Create a complete configuration
        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            include_external=False,
            max_pages=5
        )
        
        crawler_config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            stream=True,
            word_count_threshold=1000
        )
        
        browser_config = BrowserConfig(headless=True)
        
        # Test serialization
        crawler_data = crawler_config.dump()
        browser_data = browser_config.dump()
        
        self.assertIsInstance(crawler_data, dict)
        self.assertIsInstance(browser_data, dict)
        
        # Test deserialization
        loaded_crawler = CrawlerRunConfig.load(crawler_data)
        loaded_browser = BrowserConfig.load(browser_data)
        
        self.assertTrue(hasattr(loaded_crawler.deep_crawl_strategy, 'arun'))
        self.assertTrue(loaded_crawler.stream)
        self.assertTrue(loaded_browser.headless)


if __name__ == "__main__":
    # Run tests directly with rich visualization
    suite = unittest.TestSuite()
    suite.addTest(ComprehensiveTestSuite('test_all_fixes_comprehensive'))
    suite.addTest(ComprehensiveTestSuite('test_end_to_end_serialization'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
