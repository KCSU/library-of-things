import logging
import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify
from flask.typing import ResponseReturnValue
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.common.uuid import parse_id

logger = logging.getLogger(__name__)

type View = Callable[..., ResponseReturnValue]


def json_errors(f: View) -> View:
    """
    Turn exceptions escaping a JSON endpoint into a JSON body.
    ValueError raises a 400, other errors surface as a 500.
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> ResponseReturnValue:
        try:
            return f(*args, **kwargs)
        except HTTPException:
            raise
        except ValidationError as exc:
            return jsonify({'error': _describe(exc)}), 400
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        except Exception:
            logger.exception('Unhandled error in %s', getattr(f, '__name__', f))
            return jsonify({'error': 'Something went wrong'}), 500

    return wrapper


def _describe(exc: ValidationError) -> str:
    """One readable line per invalid field."""
    lines = []
    for error in exc.errors():
        field = '.'.join(str(part) for part in error['loc'])
        message = error['msg'].removeprefix('Value error, ')
        lines.append(f'{field}: {message}' if field else message)
    return '\n'.join(lines)


def json_uuid(payload: dict[str, Any], key: str) -> uuid.UUID:
    value = parse_id(payload.get(key))
    if value is None:
        raise ValueError(f'A valid {key} is required')
    return value
