from app.models import Setting
from app.utils.database import db_session


class SettingsService:
    """Service class for managing application settings"""
    
    @staticmethod
    def get_announcement() -> dict:
        with db_session() as session:
            settings = session.query(Setting).filter(Setting.id == 1).first()
            if not settings:
                return {'text': '', 'enabled': False}
            return {
                'text': settings.announcement_text or '',
                'enabled': settings.announcement_enabled
            }
    
    @staticmethod
    def update_announcement(text: str, enabled: bool) -> bool:
        with db_session() as session:
            settings = session.query(Setting).filter(Setting.id == 1).first()
            if not settings:
                settings = Setting(id=1)
                session.add(settings)
            
            settings.announcement_text = text
            settings.announcement_enabled = enabled
            return True
    
    @staticmethod
    def get_read_only_mode() -> bool:
        with db_session() as session:
            settings = session.query(Setting).filter(Setting.id == 1).first()
            if not settings:
                return False
            return settings.read_only_mode
    
    @staticmethod
    def set_read_only_mode(enabled: bool) -> bool:
        with db_session() as session:
            settings = session.query(Setting).filter(Setting.id == 1).first()
            if not settings:
                settings = Setting(id=1)
                session.add(settings)
            
            settings.read_only_mode = enabled
            return True
