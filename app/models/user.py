from app.models.base import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class User(BaseModel):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    crsid = Column(String(15), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    pigeonhole = Column(Integer, nullable=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=0)
    
    # Relationships
    group = relationship("Group", back_populates="users")
    loans = relationship("Loan", back_populates="user")
    requests = relationship("Request", back_populates="user")
    
    @property
    def active_loans(self):
        """Get active loans for this user"""
        return [loan for loan in self.loans]
    
    @property
    def pending_requests(self):
        """Get pending requests for this user"""
        return [request for request in self.requests]
    
    def to_dict(self):
        """Convert to dictionary with additional info"""
        data = super().to_dict()
        data.update({
            'active_loan_count': len(self.active_loans),
            'pending_request_count': len(self.pending_requests)
        })
        return data