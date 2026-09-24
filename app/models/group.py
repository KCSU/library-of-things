from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.uuid import new_id
from app.models.base_model import BaseModel
from app.models.uuid import UUIDBinary

if TYPE_CHECKING:
    from app.models.user import User


class Group(BaseModel):
    __tablename__ = 'groups'

    id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Comma-separated Lookup identifiers.
    lookup_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Either 'group' or 'inst'.
    lookup_type: Mapped[str | None] = mapped_column(
        String(8), nullable=True, default='group'
    )

    users: Mapped[list[User]] = relationship(back_populates='group')
