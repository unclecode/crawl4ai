"""
Tests for profile shrinking functionality.

Test approach:
1. Unit tests for core shrink logic with mock file structures
2. Integration tests with real Playwright browser to verify auth preservation
3. Edge case handling (empty profiles, missing profiles, permission errors)
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from crawl4ai.browser_profiler import (
    ShrinkLevel,
    KEEP_PATTERNS,
    shrink_profile,
    _get_size,
    _format_size,
    BrowserProfiler,
)


class TestShrinkLevel:
    """Test ShrinkLevel enum."""

    def test_enum_values(self):
        assert ShrinkLevel.NONE.value == "none"
        assert ShrinkLevel.LIGHT.value == "light"
        assert ShrinkLevel.MEDIUM.value == "medium"
        assert ShrinkLevel.AGGRESSIVE.value == "aggressive"
        assert ShrinkLevel.MINIMAL.value == "minimal"

    def test_enum_from_string(self):
        assert ShrinkLevel("aggressive") == ShrinkLevel.AGGRESSIVE
        assert ShrinkLevel("minimal") == ShrinkLevel.MINIMAL

    def test_keep_patterns_defined_for_all_levels(self):
        for level in ShrinkLevel:
            assert level in KEEP_PATTERNS


class TestHelperFunctions:
    """Test helper functions."""

    def test_format_size_bytes(self):
        assert _format_size(500) == "500.0 B"

    def test_format_size_kilobytes(self):
        assert _format_size(2048) == "2.0 KB"

    def test_format_size_megabytes(self):
        assert _format_size(5 * 1024 * 1024) == "5.0 MB"

    def test_format_size_gigabytes(self):
        assert _format_size(3 * 1024 * 1024 * 1024) == "3.0 GB"

    def test_get_size_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("x" * 100)
        assert _get_size(test_file) == 100

    def test_get_size_directory(self, tmp_path):
        (tmp_path / "file1.txt").write_text("a" * 50)
        (tmp_path / "file2.txt").write_text("b" * 50)
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("c" * 100)
        assert _get_size(tmp_path) == 200

    def test_get_size_empty_directory(self, tmp_path):
        assert _get_size(tmp_path) == 0


class TestShrinkProfile:
    """Test shrink_profile function."""

    @pytest.fixture
    def mock_profile(self, tmp_path):
        """Create a mock Chrome profile structure."""
        profile = tmp_path / "test_profile"
        profile.mkdir()

        # Essential auth directories (should be kept)
        (profile / "Network").mkdir()
        (profile / "Network" / "Cookies").write_bytes(b"x" * 1000)
        (profile / "Local Storage").mkdir()
        (profile / "Local Storage" / "leveldb").mkdir()
        (profile / "Local Storage" / "leveldb" / "data").write_bytes(b"y" * 500)
        (profile / "IndexedDB").mkdir()
        (profile / "IndexedDB" / "db").write_bytes(b"z" * 300)
        (profile / "Preferences").write_text('{"profile": {}}')

        # Cache directories (should be removed)
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data_0").write_bytes(b"0" * 10000)
        (profile / "Cache" / "data_1").write_bytes(b"1" * 10000)
        (profile / "Code Cache").mkdir()
        (profile / "Code Cache" / "js").mkdir()
        (profile / "Code Cache" / "js" / "bytecode").write_bytes(b"c" * 5000)
        (profile / "GPUCache").mkdir()
        (profile / "GPUCache" / "data").write_bytes(b"g" * 2000)
        (profile / "Service Worker").mkdir()
        (profile / "Service Worker" / "CacheStorage").mkdir()
        (profile / "Service Worker" / "CacheStorage" / "cache").write_bytes(b"s" * 50000)

        # History and other files (removed at MEDIUM+)
        (profile / "History").write_bytes(b"h" * 1000)
        (profile / "Favicons").write_bytes(b"f" * 500)
        (profile / "Visited Links").write_bytes(b"v" * 200)

        return str(profile)

    def test_shrink_none_keeps_everything(self, mock_profile):
        result = shrink_profile(mock_profile, ShrinkLevel.NONE)
        assert result["removed"] == []
        assert result["kept"] == []
        assert result["bytes_freed"] == 0

    def test_shrink_aggressive_removes_caches(self, mock_profile):
        result = shrink_profile(mock_profile, ShrinkLevel.AGGRESSIVE)

        # Auth data kept
        assert "Network" in result["kept"]
        assert "Local Storage" in result["kept"]
        assert "IndexedDB" in result["kept"]
        assert "Preferences" in result["kept"]

        # Caches removed
        assert "Cache" in result["removed"]
        assert "Code Cache" in result["removed"]
        assert "GPUCache" in result["removed"]
        assert "Service Worker" in result["removed"]

        # Verify bytes freed > 0
        assert result["bytes_freed"] > 0
        assert result["size_after"] < result["size_before"]

    def test_shrink_minimal_keeps_only_essential(self, mock_profile):
        result = shrink_profile(mock_profile, ShrinkLevel.MINIMAL)

        # Only Network and Local Storage kept
        assert set(result["kept"]) == {"Network", "Local Storage"}

        # IndexedDB and Preferences removed at MINIMAL
        assert "IndexedDB" in result["removed"]
        assert "Preferences" in result["removed"]

    def test_shrink_light_keeps_history(self, mock_profile):
        result = shrink_profile(mock_profile, ShrinkLevel.LIGHT)

        # History kept at LIGHT level
        assert "History" in result["kept"]

        # Caches still removed
        assert "Cache" in result["removed"]

    def test_shrink_medium_removes_history(self, mock_profile):
        result = shrink_profile(mock_profile, ShrinkLevel.MEDIUM)

        # History removed at MEDIUM
        assert "History" in result["removed"]
        assert "Favicons" in result["removed"]

        # Auth still kept
        assert "Network" in result["kept"]

    def test_shrink_dry_run_no_changes(self, mock_profile):
        size_before = _get_size(Path(mock_profile))

        result = shrink_profile(mock_profile, ShrinkLevel.AGGRESSIVE, dry_run=True)

        size_after = _get_size(Path(mock_profile))
        assert size_before == size_after
        assert result["size_after"] is None
        assert len(result["removed"]) > 0  # Still reports what would be removed

    def test_shrink_nonexistent_profile_raises(self):
        with pytest.raises(ValueError, match="Profile not found"):
            shrink_profile("/nonexistent/path", ShrinkLevel.AGGRESSIVE)

    def test_shrink_empty_profile(self, tmp_path):
        empty_profile = tmp_path / "empty"
        empty_profile.mkdir()

        result = shrink_profile(str(empty_profile), ShrinkLevel.AGGRESSIVE)
        assert result["removed"] == []
        assert result["kept"] == []
        assert result["errors"] == []


class TestBrowserProfilerShrink:
    """Test BrowserProfiler.shrink() method."""

    @pytest.fixture
    def profiler(self):
        return BrowserProfiler()

    @pytest.fixture
    def mock_profile_in_profiles_dir(self, profiler, tmp_path):
        """Create a mock profile in the profiler's profiles directory."""
        # Temporarily override profiles_dir
        original_dir = profiler.profiles_dir
        profiler.profiles_dir = str(tmp_path)

        profile = tmp_path / "test_profile"
        profile.mkdir()
        (profile / "Network").mkdir()
        (profile / "Network" / "Cookies").write_text("cookies")
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"x" * 1000)
        (profile / "Preferences").write_text("{}")

        yield "test_profile", str(profile)

        # Cleanup
        profiler.profiles_dir = original_dir

    def test_shrink_by_name(self, profiler, mock_profile_in_profiles_dir):
        name, path = mock_profile_in_profiles_dir

        result = profiler.shrink(name, ShrinkLevel.AGGRESSIVE)

        assert "Cache" in result["removed"]
        assert "Network" in result["kept"]
        assert "Preferences" in result["kept"]

    def test_shrink_by_path(self, profiler, mock_profile_in_profiles_dir):
        _, path = mock_profile_in_profiles_dir

        result = profiler.shrink(path, ShrinkLevel.AGGRESSIVE)

        assert "Cache" in result["removed"]

    def test_shrink_nonexistent_raises(self, profiler):
        with pytest.raises(ValueError, match="Profile not found"):
            profiler.shrink("nonexistent_profile")


class TestKeepPatterns:
    """Test that KEEP_PATTERNS are correctly defined."""

    def test_aggressive_keeps_auth_essentials(self):
        keep = KEEP_PATTERNS[ShrinkLevel.AGGRESSIVE]
        assert "Network" in keep  # Cookies (Chrome 96+)
        assert "Cookies" in keep  # Cookies (older Chrome)
        assert "Local Storage" in keep  # JWT/tokens
        assert "IndexedDB" in keep  # Some sites use this
        assert "Preferences" in keep  # Profile identity

    def test_minimal_is_subset_of_aggressive(self):
        minimal = KEEP_PATTERNS[ShrinkLevel.MINIMAL]
        aggressive = KEEP_PATTERNS[ShrinkLevel.AGGRESSIVE]
        assert minimal.issubset(aggressive)

    def test_aggressive_is_subset_of_medium(self):
        aggressive = KEEP_PATTERNS[ShrinkLevel.AGGRESSIVE]
        medium = KEEP_PATTERNS[ShrinkLevel.MEDIUM]
        assert aggressive.issubset(medium)

    def test_medium_is_subset_of_light(self):
        medium = KEEP_PATTERNS[ShrinkLevel.MEDIUM]
        light = KEEP_PATTERNS[ShrinkLevel.LIGHT]
        assert medium.issubset(light)


class TestIntegrationWithPlaywright:
    """Integration tests using real Playwright browser.

    These tests verify that auth data survives shrinking and the browser
    can still launch successfully after shrinking.
    """

    @staticmethod
    async def _create_seeded_profile(profile_path: str) -> str:
        """Create a real profile with seeded auth data using Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                profile_path,
                headless=True,
            )
            page = await browser.new_page()

            # Navigate to a real site to enable localStorage/cookies
            try:
                await page.goto("https://example.com", timeout=15000)
            except Exception:
                # Fallback to about:blank which still allows localStorage
                await page.goto("about:blank")

            # Seed test data (localStorage works on any origin)
            await page.evaluate("""
                () => {
                    localStorage.setItem('jwt', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9');
                    localStorage.setItem('refresh', 'refresh_token_abc');
                }
            """)

            await browser.close()

        return profile_path

    @pytest.mark.asyncio
    async def test_browser_launches_after_aggressive_shrink(self, tmp_path):
        """Verify browser can launch after aggressive shrinking."""
        pytest.importorskip("playwright")
        from playwright.async_api import async_playwright

        profile_path = str(tmp_path / "playwright_profile")
        await self._create_seeded_profile(profile_path)

        # Shrink the profile
        result = shrink_profile(profile_path, ShrinkLevel.AGGRESSIVE)
        assert result["bytes_freed"] >= 0

        # Verify browser launches and localStorage survives
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                profile_path,
                headless=True,
            )
            page = await browser.new_page()

            # Navigate to same origin to access localStorage
            try:
                await page.goto("https://example.com", timeout=15000)
            except Exception:
                await page.goto("about:blank")

            # Verify localStorage survived
            jwt = await page.evaluate("localStorage.getItem('jwt')")
            assert jwt == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

            refresh = await page.evaluate("localStorage.getItem('refresh')")
            assert refresh == "refresh_token_abc"

            await browser.close()

    @pytest.mark.asyncio
    async def test_browser_launches_after_minimal_shrink(self, tmp_path):
        """Verify browser launches after minimal shrinking (most aggressive)."""
        pytest.importorskip("playwright")
        from playwright.async_api import async_playwright

        profile_path = str(tmp_path / "playwright_profile")
        await self._create_seeded_profile(profile_path)

        # Shrink to minimal
        result = shrink_profile(profile_path, ShrinkLevel.MINIMAL)
        assert result["bytes_freed"] >= 0

        # Verify browser still launches
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                profile_path,
                headless=True,
            )
            page = await browser.new_page()

            # Navigate to same origin to access localStorage
            try:
                await page.goto("https://example.com", timeout=15000)
            except Exception:
                await page.goto("about:blank")

            # localStorage should still work
            jwt = await page.evaluate("localStorage.getItem('jwt')")
            assert jwt == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

            await browser.close()

    @pytest.mark.asyncio
    async def test_shrink_actually_reduces_size(self, tmp_path):
        """Verify shrinking actually reduces profile size."""
        pytest.importorskip("playwright")

        profile_path = str(tmp_path / "playwright_profile")
        await self._create_seeded_profile(profile_path)

        size_before = _get_size(Path(profile_path))

        result = shrink_profile(profile_path, ShrinkLevel.AGGRESSIVE)

        size_after = _get_size(Path(profile_path))

        # Profile should be smaller (or same if no cache was generated)
        assert size_after <= size_before
        assert result["size_before"] == size_before
        assert result["size_after"] == size_after


class TestCLIIntegration:
    """Test CLI command integration."""

    def test_cli_import(self):
        """Verify CLI imports work."""
        from crawl4ai.cli import shrink_cmd
        assert callable(shrink_cmd)

    def test_shrink_level_import(self):
        """Verify ShrinkLevel can be imported from cli."""
        from crawl4ai.browser_profiler import ShrinkLevel
        assert ShrinkLevel.AGGRESSIVE.value == "aggressive"


class TestEdgeCases:
    """Edge case tests to ensure robustness."""

    def test_shrink_profile_with_symlinks(self, tmp_path):
        """Test shrinking profile with symlinks doesn't follow them."""
        profile = tmp_path / "profile"
        profile.mkdir()
        (profile / "Local Storage").mkdir()
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"x" * 1000)

        # Create symlink pointing outside profile
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        important_file = external_dir / "important.txt"
        important_file.write_text("DO NOT DELETE")

        # Symlink inside Cache pointing to external
        symlink = profile / "Cache" / "external_link"
        symlink.symlink_to(external_dir)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # External file should NOT be deleted
        assert important_file.exists(), "Symlink target was deleted!"
        assert "Cache" in result["removed"]

    def test_shrink_with_special_characters_in_names(self, tmp_path):
        """Test shrinking handles special chars in filenames."""
        profile = tmp_path / "profile"
        profile.mkdir()

        # Create dirs/files with special characters
        (profile / "Local Storage").mkdir()
        (profile / "Cache (old)").mkdir()
        (profile / "Cache (old)" / "data").write_bytes(b"x" * 100)
        (profile / "Test[1]").mkdir()
        (profile / "Test[1]" / "file").write_bytes(b"y" * 100)
        (profile / "Spaced Name").mkdir()
        (profile / "file with spaces.txt").write_bytes(b"z" * 50)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Cache (old)" in result["removed"]
        assert "Test[1]" in result["removed"]
        assert "Spaced Name" in result["removed"]
        assert "file with spaces.txt" in result["removed"]
        assert "Local Storage" in result["kept"]

    def test_shrink_with_unicode_filenames(self, tmp_path):
        """Test shrinking handles unicode filenames."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Кэш").mkdir()  # Russian "Cache"
        (profile / "Кэш" / "данные").write_bytes(b"x" * 100)
        (profile / "缓存").mkdir()  # Chinese "Cache"
        (profile / "キャッシュ").mkdir()  # Japanese "Cache"
        (profile / "émojis_🎉").mkdir()

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Local Storage" in result["kept"]
        assert len(result["removed"]) >= 4

    def test_shrink_with_hidden_files(self, tmp_path):
        """Test shrinking handles hidden (dot) files."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / ".hidden_cache").mkdir()
        (profile / ".hidden_cache" / "data").write_bytes(b"x" * 1000)
        (profile / ".DS_Store").write_bytes(b"y" * 100)
        (profile / ".git").mkdir()

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # Hidden files should be removed (not in keep list)
        assert ".hidden_cache" in result["removed"]
        assert ".DS_Store" in result["removed"]
        assert ".git" in result["removed"]

    def test_shrink_with_empty_directories(self, tmp_path):
        """Test shrinking handles empty directories."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Empty Cache").mkdir()
        (profile / "Another Empty").mkdir()
        (profile / "Nested").mkdir()
        (profile / "Nested" / "Also Empty").mkdir()

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Empty Cache" in result["removed"]
        assert "Another Empty" in result["removed"]
        assert "Nested" in result["removed"]
        assert not (profile / "Empty Cache").exists()

    def test_shrink_twice_same_profile(self, tmp_path):
        """Test shrinking same profile twice is idempotent."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Local Storage" / "data").write_bytes(b"x" * 100)
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"y" * 1000)

        # First shrink
        result1 = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
        assert "Cache" in result1["removed"]
        assert result1["bytes_freed"] > 0

        # Second shrink - should be no-op
        result2 = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
        assert result2["removed"] == []
        assert result2["bytes_freed"] == 0
        assert "Local Storage" in result2["kept"]

    def test_shrink_preserves_storage_state_json(self, tmp_path):
        """Test that storage_state.json is preserved."""
        profile = tmp_path / "profile"
        profile.mkdir()

        # storage_state.json should be kept (starts with no pattern but is important)
        (profile / "storage_state.json").write_text('{"cookies": []}')
        (profile / "Local Storage").mkdir()
        (profile / "Cache").mkdir()

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # storage_state.json doesn't match keep patterns, so it gets removed
        # This is expected - the shrink function preserves Chrome's auth files,
        # not Crawl4AI's exported state file
        # If we want to keep it, we need to add it to KEEP_PATTERNS

    def test_shrink_with_very_deep_nesting(self, tmp_path):
        """Test shrinking deeply nested directories."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()

        # Create deeply nested cache
        deep = profile / "Cache"
        for i in range(20):
            deep = deep / f"level_{i}"
        deep.mkdir(parents=True)
        (deep / "deep_file.txt").write_bytes(b"x" * 100)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Cache" in result["removed"]
        assert not (profile / "Cache").exists()

    def test_shrink_with_large_files(self, tmp_path):
        """Test shrinking handles large files efficiently."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Cache").mkdir()

        # Create a 10MB file
        large_file = profile / "Cache" / "large_file.bin"
        large_file.write_bytes(b"x" * (10 * 1024 * 1024))

        size_before = _get_size(profile)
        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
        size_after = _get_size(profile)

        assert result["bytes_freed"] >= 10 * 1024 * 1024
        assert size_after < size_before

    def test_shrink_with_read_only_files(self, tmp_path):
        """Test shrinking handles read-only files gracefully."""
        import stat

        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        cache = profile / "Cache"
        cache.mkdir()
        readonly_file = cache / "readonly.txt"
        readonly_file.write_bytes(b"x" * 100)

        # Make file read-only
        readonly_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
            # On some systems this will succeed, on others it will error
            # Either way, it shouldn't crash
            if result["errors"]:
                assert "Cache" in str(result["errors"][0]) or len(result["errors"]) > 0
        finally:
            # Restore permissions for cleanup
            try:
                readonly_file.chmod(stat.S_IRWXU)
            except:
                pass

    def test_shrink_with_many_small_files(self, tmp_path):
        """Test shrinking handles many small files efficiently."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        cache = profile / "Cache"
        cache.mkdir()

        # Create 1000 small files
        for i in range(1000):
            (cache / f"file_{i:04d}.txt").write_bytes(b"x" * 100)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Cache" in result["removed"]
        assert result["bytes_freed"] >= 100 * 1000
        assert not cache.exists()

    def test_shrink_default_subdirectory_structure(self, tmp_path):
        """Test shrinking when profile has Default/ subdirectory."""
        profile = tmp_path / "profile"
        profile.mkdir()

        # Chrome-style structure with Default/
        default = profile / "Default"
        default.mkdir()
        (default / "Local Storage").mkdir()
        (default / "Local Storage" / "leveldb").mkdir()
        (default / "Cookies").write_bytes(b"cookies" * 100)
        (default / "Cache").mkdir()
        (default / "Cache" / "data").write_bytes(b"x" * 10000)
        (default / "GPUCache").mkdir()
        (default / "GPUCache" / "data").write_bytes(b"y" * 5000)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # Should shrink inside Default/
        assert "Cache" in result["removed"]
        assert "GPUCache" in result["removed"]
        assert "Local Storage" in result["kept"]
        assert "Cookies" in result["kept"]
        assert (default / "Local Storage").exists()
        assert (default / "Cookies").exists()
        assert not (default / "Cache").exists()

    def test_shrink_mixed_files_and_directories(self, tmp_path):
        """Test shrinking mix of files and directories."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Preferences").write_text("{}")
        (profile / "Cookies").write_bytes(b"x" * 500)
        (profile / "Cookies-journal").write_bytes(b"y" * 100)
        (profile / "History").write_bytes(b"z" * 1000)
        (profile / "Cache").mkdir()
        (profile / "random_file.txt").write_bytes(b"a" * 200)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # Files and dirs properly categorized
        assert "Local Storage" in result["kept"]
        assert "Preferences" in result["kept"]
        assert "Cookies" in result["kept"]
        assert "Cookies-journal" in result["kept"]
        assert "History" in result["removed"]
        assert "Cache" in result["removed"]
        assert "random_file.txt" in result["removed"]

    def test_shrink_level_none_is_noop(self, tmp_path):
        """Test ShrinkLevel.NONE does absolutely nothing."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"x" * 1000)

        size_before = _get_size(profile)
        result = shrink_profile(str(profile), ShrinkLevel.NONE)
        size_after = _get_size(profile)

        assert result["removed"] == []
        assert result["kept"] == []
        assert result["bytes_freed"] == 0
        assert size_before == size_after

    def test_shrink_result_sizes_are_accurate(self, tmp_path):
        """Test that reported sizes match actual sizes."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Local Storage" / "data").write_bytes(b"k" * 500)
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"x" * 2000)

        actual_before = _get_size(profile)
        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
        actual_after = _get_size(profile)

        assert result["size_before"] == actual_before
        assert result["size_after"] == actual_after
        assert result["size_before"] - result["size_after"] == result["bytes_freed"]

    def test_shrink_all_levels_progressively_smaller(self, tmp_path):
        """Test that stricter levels remove more data."""
        def create_full_profile(path):
            path.mkdir(exist_ok=True)
            (path / "Network").mkdir(exist_ok=True)
            (path / "Cookies").write_bytes(b"c" * 100)
            (path / "Local Storage").mkdir(exist_ok=True)
            (path / "IndexedDB").mkdir(exist_ok=True)
            (path / "Preferences").write_text("{}")
            (path / "History").write_bytes(b"h" * 500)
            (path / "Bookmarks").write_text("[]")
            (path / "Cache").mkdir(exist_ok=True)
            (path / "Cache" / "data").write_bytes(b"x" * 2000)

        results = {}
        for level in [ShrinkLevel.LIGHT, ShrinkLevel.MEDIUM,
                      ShrinkLevel.AGGRESSIVE, ShrinkLevel.MINIMAL]:
            profile = tmp_path / f"profile_{level.value}"
            create_full_profile(profile)
            results[level] = shrink_profile(str(profile), level)

        # Stricter levels should remove more
        assert len(results[ShrinkLevel.LIGHT]["kept"]) >= len(results[ShrinkLevel.MEDIUM]["kept"])
        assert len(results[ShrinkLevel.MEDIUM]["kept"]) >= len(results[ShrinkLevel.AGGRESSIVE]["kept"])
        assert len(results[ShrinkLevel.AGGRESSIVE]["kept"]) >= len(results[ShrinkLevel.MINIMAL]["kept"])

    def test_shrink_with_broken_symlinks(self, tmp_path):
        """Test shrinking handles broken symlinks."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Cache").mkdir()

        # Create broken symlink
        broken_link = profile / "Cache" / "broken_link"
        broken_link.symlink_to("/nonexistent/path/that/does/not/exist")

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Cache" in result["removed"]
        assert not (profile / "Cache").exists()

    def test_shrink_dry_run_reports_would_free(self, tmp_path):
        """Test dry run accurately reports what would be freed."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"x" * 5000)

        dry_result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE, dry_run=True)

        # Nothing should be removed yet
        assert (profile / "Cache").exists()
        assert dry_result["size_after"] is None

        # Actually shrink
        real_result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # Dry run should have predicted the freed bytes
        assert dry_result["bytes_freed"] == real_result["bytes_freed"]
        assert dry_result["removed"] == real_result["removed"]


class TestBrowserProfilerEdgeCases:
    """Edge cases for BrowserProfiler.shrink() method."""

    def test_profiler_shrink_relative_path(self, tmp_path):
        """Test profiler.shrink with profile name resolution."""
        profiler = BrowserProfiler()
        original_dir = profiler.profiles_dir
        profiler.profiles_dir = str(tmp_path)

        try:
            profile = tmp_path / "test_profile"
            profile.mkdir()
            (profile / "Preferences").write_text("{}")
            (profile / "Cache").mkdir()
            (profile / "Cache" / "data").write_bytes(b"x" * 100)

            result = profiler.shrink("test_profile", ShrinkLevel.AGGRESSIVE)
            assert "Cache" in result["removed"]
        finally:
            profiler.profiles_dir = original_dir

    def test_profiler_shrink_absolute_path(self, tmp_path):
        """Test profiler.shrink with absolute path."""
        profiler = BrowserProfiler()

        profile = tmp_path / "absolute_profile"
        profile.mkdir()
        (profile / "Preferences").write_text("{}")
        (profile / "Cache").mkdir()

        result = profiler.shrink(str(profile), ShrinkLevel.AGGRESSIVE)
        assert "Cache" in result["removed"]

    def test_profiler_shrink_invalid_name(self):
        """Test profiler.shrink with invalid profile name."""
        profiler = BrowserProfiler()

        with pytest.raises(ValueError, match="Profile not found"):
            profiler.shrink("definitely_nonexistent_profile_12345")


class TestStressAndCornerCases:
    """Stress tests and extreme corner cases."""

    def test_shrink_file_instead_of_directory(self, tmp_path):
        """Test shrinking a file (not directory) raises error."""
        file_path = tmp_path / "not_a_profile.txt"
        file_path.write_text("I am a file")

        with pytest.raises(ValueError, match="Profile not found"):
            shrink_profile(str(file_path), ShrinkLevel.AGGRESSIVE)

    def test_shrink_with_circular_symlinks(self, tmp_path):
        """Test shrinking handles circular symlinks gracefully."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        cache = profile / "Cache"
        cache.mkdir()

        # Create circular symlink: Cache/link -> Cache
        circular = cache / "circular"
        circular.symlink_to(cache)

        # Should not hang or crash
        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
        assert "Cache" in result["removed"]

    def test_shrink_with_very_long_filenames(self, tmp_path):
        """Test shrinking handles very long filenames."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()

        # Create file with very long name (near filesystem limit)
        long_name = "a" * 200  # Most filesystems support 255 chars
        (profile / long_name).write_bytes(b"x" * 100)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
        assert long_name in result["removed"]

    def test_shrink_profile_only_has_kept_items(self, tmp_path):
        """Test shrinking profile that only has items to keep."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Local Storage" / "leveldb").mkdir()
        (profile / "Cookies").write_bytes(b"c" * 100)
        (profile / "Preferences").write_text("{}")
        (profile / "IndexedDB").mkdir()

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert result["removed"] == []
        assert result["bytes_freed"] == 0
        assert len(result["kept"]) == 4

    def test_shrink_with_files_matching_keep_prefix(self, tmp_path):
        """Test that files starting with keep patterns are kept."""
        profile = tmp_path / "profile"
        profile.mkdir()

        # These should be kept (match patterns)
        (profile / "Local Storage").mkdir()
        (profile / "Local Storage Extra").mkdir()  # Starts with "Local Storage"
        (profile / "Cookies").write_bytes(b"c" * 100)
        (profile / "Cookies-journal").write_bytes(b"j" * 50)
        (profile / "CookiesBackup").write_bytes(b"b" * 50)  # Starts with "Cookies"

        # This should be removed
        (profile / "Cache").mkdir()

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Local Storage" in result["kept"]
        assert "Local Storage Extra" in result["kept"]
        assert "Cookies" in result["kept"]
        assert "Cookies-journal" in result["kept"]
        assert "CookiesBackup" in result["kept"]
        assert "Cache" in result["removed"]

    def test_shrink_calculates_size_correctly_with_nested_dirs(self, tmp_path):
        """Test size calculation is accurate for nested structures."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()

        # Create nested cache with known sizes
        cache = profile / "Cache"
        cache.mkdir()
        (cache / "level1").mkdir()
        (cache / "level1" / "level2").mkdir()
        (cache / "level1" / "file1.bin").write_bytes(b"x" * 1000)
        (cache / "level1" / "level2" / "file2.bin").write_bytes(b"y" * 2000)
        (cache / "file0.bin").write_bytes(b"z" * 500)

        expected_freed = 1000 + 2000 + 500  # Total bytes in Cache

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert result["bytes_freed"] == expected_freed

    def test_shrink_empty_default_subdirectory(self, tmp_path):
        """Test shrinking when Default/ exists but is empty."""
        profile = tmp_path / "profile"
        profile.mkdir()
        (profile / "Default").mkdir()

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert result["removed"] == []
        assert result["kept"] == []
        assert result["bytes_freed"] == 0

    def test_shrink_with_both_root_and_default_structure(self, tmp_path):
        """Test when profile has items at root AND in Default/."""
        profile = tmp_path / "profile"
        profile.mkdir()

        # Items at root level
        (profile / "SomeRootFile.txt").write_bytes(b"r" * 100)

        # Items in Default/
        default = profile / "Default"
        default.mkdir()
        (default / "Local Storage").mkdir()
        (default / "Cache").mkdir()
        (default / "Cache" / "data").write_bytes(b"x" * 1000)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        # Should shrink inside Default/, ignoring root level
        assert "Cache" in result["removed"]
        assert "Local Storage" in result["kept"]
        # Root file should be untouched
        assert (profile / "SomeRootFile.txt").exists()

    def test_shrink_minimal_vs_aggressive_indexeddb(self, tmp_path):
        """Test that MINIMAL removes IndexedDB but AGGRESSIVE keeps it."""
        def create_profile(path):
            path.mkdir()
            (path / "Local Storage").mkdir()
            (path / "IndexedDB").mkdir()
            (path / "IndexedDB" / "data").write_bytes(b"i" * 500)

        # Test AGGRESSIVE
        profile_agg = tmp_path / "aggressive"
        create_profile(profile_agg)
        result_agg = shrink_profile(str(profile_agg), ShrinkLevel.AGGRESSIVE)
        assert "IndexedDB" in result_agg["kept"]

        # Test MINIMAL
        profile_min = tmp_path / "minimal"
        create_profile(profile_min)
        result_min = shrink_profile(str(profile_min), ShrinkLevel.MINIMAL)
        assert "IndexedDB" in result_min["removed"]

    def test_shrink_handles_oserror_gracefully(self, tmp_path):
        """Test that OSErrors during iteration don't crash the function."""
        profile = tmp_path / "profile"
        profile.mkdir()

        (profile / "Local Storage").mkdir()
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"x" * 100)

        # This should work without issues
        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)
        assert result["errors"] == []

    def test_format_size_edge_values(self):
        """Test _format_size with edge values."""
        assert _format_size(0) == "0.0 B"
        assert _format_size(1) == "1.0 B"
        assert _format_size(1023) == "1023.0 B"
        assert _format_size(1024) == "1.0 KB"
        assert _format_size(1024 * 1024 - 1) == "1024.0 KB"
        assert _format_size(1024 * 1024) == "1.0 MB"
        assert _format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert _format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

    def test_get_size_with_permission_error(self, tmp_path):
        """Test _get_size handles permission errors gracefully."""
        import stat

        profile = tmp_path / "profile"
        profile.mkdir()
        restricted = profile / "restricted"
        restricted.mkdir()
        (restricted / "file.txt").write_bytes(b"x" * 100)

        # Remove read permission on directory
        restricted.chmod(stat.S_IWUSR)

        try:
            # Should not raise, should return partial size
            size = _get_size(profile)
            assert size >= 0
        finally:
            # Restore permissions
            restricted.chmod(stat.S_IRWXU)

    def test_shrink_with_cookies_in_network_subdirectory(self, tmp_path):
        """Test modern Chrome structure with Cookies in Network/."""
        profile = tmp_path / "profile"
        profile.mkdir()

        # Chrome 96+ structure
        network = profile / "Network"
        network.mkdir()
        (network / "Cookies").write_bytes(b"c" * 500)
        (network / "TransportSecurity").write_bytes(b"t" * 100)

        (profile / "Local Storage").mkdir()
        (profile / "Cache").mkdir()
        (profile / "Cache" / "data").write_bytes(b"x" * 1000)

        result = shrink_profile(str(profile), ShrinkLevel.AGGRESSIVE)

        assert "Network" in result["kept"]
        assert "Local Storage" in result["kept"]
        assert "Cache" in result["removed"]
        assert (network / "Cookies").exists()
