"""Item and category operations."""

import uuid
from typing import Any

from sqlalchemy.orm import joinedload

from app.common.database import db_session
from app.common.timing import log_slow
from app.models import Category, Item

_ITEM_RELATIONS = (
    joinedload(Item.loans),
    joinedload(Item.requests),
    joinedload(Item.category),
)


@log_slow
def get_all_admin_visible_items() -> list[dict[str, Any]]:
    """Every item, including ones admins have hidden from users."""
    with db_session() as session:
        items = (session.query(Item)
                 .options(*_ITEM_RELATIONS)
                 .order_by(Item.display_id)
                 .all())
        return [item.to_dict() for item in items]


@log_slow
def get_all_user_visible_items(
    category: str | None = None,
) -> list[dict[str, Any]]:
    """What a normal user may see, available items first."""
    with db_session() as session:
        query = (session.query(Item)
                 .filter(Item.visible.is_(True))
                 .options(*_ITEM_RELATIONS))

        if category:
            query = query.join(Category).filter(
                Category.category.ilike(category)
            )

        items = [item.to_dict() for item in query.order_by(Item.display_id)]
        return sorted(items, key=lambda item: item['available_count'] <= 0)


def create_item(data: dict[str, Any]) -> uuid.UUID:
    with db_session() as session:
        item = Item()
        item.update_from_dict(data)
        session.add(item)
        session.flush()
        return item.id


def update_item(item_id: uuid.UUID, new_data: dict[str, Any]) -> bool:
    with db_session() as session:
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            return False

        item.update_from_dict(new_data)
        return True


def delete_item(item_id: uuid.UUID) -> bool:
    with db_session() as session:
        return bool(session.query(Item).filter(Item.id == item_id).delete())


def get_all_categories() -> list[dict[str, Any]]:
    with db_session() as session:
        categories = session.query(Category).order_by(Category.id).all()
        return [category.to_dict() for category in categories]
