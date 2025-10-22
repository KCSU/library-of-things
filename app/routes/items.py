from flask import Blueprint, jsonify, request, render_template
from app.utils.decorators import login_required
from app.services.item_service import ItemService
from app.services.loan_service import LoanService

items_bp = Blueprint('items', __name__)

@items_bp.route('/items/<int:item_id>/request', methods=['POST'])
@login_required
def request_item(user, item_id):
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
        
        # Fetch items with optional category filter
        items = ItemService.get_all_visible_items(category=category)
        
        return render_template('cards.html', items=items)
    except Exception as e:
        return f"Error loading items: {str(e)}", 500