"""The restarted permanent browser must be built the way startup builds it.

Startup creates the permanent browser from get_default_browser_config(), which
applies the egress hardening (#2237), and incoming requests reach it by pool
signature. A restart that assembled its own BrowserConfig got a different
signature, so no request matched the restarted browser; it sat idle while
default-config requests built cold-pool browsers instead.
"""

import asyncio


def test_restart_rebuilds_permanent_browser_from_startup_config(
    server_module, monkeypatch
):
    import crawler_pool
    import monitor_routes

    rebuilt = []

    async def fake_restart_permanent(cfg):
        rebuilt.append(cfg)

    monkeypatch.setattr(crawler_pool, "restart_permanent", fake_restart_permanent)

    result = asyncio.run(
        monitor_routes.restart_browser(
            monitor_routes.KillBrowserRequest(sig="permanent")
        )
    )

    assert result == {"success": True, "restarted": "permanent"}
    assert len(rebuilt) == 1

    def pool_sig(cfg):
        return crawler_pool._sig(crawler_pool._apply_pool_defaults(cfg))

    assert pool_sig(rebuilt[0]) == pool_sig(server_module.get_default_browser_config())
    # The hardening itself, not only the signature.
    assert rebuilt[0].ignore_https_errors is False
