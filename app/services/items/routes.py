"""Catalogue and inventory routes."""

import json
from typing import Any

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

from app.common.api import json_errors, json_uuid
from app.common.auth import role_required
from app.common.images import WebPImageBytes
from app.models import Role
from app.services.images import service as image_service
from app.services.items import service as item_service
from app.services.items.schemas import ItemInput
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


def _item_form() -> tuple[dict[str, Any], WebPImageBytes | None]:
    """Read the inventory form: a multipart request whose 'payload' field is
    the JSON body, with an optional new image in 'image'."""
    payload = json.loads(request.form.get('payload') or '{}')
    if not isinstance(payload, dict):
        raise ValueError('payload must be a JSON object')

    file = request.files.get('image')
    image = image_service.encode_upload(file) if file else None
    return payload, image


@items_bp.route('/admin/api/edit_item', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_edit_item(user: dict[str, Any]) -> ResponseReturnValue:
    payload, image = _item_form()
    item_id = json_uuid(payload, 'id')
    data = ItemInput.model_validate(payload.get('data'))

    if not item_service.update_item(item_id, data, user['crsid'], image):
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'success': True})


@items_bp.route('/admin/api/new_item', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_new_item(user: dict[str, Any]) -> ResponseReturnValue:
    payload, image = _item_form()
    data = ItemInput.model_validate(payload.get('data'))

    item_id = item_service.create_item(data, user['crsid'], image)
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
