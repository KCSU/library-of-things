from datetime import datetime
from typing import List, Optional, Dict

from app.models.item import Item
from app.models.loan import Loan, Request
from app.models.user import User
from app.services.item_service import ItemService
from app.utils.database import db_session


class LoanService:
    """Service class for loan and request operations"""
    
    @staticmethod
    def _create_loan_internal(session, item_id: int, user_id: int) -> Optional[int]:
        """
        Create a loan or handle permanent item transfer.
        For permanent items: decrements count, returns None.
        For temporary items: creates loan record, returns loan ID.
        """
        item = session.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise Exception(f"Item '{item.name}' not found")
        
        # Prevent hidden items from being borrowed
        if not item.visible:
            raise Exception(f"Item '{item.name}' is unavailable for borrowing")
        
        # Handle permanent loan policy - decrement count instead of creating loan
        if item.loan_policy == 'permanent':
            if item.count <= 0:
                raise Exception(f"Item '{item.name}' is out of stock")
            item.count -= 1
            session.flush()
            return None  # No loan record created for permanent items
        
        # Create loan for temporary items
        start_time = datetime.now()
        loan = Loan(
            item_id=item_id,
            user_id=user_id,
            start_time=start_time,
            due_date=item.compute_due_date(start_time)
        )
        session.add(loan)
        session.flush()
        
        return loan.id
    
    @staticmethod
    def end_loan(loan_id: int) -> bool:
        """End a loan by removing it from the database"""
        with db_session() as session:
            deleted = session.query(Loan).filter(Loan.id == loan_id).delete()
            if deleted:
                ItemService._clear_cache()
                return True
        return False
    
    @staticmethod
    def request_item(item_id: int, user_session: dict) -> bool:
        """Create a request for an item"""
        crsid = user_session.get('crsid')

        with db_session() as session:
            user = session.query(User).filter(User.crsid == crsid).first()
            if not user:
                raise Exception(f"User {crsid} not found")
            
            item = session.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise Exception(f"Item {item_id} not found")
            
            if item.available_count <= 0:
                raise Exception("No items available")
            
            request = Request(
                item_id=item_id,
                user_id=user.id,
                request_time=datetime.now()
            )
            session.add(request)
            ItemService._clear_cache()
                
        return True
    
    @staticmethod
    def delete_request(request_id: int) -> bool:
        """Delete a request (used for both refusing and canceling requests)"""
        with db_session() as session:
            deleted = session.query(Request).filter(Request.id == request_id).delete()
            if deleted:
                ItemService._clear_cache()
                return True
        return False
    
    @staticmethod
    def get_all_requests() -> List[dict]:
        """Get all pending requests ordered by request time (oldest first)"""
        with db_session() as session:
            requests = (session.query(Request)
                       .join(Item)
                       .join(User)
                       .order_by(Request.request_time.asc())
                       .all())
            return [req.to_dict() for req in requests]
    
    @staticmethod
    def get_all_active_loans() -> List[dict]:
        """Get all loans ordered by due date (soonest first)"""
        with db_session() as session:
            loans = (session.query(Loan)
                    .join(Item)
                    .join(User)
                    .order_by(Loan.due_date.asc())
                    .all())
            return [loan.to_dict() for loan in loans]
    
    @staticmethod
    def approve_request(request_id: int) -> Dict:
        """
        Approve a request and create a loan (or handle permanent item transfer).
        Returns dict with 'success', 'loan_id' (or None for permanent items), and 'permanent' flag.
        """
        with db_session() as session:
            req = session.query(Request).filter(Request.id == request_id).first()
            if not req:
                return {'success': False, 'error': 'Request not found'}
            
            # Create loan or handle permanent transfer
            loan_id = LoanService._create_loan_internal(session, req.item_id, req.user_id)
            session.delete(req)
            ItemService._clear_cache()
            
            return {
                'success': True,
                'loan_id': loan_id,
                'permanent': loan_id is None
            }
