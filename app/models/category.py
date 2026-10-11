from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.uuid import new_id
from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.item import Item


class Category(BaseModel):
    __tablename__ = 'categories'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    category: Mapped[str] = mapped_column(String(255), nullable=False)

    items: Mapped[list[Item]] = relationship(back_populates='category')
