from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import TIMESTAMP, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.common.uuid import new_id
from app.models.base_model import BaseModel
from app.models.uuid import UUIDBinary

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.user import User

_TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


class Loan(BaseModel):
    __tablename__ = 'loans'

    id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, primary_key=True,
                                          default=new_id)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey('items.id'), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey('users.id'), nullable=False)

    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now())

    # None if item was given away rather than lent.
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime,
                                                         nullable=True)

    # Admin ID if created manually by an admin, None otherwise.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey('users.id'), nullable=True)

    item: Mapped[Item] = relationship(back_populates='loans')
    user: Mapped[User] = relationship(foreign_keys=[user_id],
                                      back_populates='loans')
    created_by: Mapped[User | None] = relationship(
        foreign_keys=[created_by_id])

    @property
    def is_returned(self) -> bool:
        return self.returned_at is not None

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None or self.returned_at is not None:
            return False
        return datetime.now() > self.due_date

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'start_time': self.start_time.strftime(_TIMESTAMP_FORMAT),
            'due_date': (self.due_date.strftime(_TIMESTAMP_FORMAT)
                         if self.due_date else None),
            'returned_at': (self.returned_at.strftime(_TIMESTAMP_FORMAT)
                            if self.returned_at else None),
            'is_overdue': self.is_overdue,
            'is_returned': self.is_returned,
            'created_by': self.created_by.name if self.created_by else None,
            'item_title': self.item.title,
            'item_display_id': self.item.display_id,
            'item_image_src': self.item.image_src,
            'borrower_name': self.user.name,
            'borrower_crsid': self.user.crsid,
        }


class Request(BaseModel):
    __tablename__ = 'requests'

    id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, primary_key=True,
                                          default=new_id)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey('items.id'), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey('users.id'), nullable=False)
    request_time: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now())

    item: Mapped[Item] = relationship(back_populates='requests')
    user: Mapped[User] = relationship(back_populates='requests')

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'request_time': self.request_time.strftime(_TIMESTAMP_FORMAT),
            'item_title': self.item.title,
            'item_display_id': self.item.display_id,
            'item_image_src': self.item.image_src,
            'item_location': self.item.location,
            'borrower_name': self.user.name,
            'borrower_crsid': self.user.crsid,
        }
