"""Item-image model. Each item may optionally have one image."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.uuid import new_id
from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.item import Item


class ItemImage(BaseModel):
    __tablename__ = 'item_images'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey('items.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # sha256 hash of the content
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    item: Mapped[Item] = relationship(back_populates='image')
