"""Site-wide admin queries."""

import json
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.common.database import db_session
from app.models import Audit

PAGE_SIZE = 20


def _audit_query(session: Session, search: str) -> Query[Audit]:
    """Entries whose message or actor contains the search text."""
    query = session.query(Audit)
    if search:
        query = query.filter(
            or_(
                Audit.message.icontains(search, autoescape=True),
                Audit.actor_crsid.icontains(search, autoescape=True),
            )
        )
    return query


def count_audit_entries(search: str = '') -> int:
    with db_session() as session:
        return _audit_query(session, search).count()


def get_audit_log(page: int = 1, search: str = '') -> list[dict[str, Any]]:
    """One page of the audit log, newest first. Pages count from 1."""
    with db_session() as session:
        rows = (
            _audit_query(session, search)
            .order_by(Audit.created_at.desc(), Audit.id.desc())
            .offset((page - 1) * PAGE_SIZE)
            .limit(PAGE_SIZE)
            .all()
        )
        return [
            {
                'when': row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'actor': row.actor_crsid or 'system',
                'message': row.message,
                'extra': (
                    json.dumps(row.extra, indent=2, ensure_ascii=False)
                    if row.extra
                    else None
                ),
            }
            for row in rows
        ]
