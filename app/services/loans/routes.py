"""Borrowing routes: requests, approvals and loans."""

from datetime import datetime
from typing import Any
from uuid import UUID

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

from app.common.api import json_errors, json_uuid
from app.common.auth import role_required
from app.models import Role
from app.services.items import service as item_service
from app.services.loans import service as loan_service
from app.services.settings import service as settings_service

loans_bp = Blueprint('loans', __name__)


@loans_bp.route('/admin/requests')
@role_required(Role.LIBRARIAN)
def admin_requests(user: dict[str, Any]) -> ResponseReturnValue:
    return render_template('admin/requests.html',
                           requests=loan_service.get_all_requests(),
                           items=item_service.get_all_admin_visible_items(), user=user)


@loans_bp.route('/admin/loans')
@role_required(Role.LIBRARIAN)
def admin_loans(user: dict[str, Any]) -> ResponseReturnValue:
    return render_template('admin/loans.html',
                           loans=loan_service.get_all_active_loans(), user=user)


@loans_bp.route('/admin/api/end_loan', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_end_loan(user: dict[str, Any]) -> ResponseReturnValue:
    loan_id = json_uuid(request.get_json() or {}, 'loan_id')

    if not loan_service.end_loan(loan_id, acting_crsid=user['crsid']):
        return jsonify({'error': 'Loan not found'}), 404
    return jsonify({'success': True})


@loans_bp.route('/admin/api/accept_request', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_accept_request(user: dict[str, Any]) -> ResponseReturnValue:
    """Approve a request, creating a loan or handing a permanent item over."""
    request_id = json_uuid(request.get_json() or {}, 'id')

    result = loan_service.approve_request(request_id, acting_crsid=user['crsid'])
    if not result['success']:
        return jsonify({'error': result.get('error', 'Unknown error')}), 409
    return jsonify(result)


@loans_bp.route('/admin/api/refuse_request', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_refuse_request(user: dict[str, Any]) -> ResponseReturnValue:
    payload = request.get_json() or {}
    request_id = json_uuid(payload, 'id')
    reason = (payload.get('reason') or '').strip()

    if not reason:
        return jsonify({'error': 'A reason is required'}), 400

    if not loan_service.refuse_request(request_id, reason,
                                       acting_crsid=user['crsid']):
        return jsonify({'error': 'Request not found'}), 404
    return jsonify({'success': True})


@loans_bp.route('/items/<uuid:item_id>/request', methods=['POST'])
@role_required(Role.USER)
@json_errors
def request_item(user: dict[str, Any], item_id: UUID) -> ResponseReturnValue:
    if settings_service.get_read_only_mode():
        return jsonify({
            'success': False,
            'error': 'Site is currently in read-only mode. '
                     'Item requests are temporarily disabled.',
        }), 403

    loan_service.request_item(item_id, user)
    return jsonify({'success': True,
                    'message': 'Item request submitted successfully'})


@loans_bp.route('/user/requests')
@role_required(Role.USER)
def my_requests(user: dict[str, Any]) -> ResponseReturnValue:
    requests = loan_service.get_user_pending_requests(user.get('crsid'))
    return render_template('user/requests.html', user=user, requests=requests)


@loans_bp.route('/user/borrowed')
@role_required(Role.USER)
def borrowed(user: dict[str, Any]) -> ResponseReturnValue:
    loans = loan_service.get_user_active_loans(user.get('crsid'))
    return render_template('user/borrowed.html', user=user, loans=loans)


@loans_bp.route('/admin/api/lend', methods=['POST'])
@role_required(Role.LIBRARIAN)
@json_errors
def api_lend(user: dict[str, Any]) -> ResponseReturnValue:
    """Record a loan done in person, skipping the request approval cycle."""
    payload = request.get_json() or {}
    item_id = json_uuid(payload, 'item_id')
    crsid = (payload.get('crsid') or '').strip().lower()
    if not crsid:
        return jsonify({'error': 'A CRSid is required'}), 400

    start_time = None
    raw_start = payload.get('start_time')
    if raw_start:
        try:
            start_time = datetime.fromisoformat(raw_start)
        except ValueError:
            return jsonify({'error': 'Start date is not a valid date'}), 400

    result = loan_service.lend_to_user(
        item_id, crsid, admin_crsid=user['crsid'], start_time=start_time)

    if not result['success']:
        return jsonify({'error': result['error']}), 409
    return jsonify(result)
