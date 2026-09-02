"""
Tests for type annotation correctness across the crawl4ai public API.

Catches issues like #1898 where arun() was annotated as returning
RunManyReturn (includes AsyncGenerator) but actually always returns
CrawlResultContainer.

These tests use static analysis (inspect + typing introspection) to verify
return type annotations match actual behavior — without needing pyright/mypy
installed in CI.
"""
import asyncio
import collections.abc
import inspect
import typing
from typing import Union, AsyncGenerator, get_type_hints
import pytest


# ── Return type annotation tests ─────────────────────────────────────────

class TestReturnTypeAnnotations:
    """Verify that public method return types are correctly annotated."""

    def _get_return_annotation(self, cls, method_name):
        """Get the return type annotation for a method."""
        method = getattr(cls, method_name)
        hints = typing.get_type_hints(method)
        return hints.get("return")

    def _annotation_contains(self, annotation, target_type):
        """Check if a type annotation contains a specific type (including in unions).

        Handles both typing.AsyncGenerator and collections.abc.AsyncGenerator,
        since typing generics have __origin__ pointing to the abc class.
        """
        if annotation is target_type:
            return True
        origin = getattr(annotation, "__origin__", None)
        if origin is target_type:
            return True
        if origin is Union:
            return any(
                self._annotation_contains(arg, target_type)
                for arg in annotation.__args__
            )
        return False

    def test_arun_does_not_include_async_generator(self):
        """
        #1898: arun() always returns CrawlResultContainer, never AsyncGenerator.
        The return type should NOT include AsyncGenerator.
        """
        from crawl4ai import AsyncWebCrawler
        ret = self._get_return_annotation(AsyncWebCrawler, "arun")
        assert ret is not None, "arun() has no return type annotation"

        # Check both typing.AsyncGenerator and collections.abc.AsyncGenerator
        # (typing generics have __origin__ = collections.abc.AsyncGenerator)
        has_async_gen = (
            self._annotation_contains(ret, collections.abc.AsyncGenerator)
            or self._annotation_contains(ret, AsyncGenerator)
        )
        assert not has_async_gen, (
            f"arun() return type includes AsyncGenerator but arun() never yields. "
            f"Current annotation: {ret}. "
            f"Should be CrawlResultContainer or CrawlResult."
        )

    def test_arun_many_return_type_exists(self):
        """arun_many() should have a return type annotation."""
        from crawl4ai import AsyncWebCrawler
        ret = self._get_return_annotation(AsyncWebCrawler, "arun_many")
        assert ret is not None, "arun_many() has no return type annotation"

    def test_aprocess_html_return_type_exists(self):
        """aprocess_html() should have a return type annotation."""
        from crawl4ai import AsyncWebCrawler
        ret = self._get_return_annotation(AsyncWebCrawler, "aprocess_html")
        assert ret is not None, "aprocess_html() has no return type annotation"


# ── Parameter annotation tests ───────────────────────────────────────────

class TestParameterAnnotations:
    """Verify that public method parameters have type annotations."""

    def _get_untyped_params(self, cls, method_name, ignore=("self", "kwargs")):
        """Find parameters without type annotations."""
        method = getattr(cls, method_name)
        sig = inspect.signature(method)
        untyped = []
        for name, param in sig.parameters.items():
            if name in ignore:
                continue
            if param.annotation is inspect.Parameter.empty:
                untyped.append(name)
        return untyped

    def test_arun_params_annotated(self):
        """arun() public params should have type annotations."""
        from crawl4ai import AsyncWebCrawler
        untyped = self._get_untyped_params(AsyncWebCrawler, "arun")
        # Allow **kwargs to be untyped, but core params should be typed
        assert "url" not in untyped, "arun(url=...) missing type annotation"
        assert "config" not in untyped, "arun(config=...) missing type annotation"

    def test_arun_many_params_annotated(self):
        """arun_many() public params should have type annotations."""
        from crawl4ai import AsyncWebCrawler
        untyped = self._get_untyped_params(AsyncWebCrawler, "arun_many")
        assert "urls" not in untyped, "arun_many(urls=...) missing type annotation"


# ── Consistency tests ────────────────────────────────────────────────────

class TestAnnotationConsistency:
    """Verify that annotations match actual runtime behavior."""

    def test_arun_actually_returns_what_annotation_says(self):
        """
        arun() should be annotated as returning CrawlResult directly.
        """
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.models import CrawlResult

        hints = typing.get_type_hints(AsyncWebCrawler.arun)
        ret = hints.get("return")
        if ret is None:
            pytest.skip("No return annotation to check")

        # Get the actual type (unwrap generics if needed)
        actual_type = getattr(ret, "__origin__", ret)

        assert actual_type is CrawlResult, (
            f"arun() should return CrawlResult, but annotation is {ret}"
        )

    def test_config_classes_init_params_match_attributes(self):
        """
        CrawlerRunConfig.__init__ params should become attributes.
        Catches cases where a param is added to __init__ but not stored.
        """
        from crawl4ai import CrawlerRunConfig

        sig = inspect.signature(CrawlerRunConfig.__init__)
        config = CrawlerRunConfig()

        missing = []
        for name in sig.parameters:
            if name == "self":
                continue
            if not hasattr(config, name):
                missing.append(name)

        assert not missing, (
            f"CrawlerRunConfig.__init__ has params that aren't stored as attributes: {missing}"
        )


# ── Public API export tests ──────────────────────────────────────────────

class TestPublicAPIExports:
    """Verify that types referenced in public annotations are importable."""

    def test_crawl_result_importable(self):
        from crawl4ai import CrawlResult
        assert CrawlResult is not None

    def test_crawl_result_container_importable(self):
        from crawl4ai.models import CrawlResultContainer
        assert CrawlResultContainer is not None

    def test_run_many_return_importable(self):
        from crawl4ai.models import RunManyReturn
        assert RunManyReturn is not None

    def test_markdown_generation_result_importable(self):
        from crawl4ai import MarkdownGenerationResult
        assert MarkdownGenerationResult is not None
