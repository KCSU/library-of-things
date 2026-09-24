"""Custom column types."""

import uuid
from typing import Any

from sqlalchemy.engine import Dialect
from sqlalchemy.types import BINARY, TypeDecorator


class UUIDBinary(TypeDecorator[uuid.UUID]):
    """A UUID stored as BINARY(16)."""

    impl = BINARY(16)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> bytes | None:
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value.bytes

    def process_result_value(
        self, value: bytes | None, dialect: Dialect
    ) -> uuid.UUID | None:
        return uuid.UUID(bytes=value) if value is not None else None
