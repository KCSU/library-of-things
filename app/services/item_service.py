from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.utils.database import db_session
from app.models.item import Item
from app.models.category import Category

class ItemService:
    """Service class for item operations"""
    
    # CAUTION: this query may contain items marked hidden by admins!
    @staticmethod
    def get_all_items() -> List[dict]:
        """Get all items"""
        with db_session() as session:
            items = (session.query(Item)
                    .options(
                        joinedload(Item.loans),
                        joinedload(Item.requests),
                        joinedload(Item.category)
                    )
                    .order_by(Item.display_id)
                    .all())
            return [item.to_dict() for item in items]
    
    # This is what normal users should see
    @staticmethod
    def get_all_visible_items(category: Optional[str] = None) -> List[dict]:
        """Get all visible items, optionally filtered by category"""
        with db_session() as session:
            query = session.query(Item).filter(Item.visible == True)
            
            # Eager load relationships for available_count calculation
            query = query.options(
                joinedload(Item.loans),
                joinedload(Item.requests),
                joinedload(Item.category)
            )
            
            # Apply category filter if provided (case-insensitive)
            if category:
                # case-insensitive
                query = query.join(Category).filter(Category.category.ilike(category))
            
            items = query.order_by(Item.display_id).all()
            items_dict = [item.to_dict() for item in items]

            # Available items should come first
            available_items = [item for item in items_dict if item['available_count'] > 0]
            unavailable_items = [item for item in items_dict if item['available_count'] <= 0]
            return available_items + unavailable_items
    
    @staticmethod
    def get_item_by_id(item_id: int) -> Optional[dict]:
        """Get item by ID"""
        with db_session() as session:
            item = session.query(Item).filter(Item.id == item_id).first()
            return item.to_dict() if item else None
    
    @staticmethod
    def create_item(data: dict) -> int:
        """Create a new item"""
        with db_session() as session:
            item = Item()
            item.update_from_dict(data)
            session.add(item)
            session.flush()  # Get the ID
            ItemService._clear_cache()
            return item.id
    
    @staticmethod
    def update_item(item_id: int, new_data: dict) -> bool:
        """Update an existing item"""
        with db_session() as session:
            item = session.query(Item).filter(Item.id == item_id).first()
            if not item:
                return False
            
            item.update_from_dict(new_data)
            ItemService._clear_cache()
            return True
    
    @staticmethod
    def delete_item(item_id: int) -> bool:
        """Delete an item"""
        with db_session() as session:
            deleted = session.query(Item).filter(Item.id == item_id).delete()
            if deleted:
                ItemService._clear_cache()
                return True
        return False
    
    # @staticmethod
    # def search_items(query: str) -> List[dict]:
    #     """Search items by title or description"""
    #     with db_session() as session:
    #         items = (session.query(Item)
    #                 .filter(
    #                     Item.visible == True,
    #                     (Item.title.ilike(f'%{query}%') | 
    #                      Item.description.ilike(f'%{query}%'))
    #                 )
    #                 .order_by(Item.display_id)
    #                 .all())
    #         return [item.to_dict() for item in items]
    
    @staticmethod
    def get_all_categories() -> List[dict]:
        """Get all categories"""
        with db_session() as session:
            categories = session.query(Category).order_by(Category.id).all()
            return [category.to_dict() for category in categories]
    
    @staticmethod
    def _clear_cache():
        pass
