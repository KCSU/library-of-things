from __future__ import annotations

import uuid
from enum import IntEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.uuid import new_id
from app.models.base_model import BaseModel
from app.models.uuid import UUIDBinary

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.loan import Loan, Request


class Role(IntEnum):
    USER = 10  # plain user
    LIBRARIAN = 20  # + manage items, loans and requests, read settings
    ADMIN = 30  # + everything else

    @property
    def label(self) -> str:
        return self.name.capitalize()


class User(BaseModel):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, primary_key=True, default=new_id)
    crsid: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey('groups.id'), nullable=False
    )
    role: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=Role.USER)
    # Cleared when Lookup stops listing the user. They can no longer sign in
    # but their loan history survives.
    user_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Hand-added users are invisible to Lookup and must survive a sync.
    is_manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    group: Mapped[Group] = relationship(back_populates='users')
    loans: Mapped[list[Loan]] = relationship(
        foreign_keys='Loan.user_id', back_populates='user'
    )
    requests: Mapped[list[Request]] = relationship(back_populates='user')
