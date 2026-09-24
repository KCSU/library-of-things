"""Site settings routes."""

from typing import Any

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

from app.common.api import json_errors
from app.common.auth import role_required
from app.models import Role
from app.services.settings import service as settings_service

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/admin/settings')
@role_required(Role.LIBRARIAN)
def settings(user: dict[str, Any]) -> ResponseReturnValue:
    return render_template(
        'admin/settings.html',
        user=user,
        announcement=settings_service.get_announcement(),
        read_only=settings_service.get_read_only_mode(),
        can_edit=user['is_admin'],
    )


@settings_bp.route('/admin/api/update_settings', methods=['POST'])
@role_required(Role.ADMIN)
@json_errors
def api_update_settings(user: dict[str, Any]) -> ResponseReturnValue:
    payload = request.get_json()

    announcement = payload.get('announcement', {})
    settings_service.update_settings(
        announcement.get('text', ''),
        announcement.get('enabled', False),
        payload.get('read_only', False),
        user['crsid'],
    )

    return jsonify({'success': True})
