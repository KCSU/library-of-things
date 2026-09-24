"""User directory and role management routes."""

from typing import Any

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

from app.common.api import json_errors
from app.common.auth import role_required
from app.models import Role
from app.services.users import service as user_service

users_bp = Blueprint('users', __name__)


@users_bp.route('/admin/directory')
@role_required(Role.LIBRARIAN)
def directory(user: dict[str, Any]) -> ResponseReturnValue:
    return render_template(
        'admin/directory.html',
        users=user_service.get_all_users(),
        user=user,
        can_edit=user['is_admin'],
    )


@users_bp.route('/admin/roles')
@role_required(Role.ADMIN)
def roles(user: dict[str, Any]) -> ResponseReturnValue:
    return render_template(
        'admin/roles.html',
        user=user,
        staff=user_service.get_staff(),
        grantable=[Role.LIBRARIAN, Role.ADMIN],
        all_roles=list(Role),
    )


@users_bp.route('/admin/api/set_role', methods=['POST'])
@role_required(Role.ADMIN)
@json_errors
def api_set_role(user: dict[str, Any]) -> ResponseReturnValue:
    """Grant or revoke staff access. Admin only."""
    payload = request.get_json() or {}
    crsid = (payload.get('crsid') or '').strip().lower()
    if not crsid:
        return jsonify({'error': 'A CRSid is required'}), 400

    raw_role = payload.get('role')
    if raw_role is None:
        return jsonify({'error': 'A role is required'}), 400
    try:
        role = Role(int(raw_role))
    except TypeError, ValueError:
        return jsonify({'error': f'Unknown role: {raw_role!r}'}), 400

    changed = user_service.set_role(crsid, role, acting_crsid=user['crsid'])
    return jsonify({'success': True, **changed})


@users_bp.route('/admin/api/set_user_enabled', methods=['POST'])
@role_required(Role.ADMIN)
@json_errors
def api_set_user_enabled(user: dict[str, Any]) -> ResponseReturnValue:
    """Enable or disable a user's site access. Admin only."""
    payload = request.get_json() or {}
    crsid = (payload.get('crsid') or '').strip().lower()
    enabled = payload.get('enabled')
    if not crsid:
        return jsonify({'error': 'A CRSid is required'}), 400
    if not isinstance(enabled, bool):
        return jsonify({'error': 'enabled must be true or false'}), 400
    reason = (payload.get('reason') or '').strip()
    if not reason:
        return jsonify({'error': 'A reason is required'}), 400

    changed = user_service.set_user_enabled(
        crsid, enabled, acting_crsid=user['crsid'], reason=reason
    )
    return jsonify({'success': True, **changed})
