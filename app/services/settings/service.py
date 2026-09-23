"""Site settings operations."""

from typing import Any

from sqlalchemy.orm import Session

from app.common.database import db_session
from app.models import Setting


def _row(session: Session) -> Setting | None:
    """The singular settings row, or None before anything has been saved."""
    return session.query(Setting).first()


def _row_for_write(session: Session) -> Setting:
    settings = session.query(Setting).first()
    if settings is None:
        settings = Setting()
        session.add(settings)
    return settings


def get_announcement() -> dict[str, Any]:
    with db_session() as session:
        settings = _row(session)
        if settings is None:
            return {'text': '', 'enabled': False}
        return {
            'text': settings.announcement_text or '',
            'enabled': settings.announcement_enabled,
        }


def update_announcement(text: str, enabled: bool) -> bool:
    with db_session() as session:
        settings = _row_for_write(session)
        settings.announcement_text = text
        settings.announcement_enabled = enabled
        return True


def get_read_only_mode() -> bool:
    with db_session() as session:
        settings = _row(session)
        return bool(settings and settings.read_only_mode)


def set_read_only_mode(enabled: bool) -> bool:
    with db_session() as session:
        _row_for_write(session).read_only_mode = enabled
        return True
