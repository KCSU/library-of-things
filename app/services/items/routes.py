"""Catalogue and inventory routes."""

from typing import Any

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

from app.common.api import json_errors, json_uuid
from app.common.auth import role_required
from app.models import Role
from app.services.items import service as item_service
from app.services.settings import service as settings_service

items_bp = Blueprint('items', __name__)


@items_bp.route('/admin/inventory')
@role_required(Role.LIBRARIAN)
def inventory(user: dict[str, Any]) -> ResponseReturnValue:
    return render_template(
        'admin/inventory.html',
        items=item_service.get_all_admin_visible_items(),
        categories=item_service.get_all_categories(),
        user=user,
    )


@items_bp.route('/admin/api/edit_item', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_edit_item(user: dict[str, Any]) -> ResponseReturnValue:
    payload = request.get_json() or {}
    item_id = json_uuid(payload, 'id')
    data = payload.get('data')

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400

    if not item_service.update_item(item_id, data, user['crsid']):
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'success': True})


@items_bp.route('/admin/api/new_item', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_new_item(user: dict[str, Any]) -> ResponseReturnValue:
    data = request.get_json().get('data')

    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400

    item_id = item_service.create_item(data, user['crsid'])
    return jsonify({'success': True, 'id': item_id})


@items_bp.route('/admin/api/delete_item', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_delete_item(user: dict[str, Any]) -> ResponseReturnValue:
    item_id = json_uuid(request.get_json() or {}, 'id')

    if not item_service.delete_item(item_id, user['crsid']):
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'success': True})


@items_bp.route('/')
@role_required(Role.USER)
def index(user: dict[str, Any]) -> ResponseReturnValue:
    category = request.args.get('category')
    return render_template(
        'index.html',
        user=user,
        category=category,
        announcement=settings_service.get_announcement(),
        items=item_service.get_all_user_visible_items(category=category),
        read_only=settings_service.get_read_only_mode(),
    )
