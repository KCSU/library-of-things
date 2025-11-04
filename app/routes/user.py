from flask import Blueprint, render_template
from app.utils.decorators import login_required
from app.services.loan_service import LoanService

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/requests')
@login_required
def requests(user):
    """Display user's pending item requests"""
    crsid = user.get('crsid')
    pending_requests = LoanService.get_user_pending_requests(crsid)
    return render_template('user/requests.html', 
                           user=user, 
                           requests=pending_requests)

@user_bp.route('/borrowed')
@login_required
def borrowed(user):
    """Display user's currently borrowed items"""
    crsid = user.get('crsid')
    borrowed_items = LoanService.get_user_active_loans(crsid)
    return render_template('user/borrowed.html',
                           user=user, 
                           loans=borrowed_items)