"""Item image storage."""

import logging
import uuid
from typing import Any

from app.common.database import db_session
from app.common.images import encode
from app.common.timing import log_slow
from app.models import Item, ItemImage

logger = logging.getLogger(__name__)



@log_slow
def store(item_id: uuid.UUID, raw: bytes) -> dict[str, Any] | None:
    """Normalise and save an image, replacing any existing one.

    Returns the stored image's metadata, or None if the item is unknown.
    Raises ValueError if the bytes are not a usable image.
    """
    encoded = encode(raw)

    with db_session() as session:
        item = session.query(Item).filter(Item.id == item_id).first()
        if item is None:
            return None

        image = (session.query(ItemImage)
                 .filter(ItemImage.item_id == item_id).first())
        if image is None:
            image = ItemImage(item_id=item_id)
            session.add(image)

        image.content = encoded.content
        image.byte_size = encoded.byte_size
        image.width = encoded.width
        image.height = encoded.height
        image.checksum = encoded.checksum
        session.flush()

        return {
            'byte_size': encoded.byte_size,
            'width': encoded.width,
            'height': encoded.height,
            'checksum': encoded.checksum,
        }


@log_slow
def fetch(item_id: uuid.UUID) -> tuple[bytes, str] | None:
    """Return (content, checksum) for an item's image."""
    with db_session() as session:
        image = (session.query(ItemImage)
                 .filter(ItemImage.item_id == item_id).first())
        if image is None:
            return None
        return image.content, image.checksum


def delete(item_id: uuid.UUID) -> bool:
    with db_session() as session:
        return bool(
            session.query(ItemImage)
            .filter(ItemImage.item_id == item_id).delete()
        )
