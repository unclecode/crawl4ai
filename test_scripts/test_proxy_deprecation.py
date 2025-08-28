import sys
import warnings

from crawl4ai.async_configs import BrowserConfig, ProxyConfig


def main() -> int:
    warnings.simplefilter("always", DeprecationWarning)

    # Case 1: Using deprecated proxy string should emit DeprecationWarning and auto-convert
    captured = []
    proxy_str = "23.95.150.145:6114:username:password"
    with warnings.catch_warnings(record=True) as w:
        cfg = BrowserConfig(proxy=proxy_str, headless=True)
        captured = [m for m in w if issubclass(m.category, DeprecationWarning)]

    if not captured:
        print("[FAIL] No DeprecationWarning emitted for BrowserConfig(proxy=...) usage.")
        return 1

    if cfg.proxy is not None:
        print("[FAIL] cfg.proxy should be None after auto-conversion.")
        return 1

    if not isinstance(cfg.proxy_config, ProxyConfig):
        print("[FAIL] cfg.proxy_config should be a ProxyConfig instance after auto-conversion.")
        return 1

    # Basic sanity checks on auto-parsed proxy_config
    if not cfg.proxy_config.server or ":" not in (cfg.proxy_config.server or ""):
        print("[FAIL] proxy_config.server appears invalid after conversion:", cfg.proxy_config.server)
        return 1

    if not cfg.proxy_config.username or not cfg.proxy_config.password:
        print("[FAIL] proxy_config credentials missing after conversion.")
        return 1

    print("[OK] DeprecationWarning captured and proxy auto-converted to proxy_config.")

    # Case 2: Using proxy_config directly should not emit DeprecationWarning
    with warnings.catch_warnings(record=True) as w2:
        cfg2 = BrowserConfig(
            proxy_config={
                "server": "http://127.0.0.1:8080",
                "username": "u",
                "password": "p",
            },
            headless=True,
        )

    if any(issubclass(m.category, DeprecationWarning) for m in w2):
        print("[FAIL] Unexpected DeprecationWarning when using proxy_config.")
        return 1

    if cfg2.proxy is not None:
        print("[FAIL] cfg2.proxy should be None (only proxy_config should be used).")
        return 1

    if not isinstance(cfg2.proxy_config, ProxyConfig):
        print("[FAIL] cfg2.proxy_config should be a ProxyConfig instance.")
        return 1

    print("[OK] proxy_config path works without deprecation warnings.")
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

