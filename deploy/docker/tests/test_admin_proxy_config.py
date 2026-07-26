"""Operator-token trusted configuration regression tests."""

from unittest.mock import AsyncMock, patch

import pytest

from auth import create_access_token
from crawl4ai.async_configs import Provenance, UntrustedConfigError

pytestmark = pytest.mark.posture


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestTrustedConfigLoading:
    def test_operator_browser_config_is_fully_trusted(self):
        import api

        config = api._load_browser_config(
            {
                "proxy_config": {
                    "server": "http://proxy.example:8080",
                    "username": "user",
                    "password": "secret",
                },
                "extra_args": ["--disable-web-security"],
            },
            provenance=Provenance.TRUSTED,
        )

        assert config.proxy_config.server == "http://proxy.example:8080"
        assert config.proxy_config.username == "user"
        assert config.proxy_config.password == "secret"
        assert config.extra_args == ["--disable-web-security"]

    def test_regular_authenticated_config_remains_untrusted(self):
        import api

        with pytest.raises(UntrustedConfigError):
            api._load_browser_config(
                {"proxy_config": {"server": "http://proxy.example:8080"}},
                provenance=Provenance.UNTRUSTED,
            )

    def test_typed_sdk_proxy_config_is_supported_for_operator(self):
        import api

        config = api._load_browser_config(
            {
                "type": "BrowserConfig",
                "params": {
                    "proxy_config": {
                        "type": "ProxyConfig",
                        "params": {
                            "server": "http://proxy.example:8080",
                            "username": "sdk-user",
                            "password": "sdk-secret",
                        },
                    },
                },
            },
            provenance=Provenance.TRUSTED,
        )

        assert config.proxy_config.server == "http://proxy.example:8080"
        assert config.proxy_config.username == "sdk-user"
        assert config.proxy_config.password == "sdk-secret"


def test_operator_token_selects_trusted_provenance(
    stock_client, server_module, monkeypatch
):
    operator_token = "operator-proxy-test-token"
    monkeypatch.setitem(
        server_module.config["security"], "api_token", operator_token
    )
    response_data = {
        "success": True,
        "results": [{"url": "https://example.com", "success": True}],
    }

    with patch.object(
        server_module,
        "handle_crawl_request",
        new=AsyncMock(return_value=response_data),
    ) as handler:
        response = stock_client.post(
            "/crawl",
            json={
                "urls": ["https://example.com"],
                "browser_config": {
                    "proxy_config": {"server": "http://proxy.example:8080"}
                },
                "crawler_config": {"js_code": "window.operatorConfigured = true"},
            },
            headers=_bearer(operator_token),
        )

    assert response.status_code == 200, response.text
    assert handler.await_args.kwargs["provenance"] == Provenance.TRUSTED


def test_admin_jwt_does_not_impersonate_operator_token(
    stock_client, server_module
):
    token = create_access_token({"sub": "admin"}, scope="admin")

    with patch.object(
        server_module,
        "stream_process",
        new=AsyncMock(return_value={"success": True}),
    ) as handler:
        response = stock_client.post(
            "/crawl/stream",
            json={"urls": ["https://example.com"]},
            headers=_bearer(token),
        )

    assert response.status_code == 200, response.text
    assert handler.await_args.kwargs["provenance"] == Provenance.UNTRUSTED
