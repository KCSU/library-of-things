"""Loan and request operations."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.common.database import db_session
from app.models import Audit, Item, Loan, Request, User


def _create_loan(
    session: Session,
    item_id: uuid.UUID,
    user_id: uuid.UUID,
    start_time: datetime | None = None,
    created_by_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Lend one copy of an item, and return the new loan's id."""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise ValueError(f'Item {item_id} not found')

    if not item.visible:
        raise ValueError(f'Item {item_id} is unavailable for borrowing')

    if item.count <= 0:
        raise ValueError(f'Item {item_id} is out of stock')

    outstanding = (
        session.query(Loan)
        .filter(Loan.item_id == item_id, Loan.returned_at.is_(None))
        .with_for_update()
        .all()
    )
    if len(outstanding) >= item.count:
        raise ValueError('No copies available to lend')

    # May be backdated when an admin records a loan that already happened.
    start_time = start_time or datetime.now()
    loan = Loan(
        item_id=item_id,
        user_id=user_id,
        start_time=start_time,
        due_date=item.compute_due_date(start_time),
        created_by_id=created_by_id,
    )
    session.add(loan)
    session.flush()

    return loan.id


def end_loan(
    loan_id: uuid.UUID, acting_crsid: str, returned_at: datetime | None = None
) -> bool:
    """Mark a loan as returned."""
    with db_session() as session:
        loan = session.query(Loan).filter(Loan.id == loan_id).first()
        if loan is None or loan.returned_at is not None:
            return False
        loan.returned_at = returned_at or datetime.now()
        session.add(
            Audit(
                actor_crsid=acting_crsid,
                message=(
                    f'Recorded return of {loan.item.title} from {loan.user.crsid}'
                ),
                extra={
                    'user_id': str(loan.user_id),
                    'user_crsid': loan.user.crsid,
                    'item_id': str(loan.item_id),
                },
            )
        )
        return True


def request_item(item_id: uuid.UUID, user_session: dict[str, Any]) -> bool:
    """Queue a request for an item on behalf of the signed-in user."""
    crsid = user_session.get('crsid')
    with db_session() as session:
        user = session.query(User).filter(User.crsid == crsid).first()
        if not user:
            raise ValueError(f'User {crsid} not found')

        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f'Item {item_id} not found')

        if not item.visible:
            raise ValueError('Item is unavailable for borrowing')

        if item.available_count <= 0:
            raise ValueError('No items available')

        # Limit one pending request per user per item.
        # TODO(khm39): allow (in both frontend and backend) to select borrow count
        existing = (
            session.query(Request)
            .filter(Request.item_id == item_id, Request.user_id == user.id)
            .first()
        )
        if existing:
            raise ValueError('You already have a pending request for this item')

        session.add(
            Request(item_id=item_id, user_id=user.id, request_time=datetime.now())
        )

    return True


def refuse_request(request_id: uuid.UUID, reason: str, acting_crsid: str) -> bool:
    """Drop a request, recording who refused it and the reason for it."""
    with db_session() as session:
        req = session.query(Request).filter(Request.id == request_id).first()
        if req is None:
            return False

        borrower, title = req.user.crsid, req.item.title
        extra = {
            'user_id': str(req.user_id),
            'user_crsid': borrower,
            'item_id': str(req.item_id),
            'reason': reason,
        }
        session.delete(req)
        session.add(
            Audit(
                actor_crsid=acting_crsid,
                message=f'Refused request from {borrower} for {title}',
                extra=extra,
            )
        )
        return True


def count_requests() -> int:
    """Pending requests, for the admin sidebar badge."""
    with db_session() as session:
        return session.query(Request).count()


def get_all_requests() -> list[dict[str, Any]]:
    """Every pending request, oldest first."""
    with db_session() as session:
        requests = (
            session.query(Request)
            .join(Item)
            .join(User, Request.user_id == User.id)
            .options(selectinload(Request.item), selectinload(Request.user))
            .order_by(Request.request_time.asc())
            .all()
        )
        return [req.to_dict() for req in requests]


def get_all_active_loans() -> list[dict[str, Any]]:
    """Every active loan, soonest due first."""
    with db_session() as session:
        loans = (
            session.query(Loan)
            .join(Item)
            .join(User, Loan.user_id == User.id)
            .filter(Loan.returned_at.is_(None))
            .options(selectinload(Loan.item), selectinload(Loan.user))
            .order_by(Loan.due_date.asc())
            .all()
        )
        return [loan.to_dict() for loan in loans]


def get_user_pending_requests(crsid: str | None) -> list[dict[str, Any]]:
    with db_session() as session:
        user = session.query(User).filter(User.crsid == crsid).first()
        if not user:
            return []

        requests = (
            session.query(Request)
            .join(Item)
            .filter(Request.user_id == user.id)
            .order_by(Request.request_time.desc())
            .all()
        )
        return [req.to_dict() for req in requests]


def get_user_active_loans(crsid: str | None) -> list[dict[str, Any]]:
    with db_session() as session:
        user = session.query(User).filter(User.crsid == crsid).first()
        if not user:
            return []

        loans = (
            session.query(Loan)
            .join(Item)
            .filter(Loan.user_id == user.id, Loan.returned_at.is_(None))
            .options(selectinload(Loan.item), selectinload(Loan.user))
            .order_by(Loan.due_date.asc())
            .all()
        )
        return [loan.to_dict() for loan in loans]


def approve_request(request_id: uuid.UUID, acting_crsid: str) -> dict[str, Any]:
    """Turn a pending request into a loan.

    'permanent' says whether the item is given away rather than lent; either
    way a loan row is written, without a due date in the permanent case.
    """
    with db_session() as session:
        req = session.query(Request).filter(Request.id == request_id).first()
        if not req:
            return {'success': False, 'error': 'Request not found'}

        item = (
            session.query(Item).filter(Item.id == req.item_id).with_for_update().first()
        )
        if not item:
            return {'success': False, 'error': 'Item no longer exists'}

        try:
            loan_id = _create_loan(session, req.item_id, req.user_id)
        except ValueError as exc:
            return {'success': False, 'error': str(exc)}

        session.add(
            Audit(
                actor_crsid=acting_crsid,
                message=(f'Approved request from {req.user.crsid} for {item.title}'),
                extra={
                    'user_id': str(req.user_id),
                    'user_crsid': req.user.crsid,
                    'item_id': str(req.item_id),
                },
            )
        )
        session.delete(req)

        return {
            'success': True,
            'loan_id': loan_id,
            'permanent': item.is_permanent,
        }


def lend_to_user(
    item_id: uuid.UUID, crsid: str, admin_crsid: str, start_time: datetime | None = None
) -> dict[str, Any]:
    """Record a loan an admin has handed over in person."""
    if start_time and start_time > datetime.now():
        return {'success': False, 'error': 'Start date cannot be in the future'}

    with db_session() as session:
        borrower = session.query(User).filter(User.crsid == crsid).first()
        if borrower is None:
            return {'success': False, 'error': f'No user with CRSid {crsid}'}
        if not borrower.user_enabled:
            return {'success': False, 'error': f'{crsid} is no longer an active member'}

        admin = session.query(User).filter(User.crsid == admin_crsid).first()

        item = session.query(Item).filter(Item.id == item_id).with_for_update().first()
        if item is None:
            return {'success': False, 'error': 'Item not found'}

        try:
            loan_id = _create_loan(
                session,
                item_id,
                borrower.id,
                start_time=start_time,
                created_by_id=admin.id if admin else None,
            )
        except ValueError as exc:
            return {'success': False, 'error': str(exc)}

        session.add(
            Audit(
                actor_crsid=admin_crsid,
                message=(
                    f'Manually {"gave" if item.is_permanent else "lent"} '
                    f'{item.title} to {crsid} on their behalf'
                ),
                extra={
                    'user_id': str(borrower.id),
                    'user_crsid': crsid,
                    'item_id': str(item_id),
                },
            )
        )

        return {
            'success': True,
            'loan_id': str(loan_id),
            'permanent': item.is_permanent,
            'borrower': borrower.name,
        }
