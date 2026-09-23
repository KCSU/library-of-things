"""Image normalisation functions."""

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps

from app.config import (
    IMAGE_MAX_DIMENSION,
    IMAGE_MAX_STORED_BYTES,
    IMAGE_QUALITY,
)


@dataclass(frozen=True)
class WebPImageBytes:
    content: bytes
    width: int
    height: int
    checksum: str

    @property
    def byte_size(self) -> int:
        return len(self.content)


def encode(raw: bytes) -> WebPImageBytes:
    """Normalise arbitrary image bytes to a WebP image."""
    if not raw:
        raise ValueError('Image cannot be empty.')

    try:
        source = Image.open(io.BytesIO(raw))
        source = ImageOps.exif_transpose(source)
        source.load()
    except Exception as exc:
        raise ValueError(f'Image unreadable: {exc}') from exc

    # Convert to opaque RGB
    if source.mode in ('RGBA', 'LA') or 'transparency' in source.info:
        source = source.convert('RGBA')
        flattened = Image.new('RGB', source.size, (255, 255, 255))
        flattened.paste(source, mask=source.split()[3])
        source = flattened
    elif source.mode != 'RGB':
        source = source.convert('RGB')

    source.thumbnail((IMAGE_MAX_DIMENSION, IMAGE_MAX_DIMENSION),
                     Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    source.save(buffer, format='WEBP', quality=IMAGE_QUALITY, method=6)
    content = buffer.getvalue()

    if len(content) > IMAGE_MAX_STORED_BYTES:
        raise ValueError(
            f'Encoded image is too large ({len(content)} bytes), over the '
            f'{IMAGE_MAX_STORED_BYTES} byte limit.'
        )

    return WebPImageBytes(
        content=content,
        width=source.width,
        height=source.height,
        checksum=hashlib.sha256(content).hexdigest(),
    )
