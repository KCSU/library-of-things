from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.common.uuid import new_id
from app.models.base_model import BaseModel


class Setting(BaseModel):
    """Application settings: a single row with typed columns."""

    __tablename__ = 'settings'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)

    announcement_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    announcement_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    read_only_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Which emails are sent to borrowers. See app/templates/email.
    email_request_approved: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    email_request_refused: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    email_loan_due: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_loan_overdue: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'announcement_text': self.announcement_text,
            'announcement_enabled': self.announcement_enabled,
            'read_only_mode': self.read_only_mode,
            'email_request_approved': self.email_request_approved,
            'email_request_refused': self.email_request_refused,
            'email_loan_due': self.email_loan_due,
            'email_loan_overdue': self.email_loan_overdue,
        }
