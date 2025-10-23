from sqlalchemy import Column, Integer, Text, Boolean
from app.models.base import BaseModel


class Setting(BaseModel):
    """Model for application settings - single row with typed columns"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True, default=1)
    
    # Announcement settings
    announcement_text = Column(Text, nullable=True)
    announcement_enabled = Column(Boolean, default=False, nullable=False)
    
    # Read-only mode
    read_only_mode = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'announcement_text': self.announcement_text,
            'announcement_enabled': self.announcement_enabled,
            'read_only_mode': self.read_only_mode,
        }
