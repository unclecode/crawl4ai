"""Word-count thresholds must not treat a Chinese/Japanese block as a single word.

Chinese and Japanese are written without spaces, so ``len(text.split())`` is 1
for a whole paragraph and every ``*_word_threshold`` setting above 1 dropped it.
All inputs are local HTML strings; no network or browser is used.
"""

import random
import warnings

import pytest
from lxml import html as lhtml

from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter
from crawl4ai.content_filter_strategy_lxml import PruningContentFilterLXML
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.utils import count_cjk_chars, count_words

JA = "東京は日本の首都であり、世界最大級の都市圏を形成しています。"
ZH = "北京是中华人民共和国的首都，也是全国的政治和文化中心。"
EN = "Tokyo is the capital of Japan and forms one of the largest urban areas in the world."


def page(text: str) -> str:
    return f"<html><body><article><p>{text}</p></article></body></html>"


class TestCountWords:
    @pytest.mark.parametrize(
        "text",
        [
            "",
            "   ",
            "hello",
            "hello world",
            "  leading and   multiple\tspaces\nand newlines ",
            EN,
            "안녕하세요 세계 여러분",  # Hangul is space-delimited: unchanged
            "Привет мир",
            "3.14 + 2 = 5.14",
        ],
    )
    def test_text_without_cjk_matches_split(self, text):
        assert count_words(text) == len(text.split())

    def test_japanese_counts_each_character(self):
        # 13 characters; the trailing "。" is punctuation and not counted
        assert count_words("東京は日本の首都であります。") == 13
        assert count_words("カタカナ") == 4
        assert count_words("ｶﾀｶﾅ") == 4  # half-width katakana

    def test_chinese_counts_each_character(self):
        assert count_words("北京是中国的首都，") == 8  # "，" is not counted

    def test_extension_b_ideographs(self):
        assert count_words("\U00020bb7野家") == 3  # 𠮷野家

    def test_mixed_text(self):
        # "iPhone" and "15" stay whole words, each CJK character is a word
        assert count_words("iPhone 15は速い") == 5
        assert count_words("Python で Web を取得") == 6
        assert count_words("使い方: pip install crawl4ai,すぐ使えます") == 12

    def test_cjk_punctuation_and_fullwidth_are_not_words(self):
        assert count_words("東京、") == 2
        assert count_words("「東京」") == 2
        assert count_words("東京。 ！？") == 2
        assert (
            count_words("日本語, 中文, 한국어.") == 6
        )  # 日本語 + 中文 + one Hangul word

    def test_long_japanese_page_exceeds_threshold(self):
        assert count_words(JA) > 20
        assert count_words(ZH) > 20

    def test_hangul_and_fullwidth_alnum_count_as_ordinary_words(self):
        # not counted per character: they are whitespace-separated like Latin text
        assert count_words("안녕하세요 세계") == 2
        assert count_words("東京ＡＢＣ１２３") == 3  # 東, 京, "ＡＢＣ１２３"
        assert count_words("日本語 한국어") == 4

    @pytest.mark.parametrize(
        "codepoint",
        [
            0x3005,
            0x3041,
            0x3096,
            0x30A1,
            0x30FA,
            0x30FC,  # marks, kana
            0x31F0,
            0xFF66,
            0xFF9F,  # Katakana Phonetic Extensions, half-width
            0x3400,
            0x4DBF,
            0x4E00,
            0x9FFF,  # Ext A, URO
            0xF900,
            0xFAD9,  # compatibility ideographs
            0x1AFF0,
            0x1AFFE,
            0x1B000,
            0x1B11F,
            0x1B132,
            0x1B155,
            0x1B16F,  # kana blocks
            0x20000,
            0x2A6DF,  # Ext B
            0x2A700,
            0x2B739,  # Ext C
            0x2B740,
            0x2B81D,  # Ext D
            0x2B820,
            0x2CEA1,  # Ext E
            0x2CEB0,
            0x2EBE0,  # Ext F
            0x2EBF0,
            0x2EE5D,  # Ext I
            0x2F800,
            0x2FA1D,  # compatibility supplement
            0x30000,
            0x3134A,  # Ext G
            0x31350,
            0x323AF,  # Ext H
        ],
    )
    def test_each_block_counts_one_word_per_character(self, codepoint):
        text = chr(codepoint) * 3
        assert count_cjk_chars(text) == 3
        assert count_words(text) == 3

    def test_rare_ideographs_and_small_kana(self):
        assert count_words("\U00031350\U00031351\U00031352") == 3  # Ext H
        assert count_words("\U0001b001\U0001b001\U0001b001") == 3  # Kana Supplement


class TestScrapingStrategyThreshold:
    @staticmethod
    def _keeps_paragraph(text: str, threshold: int) -> bool:
        root = lhtml.document_fromstring(page(text))
        LXMLWebScrapingStrategy().remove_empty_elements_fast(root, threshold)
        return bool(root.xpath("//p"))

    @pytest.mark.parametrize("text", [JA, ZH])
    def test_cjk_paragraph_kept_above_threshold(self, text):
        assert self._keeps_paragraph(text, 5)
        assert self._keeps_paragraph(text, 20)

    def test_short_cjk_paragraph_removed_below_threshold(self):
        assert not self._keeps_paragraph("東京です", 10)

    def test_english_behaviour_unchanged(self):
        assert self._keeps_paragraph(EN, 5)
        assert not self._keeps_paragraph("too short", 5)


class TestContentFilterThreshold:
    @pytest.mark.parametrize("text", [JA, ZH, EN])
    def test_bm25_keeps_block_above_min_word_threshold(self, text):
        f = BM25ContentFilter(user_query="x", bm25_threshold=-100)
        assert len(f.filter_content(page(text), min_word_threshold=5)) == 1

    @pytest.mark.parametrize("text", [JA, ZH, EN])
    def test_pruning_keeps_block_above_min_word_threshold(self, text):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            bs4_out = PruningContentFilter(
                min_word_threshold=5, threshold=0.0
            ).filter_content(page(text))
        lxml_out = PruningContentFilterLXML(
            min_word_threshold=5, threshold=0.0
        ).filter_content(page(text))
        assert len(bs4_out) == 1
        # PruningContentFilterLXML must stay output-identical to PruningContentFilter
        assert lxml_out == bs4_out

    def test_pruning_still_drops_short_cjk_block(self):
        f = PruningContentFilterLXML(min_word_threshold=10, threshold=0.0)
        assert f.filter_content(page("東京です")) == []


def _squash(blocks):
    return [" ".join(block.split()) for block in blocks]


def _prune(cls, html, threshold):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return cls(min_word_threshold=threshold, threshold=0.0).filter_content(html)


class TestPruningWordCountBoundaries:
    """Pruning counts CJK text exactly like count_words, both implementations."""

    @pytest.mark.parametrize("cls", [PruningContentFilter, PruningContentFilterLXML])
    @pytest.mark.parametrize(
        "text, words",
        [
            ("東京", 2),
            ("東京 日本 首都", 6),
            (JA, count_words(JA)),
            ("Python で Web を取得", 6),
            ("東京ＡＢＣ１２３", 3),
        ],
    )
    def test_threshold_at_and_just_above_word_count(self, cls, text, words):
        assert len(_prune(cls, page(text), words)) == 1
        assert _prune(cls, page(text), words + 1) == []

    @pytest.mark.parametrize("cls", [PruningContentFilter, PruningContentFilterLXML])
    def test_text_without_cjk_keeps_the_space_count_plus_one_rule(self, cls):
        # "a  b" has two spaces: count(" ") + 1 == 3, not len(split()) == 2
        assert len(_prune(cls, page("a  b"), 3)) == 1
        assert _prune(cls, page("a  b"), 4) == []

    def test_nested_inline_fragments(self):
        # fragments are concatenated without a separator: "Hello" + "東京" + "world"
        html = "<html><body><p>Hello <b>東京</b> world</p></body></html>"
        assert count_words("Hello東京world") == 4
        for cls in (PruningContentFilter, PruningContentFilterLXML):
            assert len(_prune(cls, html, 4)) == 1
            assert _prune(cls, html, 5) == []

    @pytest.mark.parametrize(
        "removed", ["<!--x-->", "<script>x</script>", "<nav>x</nav>"]
    )
    def test_text_around_a_removed_node(self, removed):
        # "東Hello " and " world" are stripped separately: "東Helloworld", 2 words
        html = f"<html><body><p>東Hello {removed} world</p></body></html>"
        assert count_words("東Helloworld") == 2
        for cls in (PruningContentFilter, PruningContentFilterLXML):
            assert len(_prune(cls, html, 2)) == 1
            assert _prune(cls, html, 3) == []

    @pytest.mark.parametrize(
        "skipped",
        [
            "<template>東京日本</template>",
            "<ruby>本<rt>ほん にほん</rt></ruby>",
            "<ruby>本<rp>東京日本</rp></ruby>",
        ],
    )
    @pytest.mark.parametrize("text", ["hello world", "東京 hello"])
    def test_text_that_get_text_skips(self, skipped, text):
        # get_text() of the <p> skips text inside <template>, <rt> and <rp>
        html = f"<html><body><p>{text}{skipped}</p></body></html>"
        for threshold in range(1, 9):
            lxml_out = _prune(PruningContentFilterLXML, html, threshold)
            bs4_out = _prune(PruningContentFilter, html, threshold)
            assert _squash(lxml_out) == _squash(bs4_out), threshold

    def test_deep_nesting_measures_each_text_once(self, monkeypatch):
        import crawl4ai.content_filter_strategy_lxml as lxml_filter

        measured = []
        word_stats = lxml_filter._word_stats

        def counting_word_stats(text):
            measured.append(len(text))
            return word_stats(text)

        monkeypatch.setattr(lxml_filter, "_word_stats", counting_word_stats)
        text = "中 " + "hello world " * 2000
        html = f"<html><body>{'<div>' * 128}{text}{'</div>' * 128}</body></html>"
        out = _prune(PruningContentFilterLXML, html, 5)
        assert _squash(out) == _squash(_prune(PruningContentFilter, html, 5))
        assert len(out) == 1
        # once in total, not once per enclosing <div>
        assert sum(measured) == len(text.strip())

    def test_lxml_matches_bs4_on_random_mixed_documents(self):
        rng = random.Random(0)
        pieces = [
            "東京",
            "日本語",
            "Hello",
            "world",
            "a",
            "。",
            "，",
            "한국어",
            "ＡＢＣ",
            "x y",
            "  ",
            "-",
            "!",
            "_",
            "Hello!",
            "東Hello",
        ]
        # removed nodes, and text that get_text() of an ancestor skips
        specials = [
            "<!--c-->",
            "<script>x</script>",
            "<nav>{}</nav>",
            "<template>{}</template>",
            "<ruby>{}<rt>{}</rt></ruby>",
            "<ruby>{}<rp>(</rp><rt>{}</rt><rp>)</rp></ruby>",
        ]
        words = [p for p in pieces if p.strip() and " " not in p]

        def fragment(depth=0):
            out = []
            for _ in range(rng.randint(1, 3)):
                out.append(
                    " ".join(rng.choice(pieces) for _ in range(rng.randint(0, 3)))
                )
                if depth < 3 and rng.random() < 0.6:
                    tag = rng.choice(["span", "b", "div", "p", "a"])
                    out.append(f"<{tag}>{fragment(depth + 1)}</{tag}>")
                if rng.random() < 0.3:
                    special = rng.choice(specials)
                    out.append(special.format(*(rng.choice(words) for _ in range(2))))
            return rng.choice(["", " "]).join(out)

        for _ in range(200):
            # leading "z": an <article> whose only text is in a <template> is
            # returned by the lxml filter alone, also without word thresholds
            html = f"<html><body><article>z {fragment()}</article></body></html>"
            for threshold in (1, 2, 3, 5, 8, 13):
                # compare which blocks survive; both engines serialize a
                # run of spaces between two tags differently (unrelated to counting)
                assert _squash(
                    _prune(PruningContentFilterLXML, html, threshold)
                ) == _squash(_prune(PruningContentFilter, html, threshold)), (
                    html,
                    threshold,
                )


class TestClusterFilterThreshold:
    def test_cosine_strategy_keeps_cjk_cluster(self):
        from crawl4ai.extraction_strategy import CosineStrategy

        strategy = object.__new__(CosineStrategy)  # skip loading the embedding model
        strategy.word_count_threshold = 10
        clusters = {0: [JA, ZH], 1: ["東京です"], 2: ["too short"]}
        assert set(strategy.filter_clusters_by_word_count(clusters)) == {0}
