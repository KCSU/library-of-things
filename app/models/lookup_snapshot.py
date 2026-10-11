"""The latest membership of a Lookup group, as published by kcsu-admin."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class LookupSnapshot(BaseModel):
    __tablename__ = 'lookup_snapshots'

    # Lookup's numeric group ID, e.g. '105777'.
    group_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    # Lookup's group name, e.g. 'kings-sis-ug'.
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # When kcsu-admin read it from Lookup, in UTC.
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # [{'crsid': ..., 'name': ...}, ...]
    members: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
