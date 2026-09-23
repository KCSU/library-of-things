import uuid
from typing import Any


def new_id() -> uuid.UUID:
    """Returns a fresh UUIDv7."""
    return uuid.uuid7()


def parse_id(value: Any) -> uuid.UUID | None:
    """Try coercing a client-supplied id to a UUID, None if it isn't one."""
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return None
    return None
