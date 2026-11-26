"""The class penalty in calculate_link_intrinsic_score: "ad" is a class word, not two letters."""

import pytest

from crawl4ai.utils import calculate_link_intrinsic_score

CONTEXT = {"terms": set(), "is_docs_site": False}


def _score(class_attr):
    return calculate_link_intrinsic_score(
        link_text="Getting started guide",
        url="https://example.com/docs/start",
        title_attr="",
        class_attr=class_attr,
        rel_attr="",
        page_context=CONTEXT,
    )


@pytest.mark.parametrize(
    "class_attr",
    ["ad-slot", "sidebar-ad", "ads", "ad1", "adContainer", "googleAd", "adwrap", "text-link ad"],
)
def test_ad_class_loses_a_point(class_attr):
    assert _score(class_attr) == _score("") - 1.0


@pytest.mark.parametrize(
    "class_attr",
    ["breadcrumb", "header-link", "badge", "download-btn", "loading", "read-more", "ad-free", "headLine"],
)
def test_class_containing_ad_letters_keeps_its_score(class_attr):
    assert _score(class_attr) == _score("")
