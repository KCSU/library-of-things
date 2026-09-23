import uuid
from datetime import date, time
from typing import Any

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, date | time):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)

            result[column.name] = value
        return result

    def update_from_dict(self, data: dict[str, Any]) -> None:
        columns = {column.name for column in self.__table__.columns}
        for key, value in data.items():
            if key in columns:
                setattr(self, key, value)
