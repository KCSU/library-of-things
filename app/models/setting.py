from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.uuid import new_id
from app.models.base_model import BaseModel
from app.models.uuid import UUIDBinary


class Setting(BaseModel):
    """Application settings: a single row with typed columns."""

    __tablename__ = 'settings'

    id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, primary_key=True, default=new_id)

    announcement_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    announcement_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    read_only_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': str(self.id),
            'announcement_text': self.announcement_text,
            'announcement_enabled': self.announcement_enabled,
            'read_only_mode': self.read_only_mode,
        }
