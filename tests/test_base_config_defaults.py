"""Regression tests: crawler.base_config must apply to fields the client omitted.

The old guard treated only None/"" as "not provided", so any base_config key
whose CrawlerRunConfig default is False or 0 (simulate_user, magic,
override_navigator, check_robots_txt, ...) was silently dropped.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deploy', 'docker'))

from crawl4ai import CrawlerRunConfig
from crawl4ai.async_configs import Provenance
from api import _apply_base_config


def test_boolean_base_config_applies_when_client_omits():
    cfg = CrawlerRunConfig()
    _apply_base_config(cfg, {"simulate_user": True}, None)
    assert cfg.simulate_user is True


def test_client_value_wins():
    """#1505: an explicitly sent value must not be clobbered by base_config.

    Uses check_robots_txt because simulate_user is forbidden on untrusted
    bodies — base_config is the only way that one is ever set.
    """
    raw = {"type": "CrawlerRunConfig", "params": {"check_robots_txt": False}}
    cfg = CrawlerRunConfig.load(raw, provenance=Provenance.UNTRUSTED)
    _apply_base_config(cfg, {"check_robots_txt": True}, raw)
    assert cfg.check_robots_txt is False

    flat = CrawlerRunConfig()
    _apply_base_config(flat, {"check_robots_txt": True}, {"check_robots_txt": False})
    assert flat.check_robots_txt is False
