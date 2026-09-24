"""Item image routes."""

from typing import Any
from uuid import UUID

from flask import Blueprint, Response, jsonify, request
from flask.typing import ResponseReturnValue

from app.common.auth import role_required
from app.config import IMAGE_CONTENT_TYPE
from app.models import Role
from app.services.images import files as file_service
from app.services.images import service as image_service

images_bp = Blueprint('images', __name__)


@images_bp.route('/admin/api/items/<uuid:item_id>/image', methods=['POST'])
@role_required(Role.LIBRARIAN)
def api_upload_item_image(user: dict[str, Any], item_id: UUID) -> ResponseReturnValue:
    """Replace an item's image. Admin only."""
    try:
        content = file_service.read_upload(request.files.get('image'))
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    try:
        stored = image_service.store(item_id, content)
    except ValueError as exc:
        return jsonify({'error': f'Unsupported image: {exc}'}), 400

    if stored is None:
        return jsonify({'error': 'Item not found'}), 404

    return jsonify({'success': True, **stored})


@images_bp.route('/admin/api/items/<uuid:item_id>/image', methods=['DELETE'])
@role_required(Role.LIBRARIAN)
def api_delete_item_image(user: dict[str, Any], item_id: UUID) -> ResponseReturnValue:
    if not image_service.delete(item_id):
        return jsonify({'error': 'No image to remove'}), 404
    return jsonify({'success': True})


@images_bp.route('/items/<uuid:item_id>/image')
@role_required(Role.USER)
def item_image(user: dict[str, Any], item_id: UUID) -> ResponseReturnValue:
    """Serve an item's stored image."""
    stored = image_service.fetch(item_id)
    if stored is None:
        return '', 404
    content, checksum = stored

    etag = f'"{checksum}"'
    if request.headers.get('If-None-Match') == etag:
        return Response(status=304, headers={'ETag': etag})

    return Response(
        content,
        mimetype=IMAGE_CONTENT_TYPE,
        headers={
            'ETag': etag,
            'Cache-Control': 'public, max-age=31536000, immutable',
            'Content-Length': str(len(content)),
        },
    )
