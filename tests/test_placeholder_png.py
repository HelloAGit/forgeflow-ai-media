"""Tests that _make_placeholder_png() returns a valid PNG byte stream."""
import struct
import zlib


def _parse_png_chunks(data: bytes):
    """Yield (tag, chunk_data) for each chunk in a PNG stream (after signature)."""
    pos = 8  # skip 8-byte PNG signature
    chunks = []
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        stored_crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        expected_crc = zlib.crc32(tag + chunk_data) & 0xFFFFFFFF
        chunks.append((tag, chunk_data, stored_crc == expected_crc))
        pos += 12 + length
    return chunks


def test_png_signature():
    from app.services.pipeline import _make_placeholder_png
    data = _make_placeholder_png()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "Missing PNG signature"


def test_png_has_ihdr():
    from app.services.pipeline import _make_placeholder_png
    data = _make_placeholder_png()
    chunks = _parse_png_chunks(data)
    tags = [c[0] for c in chunks]
    assert b"IHDR" in tags


def test_png_has_idat():
    from app.services.pipeline import _make_placeholder_png
    data = _make_placeholder_png()
    chunks = _parse_png_chunks(data)
    tags = [c[0] for c in chunks]
    assert b"IDAT" in tags


def test_png_ends_with_iend():
    from app.services.pipeline import _make_placeholder_png
    data = _make_placeholder_png()
    chunks = _parse_png_chunks(data)
    assert chunks[-1][0] == b"IEND"


def test_png_crc_valid():
    from app.services.pipeline import _make_placeholder_png
    data = _make_placeholder_png()
    chunks = _parse_png_chunks(data)
    for tag, _, crc_ok in chunks:
        assert crc_ok, f"CRC mismatch in chunk {tag}"


def test_png_dimensions_1x1():
    from app.services.pipeline import _make_placeholder_png
    data = _make_placeholder_png()
    chunks = _parse_png_chunks(data)
    ihdr_data = next(d for t, d, _ in chunks if t == b"IHDR")
    width, height = struct.unpack(">II", ihdr_data[:8])
    assert width == 1
    assert height == 1


def test_placeholder_is_deterministic():
    from app.services.pipeline import _make_placeholder_png
    assert _make_placeholder_png() == _make_placeholder_png()
