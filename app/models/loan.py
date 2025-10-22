from sqlalchemy import Column, Integer, DateTime, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.models.base import BaseModel
from typing import Optional

class Loan(BaseModel):
    __tablename__ = 'loans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False, server_default=func.now())
    due_date = Column(DateTime, nullable=False)
    
    # Relationships
    item = relationship("Item", back_populates="loans")
    user = relationship("User", back_populates="loans")
    
    @property
    def is_overdue(self) -> bool:
        """Check if loan is overdue"""
        return datetime.now() > self.due_date
    
    def to_dict(self):
        """Convert to dictionary with additional loan info"""
        data = super().to_dict()
        data.update({
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': self.due_date.strftime('%Y-%m-%d %H:%M:%S'),
            'is_overdue': self.is_overdue,
            'item_title': self.item.title,
            'item_display_id': self.item.display_id,
            'item_image_url': self.item.image_url,
            'borrower_name': self.user.name,
            'borrower_crsid': self.user.crsid
        })
        return data

class Request(BaseModel):
    __tablename__ = 'requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    request_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    
    # Relationships
    item = relationship("Item", back_populates="requests")
    user = relationship("User", back_populates="requests")
    
    def to_dict(self):
        """Convert to dictionary with additional item request info"""
        data = super().to_dict()
        data.update({
            'request_time': self.request_time.strftime('%Y-%m-%d %H:%M:%S'),
            'item_title': self.item.title,
            'item_display_id': self.item.display_id,
            'item_image_url': self.item.image_url,
            'item_location': self.item.location,
            'borrower_name': self.user.name,
            'borrower_crsid': self.user.crsid,
            'borrower_pigeonhole': self.user.pigeonhole
        })
        return data