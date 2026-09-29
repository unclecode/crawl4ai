import pytest

from crawl4ai.processors.pdf.utils import apply_png_predictor


@pytest.mark.parametrize(
    "width,bits", [(9, 1), (16, 1), (5, 2), (8, 2), (3, 4), (4, 4)]
)
@pytest.mark.parametrize(
    "second_row",
    [
        b"\x00\x30\x40",  # None
        b"\x01\x30\x10",  # Sub
        b"\x02\x20\x20",  # Up
        b"\x03\x28\x18",  # Average
        b"\x04\x20\x10",  # Paeth
    ],
)
def test_png_predictor_decodes_packed_scanlines(width, bits, second_row):
    # Each row contains two packed bytes, including padding bits for odd widths.
    encoded = b"\x00\x10\x20" + second_row

    assert apply_png_predictor(encoded, width, bits, 1) == b"\x10\x20\x30\x40"


@pytest.mark.parametrize("bits,channels", [(8, 1), (8, 3), (16, 1), (16, 3)])
def test_png_predictor_preserves_byte_aligned_samples(bits, channels):
    row = bytes(range(2 * channels * (bits // 8)))
    encoded = b"\x00" + row + b"\x02" + bytes(len(row))

    assert apply_png_predictor(encoded, 2, bits, channels) == row + row


def test_png_predictor_rejects_truncated_packed_row():
    with pytest.raises(ValueError, match="Invalid scanline structure"):
        apply_png_predictor(b"\x00\x10", 9, 1, 1)
