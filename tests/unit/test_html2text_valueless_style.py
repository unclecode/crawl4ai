"""Google Docs mode must tolerate HTML attributes without a value."""

import pytest

from crawl4ai.html2text import HTML2Text, CustomHTML2Text
from crawl4ai.html2text.utils import element_style


@pytest.mark.parametrize("converter_type", [HTML2Text, CustomHTML2Text])
@pytest.mark.parametrize(
    "attributes",
    ["class", "style", "class style", 'class=""', 'style=""', 'class="" style'],
)
def test_google_doc_conversion_accepts_empty_style_attributes(
    converter_type, attributes
):
    converter = converter_type()
    converter.google_doc = True
    result = converter.handle(f"<p><span {attributes}>Alpha</span> Beta</p>")
    assert "Alpha Beta" in result


@pytest.mark.parametrize("attribute", ["class", "style"])
@pytest.mark.parametrize("value", [None, ""])
def test_empty_attribute_preserves_parent_style_without_mutation(attribute, value):
    attrs = {attribute: value}
    parent = {"font-weight": "bold"}
    result = element_style(attrs, {}, parent)
    assert result == parent
    assert result is not parent
    assert attrs == {attribute: value}
    assert parent == {"font-weight": "bold"}


@pytest.mark.parametrize("converter_type", [HTML2Text, CustomHTML2Text])
@pytest.mark.parametrize(
    "attributes",
    ['class="strong" style', 'class style="font-weight: bold"'],
)
def test_valid_style_still_applies_next_to_valueless_attribute(
    converter_type, attributes
):
    converter = converter_type()
    converter.google_doc = True
    converter.style_def = {".strong": {"font-weight": "bold"}}
    result = converter.handle(f"<p><span {attributes}>Alpha</span></p>")
    assert "**Alpha**" in result


def test_inline_style_still_overrides_class_and_parent_style():
    attrs = {"class": "strong", "style": "font-weight: normal"}
    assert element_style(
        attrs,
        {".strong": {"font-weight": "bold"}},
        {"color": "red"},
    ) == {"color": "red", "font-weight": "normal"}


@pytest.mark.parametrize("converter_type", [HTML2Text, CustomHTML2Text])
def test_default_mode_conversion_is_unchanged(converter_type):
    result = converter_type().handle("<p><span class style>Alpha</span> Beta</p>")
    assert "Alpha Beta" in result
