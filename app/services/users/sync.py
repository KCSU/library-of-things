"""Reconcile the user table against the Lookup directory."""

import logging
from dataclasses import dataclass, field

from app.common.database import db_session
from app.common.lookup import LookupClient, LookupPerson
from app.common.timing import log_duration
from app.models import Audit, Group, Role, User

logger = logging.getLogger(__name__)


@dataclass
class SyncReport:
    # All strings are CRSids.
    created: list[str] = field(default_factory=list)
    reenabled: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)
    moved: list[str] = field(default_factory=list)
    renamed: list[str] = field(default_factory=list)
    unchanged: int = 0
    groups_synced: list[str] = field(default_factory=list)
    groups_skipped: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(
            self.created
            or self.reenabled
            or self.disabled
            or self.moved
            or self.renamed
        )

    def summary(self) -> str:
        return (
            f'created={len(self.created)} reenabled={len(self.reenabled)} '
            f'disabled={len(self.disabled)} moved={len(self.moved)} '
            f'renamed={len(self.renamed)} unchanged={self.unchanged}'
        )


@log_duration
def sync_users(client: LookupClient, dry_run: bool = False) -> SyncReport:
    """Reconcile every Lookup-backed group. Returns what changed."""
    report = SyncReport()

    with db_session() as session:
        groups = session.query(Group).all()

        # Phase 1: read and parse data from Lookup.
        memberships: dict[str, list[LookupPerson]] = {}
        for group in groups:
            if not group.lookup_type:
                report.groups_skipped.append(group.name)
                continue
            # One app group can draw on several Lookup objects; de-duplicate
            # by crsid, since a student can appear in more than one.
            people: dict[str, LookupPerson] = {}
            for source in (group.lookup_name or group.name).split(','):
                source = source.strip()
                if not source:
                    continue
                for person in client.members(source, group.lookup_type):
                    people.setdefault(person.crsid, person)
            memberships[group.name] = list(people.values())
            report.groups_synced.append(group.name)

        if not memberships:
            logger.warning('No Lookup-backed groups configured; nothing to do')
            return report

        # crsid -> (group, person), last group wins if somebody is in both
        directory: dict[str, tuple[Group, LookupPerson]] = {}
        for group in groups:
            for lookup_person in memberships.get(group.name, []):
                directory[lookup_person.crsid] = (group, lookup_person)

        existing = {user.crsid: user for user in session.query(User).all()}

        # Phase 2: reconcile against database.
        for crsid, (group, person) in directory.items():
            user = existing.get(crsid)
            if user is None:
                report.created.append(crsid)
                if not dry_run:
                    session.add(
                        User(
                            crsid=crsid,
                            name=person.name,
                            group_id=group.id,
                            role=Role.USER,
                            user_enabled=True,
                            is_manual=False,
                        )
                    )
                continue

            if not user.user_enabled:
                report.reenabled.append(crsid)
                if not dry_run:
                    user.user_enabled = True
            if user.group_id != group.id:
                report.moved.append(crsid)
                if not dry_run:
                    user.group_id = group.id
            if person.name and user.name != person.name:
                report.renamed.append(crsid)
                if not dry_run:
                    user.name = person.name
            if (
                crsid not in report.reenabled
                and crsid not in report.moved
                and crsid not in report.renamed
            ):
                report.unchanged += 1

        # Anyone Lookup no longer lists should lose access.
        synced_group_ids = {g.id for g in groups if g.name in memberships}
        for crsid, user in existing.items():
            if crsid in directory or user.is_manual:
                continue
            if user.group_id not in synced_group_ids:
                continue  # belongs to a group we didn't sync; leave alone
            if user.user_enabled:
                report.disabled.append(crsid)
                if not dry_run:
                    user.user_enabled = False

        # Leave an audit trail if nonempty report.
        if report.changed and not dry_run:
            session.add(Audit(message=f'[lookup sync] {report.summary()}'))

    logger.info(
        'Lookup sync %s: %s', '(dry run)' if dry_run else 'applied', report.summary()
    )
    return report
