"""Reconcile the user table against Lookup group snapshots from kcsu-admin."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.common.database import db_session
from app.common.timing import log_duration
from app.config import LOOKUP_GROUPS
from app.models import Audit, LookupSnapshot, Role, User
from app.proto.kcsu.lookup.v1.group_snapshot_pb2 import GroupSnapshot

logger = logging.getLogger(__name__)


@dataclass
class SyncReport:
    # All strings are CRSids.
    created: set[str] = field(default_factory=set)
    reenabled: set[str] = field(default_factory=set)
    disabled: set[str] = field(default_factory=set)
    renamed: set[str] = field(default_factory=set)
    unchanged: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.created | self.reenabled | self.disabled | self.renamed)

    def summary(self) -> str:
        return (
            f'created={len(self.created)} reenabled={len(self.reenabled)} '
            f'disabled={len(self.disabled)} renamed={len(self.renamed)} '
            f'unchanged={self.unchanged}'
        )


@log_duration
def apply_snapshot(snapshot: GroupSnapshot) -> SyncReport | None:
    """Store a Lookup group's snapshot, then reconcile the users against every
    group in LOOKUP_GROUPS. Returns what changed.

    Returns None, changing no users, if the snapshot is no newer than the one
    already stored, or if a group in LOOKUP_GROUPS has no snapshot yet.
    """
    fetched_at = datetime.fromtimestamp(snapshot.fetched_at_unix, UTC)
    members = [
        {'crsid': crsid, 'name': member.name.strip() or crsid}
        for member in snapshot.members
        if (crsid := member.crsid.strip().lower())
    ]

    with db_session() as session:
        stored = session.get(LookupSnapshot, snapshot.id, with_for_update=True)
        if stored is not None and stored.fetched_at >= fetched_at:
            logger.info(
                'Ignoring snapshot of %s from %s: already have one from %s',
                snapshot.name,
                fetched_at,
                stored.fetched_at,
            )
            return None

        # Persist snapshot to database
        if stored is None:
            stored = LookupSnapshot(group_id=snapshot.id)
            session.add(stored)

        stored.name = snapshot.name
        stored.fetched_at = fetched_at
        stored.members = members
        session.flush()

        report = _reconcile(session, snapshot.name)

    if report is not None:
        logger.info('Lookup sync after %s: %s', snapshot.name, report.summary())

    return report


def _reconcile(session: Session, group: str) -> SyncReport | None:
    report = SyncReport()
    snapshots = {
        snapshot.name: snapshot
        for snapshot in session.query(LookupSnapshot).filter(
            LookupSnapshot.name.in_(LOOKUP_GROUPS)
        )
    }

    missing = set(LOOKUP_GROUPS) - snapshots.keys()
    if missing:
        # Disabling now would remove everyone in the missing groups. Not an
        # error, this just means a snapshot of the missing group hasn't arrived.
        logger.warning(
            'Refusing to sync: missing snapshot: %s', ', '.join(sorted(missing))
        )
        return None

    # crsid -> name, for everyone in any of the groups
    name_of_crsid = {
        member['crsid']: member['name']
        for name in LOOKUP_GROUPS
        for member in snapshots[name].members
    }
    users = {user.crsid: user for user in session.query(User).all()}

    report.created = name_of_crsid.keys() - users.keys()
    for crsid in report.created:
        session.add(
            User(
                crsid=crsid,
                name=name_of_crsid[crsid],
                role=Role.USER,
                user_enabled=True,
                is_manual=False,
            )
        )

    still_listed = name_of_crsid.keys() & users.keys()
    for crsid in still_listed:
        user = users[crsid]

        # User may be previously disabled
        if not user.user_enabled:
            report.reenabled.add(crsid)
            user.user_enabled = True

        # User's display name may have changed
        if user.name != name_of_crsid[crsid]:
            report.renamed.add(crsid)
            user.name = name_of_crsid[crsid]

    report.unchanged = len(still_listed - report.reenabled - report.renamed)

    # Anyone Lookup no longer lists now loses access (except manual users).
    report.disabled = {
        crsid
        for crsid in users.keys() - name_of_crsid.keys()
        if users[crsid].user_enabled and not users[crsid].is_manual
    }
    for crsid in report.disabled:
        users[crsid].user_enabled = False

    # If there is a change, log it in the audit table.
    if report.changed:
        session.add(
            Audit(
                message=f'[lookup sync] {report.summary()}',
                extra={
                    'group': group,
                    'created': sorted(report.created),
                    'reenabled': sorted(report.reenabled),
                    'disabled': sorted(report.disabled),
                    'renamed': sorted(report.renamed),
                },
            )
        )

    return report
