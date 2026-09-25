#!/usr/bin/env python3
"""The playground's Advanced Config panel must speak the protocol the server
still accepts.

Issue #2260: the panel posted {type, code} to /config/dump long after the 0.8.x
security work dropped the eval-based `code` path. `code` is forbidden under the
untrusted trust boundary, so the pre-flight always 400'd; a regex fallback in
runCrawl() then swapped the user's config for a stream-only one, so everything
else they typed was silently discarded.

These tests read the shipped page as text -- no browser, no server boot -- and
check the templates against the real untrusted gate.
"""

import json
import os
import re
import unittest

from crawl4ai.async_configs import (
    UNTRUSTED_FIELD_ALLOWLIST,
    BrowserConfig,
    CrawlerRunConfig,
    Provenance,
)

PLAYGROUND = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "static", "playground", "index.html"
)
CONFIG_CLASSES = {"CrawlerRunConfig": CrawlerRunConfig, "BrowserConfig": BrowserConfig}


def read_page() -> str:
    with open(PLAYGROUND, encoding="utf-8") as fh:
        return fh.read()


def read_templates() -> dict:
    """Pull the TEMPLATES literal out of the page."""
    block = re.search(r"const TEMPLATES = \{(.*?)\n        \};", read_page(), re.S)
    assert block, "TEMPLATES literal not found in the playground"
    return dict(re.findall(r"(\w+): `(\{.*?\})`", block.group(1), re.S))


class TestConfigProtocol(unittest.TestCase):
    def test_config_dump_is_not_sent_a_code_field(self):
        """`code` is forbidden under UNTRUSTED, so sending it always 400s."""
        page = read_page()
        call = re.search(r"authFetch\('/config/dump'.*?\}\);", page, re.S)
        self.assertIsNotNone(call, "/config/dump call not found")
        self.assertNotIn("code", call.group(0).split("body:")[1],
                         "playground must not post a `code` field to /config/dump")
        self.assertIn("params", call.group(0),
                      "playground must post the {type, params} shape /config/dump accepts")

    def test_rejected_config_aborts_instead_of_falling_back(self):
        """The stream=True regex fallback is what made the config loss silent."""
        page = read_page()
        self.assertNotIn("streamFlag", page, "the regex fallback must be gone")
        self.assertNotRegex(page, r"stream\\s\*=\\s\*True",
                            "the editor text must not be regex-scraped for stream")


class TestTemplatesSurviveTheUntrustedGate(unittest.TestCase):
    def test_templates_are_valid_json_objects(self):
        templates = read_templates()
        self.assertEqual(set(templates), set(CONFIG_CLASSES))
        for name, body in templates.items():
            with self.subTest(config=name):
                params = json.loads(body)
                self.assertIsInstance(params, dict)
                self.assertTrue(params, "template must not be empty")

    def test_every_template_field_is_allowlisted(self):
        """A template field outside the allowlist would 400 on every run."""
        for name, body in read_templates().items():
            with self.subTest(config=name):
                unknown = set(json.loads(body)) - UNTRUSTED_FIELD_ALLOWLIST[name]
                self.assertFalse(unknown, f"{name} template uses forbidden field(s): {unknown}")

    def test_every_template_field_reaches_the_config_object(self):
        """Load each template the way /config/dump does and read the result back.

        dump() omits values equal to the class default, so assert on the object,
        not on the echoed payload.
        """
        for name, body in read_templates().items():
            with self.subTest(config=name):
                params = json.loads(body)
                obj = CONFIG_CLASSES[name].load(
                    {"type": name, "params": params}, provenance=Provenance.UNTRUSTED
                )
                applied = {key: getattr(obj, key) for key in params}
                self.assertEqual(applied, params)

    def test_stream_reaches_the_shape_should_use_stream_reads(self):
        """runCrawl picks the streaming endpoint off crawler_config.params.stream."""
        params = json.loads(read_templates()["CrawlerRunConfig"])
        self.assertIs(params.get("stream"), True)

    def test_the_validated_params_are_forwarded_not_the_dump_echo(self):
        """dump() adds server-derived fields the untrusted gate then refuses.

        BrowserConfig picks up generated `headers`, which is not allowlisted, so
        posting /config/dump's echo to /crawl 400s. The page must forward the
        params the user typed.
        """
        params = json.loads(read_templates()["BrowserConfig"])
        echo = BrowserConfig.load(
            {"type": "BrowserConfig", "params": params}, provenance=Provenance.UNTRUSTED
        ).dump()
        forbidden = set(echo["params"]) - UNTRUSTED_FIELD_ALLOWLIST["BrowserConfig"]
        self.assertTrue(
            forbidden,
            "if dump() ever became re-submittable this guard can go, but check the page first",
        )
        page = read_page()
        self.assertIn("return { type: cfgType, params };", page,
                      "validateConfig must forward the typed params, not the echo")
        self.assertNotIn("return await res.json();", page,
                         "the /config/dump echo must not be forwarded to /crawl")

    def test_the_old_code_protocol_is_still_refused(self):
        """Guards the reason for this change: {type, code} cannot come back."""
        for name, cls in CONFIG_CLASSES.items():
            with self.subTest(config=name):
                with self.assertRaises(Exception) as ctx:
                    cls.load({"type": name, "code": f"{name}()"}, provenance=Provenance.UNTRUSTED)
                self.assertIn("code", str(ctx.exception))


class TestConfigStatusIsReset(unittest.TestCase):
    def test_status_is_cleared_when_the_endpoint_changes(self):
        """md/llm skip validation, so a stale '✖ config error' used to linger."""
        page = read_page()
        handler = re.search(
            r"getElementById\('endpoint'\)\.addEventListener\('change'.*?\n        \}\);",
            page, re.S,
        )
        self.assertIsNotNone(handler, "endpoint change handler not found")
        self.assertIn("setCfgStatus('',", handler.group(0),
                      "switching endpoint must clear #cfg-status")


if __name__ == "__main__":
    unittest.main()
