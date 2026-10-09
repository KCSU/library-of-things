"""Site settings operations."""

from typing import Any

from sqlalchemy.orm import Session

from app.common.database import db_session
from app.models import Audit, Setting

EMAILS = ('request_approved', 'request_refused', 'loan_due', 'loan_overdue')

_ANNOUNCEMENT_FIELDS = {'announcement_text', 'announcement_enabled'}
_EMAIL_FIELDS = {f'email_{email}' for email in EMAILS}


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


def get_read_only_mode() -> bool:
    with db_session() as session:
        settings = _row(session)
        return bool(settings and settings.read_only_mode)


def get_emails() -> dict[str, bool]:
    """Which emails are enabled, e.g. {'loan_due': True}. All are by default."""
    with db_session() as session:
        settings = _row(session)
        return {
            email: settings is None or bool(getattr(settings, f'email_{email}'))
            for email in EMAILS
        }


def update_settings(
    announcement_text: str,
    announcement_enabled: bool,
    read_only: bool,
    emails: dict[str, bool],
    acting_crsid: str,
) -> bool:
    with db_session() as session:
        settings = _row_for_write(session)
        before = {
            'announcement_text': settings.announcement_text or '',
            'announcement_enabled': bool(settings.announcement_enabled),
            'read_only_mode': bool(settings.read_only_mode),
        } | {field: bool(getattr(settings, field)) for field in _EMAIL_FIELDS}
        after = {
            'announcement_text': announcement_text,
            'announcement_enabled': announcement_enabled,
            'read_only_mode': read_only,
        } | {f'email_{email}': emails[email] for email in EMAILS}
        for field, value in after.items():
            setattr(settings, field, value)

        changes = {
            field: {'before': before[field], 'after': after[field]}
            for field in after
            if after[field] != before[field]
        }
        if changes:
            session.add(
                Audit(
                    actor_crsid=acting_crsid,
                    message=_describe(changes),
                    extra={'changes': changes},
                )
            )
        return True


def _describe(changes: dict[str, Any]) -> str:
    if set(changes) == {'read_only_mode'}:
        state = 'on' if changes['read_only_mode']['after'] else 'off'
        return f'Turned {state} read-only mode'
    if set(changes) <= _ANNOUNCEMENT_FIELDS:
        return 'Updated the announcement'
    if set(changes) <= _EMAIL_FIELDS:
        return 'Updated email notifications'
    return 'Changed site settings'
