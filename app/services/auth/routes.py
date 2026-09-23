"""Authentication routes."""

import logging

from authlib.integrations.base_client import OAuthError
from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    session,
    url_for,
)
from flask.typing import ResponseReturnValue

from app.services.users import service as user_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

_NOT_AUTHORIZED = (
    'You are not authorized to access this website. If you are a current student from '
    "King's College, Cambridge, and believe you should have access, please contact the "
    "KCSU's Computer Officer."
)


@auth_bp.route('/login')
def login() -> ResponseReturnValue:
    if session.get('user') is None:
        return render_template('login.html')
    return redirect(url_for('items.index'))


@auth_bp.route('/logout')
def logout() -> ResponseReturnValue:
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/oauth2')
def oauth2() -> ResponseReturnValue:
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    if oauth is None:
        return redirect(url_for('auth.login'))
    return oauth.google.authorize_redirect(
        url_for('auth.authorized', _external=True)
    )


@auth_bp.route('/authorized')
def authorized() -> ResponseReturnValue:
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    if oauth is None:
        return redirect(url_for('auth.login'))

    try:
        token = oauth.google.authorize_access_token()
    except OAuthError as exc:
        logger.info('OAuth callback rejected: %s', exc)
        return redirect(url_for('auth.login'))

    if not token:
        return redirect(url_for('auth.login'))

    userinfo = token['userinfo']
    email = userinfo.get('email', '')

    # Email suffix matches exactly '@cam.ac.uk'.
    if (email.lower().endswith('@cam.ac.uk')
            and userinfo.get('email_verified') is True
            and userinfo.get('hd') == 'cam.ac.uk'):
        crsid = email.split('@')[0].lower()

        if user_service.check_user_access(crsid) is not None:
            session['user'] = userinfo
            session['user']['crsid'] = crsid
            return redirect(url_for('items.index'))

    session.clear()
    return render_template('login.html', error=_NOT_AUTHORIZED)
