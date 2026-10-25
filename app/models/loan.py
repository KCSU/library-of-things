from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.common.timing import format_london, utcnow
from app.common.uuid import new_id
from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.user import User


class Loan(BaseModel):
    __tablename__ = 'loans'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('items.id'), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('users.id'), nullable=False
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # None if item was given away rather than lent.
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Admin ID if created manually by an admin, None otherwise.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey('users.id'), nullable=True
    )

    item: Mapped[Item] = relationship(back_populates='loans')
    user: Mapped[User] = relationship(foreign_keys=[user_id], back_populates='loans')
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])

    @property
    def is_returned(self) -> bool:
        return self.returned_at is not None

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None or self.returned_at is not None:
            return False
        return utcnow() > self.due_date

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'start_time': format_london(self.start_time),
            'due_date': format_london(self.due_date),
            'returned_at': format_london(self.returned_at),
            'is_overdue': self.is_overdue,
            'is_returned': self.is_returned,
            'created_by': self.created_by.name if self.created_by else None,
            'item_title': self.item.title,
            'item_image_src': self.item.image_src,
            'borrower_name': self.user.name,
            'borrower_crsid': self.user.crsid,
        }


class Request(BaseModel):
    __tablename__ = 'requests'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('items.id'), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey('users.id'), nullable=False
    )
    request_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    item: Mapped[Item] = relationship(back_populates='requests')
    user: Mapped[User] = relationship(back_populates='requests')

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'request_time': format_london(self.request_time),
            'item_title': self.item.title,
            'item_image_src': self.item.image_src,
            'item_location': self.item.location,
            'borrower_name': self.user.name,
            'borrower_crsid': self.user.crsid,
        }
