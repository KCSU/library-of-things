from flask import Blueprint, jsonify, request, render_template
from app.utils.decorators import login_required
from app.services.item_service import ItemService
from app.services.loan_service import LoanService
from app.services.settings_service import SettingsService

items_bp = Blueprint('items', __name__)

@items_bp.route('/items/<int:item_id>/request', methods=['POST'])
@login_required
def request_item(user, item_id):
    # Check if read-only mode is enabled
    if SettingsService.get_read_only_mode():
        return jsonify({
            'success': False,
            'error': 'Site is currently in read-only mode. Item requests are temporarily disabled.'
        }), 403
    
    try:
        success = LoanService.request_item(item_id, user)
        if success:
            return jsonify({
                'success': True,
                'message': 'Item request submitted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to submit request'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@items_bp.route('/ssr/cards')
@login_required
def ssr_cards(user):
    """Server-side rendered item cards, optionally filtered by category"""
    try:
        # Get category filter from query parameters
        category = request.args.get('category', None)
        items = ItemService.get_all_visible_items(category=category)
        read_only = SettingsService.get_read_only_mode()
        return render_template('cards.html', items=items, read_only=read_only)
    
    except Exception as e:
        return f"Error loading items: {str(e)}", 500