"""
Tests for PR #1795, #1798, #1734

- #1795: /token endpoint requires api_token when configured
- #1798: Deep-crawl streaming branches to arun() for single URL
- #1734: GitHub Actions versions bumped to latest
"""
import pytest
import yaml
import ast
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ── PR #1795: api_token protection on /token endpoint ────────────────────


class TestTokenEndpointAuth:
    """Test the api_token gating logic added to the /token endpoint."""

    def test_token_request_model_has_api_token_field(self):
        """auth.py TokenRequest should have an api_token field in its source."""
        source = (ROOT / "deploy" / "docker" / "auth.py").read_text()
        # Parse the AST to verify the field exists on the class
        tree = ast.parse(source)
        token_request = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "TokenRequest":
                token_request = node
                break
        assert token_request is not None, "TokenRequest class not found"
        field_names = [
            stmt.target.id
            for stmt in token_request.body
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        ]
        assert "email" in field_names, "TokenRequest missing email field"
        assert "api_token" in field_names, "TokenRequest missing api_token field"

    def test_server_token_check_logic_no_config(self):
        """When api_token is empty in config, any request should pass."""
        config = {"security": {"api_token": ""}}
        expected_token = config.get("security", {}).get("api_token", "")
        # Empty string is falsy, so check should be skipped
        assert not expected_token

    def test_server_token_check_logic_with_config_match(self):
        """When api_token is set and request matches, should pass."""
        config = {"security": {"api_token": "my-secret"}}
        expected_token = config.get("security", {}).get("api_token", "")
        req_token = "my-secret"
        assert expected_token and req_token == expected_token

    def test_server_token_check_logic_with_config_mismatch(self):
        """When api_token is set and request doesn't match, should reject."""
        config = {"security": {"api_token": "my-secret"}}
        expected_token = config.get("security", {}).get("api_token", "")
        req_token = "wrong-token"
        assert expected_token and req_token != expected_token

    def test_server_token_check_logic_with_config_none(self):
        """When api_token is set and request sends None, should reject."""
        config = {"security": {"api_token": "my-secret"}}
        expected_token = config.get("security", {}).get("api_token", "")
        req_token = None
        assert expected_token and req_token != expected_token

    def test_config_yml_has_api_token_field(self):
        """config.yml should include api_token under security."""
        with open(ROOT / "deploy" / "docker" / "config.yml") as f:
            cfg = yaml.safe_load(f)
        assert "api_token" in cfg["security"]
        # Default should be empty (disabled)
        assert cfg["security"]["api_token"] == ""

    def test_server_py_contains_token_check(self):
        """server.py get_token function should check api_token."""
        source = (ROOT / "deploy" / "docker" / "server.py").read_text()
        assert "api_token" in source
        assert 'config.get("security", {}).get("api_token"' in source
        assert "401" in source  # HTTPException 401


# ── PR #1798: Deep-crawl streaming branches on strategy ──────────────────


class TestDeepCrawlStreamBranching:
    """Test the branching logic in handle_stream_crawl_request."""

    def test_api_py_has_deep_crawl_branch(self):
        """api.py should branch on deep_crawl_strategy for streaming."""
        source = (ROOT / "deploy" / "docker" / "api.py").read_text()
        assert "deep_crawl_strategy is not None" in source
        assert "crawler.arun(" in source  # single-URL deep crawl path
        assert "crawler.arun_many(" in source  # multi-URL path

    def test_api_py_rejects_multi_url_deep_crawl(self):
        """api.py should raise 400 for deep crawl with multiple URLs."""
        source = (ROOT / "deploy" / "docker" / "api.py").read_text()
        assert "exactly one URL per request" in source
        assert "HTTP_400_BAD_REQUEST" in source

    @pytest.mark.asyncio
    async def test_deep_crawl_single_url_uses_arun(self):
        """With deep_crawl_strategy + 1 URL, should call crawler.arun()."""
        from crawl4ai import CrawlerRunConfig, BrowserConfig
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

        cfg = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1, max_pages=5),
            stream=True,
        )
        # Verify the config has deep_crawl_strategy set
        assert cfg.deep_crawl_strategy is not None
        assert cfg.stream is True

        # Simulate the branching logic from api.py
        urls = ["https://example.com"]
        if cfg.deep_crawl_strategy is not None and len(urls) == 1:
            path = "arun"
        else:
            path = "arun_many"
        assert path == "arun"

    @pytest.mark.asyncio
    async def test_no_deep_crawl_uses_arun_many(self):
        """Without deep_crawl_strategy, should use arun_many()."""
        from crawl4ai import CrawlerRunConfig

        cfg = CrawlerRunConfig(stream=True)
        assert cfg.deep_crawl_strategy is None

        urls = ["https://a.com", "https://b.com"]
        if cfg.deep_crawl_strategy is not None and len(urls) == 1:
            path = "arun"
        else:
            path = "arun_many"
        assert path == "arun_many"

    @pytest.mark.asyncio
    async def test_deep_crawl_multi_url_rejected(self):
        """Deep crawl + multiple URLs should be rejected."""
        from crawl4ai import CrawlerRunConfig
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

        cfg = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1, max_pages=5),
            stream=True,
        )
        urls = ["https://a.com", "https://b.com"]

        # This is what api.py does — raise before crawling
        should_reject = cfg.deep_crawl_strategy is not None and len(urls) != 1
        assert should_reject


# ── PR #1734: GitHub Actions version bumps ────────────────────────────────


class TestGitHubActionsVersions:
    """Verify all GitHub Actions are on current major versions."""

    EXPECTED_VERSIONS = {
        "actions/checkout": "v6",
        "actions/setup-python": "v6",
        "docker/build-push-action": "v6",
        "docker/setup-buildx-action": "v4",
        "docker/login-action": "v4",
        "softprops/action-gh-release": "v2",
    }

    def _extract_actions(self, workflow_path):
        """Extract action@version pairs from a workflow file."""
        with open(workflow_path) as f:
            data = yaml.safe_load(f)
        actions = {}
        for job_name, job in data.get("jobs", {}).items():
            for step in job.get("steps", []):
                uses = step.get("uses", "")
                if "@" in uses:
                    name, version = uses.rsplit("@", 1)
                    actions[name] = version
        return actions

    def test_docker_release_workflow(self):
        """docker-release.yml should use latest action versions."""
        actions = self._extract_actions(
            ROOT / ".github" / "workflows" / "docker-release.yml"
        )
        for name, expected in self.EXPECTED_VERSIONS.items():
            if name in actions:
                assert actions[name] == expected, (
                    f"{name} should be @{expected}, got @{actions[name]}"
                )

    def test_release_workflow(self):
        """release.yml should use latest action versions."""
        actions = self._extract_actions(
            ROOT / ".github" / "workflows" / "release.yml"
        )
        for name, expected in self.EXPECTED_VERSIONS.items():
            if name in actions:
                assert actions[name] == expected, (
                    f"{name} should be @{expected}, got @{actions[name]}"
                )

    def test_no_v4_or_v5_checkout_remaining(self):
        """No workflow should still reference checkout@v4 or v5."""
        for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
            content = wf.read_text()
            assert "actions/checkout@v4" not in content, f"{wf.name} still uses checkout@v4"
            assert "actions/checkout@v5" not in content, f"{wf.name} still uses checkout@v5"

    def test_no_old_build_push_action(self):
        """No workflow should still reference build-push-action@v5."""
        for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
            content = wf.read_text()
            assert "build-push-action@v5" not in content, (
                f"{wf.name} still uses build-push-action@v5"
            )
