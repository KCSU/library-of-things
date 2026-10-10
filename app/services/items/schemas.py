"""Validation for item data sent by the admin inventory form."""

import datetime
import uuid
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ItemInput(BaseModel):
    """Every editable field of an item."""

    # Unknown keys are rejected.
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=2047)
    category_id: uuid.UUID
    loan_duration_days: int | None = Field(default=None, ge=1)
    loan_end_date: datetime.date | None = None
    loan_end_recurs_annually: bool = False
    visible: bool = True
    count: int = Field(default=1, ge=0)
    location: str | None = Field(default=None, max_length=255)
    comments: str | None = None

    @field_validator('location', 'comments', mode='before')
    @classmethod
    def _blank_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode='after')
    def _one_loan_term(self) -> Self:
        if self.loan_duration_days is not None and self.loan_end_date is not None:
            raise ValueError('Set either a loan duration or an end date, not both')
        return self
