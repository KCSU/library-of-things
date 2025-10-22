from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Category(BaseModel):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(255), nullable=False)
    
    # Relationships
    items = relationship("Item", back_populates="category")
    
    def to_dict(self):
        data = super().to_dict()
        return data