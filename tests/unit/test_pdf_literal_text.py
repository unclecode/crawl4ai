"""PDF text is already decoded when it reaches the formatting helpers."""

import pytest
from lxml import html

pytest.importorskip("pypdf")
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.processors.pdf.processor import NaivePDFProcessorStrategy


def write_text_pdf(path, text):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
            NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
        }
    )
    # A real PDF ToUnicode map lets the fixture include non-BMP text without
    # downloading or embedding an additional font.
    characters = list(dict.fromkeys(text.replace("\n", "")))
    codes = {}
    for char in characters:
        try:
            codes[char] = char.encode("cp1252")
        except UnicodeEncodeError:
            pass
    available_codes = (bytes([value]) for value in range(128, 256))
    for char in characters:
        if char not in codes:
            codes[char] = next(
                code for code in available_codes if code not in codes.values()
            )
    unicode_map = DecodedStreamObject()
    mappings = "\n".join(
        f"<{code.hex()}> <{char.encode('utf-16-be').hex()}>"
        for char, code in codes.items()
    )
    unicode_map.set_data(
        (
            "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
            "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
            "/CMapName /LiteralText def\n/CMapType 2 def\n"
            "1 begincodespacerange\n<00> <ff>\nendcodespacerange\n"
            f"{len(codes)} beginbfchar\n{mappings}\nendbfchar\n"
            "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n"
        ).encode("ascii")
    )
    font[NameObject("/ToUnicode")] = writer._add_object(unicode_map)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    commands = ["BT /F1 12 Tf 72 720 Td"]
    for index, line in enumerate(text.split("\n")):
        if index:
            commands.append("0 -16 Td")
        encoded = b"".join(codes[char] for char in line)
        commands.append(f"<{encoded.hex()}> Tj")
    commands.append("ET")
    stream = DecodedStreamObject()
    stream.set_data("\n".join(commands).encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.write(path)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(r"path: C:\new\test.txt.", id="windows-path"),
        pytest.param(r"literal: \u0041.", id="literal-unicode-escape"),
        pytest.param(r"slashes: \\server.", id="literal-double-backslash"),
        pytest.param(r"literal: \u2020.", id="literal-dagger-escape"),
        pytest.param(r"literal: \ud835.", id="literal-surrogate-escape"),
        pytest.param(r"literal: \ud835\udc00.", id="literal-surrogate-pair"),
        pytest.param("ordinary: café £42.", id="ordinary-unicode"),
        pytest.param("symbols: † 𝐀.", id="actual-dagger-and-non-bmp"),
        pytest.param("first line remains.\nsecond line remains.", id="actual-newline"),
        pytest.param(r"literal: \q.", id="non-escape-backslash"),
    ],
)
def test_public_pdf_processing_preserves_literal_text(tmp_path, text):
    path = tmp_path / "literal-text.pdf"
    write_text_pdf(path, text)
    reader_text = PdfReader(path).pages[0].extract_text()
    page = NaivePDFProcessorStrategy(extract_images=False).process(path).pages[0]
    scraped = PDFContentScrapingStrategy(extract_images=False).scrap(str(path), "")
    actual = {
        "reader_text": reader_text,
        "raw_text": page.raw_text,
        "markdown": page.markdown,
        "page_html_text": html.fromstring(page.html).text_content(),
        "scraped_html_text": html.fromstring(scraped.cleaned_html).text_content(),
    }
    assert reader_text.strip() == text
    assert page.raw_text.strip() == text
    expected = " ".join(text.split())
    for key in ("markdown", "page_html_text", "scraped_html_text"):
        assert expected in " ".join(actual[key].split()), key
