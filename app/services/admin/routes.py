"""Admin pages."""

from typing import Any

from flask import Blueprint, render_template
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
    return render_template('admin/audit.html', user=user,
                           entries=admin_service.get_audit_log(),
                           limit=admin_service.LOG_LIMIT)
