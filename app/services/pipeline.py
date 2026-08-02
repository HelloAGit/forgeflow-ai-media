import logging
import struct
import zlib

from app.config import settings

logger = logging.getLogger(__name__)

try:
    import genblaze  # type: ignore[import]
    _GENBLAZE_AVAILABLE = True
except ImportError:
    _GENBLAZE_AVAILABLE = False
    logger.warning(
        "genblaze SDK not installed; media generation will return a placeholder PNG. "
        "Install it with: pip install genblaze"
    )


def _make_placeholder_png() -> bytes:
    """Return a minimal valid 1×1 white PNG encoded as raw bytes."""

    def _chunk(tag: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return length + tag + data + crc

    signature = b"\x89PNG\r\n\x1a\n"
    # IHDR: width=1, height=1, bit_depth=8, color_type=2 (RGB), compression=0, filter=0, interlace=0
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)
    # IDAT: one scanline; filter byte 0x00 followed by RGB (255, 255, 255) = white
    raw_scanline = b"\x00\xff\xff\xff"
    idat = _chunk(b"IDAT", zlib.compress(raw_scanline))
    iend = _chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


class GenblazePipeline:
    def __init__(self) -> None:
        self.api_key = settings.GMI_API_KEY
        if _GENBLAZE_AVAILABLE:
            self._client = genblaze.Client(api_key=self.api_key)
        else:
            self._client = None

    def generate_media(self, prompt: str, parameters: dict) -> bytes:
        """
        Generate media via the Genblaze SDK.

        Returns the raw bytes of the generated asset (PNG).
        Falls back to a placeholder PNG when the SDK is not installed.
        """
        if self._client is not None:
            try:
                result = self._client.generate(prompt=prompt, **parameters)
                return result.content
            except Exception:
                logger.exception("Genblaze SDK call failed; returning placeholder PNG.")
                return _make_placeholder_png()

        logger.warning("Genblaze SDK unavailable; returning placeholder PNG.")
        return _make_placeholder_png()


pipeline_service = GenblazePipeline()
