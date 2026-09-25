"""
content_filter_strategy_lxml.py
===============================

An lxml-native, single-pass reimplementation of :class:`PruningContentFilter`.

Why
---
The original (BeautifulSoup) ``PruningContentFilter`` recomputes
``node.get_text(strip=True)`` and ``node.encode_contents()`` for *every* node it
visits while pruning. Both calls walk the node's entire subtree, and in
BeautifulSoup they are pure-Python and slow. Because pruning visits most nodes
in the document, the total work is effectively ``O(N * average_subtree_size)``
-- it degrades super-linearly on wide/deep pages. A 6,000-card page spent
~2.1 s purely inside ``filter_content``, dominated by repeated subtree
serialization (``str(node)`` / ``encode_contents``).

How this version is different
-----------------------------
Every per-node metric the score needs -- visible-text length, inner-HTML
length, direct-link text length and word count -- is computed **exactly once**
in a single *bottom-up* pass and cached on a slotted metrics object. Each text
fragment in the document is therefore touched a constant number of times
total, not once per ancestor. Scoring + pruning then run in a single
*top-down* pass over the cached metrics. Total work is ``O(N)`` plus
``O(total_text_size)``, entirely on libxml2's C-backed tree.

Fidelity
--------
BeautifulSoup's ``lxml`` tree-builder and ``lxml.html`` both parse through
libxml2, so the parsed trees are structurally identical node-for-node. The
scoring math, thresholds, tag weights and the original's edge-case quirks
(the always-zero ``class_id`` contribution, the separator-less word count) are
reproduced 1:1.

Two details are needed to match BeautifulSoup exactly:

* **Per-fragment stripping.** ``get_text(strip=True)`` strips each text
  fragment independently. BeautifulSoup's ``decompose()`` leaves the text that
  surrounded a removed tag as *separate* fragments, so each is stripped on its
  own. We therefore compute metrics *before* physically removing comments and
  excluded tags: a removed child contributes 0, but its trailing text (tail)
  is still measured as its own stripped fragment -- identical to what
  BeautifulSoup sees after ``decompose``.
* **No depth cap.** libxml2's HTML parser caps tree depth at 256 by default;
  ``huge_tree=True`` lifts that so deeply nested pages parse like they do under
  BeautifulSoup.
"""

from __future__ import annotations

import math
from typing import Dict, List

from lxml import etree
from lxml import html as lhtml

from .content_filter_strategy import PruningContentFilter

# HTML void elements, taken verbatim from BeautifulSoup's LXMLTreeBuilder
# ``empty_element_tags``. These serialize self-closed (``<br/>``) with no end
# tag, which we must account for when reproducing inner-HTML length.
VOID_ELEMENTS = frozenset(
    {
        "area", "base", "basefont", "bgsound", "br", "col", "command", "embed",
        "frame", "hr", "image", "img", "input", "isindex", "keygen", "link",
        "menuitem", "meta", "nextid", "param", "source", "spacer", "track", "wbr",
    }
)

# A single reused parser. ``huge_tree=True`` lifts libxml2's 256-level depth
# cap (and other limits) so output matches BeautifulSoup on pathological pages.
_HTML_PARSER = lhtml.HTMLParser(huge_tree=True)

# libxml2 treats only these as "blank" characters (IS_BLANK_CH); a text node
# made up entirely of them is collapsed to a single character by BeautifulSoup's
# tree builder. Note this is ASCII-only -- U+00A0 (&nbsp;) is NOT collapsed,
# even though Python's str.strip() would remove it.
_ASCII_WS = " \t\n\r"


def _esc_len(s: str) -> int:
    """Serialized length of ``s`` after HTML entity escaping (``&``->``&amp;``,
    ``<``->``&lt;``, ``>``->``&gt;``), matching BeautifulSoup's minimal formatter."""
    return len(s) + (s.count("&") << 2) + 3 * (s.count("<") + s.count(">"))


class _NodeMetrics:
    """Cached, slotted metrics for a single element (one instance per node).

    Attributes
    ----------
    text_len:
        Length of the element's visible text, computed the way
        BeautifulSoup's ``get_text(strip=True)`` does it: every text fragment
        (``.text`` of the node + ``.tail`` of each child) is stripped
        independently and concatenated with no separator.
    inner_len:
        Length of the element's serialized inner HTML, matching
        ``encode_contents()`` (entity-escaped text, child tags including
        attributes, void elements self-closed).
    space_count:
        Number of ASCII spaces in the stripped, concatenated visible text.
        ``word_count`` is ``space_count + 1`` -- the original counts words by
        ``text.count(" ") + 1`` on the separator-less concatenation, and we
        reproduce that exactly.
    string_len:
        Length of the stripped BeautifulSoup ``.string`` for this node, or
        ``-1`` when ``.string`` would be ``None``. Used only to evaluate
        ``link_text_len`` over direct-child ``<a>`` elements.
    """

    __slots__ = ("text_len", "inner_len", "space_count", "string_len")

    def __init__(self, text_len: int, inner_len: int, space_count: int, string_len: int):
        self.text_len = text_len
        self.inner_len = inner_len
        self.space_count = space_count
        self.string_len = string_len


class PruningContentFilterLXML(PruningContentFilter):
    """Drop-in, lxml-native replacement for :class:`PruningContentFilter`.

    Same constructor and same ``filter_content`` contract (returns a list of
    HTML block strings). Subclasses :class:`PruningContentFilter` so it shares
    the exact tag weights, metric weights, thresholds and negative-class
    patterns -- only the engine changes.
    """

    def __init__(
        self,
        user_query: str = None,
        min_word_threshold: int = None,
        threshold_type: str = "fixed",
        threshold: float = 0.48,
        preserve_classes: list = None,
        preserve_tags: list = None,
    ):
        # Mirror PruningContentFilter's explicit signature (rather than
        # *args/**kwargs) so config (de)serialization can introspect and
        # round-trip these fields.
        super().__init__(
            user_query=user_query,
            min_word_threshold=min_word_threshold,
            threshold_type=threshold_type,
            threshold=threshold,
            preserve_classes=preserve_classes,
            preserve_tags=preserve_tags,
        )
        # word count is only needed when a min-word threshold is active; skip
        # the per-fragment space counting otherwise.
        self._need_words = self.min_word_threshold is not None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def _is_preserved(self, node) -> bool:
        """Check if a node matches the preserve whitelist."""
        if self.preserve_tags and node.tag in self.preserve_tags:
            return True
        if self.preserve_classes:
            node_classes_raw = node.get("class")
            if node_classes_raw:
                node_classes = set(node_classes_raw.split())
                if node_classes & self.preserve_classes:
                    return True
        return False

    def filter_content(self, html: str, min_word_threshold: int = None) -> List[str]:
        if not html or not isinstance(html, str):
            return []

        try:
            root = lhtml.document_fromstring(html, parser=_HTML_PARSER)
        except (etree.ParserError, etree.LxmlError, ValueError):
            return []

        body = root.find("body")
        if body is None:
            body = root

        # Metrics are computed on the *un-stripped* tree so that text which
        # surrounds soon-to-be-removed nodes is measured as separate fragments
        # (matching BeautifulSoup's decompose semantics).
        metrics = self._compute_metrics(body)

        # Now physically drop comments and unwanted tags (skipping preserved ones).
        # ``with_tail=False`` keeps the text that followed them (merged into the
        # previous sibling / parent) so the serialized output still contains it,
        # exactly as a BeautifulSoup decompose would leave it.
        etree.strip_elements(body, etree.Comment, with_tail=False)
        for tag in self.excluded_tags:
            for el in list(body.iter(tag)):
                if el.getparent() is not None and not self._is_preserved(el):
                    el.drop_tree()

        body_metrics = metrics.get(body)
        if body_metrics is None:
            return []

        # The original scores the body itself first; if it fails, the whole
        # body is decomposed and nothing is returned.
        if self._should_remove(body, body_metrics, metrics):
            return []

        # Top-down pass: a node survives only if it and every ancestor up to
        # body pass the threshold. Iterative (explicit stack) to avoid Python
        # recursion limits on deeply nested documents.
        stack = [body]
        while stack:
            node = stack.pop()
            for child in list(node):
                if not isinstance(child.tag, str):
                    continue
                # Never prune inside <pre>/<code>: whitespace is significant
                # inside code blocks (syntax-highlighter whitespace spans would
                # otherwise be removed, corrupting formatting).
                if child.tag in ("pre", "code") or self._is_preserved(child):
                    stack.append(child)
                    continue
                child_metrics = metrics.get(child)
                if child_metrics is None or self._should_remove(child, child_metrics, metrics):
                    child.drop_tree()  # removes subtree, preserves following text
                else:
                    stack.append(child)

        # Collect surviving direct children of body, in document order,
        # skipping any that no longer carry visible text after pruning.
        blocks: List[str] = []
        for el in body:
            if not isinstance(el.tag, str):
                continue
            if any(t.strip() for t in el.itertext()):
                blocks.append(lhtml.tostring(el, encoding="unicode", with_tail=False))
        return blocks

    # ------------------------------------------------------------------ #
    # Metrics (single bottom-up pass)
    # ------------------------------------------------------------------ #
    def _compute_metrics(self, body) -> Dict[object, _NodeMetrics]:
        """Compute and cache metrics for ``body`` and every descendant element,
        skipping the interior of excluded subtrees (they will be removed).

        Nodes are visited in reverse document order so every parent sees its
        children's metrics already cached. A parent is always appended to the
        work list before its children, so ``reversed`` guarantees children are
        processed first.
        """
        metrics: Dict[object, _NodeMetrics] = {}
        need_words = self._need_words
        excluded = self.excluded_tags

        # Pre-order collection that does not descend into excluded subtrees
        # unless they match the preserve whitelist.
        nodes = []
        stack = [body]
        while stack:
            el = stack.pop()
            nodes.append(el)
            for child in el:
                ct = child.tag
                if isinstance(ct, str) and (ct not in excluded or self._is_preserved(child)):
                    stack.append(child)

        for el in reversed(nodes):
            txt = el.text
            if txt:
                stripped = txt.strip()
                text_len = len(stripped)
                # BeautifulSoup's tree builder collapses an ASCII-whitespace-only
                # text node to a single character; anything else is kept verbatim.
                if stripped or txt.strip(_ASCII_WS):
                    inner_len = _esc_len(txt)
                else:
                    inner_len = 1
                space_count = stripped.count(" ") if need_words else 0
                frag_count = 1
                string_len = text_len  # candidate, valid only if frag_count == 1
            else:
                text_len = inner_len = space_count = 0
                frag_count = 0
                string_len = -1

            for child in el:
                ct = child.tag
                kept_element = isinstance(ct, str) and (ct not in excluded or self._is_preserved(child))

                if kept_element:
                    cm = metrics[child]
                    text_len += cm.text_len
                    inner_len += self._outer_len(child, cm.inner_len)
                    if need_words:
                        space_count += cm.space_count
                    frag_count += 1
                    string_len = cm.string_len  # recurse if this is the sole content
                # else: comment / excluded element -> removed, contributes 0,
                # but its trailing text is still a separate fragment below.

                tail = child.tail
                if tail:
                    st = tail.strip()
                    text_len += len(st)
                    inner_len += _esc_len(tail) if (st or tail.strip(_ASCII_WS)) else 1
                    if need_words:
                        space_count += st.count(" ")
                    frag_count += 1
                    string_len = len(st)  # candidate, valid only if frag_count == 1

            # BeautifulSoup ``Tag.string`` is non-None only when the element has
            # exactly one content fragment.
            if frag_count != 1:
                string_len = -1

            metrics[el] = _NodeMetrics(text_len, inner_len, space_count, string_len)

        return metrics

    def _outer_len(self, el, inner_len: int) -> int:
        """Serialized outer-HTML length of ``el`` given its cached inner length.

        Mirrors BeautifulSoup's default (minimal) serialization:
        ``<tag attr="val">inner</tag>``, with void elements self-closed as
        ``<tag/>`` and HTML entity escaping inside attribute values.
        """
        tag = el.tag
        attrs_len = 0
        for k, v in el.attrib.items():
            # ' key="value"' -> 1 space + len(key) + '="' + escaped value + '"'
            attrs_len += 4 + len(k) + _esc_len(v)
        tag_len = len(tag)
        if tag in VOID_ELEMENTS:
            return 1 + tag_len + attrs_len + 2  # <tag ... />
        # start "<tag ...>" = 2 + tag_len + attrs_len ; end "</tag>" = 3 + tag_len
        return (2 + tag_len + attrs_len) + inner_len + (3 + tag_len)

    # ------------------------------------------------------------------ #
    # Scoring (top-down pass)
    # ------------------------------------------------------------------ #
    def _should_remove(self, node, m: _NodeMetrics, metrics: Dict[object, _NodeMetrics]) -> bool:
        text_len = m.text_len
        tag_len = m.inner_len

        link_text_len = 0
        for child in node:
            if child.tag == "a":
                cm = metrics.get(child)
                if cm is not None and cm.string_len > 0:
                    link_text_len += cm.string_len

        score = self._composite_score(node, m, text_len, tag_len, link_text_len)

        if self.threshold_type == "fixed":
            return score < self.threshold

        # dynamic threshold
        tag_importance = self.tag_importance.get(node.tag, 0.7)
        text_ratio = text_len / tag_len if tag_len > 0 else 0
        link_ratio = link_text_len / text_len if text_len > 0 else 1

        threshold = self.threshold
        if tag_importance > 1:
            threshold *= 0.8
        if text_ratio > 0.4:
            threshold *= 0.9
        if link_ratio > 0.6:
            threshold *= 1.2

        return score < threshold

    def _composite_score(self, node, m: _NodeMetrics, text_len: int, tag_len: int, link_text_len: int) -> float:
        if self.min_word_threshold:
            word_count = m.space_count + 1
            if word_count < self.min_word_threshold:
                return -1.0

        cfg = self.metric_config
        w = self.metric_weights
        score = 0.0
        total = 0.0

        if cfg["text_density"]:
            density = text_len / tag_len if tag_len > 0 else 0
            score += w["text_density"] * density
            total += w["text_density"]

        if cfg["link_density"]:
            link_density = 1 - (link_text_len / text_len if text_len > 0 else 0)
            score += w["link_density"] * link_density
            total += w["link_density"]

        if cfg["tag_weight"]:
            score += w["tag_weight"] * self.tag_weights.get(node.tag, 0.5)
            total += w["tag_weight"]

        if cfg["class_id_weight"]:
            # Faithful to the original: _class_id_score is <= 0, so max(0, .)
            # contributes nothing -- it only dilutes the denominator.
            score += w["class_id_weight"] * max(0, self._class_id_score(node))
            total += w["class_id_weight"]

        if cfg["text_length"]:
            score += w["text_length"] * math.log(text_len + 1)
            total += w["text_length"]

        return score / total if total > 0 else 0

    def _class_id_score(self, node) -> float:
        score = 0.0
        cls = node.get("class")
        if cls is not None and self.negative_patterns.match(cls):
            score -= 0.5
        node_id = node.get("id")
        if node_id is not None and self.negative_patterns.match(node_id):
            score -= 0.5
        return score
