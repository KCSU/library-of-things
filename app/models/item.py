"""Library item model."""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.uuid import new_id
from app.models.base_model import BaseModel
from app.models.uuid import UUIDBinary

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.image import ItemImage
    from app.models.loan import Loan, Request


class Item(BaseModel):
    __tablename__ = 'items'

    id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, primary_key=True, default=new_id)
    display_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2047), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey('categories.id'), nullable=False
    )

    # A set duration from the borrowing date, or a fixed calendar end date.
    # If neither set, item is given away rather than lent.
    loan_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loan_end_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    loan_end_recurs_annually: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Whether item is visible to a normal user.
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Natural language comments on an item, set and read by admins.
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[Category] = relationship(back_populates='items')
    loans: Mapped[list[Loan]] = relationship(back_populates='item')
    requests: Mapped[list[Request]] = relationship(back_populates='item')

    # Each item may have an image.
    image: Mapped[ItemImage | None] = relationship(
        back_populates='item', uselist=False, cascade='all, delete-orphan'
    )

    @property
    def is_permanent(self) -> bool:
        """Whether this item is given away, rather than lent for a period of time."""
        return self.loan_duration_days is None and self.loan_end_date is None

    @property
    def outstanding_loans_count(self) -> int:
        return sum(1 for loan in self.loans if loan.returned_at is None)

    @property
    def available_count(self) -> int:
        """Copies neither out on loan, nor being waited on by a pending request."""
        return max(0, self.count - self.outstanding_loans_count - len(self.requests))

    @property
    def has_image(self) -> bool:
        return self.image is not None

    @property
    def image_src(self) -> str | None:
        return f'/items/{self.id}/image' if self.has_image else None

    @property
    def pretty_loan_terms(self) -> str:
        """Human-readable lending terms for badges and labels."""
        if self.loan_duration_days is not None:
            days = self.loan_duration_days
            if days >= 30:
                weeks = days // 7
                return '1 week' if weeks == 1 else f'{weeks} weeks'
            return '1 day' if days == 1 else f'{days} days'

        if self.loan_end_date is not None:
            return f'Until {self.loan_end_date.strftime("%-d %B")}'

        return 'Yours to keep'

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'category': self.category.category if self.category else 'Unknown',
            'is_permanent': self.is_permanent,
            'loan_terms': self.pretty_loan_terms,
            'image_src': self.image_src,
            'has_image': self.has_image,
            'available_count': self.available_count,
        }

    def compute_due_date(
        self, start_time: datetime.datetime
    ) -> datetime.datetime | None:
        if self.loan_duration_days is not None:
            return start_time + datetime.timedelta(days=self.loan_duration_days)

        if self.loan_end_date is not None:
            end = self.loan_end_date
            if self.loan_end_recurs_annually:
                end = _next_occurrence(end, start_time.date())
            return datetime.datetime.combine(end, datetime.time.max)

        return None  # no due date


def _next_occurrence(
    anniversary: datetime.date, on_or_after: datetime.date
) -> datetime.date:
    """The next time this month/day comes round, at or after a given date."""
    for year in (on_or_after.year, on_or_after.year + 1):
        try:
            candidate = anniversary.replace(year=year)
        except ValueError:
            # 29 February in a non-leap year, fall back to the 28th.
            candidate = datetime.date(year, anniversary.month, 28)
        if candidate >= on_or_after:
            return candidate
    return anniversary
