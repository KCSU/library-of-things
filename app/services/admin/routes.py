"""Admin pages."""

from typing import Any

from flask import Blueprint, render_template, request
from flask.typing import ResponseReturnValue

from app.common.auth import role_required
from app.models import Role
from app.services.admin import service as admin_service

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/site-manual')
@role_required(Role.LIBRARIAN)
def site_manual(user: dict[str, Any]) -> ResponseReturnValue:
    return render_template('admin/site_manual.html', user=user)


@admin_bp.route('/admin/audit')
@role_required(Role.ADMIN)
def audit_log(user: dict[str, Any]) -> ResponseReturnValue:
    search = request.args.get('q', '').strip()
    total = admin_service.count_audit_entries(search)
    pages = max(1, -(-total // admin_service.PAGE_SIZE))  # ceiling division
    # Clamp to nearest real page
    page = min(max(request.args.get('page', 1, type=int), 1), pages)
    entries = admin_service.get_audit_log(page, search)
    start = (page - 1) * admin_service.PAGE_SIZE + 1 if entries else 0
    return render_template(
        'admin/audit.html',
        user=user,
        entries=entries,
        start=start,
        end=start + len(entries) - 1 if entries else 0,
        page=page,
        pages=pages,
        total=total,
        q=search,
    )
