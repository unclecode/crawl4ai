import html.entities
from typing import Dict, List, Optional

from . import config

unifiable_n = {
    html.entities.name2codepoint[k]: v
    for k, v in config.UNIFIABLE.items()
    if k != "nbsp"
}


def hn(tag: str) -> int:
    if tag[0] == "h" and len(tag) == 2:
        n = tag[1]
        if "0" < n <= "9":
            return int(n)
    return 0


def dumb_property_dict(style: str) -> Dict[str, str]:
    """
    :returns: A hash of css attributes
    """
    return {
        x.strip().lower(): y.strip().lower()
        for x, y in [z.split(":", 1) for z in style.split(";") if ":" in z]
    }


def dumb_css_parser(data: str) -> Dict[str, Dict[str, str]]:
    """
    :type data: str

    :returns: A hash of css selectors, each of which contains a hash of
    css attributes.
    :rtype: dict
    """
    # remove @import sentences
    data += ";"
    importIndex = data.find("@import")
    while importIndex != -1:
        data = data[0:importIndex] + data[data.find(";", importIndex) + 1 :]
        importIndex = data.find("@import")

    # parse the css. reverted from dictionary comprehension in order to
    # support older pythons
    pairs = [x.split("{") for x in data.split("}") if "{" in x.strip()]
    try:
        elements = {a.strip(): dumb_property_dict(b) for a, b in pairs}
    except ValueError:
        elements = {}  # not that important

    return elements


def element_style(
    attrs: Dict[str, Optional[str]],
    style_def: Dict[str, Dict[str, str]],
    parent_style: Dict[str, str],
) -> Dict[str, str]:
    """
    :type attrs: dict
    :type style_def: dict
    :type style_def: dict

    :returns: A hash of the 'final' style attributes of the element
    :rtype: dict
    """
    style = parent_style.copy()
    if "class" in attrs:
        assert attrs["class"] is not None
        for css_class in attrs["class"].split():
            css_style = style_def.get("." + css_class, {})
            style.update(css_style)
    if "style" in attrs:
        assert attrs["style"] is not None
        immediate_style = dumb_property_dict(attrs["style"])
        style.update(immediate_style)

    return style


def google_list_style(style: Dict[str, str]) -> str:
    """
    Finds out whether this is an ordered or unordered list

    :type style: dict

    :rtype: str
    """
    if "list-style-type" in style:
        list_style = style["list-style-type"]
        if list_style in ["disc", "circle", "square", "none"]:
            return "ul"

    return "ol"


def google_has_height(style: Dict[str, str]) -> bool:
    """
    Check if the style of the element has the 'height' attribute
    explicitly defined

    :type style: dict

    :rtype: bool
    """
    return "height" in style


def google_text_emphasis(style: Dict[str, str]) -> List[str]:
    """
    :type style: dict

    :returns: A list of all emphasis modifiers of the element
    :rtype: list
    """
    emphasis = []
    if "text-decoration" in style:
        emphasis.append(style["text-decoration"])
    if "font-style" in style:
        emphasis.append(style["font-style"])
    if "font-weight" in style:
        emphasis.append(style["font-weight"])

    return emphasis


def google_fixed_width_font(style: Dict[str, str]) -> bool:
    """
    Check if the css of the current element defines a fixed width font

    :type style: dict

    :rtype: bool
    """
    font_family = ""
    if "font-family" in style:
        font_family = style["font-family"]
    return "courier new" == font_family or "consolas" == font_family


def list_numbering_start(attrs: Dict[str, Optional[str]]) -> int:
    """
    Extract numbering from list element attributes

    :type attrs: dict

    :rtype: int or None
    """
    if "start" in attrs:
        assert attrs["start"] is not None
        try:
            return int(attrs["start"]) - 1
        except ValueError:
            pass

    return 0


def skipwrap(
    para: str, wrap_links: bool, wrap_list_items: bool, wrap_tables: bool
) -> bool:
    # If it appears to contain a link
    # don't wrap
    if not wrap_links and config.RE_LINK.search(para):
        return True
    # If the text begins with four spaces or one tab, it's a code block;
    # don't wrap
    if para[0:4] == "    " or para[0] == "\t":
        return True

    # If the text begins with only two "--", possibly preceded by
    # whitespace, that's an emdash; so wrap.
    stripped = para.lstrip()
    if stripped[0:2] == "--" and len(stripped) > 2 and stripped[2] != "-":
        return False

    # I'm not sure what this is for; I thought it was to detect lists,
    # but there's a <br>-inside-<span> case in one of the tests that
    # also depends upon it.
    if stripped[0:1] in ("-", "*") and not stripped[0:2] == "**":
        return not wrap_list_items

    # If text contains a pipe character it is likely a table
    if not wrap_tables and config.RE_TABLE.search(para):
        return True

    # If the text begins with a single -, *, or +, followed by a space,
    # or an integer, followed by a ., followed by a space (in either
    # case optionally proceeded by whitespace), it's a list; don't wrap.
    return bool(
        config.RE_ORDERED_LIST_MATCHER.match(stripped)
        or config.RE_UNORDERED_LIST_MATCHER.match(stripped)
    )


def escape_md(text: str) -> str:
    """
    Escapes markdown-sensitive characters within other markdown
    constructs.
    """
    return config.RE_MD_CHARS_MATCHER.sub(r"\\\1", text)


def escape_md_section(
    text: str,
    escape_backslash: bool = True,
    snob: bool = False,
    escape_dot: bool = True,
    escape_plus: bool = True,
    escape_dash: bool = True,
) -> str:
    """
    Escapes markdown-sensitive characters across whole document sections.
    Each escaping operation can be controlled individually.
    """
    if escape_backslash:
        text = config.RE_MD_BACKSLASH_MATCHER.sub(r"\\\1", text)

    if snob:
        text = config.RE_MD_CHARS_MATCHER_ALL.sub(r"\\\1", text)

    if escape_dot:
        text = config.RE_MD_DOT_MATCHER.sub(r"\1\\\2", text)

    if escape_plus:
        text = config.RE_MD_PLUS_MATCHER.sub(r"\1\\\2", text)

    if escape_dash:
        text = config.RE_MD_DASH_MATCHER.sub(r"\1\\\2", text)

    return text


def reformat_table(lines: List[str], right_margin: int) -> List[str]:
    """
    Given the lines of a table
    padds the cells and returns the new lines
    """
    # find the maximum width of the columns
    max_width = [len(x.rstrip()) + right_margin for x in lines[0].split("|")]
    max_cols = len(max_width)
    for line in lines:
        cols = [x.rstrip() for x in line.split("|")]
        num_cols = len(cols)

        # don't drop any data if colspan attributes result in unequal lengths
        if num_cols < max_cols:
            cols += [""] * (max_cols - num_cols)
        elif max_cols < num_cols:
            max_width += [len(x) + right_margin for x in cols[-(num_cols - max_cols) :]]
            max_cols = num_cols

        max_width = [
            max(len(x) + right_margin, old_len) for x, old_len in zip(cols, max_width)
        ]

    # reformat
    new_lines = []
    for line in lines:
        cols = [x.rstrip() for x in line.split("|")]
        if set(line.strip()) == set("-|"):
            filler = "-"
            new_cols = [
                x.rstrip() + (filler * (M - len(x.rstrip())))
                for x, M in zip(cols, max_width)
            ]
            new_lines.append("|-" + "|".join(new_cols) + "|")
        else:
            filler = " "
            new_cols = [
                x.rstrip() + (filler * (M - len(x.rstrip())))
                for x, M in zip(cols, max_width)
            ]
            new_lines.append("| " + "|".join(new_cols) + "|")
    return new_lines


def pad_tables_in_text(text: str, right_margin: int = 1) -> str:
    """
    Provide padding for tables in the text
    """
    lines = text.split("\n")
    table_buffer = []  # type: List[str]
    table_started = False
    new_lines = []
    for line in lines:
        # Toggle table started
        if config.TABLE_MARKER_FOR_PAD in line:
            table_started = not table_started
            if not table_started:
                table = reformat_table(table_buffer, right_margin)
                new_lines.extend(table)
                table_buffer = []
                new_lines.append("")
            continue
        # Process lines
        if table_started:
            table_buffer.append(line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)
