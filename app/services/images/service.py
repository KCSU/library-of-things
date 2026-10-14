"""Item image storage."""

import logging
import uuid

from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

from app.common.database import db_session
from app.common.images import WebPImageBytes, encode
from app.common.timing import log_slow
from app.models import ItemImage
from app.services.images.files import read_upload

logger = logging.getLogger(__name__)


@log_slow
def encode_upload(file_storage: FileStorage) -> WebPImageBytes:
    """Read and normalise an uploaded image.

    Raises ValueError if the upload is too large or not a usable image.
    """
    raw = read_upload(file_storage)
    try:
        return encode(raw)
    except ValueError as exc:
        raise ValueError(f'Unsupported image: {exc}') from exc


def save(session: Session, item_id: uuid.UUID, encoded: WebPImageBytes) -> None:
    """Set an item's image, replacing any existing one, in the caller's
    transaction."""
    image = session.query(ItemImage).filter(ItemImage.item_id == item_id).first()
    if image is None:
        image = ItemImage(item_id=item_id)
        session.add(image)

    image.content = encoded.content
    image.byte_size = encoded.byte_size
    image.width = encoded.width
    image.height = encoded.height
    image.checksum = encoded.checksum


@log_slow
def fetch(item_id: uuid.UUID) -> tuple[bytes, str] | None:
    """Return (content, checksum) for an item's image."""
    with db_session() as session:
        image = session.query(ItemImage).filter(ItemImage.item_id == item_id).first()
        if image is None:
            return None
        return image.content, image.checksum


def delete(item_id: uuid.UUID) -> bool:
    with db_session() as session:
        return bool(
            session.query(ItemImage).filter(ItemImage.item_id == item_id).delete()
        )
