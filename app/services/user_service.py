from typing import List, Optional
from cachetools.func import ttl_cache
from sqlalchemy.orm import selectinload
from app.utils.database import db_session
from app.models.user import User


class UserService:
    """Service class for user operations"""
    
    @staticmethod
    def user_exists(crsid: str) -> bool:
        """Check if user exists in database by CRSID"""
        with db_session() as session:
            return session.query(User).filter(User.crsid == crsid).first() is not None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[dict]:
        """Get user by database ID"""
        with db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            return user.to_dict() if user else None
    
    @staticmethod
    @ttl_cache(maxsize=1, ttl=3600)
    def get_all_users() -> List[dict]:
        """Get all users with eager loading to avoid N+1 queries"""
        with db_session() as session:
            users = (session.query(User)
                    .options(
                        selectinload(User.loans),
                        selectinload(User.requests)
                    )
                    .all())
            return [user.to_dict() for user in users]
    
    @staticmethod
    @ttl_cache(maxsize=1, ttl=300)
    def get_all_admins() -> List[dict]:
        """Get all admin users with eager loading"""
        with db_session() as session:
            admins = (session.query(User)
                     .filter(User.is_admin == True)
                     .options(
                         selectinload(User.loans),
                         selectinload(User.requests)
                     )
                     .all())
            return [user.to_dict() for user in admins]
    
    @staticmethod
    @ttl_cache(maxsize=500, ttl=300)
    def is_admin(crsid: str) -> bool:
        """Check if user is admin (cached for 5 minutes)"""
        with db_session() as session:
            user = session.query(User).filter(User.crsid == crsid).first()
            return user.is_admin if user else False
    
    @staticmethod
    def _clear_cache():
        """Clear all cached user data"""
        UserService.get_all_users.cache_clear()
        UserService.get_all_admins.cache_clear()
        UserService.is_admin.cache_clear()
