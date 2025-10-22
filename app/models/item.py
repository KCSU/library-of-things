"""Item model"""

import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, String, Integer, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Item(BaseModel):
    __tablename__ = 'items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    display_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(2047), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    loan_policy = Column(Enum(
        'seven_days', 'thirty_days', 'academic_year_end', 'permanent', 
        name='loan_policy_enum'), nullable=False)
    visible = Column(Boolean, nullable=False, default=1)
    count = Column(Integer, nullable=False, default=1)
    location = Column(String(255), nullable=True)
    image_url = Column(String(2047), nullable=False)
    comments = Column(Text, nullable=True)
    
    # Relationships
    category = relationship("Category", back_populates="items")
    loans = relationship("Loan", back_populates="item")
    requests = relationship("Request", back_populates="item")
    
    @property
    def available_count(self) -> int:
        """
        Calculate the number of available items. (not currently on loan or requested)
        """
        # Count active loans
        active_loans = len(self.loans)
        
        # Count pending loan requests
        pending_requests = len(self.requests)
        
        return max(0, self.count - active_loans - pending_requests)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'category': self.category.category if self.category else 'Unknown',
            'loan_policy': self.loan_policy,
            'available_count': self.available_count,
            'location': self.location,
            'comments': self.comments
        })
        return data
    
    def compute_due_date(self, start_time: datetime.datetime) -> Optional[datetime.datetime]:
        """Calculate due date based on item's loan policy"""
        if not self.loan_policy:
            raise Exception("Loan policy is not defined for this item!")
        
        policy = self.loan_policy
        if policy == 'seven_days':
            return start_time + datetime.timedelta(days=7)
        elif policy == 'thirty_days':
            return start_time + datetime.timedelta(days=30)
        elif policy == 'academic_year_end':
            year = start_time.year
            if start_time.month > 6:
                year += 1
            return datetime.datetime(year, 6, 30)
        elif policy == 'permanent':
            return None  # No due date
        else:
            raise Exception("Unknown loan policy!")
