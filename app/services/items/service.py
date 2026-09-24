"""Item and category operations."""

import uuid
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.common.database import db_session
from app.common.timing import log_slow
from app.models import Audit, Category, Item

# Columns whose edits are recorded in the audit entry's extra.
_AUDITED_FIELDS = (
    'display_id',
    'title',
    'description',
    'category_id',
    'loan_duration_days',
    'loan_end_date',
    'loan_end_recurs_annually',
    'visible',
    'count',
    'location',
    'comments',
)

_ITEM_RELATIONS = (
    joinedload(Item.loans),
    joinedload(Item.requests),
    joinedload(Item.category),
)


@log_slow
def get_all_admin_visible_items() -> list[dict[str, Any]]:
    """Every item, including ones admins have hidden from users."""
    with db_session() as session:
        items = (
            session.query(Item)
            .options(*_ITEM_RELATIONS)
            .order_by(Item.display_id)
            .all()
        )
        return [item.to_dict() for item in items]


@log_slow
def get_all_user_visible_items(
    category: str | None = None,
) -> list[dict[str, Any]]:
    """What a normal user may see, available items first."""
    with db_session() as session:
        query = (
            session.query(Item).filter(Item.visible.is_(True)).options(*_ITEM_RELATIONS)
        )

        if category:
            query = query.join(Category).filter(Category.category.ilike(category))

        items = [item.to_dict() for item in query.order_by(Item.display_id)]
        return sorted(items, key=lambda item: item['available_count'] <= 0)


def _shown(session: Session, field: str, value: Any) -> str:
    """A value as the audit log should read it."""
    if value is None or value == '':
        return 'none'
    if isinstance(value, bool):
        return 'yes' if value else 'no'
    if field == 'category_id':
        category = session.get(Category, uuid.UUID(str(value)))
        return category.category if category else str(value)
    return str(value)


def create_item(data: dict[str, Any], acting_crsid: str) -> uuid.UUID:
    with db_session() as session:
        item = Item()
        item.update_from_dict(data)
        session.add(item)
        session.flush()
        session.add(
            Audit(
                actor_crsid=acting_crsid,
                message=f'Added new item: {item.title}',
                extra={'item_id': str(item.id)},
            )
        )
        return item.id


def update_item(
    item_id: uuid.UUID, new_data: dict[str, Any], acting_crsid: str
) -> bool:
    with db_session() as session:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return False

        fields = [f for f in _AUDITED_FIELDS if f in new_data]
        before = {f: _shown(session, f, getattr(item, f)) for f in fields}
        item.update_from_dict(new_data)

        changes = {}
        for f in fields:
            after = _shown(session, f, getattr(item, f))
            # leave out unchanged fields
            if after != before[f]:
                changes[f] = {'before': before[f], 'after': after}

        if changes:
            session.add(
                Audit(
                    actor_crsid=acting_crsid,
                    message=f'Edited existing item: {item.title}',
                    extra={'item_id': str(item_id), 'changes': changes},
                )
            )
        return True


def delete_item(item_id: uuid.UUID, acting_crsid: str) -> bool:
    with db_session() as session:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return False
        title = item.title
        session.query(Item).filter(Item.id == item_id).delete()
        session.add(
            Audit(
                actor_crsid=acting_crsid,
                message=f'Deleted item: {title}',
                extra={'item_id': str(item_id)},
            )
        )
        return True


def get_all_categories() -> list[dict[str, Any]]:
    with db_session() as session:
        categories = session.query(Category).order_by(Category.id).all()
        return [category.to_dict() for category in categories]
