"""Site-wide admin queries."""

from typing import Any

from app.common.database import db_session
from app.models import Audit

# TODO(khm39): paginate instead of limit
LOG_LIMIT = 200


def get_audit_log(limit: int = LOG_LIMIT) -> list[dict[str, Any]]:
    with db_session() as session:
        rows = (session.query(Audit)
                .order_by(Audit.created_at.desc(), Audit.id.desc())
                .limit(limit)
                .all())
        return [{
            'when': row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'actor': row.actor_crsid or 'system',
            'message': row.message,
        } for row in rows]
