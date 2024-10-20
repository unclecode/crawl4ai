import argparse
import sys

from . import HTML2Text, __version__, config


def main() -> None:
    baseurl = ""

    class bcolors:
        HEADER = "\033[95m"
        OKBLUE = "\033[94m"
        OKGREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        ENDC = "\033[0m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"

    p = argparse.ArgumentParser()
    p.add_argument(
        "--default-image-alt",
        dest="default_image_alt",
        default=config.DEFAULT_IMAGE_ALT,
        help="The default alt string for images with missing ones",
    )
    p.add_argument(
        "--pad-tables",
        dest="pad_tables",
        action="store_true",
        default=config.PAD_TABLES,
        help="pad the cells to equal column width in tables",
    )
    p.add_argument(
        "--no-wrap-links",
        dest="wrap_links",
        action="store_false",
        default=config.WRAP_LINKS,
        help="don't wrap links during conversion",
    )
    p.add_argument(
        "--wrap-list-items",
        dest="wrap_list_items",
        action="store_true",
        default=config.WRAP_LIST_ITEMS,
        help="wrap list items during conversion",
    )
    p.add_argument(
        "--wrap-tables",
        dest="wrap_tables",
        action="store_true",
        default=config.WRAP_TABLES,
        help="wrap tables",
    )
    p.add_argument(
        "--ignore-emphasis",
        dest="ignore_emphasis",
        action="store_true",
        default=config.IGNORE_EMPHASIS,
        help="don't include any formatting for emphasis",
    )
    p.add_argument(
        "--reference-links",
        dest="inline_links",
        action="store_false",
        default=config.INLINE_LINKS,
        help="use reference style links instead of inline links",
    )
    p.add_argument(
        "--ignore-links",
        dest="ignore_links",
        action="store_true",
        default=config.IGNORE_ANCHORS,
        help="don't include any formatting for links",
    )
    p.add_argument(
        "--ignore-mailto-links",
        action="store_true",
        dest="ignore_mailto_links",
        default=config.IGNORE_MAILTO_LINKS,
        help="don't include mailto: links",
    )
    p.add_argument(
        "--protect-links",
        dest="protect_links",
        action="store_true",
        default=config.PROTECT_LINKS,
        help="protect links from line breaks surrounding them with angle brackets",
    )
    p.add_argument(
        "--ignore-images",
        dest="ignore_images",
        action="store_true",
        default=config.IGNORE_IMAGES,
        help="don't include any formatting for images",
    )
    p.add_argument(
        "--images-as-html",
        dest="images_as_html",
        action="store_true",
        default=config.IMAGES_AS_HTML,
        help=(
            "Always write image tags as raw html; preserves `height`, `width` and "
            "`alt` if possible."
        ),
    )
    p.add_argument(
        "--images-to-alt",
        dest="images_to_alt",
        action="store_true",
        default=config.IMAGES_TO_ALT,
        help="Discard image data, only keep alt text",
    )
    p.add_argument(
        "--images-with-size",
        dest="images_with_size",
        action="store_true",
        default=config.IMAGES_WITH_SIZE,
        help=(
            "Write image tags with height and width attrs as raw html to retain "
            "dimensions"
        ),
    )
    p.add_argument(
        "-g",
        "--google-doc",
        action="store_true",
        dest="google_doc",
        default=False,
        help="convert an html-exported Google Document",
    )
    p.add_argument(
        "-d",
        "--dash-unordered-list",
        action="store_true",
        dest="ul_style_dash",
        default=False,
        help="use a dash rather than a star for unordered list items",
    )
    p.add_argument(
        "-e",
        "--asterisk-emphasis",
        action="store_true",
        dest="em_style_asterisk",
        default=False,
        help="use an asterisk rather than an underscore for emphasized text",
    )
    p.add_argument(
        "-b",
        "--body-width",
        dest="body_width",
        type=int,
        default=config.BODY_WIDTH,
        help="number of characters per output line, 0 for no wrap",
    )
    p.add_argument(
        "-i",
        "--google-list-indent",
        dest="list_indent",
        type=int,
        default=config.GOOGLE_LIST_INDENT,
        help="number of pixels Google indents nested lists",
    )
    p.add_argument(
        "-s",
        "--hide-strikethrough",
        action="store_true",
        dest="hide_strikethrough",
        default=False,
        help="hide strike-through text. only relevant when -g is " "specified as well",
    )
    p.add_argument(
        "--escape-all",
        action="store_true",
        dest="escape_snob",
        default=False,
        help=(
            "Escape all special characters.  Output is less readable, but avoids "
            "corner case formatting issues."
        ),
    )
    p.add_argument(
        "--bypass-tables",
        action="store_true",
        dest="bypass_tables",
        default=config.BYPASS_TABLES,
        help="Format tables in HTML rather than Markdown syntax.",
    )
    p.add_argument(
        "--ignore-tables",
        action="store_true",
        dest="ignore_tables",
        default=config.IGNORE_TABLES,
        help="Ignore table-related tags (table, th, td, tr) " "while keeping rows.",
    )
    p.add_argument(
        "--single-line-break",
        action="store_true",
        dest="single_line_break",
        default=config.SINGLE_LINE_BREAK,
        help=(
            "Use a single line break after a block element rather than two line "
            "breaks. NOTE: Requires --body-width=0"
        ),
    )
    p.add_argument(
        "--unicode-snob",
        action="store_true",
        dest="unicode_snob",
        default=config.UNICODE_SNOB,
        help="Use unicode throughout document",
    )
    p.add_argument(
        "--no-automatic-links",
        action="store_false",
        dest="use_automatic_links",
        default=config.USE_AUTOMATIC_LINKS,
        help="Do not use automatic links wherever applicable",
    )
    p.add_argument(
        "--no-skip-internal-links",
        action="store_false",
        dest="skip_internal_links",
        default=config.SKIP_INTERNAL_LINKS,
        help="Do not skip internal links",
    )
    p.add_argument(
        "--links-after-para",
        action="store_true",
        dest="links_each_paragraph",
        default=config.LINKS_EACH_PARAGRAPH,
        help="Put links after each paragraph instead of document",
    )
    p.add_argument(
        "--mark-code",
        action="store_true",
        dest="mark_code",
        default=config.MARK_CODE,
        help="Mark program code blocks with [code]...[/code]",
    )
    p.add_argument(
        "--decode-errors",
        dest="decode_errors",
        default=config.DECODE_ERRORS,
        help=(
            "What to do in case of decode errors.'ignore', 'strict' and 'replace' are "
            "acceptable values"
        ),
    )
    p.add_argument(
        "--open-quote",
        dest="open_quote",
        default=config.OPEN_QUOTE,
        help="The character used to open quotes",
    )
    p.add_argument(
        "--close-quote",
        dest="close_quote",
        default=config.CLOSE_QUOTE,
        help="The character used to close quotes",
    )
    p.add_argument(
        "--version", action="version", version=".".join(map(str, __version__))
    )
    p.add_argument("filename", nargs="?")
    p.add_argument("encoding", nargs="?", default="utf-8")
    p.add_argument(
        "--include-sup-sub",
        dest="include_sup_sub",
        action="store_true",
        default=config.INCLUDE_SUP_SUB,
        help="Include the sup and sub tags",
    )
    args = p.parse_args()

    if args.filename and args.filename != "-":
        with open(args.filename, "rb") as fp:
            data = fp.read()
    else:
        data = sys.stdin.buffer.read()

    try:
        html = data.decode(args.encoding, args.decode_errors)
    except UnicodeDecodeError as err:
        warning = bcolors.WARNING + "Warning:" + bcolors.ENDC
        warning += " Use the " + bcolors.OKGREEN
        warning += "--decode-errors=ignore" + bcolors.ENDC + " flag."
        print(warning)
        raise err

    h = HTML2Text(baseurl=baseurl)
    # handle options
    if args.ul_style_dash:
        h.ul_item_mark = "-"
    if args.em_style_asterisk:
        h.emphasis_mark = "*"
        h.strong_mark = "__"

    h.body_width = args.body_width
    h.google_list_indent = args.list_indent
    h.ignore_emphasis = args.ignore_emphasis
    h.ignore_links = args.ignore_links
    h.ignore_mailto_links = args.ignore_mailto_links
    h.protect_links = args.protect_links
    h.ignore_images = args.ignore_images
    h.images_as_html = args.images_as_html
    h.images_to_alt = args.images_to_alt
    h.images_with_size = args.images_with_size
    h.google_doc = args.google_doc
    h.hide_strikethrough = args.hide_strikethrough
    h.escape_snob = args.escape_snob
    h.bypass_tables = args.bypass_tables
    h.ignore_tables = args.ignore_tables
    h.single_line_break = args.single_line_break
    h.inline_links = args.inline_links
    h.unicode_snob = args.unicode_snob
    h.use_automatic_links = args.use_automatic_links
    h.skip_internal_links = args.skip_internal_links
    h.links_each_paragraph = args.links_each_paragraph
    h.mark_code = args.mark_code
    h.wrap_links = args.wrap_links
    h.wrap_list_items = args.wrap_list_items
    h.wrap_tables = args.wrap_tables
    h.pad_tables = args.pad_tables
    h.default_image_alt = args.default_image_alt
    h.open_quote = args.open_quote
    h.close_quote = args.close_quote
    h.include_sup_sub = args.include_sup_sub

    sys.stdout.write(h.handle(html))
