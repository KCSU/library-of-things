from flask import Blueprint, render_template, jsonify, request
from app.utils.decorators import admin_required
from app.services.user_service import UserService
from app.services.item_service import ItemService
from app.services.loan_service import LoanService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/site-manual')
@admin_required
def site_manual(user):
    return render_template('admin/site_manual.html', user=user)

@admin_bp.route('/dashboard')
@admin_required
def dashboard(user):
    return render_template('admin/dashboard.html', user=user)

@admin_bp.route('/directory')
@admin_required
def directory(user):
    users = UserService.get_all_users()
    return render_template('admin/directory.html', users=users, user=user)

@admin_bp.route('/inventory')
@admin_required
def inventory(user):
    items = ItemService.get_all_items()
    categories = ItemService.get_all_categories()
    return render_template('admin/inventory.html', items=items, categories=categories, user=user)

@admin_bp.route('/requests')
@admin_required
def requests(user):
    requests = LoanService.get_all_requests()
    return render_template('admin/requests.html', requests=requests, user=user)

@admin_bp.route('/loans')
@admin_required
def loans(user):
    loans = LoanService.get_all_active_loans()
    return render_template('admin/loans.html', loans=loans, user=user)

@admin_bp.route('/list')
@admin_required
def admins(user):
    """List of admin users"""
    admins = UserService.get_all_admins()
    return render_template('admin/directory.html', users=admins, user=user)

@admin_bp.route('/settings')
@admin_required
def settings(user):
    return render_template('admin/settings.html', user=user)

# API endpoints for admin actions

@admin_bp.route('/api/edit_item', methods=['POST'])
@admin_required
def api_edit_item(user):
    """Edit an item"""
    payload = request.get_json()
    item_id = payload.get('id')
    data = payload.get('data')
    
    if not item_id or not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        success = ItemService.update_item(item_id, data)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/new_item', methods=['POST'])
@admin_required
def api_new_item(user):
    """Create a new item"""
    payload = request.get_json()
    data = payload.get('data')
    
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        item_id = ItemService.create_item(data)
        return jsonify({'success': True, 'id': item_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/delete_item', methods=['POST'])
@admin_required
def api_delete_item(user):
    """Delete an item"""
    payload = request.get_json()
    item_id = payload.get('id')
    
    if not item_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        success = ItemService.delete_item(item_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/end_loan', methods=['POST'])
@admin_required
def api_end_loan(user):
    """End a loan by removing it from the database"""
    payload = request.get_json()
    loan_id = payload.get('loan_id')
    
    if not loan_id:
        return jsonify({'error': 'Missing loan_id'}), 400
    
    try:
        success = LoanService.end_loan(loan_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Loan not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/accept_request', methods=['POST'])
@admin_required
def api_accept_request(user):
    """Accept an item request and create a loan (or handle permanent item transfer)"""
    payload = request.get_json()
    request_id = payload.get('id')
    if not request_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        result = LoanService.approve_request(request_id)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error', 'Unknown error')}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/approve_request', methods=['POST'])
@admin_required
def api_approve_request(user):
    """Approve an item request (loan or return)"""
    payload = request.get_json()
    request_id = payload.get('id')
    if not request_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        # Get the request to check if it's a loan or return
        from app.utils.database import db_session
        from app.models.loan import Request
        
        with db_session() as session:
            req = session.query(Request).filter(Request.id == request_id).first()
            if not req:
                return jsonify({'error': 'Request not found'}), 404
        
        success = LoanService.approve_request(request_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to process request'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/refuse_request', methods=['POST'])
@admin_required
def api_refuse_request(user):
    """Refuse an item request"""
    payload = request.get_json()
    request_id = payload.get('id')
    reason = payload.get('reason', 'Request denied')
    # TODO(lucas): do something with this request
    
    if not request_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        success = LoanService.delete_request(request_id)
        if success:
            # TODO: Send notification with reason
            return jsonify({'success': True})
        return jsonify({'error': 'Request not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    