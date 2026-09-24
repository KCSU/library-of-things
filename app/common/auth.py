from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify, redirect, request, session, url_for
from flask.typing import ResponseReturnValue

from app.models import Role
from app.services.users import service as user_service

type View = Callable[..., ResponseReturnValue]

_TOO_LOW = {
    Role.LIBRARIAN: 'You do not have the privileges to perform this action.',
    Role.ADMIN: 'Administrator access required.',
}


def _deny(message: str, status: int, fallback: str) -> ResponseReturnValue:
    if request.is_json:
        return jsonify({'error': message}), status
    return redirect(url_for(fallback))


def role_required(minimum: Role) -> Callable[[View], View]:
    """Refuse anyone acting with less than `minimum`.

    The role is re-read on every request, rather than trusted from the
    session cookie.
    """

    def decorator(f: View) -> View:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> ResponseReturnValue:
            user = session.get('user')
            if user is None:
                return _deny('Authentication required', 401, 'auth.login')

            crsid = user['email'].split('@')[0].lower()
            role = user_service.check_user_access(crsid)
            if role is None:
                session.clear()
                return _deny('Account disabled', 403, 'auth.login')
            if role < minimum:
                return _deny(_TOO_LOW[minimum], 403, 'items.index')

            user['crsid'] = crsid
            user['role'] = int(role)
            user['is_librarian'] = role >= Role.LIBRARIAN
            user['is_admin'] = role >= Role.ADMIN
            return f(user, *args, **kwargs)

        return wrapper

    return decorator
