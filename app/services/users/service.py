"""User and group operations."""

from typing import Any

from sqlalchemy.orm import joinedload

from app.common.database import db_session
from app.common.timing import log_slow
from app.models import Audit, Role, User


@log_slow
def get_all_users() -> list[dict[str, Any]]:
    """Every user with their group name, ordered by CRSid."""
    with db_session() as session:
        users = (session.query(User)
                 .options(joinedload(User.group))
                 .order_by(User.crsid)
                 .all())
        return [user.to_dict() | {
            'group': user.group.display_name if user.group else 'Unknown',
        } for user in users]


def check_user_access(crsid: str) -> Role | None:
    """The role a CRSid may act with, or None if it may not act at all."""
    with db_session() as session:
        user = session.query(User).filter(User.crsid == crsid).first()
        if user is None or not user.user_enabled:
            return None
        return Role(user.role)


def get_staff() -> list[dict[str, Any]]:
    """Everyone holding more than ordinary access, most senior first."""
    with db_session() as session:
        staff = (session.query(User)
                 .filter(User.role > Role.USER)
                 .order_by(User.role.desc(), User.crsid)
                 .all())
        return [user.to_dict() | {'role_label': Role(user.role).label}
                for user in staff]


def set_role(crsid: str, role: Role, acting_crsid: str) -> dict[str, Any]:
    """Grant or revoke staff access, and record who did it.
    Refuses to change the caller's own role.
    """
    if crsid == acting_crsid:
        raise ValueError('You cannot change your own role.')

    with db_session() as session:
        user = session.query(User).filter(User.crsid == crsid).first()
        if user is None:
            raise ValueError(f'No user with CRSid {crsid!r}.')

        previous = Role(user.role)
        if previous is role:
            raise ValueError(f'{crsid} is already {role.label.lower()}.')

        # Locking read before the write
        admins = [u.crsid for u in session.query(User)
                  .filter(User.role == Role.ADMIN).with_for_update()]
        if role < Role.ADMIN and admins == [crsid]:
            raise ValueError('That would leave the site with no administrator.')

        user.role = role
        session.flush()

        session.add(Audit(actor_crsid=acting_crsid, message=(
            f'Changed {crsid} from {previous.label.lower()} '
            f'to {role.label.lower()}')))

        return {
            'crsid': crsid,
            'name': user.name,
            'role': int(role),
            'role_label': role.label,
            'previous': previous.label,
        }


def set_user_enabled(crsid: str, enabled: bool, acting_crsid: str,
                     reason: str) -> dict[str, Any]:
    """Grant or revoke site access, and record who did it and why.

    Refuses to touch the caller's own account.
    """
    reason = reason.strip()
    if not reason:
        raise ValueError('A reason is required.')

    # TODO(khm39): this gets reset by lookup sync, account status probably
    # needs to be a >2 state enum (disabled_manually, disabled_by_lookup, etc)
    if crsid == acting_crsid:
        raise ValueError('You cannot change your own account.')

    with db_session() as session:
        user = session.query(User).filter(User.crsid == crsid).first()
        if user is None:
            raise ValueError(f'No user with CRSid {crsid!r}.')
        if bool(user.user_enabled) is enabled:
            state = 'enabled' if enabled else 'disabled'
            raise ValueError(f'{crsid} is already {state}.')

        # Locking read before the write
        admins = [u.crsid for u in session.query(User)
                  .filter(User.role == Role.ADMIN, User.user_enabled.is_(True))
                  .with_for_update()]
        if not enabled and admins == [crsid]:
            raise ValueError('That would leave the site with no administrator.')

        user.user_enabled = enabled
        session.flush()

        session.add(Audit(
            actor_crsid=acting_crsid,
            message=(f'{"Enabled" if enabled else "Disabled"} '
                     f'account for {crsid}: {reason}')))

        return {'crsid': crsid, 'name': user.name, 'enabled': enabled}
