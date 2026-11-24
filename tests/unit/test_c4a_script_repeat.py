import pytest

from crawl4ai import CrawlerRunConfig


@pytest.mark.parametrize(
    "command",
    [
        "WAIT 1",
        "WAIT `#ready` 2",
        'WAIT "Ready" 2',
        "pause_once",
    ],
)
def test_dynamic_repeat_preserves_the_async_context_of_wait(command):
    config = CrawlerRunConfig(c4a_script=f"""PROC pause_once
WAIT 1
ENDPROC
REPEAT ({command}, `Number("2")`)""")

    [script] = config.js_code
    # A block scopes the counter without introducing a non-async function.
    assert script.startswith("{\n")
    assert 'const _count = Number("2");' in script
    assert "await new Promise(" in script


def test_numeric_repeat_of_wait_uses_the_callers_async_context():
    config = CrawlerRunConfig(c4a_script="REPEAT (WAIT 1, 2)")

    [script] = config.js_code
    assert script.startswith("for (let _i = 0; _i < 2; _i++) {")
    assert "await new Promise(" in script
