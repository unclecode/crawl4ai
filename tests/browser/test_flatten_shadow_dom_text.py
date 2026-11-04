"""Local browser regressions for text serialization while flattening shadow DOM."""

from html import escape

import pytest
from playwright.sync_api import sync_playwright

from crawl4ai.js_snippet import load_js_script


FLATTEN_SCRIPT = load_js_script("flatten_shadow_dom")


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    page = browser.new_page()
    page.set_content('<div id="host"></div>')
    yield page
    page.close()


@pytest.mark.parametrize("shadow", [False, True])
def test_escapes_light_and_shadow_text(page, shadow):
    text = "A & B <em>literal</em> > Grüße"
    page.evaluate(
        """({text, shadow}) => {
            const host = document.getElementById('host');
            const root = shadow ? host.attachShadow({mode: 'open'}) : host;
            root.append(document.createTextNode(text));
        }""",
        {"text": text, "shadow": shadow},
    )

    html = page.evaluate(FLATTEN_SCRIPT)

    assert f'<div id="host">{escape(text, quote=False)}</div>' in html
    assert (
        page.evaluate(
            """html => new DOMParser().parseFromString(html, 'text/html')
            .getElementById('host').textContent""",
            html,
        )
        == text
    )


@pytest.mark.parametrize("shadow", [False, True])
def test_preserves_entities_and_closing_tags_in_code(page, shadow):
    text = '&lt;literal&gt; </code></pre><b id="injected">text</b> a < b && b > c'
    page.evaluate(
        """({text, shadow}) => {
            const host = document.getElementById('host');
            const root = shadow ? host.attachShadow({mode: 'open'}) : host;
            const code = document.createElement('code');
            code.textContent = text;
            root.append(code);
        }""",
        {"text": text, "shadow": shadow},
    )

    html = page.evaluate(FLATTEN_SCRIPT)

    assert f"<code>{escape(text, quote=False)}</code>" in html
    assert (
        page.evaluate(
            """html => {
            const document = new DOMParser().parseFromString(html, 'text/html');
            const code = document.querySelector('code');
            return [code.textContent, code.childElementCount,
                    document.getElementById('injected')];
        }""",
            html,
        )
        == [text, 0, None]
    )


def test_escapes_nested_shadow_text(page):
    page.evaluate(
        """() => {
            const root = document.getElementById('host').attachShadow({mode: 'open'});
            root.innerHTML = '<section><span id="nested"></span></section>';
            root.prepend('outer < & >');
            root.querySelector('#nested').attachShadow({mode: 'open'})
                .append('inner < & >');
        }"""
    )

    html = page.evaluate(FLATTEN_SCRIPT)

    assert (
        '<div id="host">outer &lt; &amp; &gt;<section>'
        '<span id="nested">inner &lt; &amp; &gt;</span></section></div>'
    ) in html


def test_escapes_projected_slots_and_fallback(page):
    page.evaluate(
        """() => {
            const host = document.getElementById('host');
            host.innerHTML = '<span slot="assigned"></span>';
            host.firstChild.textContent = 'projected < & >';
            host.append('default < & >');
            const root = host.attachShadow({mode: 'open'});
            root.innerHTML = '<slot name="assigned"></slot><slot></slot>'
                + '<slot name="missing">fallback &lt; &amp; &gt;</slot>';
        }"""
    )

    html = page.evaluate(FLATTEN_SCRIPT)

    assert (
        '<div id="host"><span slot="assigned">projected &lt; &amp; &gt;</span>'
        "default &lt; &amp; &gt;fallback &lt; &amp; &gt;</div>"
    ) in html
    assert "<slot" not in html


def test_preserves_raw_script_and_light_style_but_skips_shadow_style(page):
    script = '{"value": "<tag> & >"}'
    style = 'body::before { content: "< & >"; }'
    page.evaluate(
        """({script, style}) => {
            const lightScript = document.createElement('script');
            lightScript.type = 'application/json';
            lightScript.textContent = script;
            document.head.append(lightScript);
            const lightStyle = document.createElement('style');
            lightStyle.textContent = style;
            document.head.append(lightStyle);
            const root = document.getElementById('host').attachShadow({mode: 'open'});
            root.innerHTML = '<style>.shadow-only { color: red; }</style>'
                + '<section><style>.nested-shadow-only { color: blue; }</style></section>';
            root.append(lightScript.cloneNode(true));
        }""",
        {"script": script, "style": style},
    )

    html = page.evaluate(FLATTEN_SCRIPT)

    assert html.count(f'<script type="application/json">{script}</script>') == 2
    assert f"<style>{style}</style>" in html
    assert html.count("<style>") == 1
    assert "shadow-only" not in html
