"""Unit tests for head fingerprinting."""

import pytest
from crawl4ai.utils import compute_head_fingerprint


class TestHeadFingerprint:
    """Tests for the compute_head_fingerprint function."""

    def test_same_content_same_fingerprint(self):
        """Identical <head> content produces same fingerprint."""
        head = "<head><title>Test Page</title></head>"
        fp1 = compute_head_fingerprint(head)
        fp2 = compute_head_fingerprint(head)
        assert fp1 == fp2
        assert fp1 != ""

    def test_different_title_different_fingerprint(self):
        """Different title produces different fingerprint."""
        head1 = "<head><title>Title A</title></head>"
        head2 = "<head><title>Title B</title></head>"
        assert compute_head_fingerprint(head1) != compute_head_fingerprint(head2)

    def test_empty_head_returns_empty_string(self):
        """Empty or None head should return empty fingerprint."""
        assert compute_head_fingerprint("") == ""
        assert compute_head_fingerprint(None) == ""

    def test_head_without_signals_returns_empty(self):
        """Head without title or key meta tags returns empty."""
        head = "<head><link rel='stylesheet' href='style.css'></head>"
        assert compute_head_fingerprint(head) == ""

    def test_extracts_title(self):
        """Title is extracted and included in fingerprint."""
        head1 = "<head><title>My Title</title></head>"
        head2 = "<head><title>My Title</title><link href='x'></head>"
        # Same title should produce same fingerprint
        assert compute_head_fingerprint(head1) == compute_head_fingerprint(head2)

    def test_extracts_meta_description(self):
        """Meta description is extracted."""
        head1 = '<head><meta name="description" content="Test description"></head>'
        head2 = '<head><meta name="description" content="Different description"></head>'
        assert compute_head_fingerprint(head1) != compute_head_fingerprint(head2)

    def test_extracts_og_tags(self):
        """Open Graph tags are extracted."""
        head1 = '<head><meta property="og:title" content="OG Title"></head>'
        head2 = '<head><meta property="og:title" content="Different OG Title"></head>'
        assert compute_head_fingerprint(head1) != compute_head_fingerprint(head2)

    def test_extracts_og_image(self):
        """og:image is extracted and affects fingerprint."""
        head1 = '<head><meta property="og:image" content="https://example.com/img1.jpg"></head>'
        head2 = '<head><meta property="og:image" content="https://example.com/img2.jpg"></head>'
        assert compute_head_fingerprint(head1) != compute_head_fingerprint(head2)

    def test_extracts_article_modified_time(self):
        """article:modified_time is extracted."""
        head1 = '<head><meta property="article:modified_time" content="2024-01-01T00:00:00Z"></head>'
        head2 = '<head><meta property="article:modified_time" content="2024-12-01T00:00:00Z"></head>'
        assert compute_head_fingerprint(head1) != compute_head_fingerprint(head2)

    def test_case_insensitive(self):
        """Fingerprinting is case-insensitive for tags."""
        head1 = "<head><TITLE>Test</TITLE></head>"
        head2 = "<head><title>test</title></head>"
        # Both should extract title (case insensitive)
        fp1 = compute_head_fingerprint(head1)
        fp2 = compute_head_fingerprint(head2)
        assert fp1 != ""
        assert fp2 != ""

    def test_handles_attribute_order(self):
        """Handles different attribute orders in meta tags."""
        head1 = '<head><meta name="description" content="Test"></head>'
        head2 = '<head><meta content="Test" name="description"></head>'
        assert compute_head_fingerprint(head1) == compute_head_fingerprint(head2)

    def test_real_world_head(self):
        """Test with a realistic head section."""
        head = '''
        <head>
            <meta charset="utf-8">
            <title>Python Documentation</title>
            <meta name="description" content="Official Python documentation">
            <meta property="og:title" content="Python Docs">
            <meta property="og:description" content="Learn Python">
            <meta property="og:image" content="https://python.org/logo.png">
            <link rel="stylesheet" href="styles.css">
        </head>
        '''
        fp = compute_head_fingerprint(head)
        assert fp != ""
        # Should be deterministic
        assert fp == compute_head_fingerprint(head)
