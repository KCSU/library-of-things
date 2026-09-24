import logging
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from authlib.integrations.flask_client import OAuth
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_from_directory,
    session,
)
from flask.typing import ResponseReturnValue
from flask_talisman import Talisman
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from app.common import database
from app.common.database import init_database
from app.common.icons import register_icon_helper
from app.config import (
    FLASK_SESSION_SECRET_KEY,
    GOOGLE_ACCESS_TOKEN_URL,
    GOOGLE_API_BASE_URL,
    GOOGLE_AUTHORIZE_URL,
    GOOGLE_OAUTH2_CLIENT_ID,
    GOOGLE_OAUTH2_CLIENT_SECRET,
    GOOGLE_SCOPE,
    GOOGLE_SERVER_METADATA_URL,
    MYSQL_DATABASE_URL,
)
from app.lookup_sync import register_cli

logger = logging.getLogger(__name__)

# Logs are timestamped in UTC.
logging.Formatter.converter = time.gmtime

_LOG_FORMAT = '%(asctime)s.%(msecs)03dZ %(levelname)s [%(name)s] %(message)s'
_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
_LOG_NAME = f'app-{datetime.now(UTC):%Y%m%d-%H%M%S}-{os.getpid()}.log'
_log_configured = False

ENVIRONMENTS = ('development', 'production')

_FAVICON_ROUTES = {
    '/favicon.ico': ('favicon.ico', 'image/vnd.microsoft.icon'),
    '/apple-touch-icon.png': ('apple-icon-180x180.png', 'image/png'),
    '/favicon-192x192.png': ('favicon-192x192.png', 'image/png'),
}

_ERROR_PAGES = {400: 'Bad request', 404: 'Not found'}


def _configure_logging(root_path: str) -> None:
    """Log to stderr and to logs/app-<start>-<pid>.log in the project root."""
    global _log_configured
    if _log_configured:
        return
    _log_configured = True

    # No-op if the host (e.g. gunicorn) has already configured handlers.
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT, datefmt=_LOG_DATEFMT)

    log_dir = Path(root_path).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    handler = logging.FileHandler(log_dir / _LOG_NAME, encoding='utf-8')
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATEFMT))
    logging.getLogger().addHandler(handler)
    logger.info('Logging to %s', log_dir / _LOG_NAME)


def create_app(config_name: str = 'production') -> Flask:
    app = Flask(__name__)
    _configure_logging(app.root_path)
    logger.info("Using '%s' configuration", config_name)

    if config_name not in ENVIRONMENTS:
        raise ValueError(f'Unknown configuration: {config_name!r}')

    Talisman(app, content_security_policy=None)

    app.config.from_object('app.config')
    app.config['SECRET_KEY'] = FLASK_SESSION_SECRET_KEY
    app.config['DEBUG'] = config_name == 'development'

    app.wsgi_app = ProxyFix(  # ty: ignore[invalid-assignment]
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

    try:
        init_database(MYSQL_DATABASE_URL)
        logger.info('Database initialised successfully')
    except Exception:
        logger.exception('Database initialisation failed; refusing to start')
        raise

    try:
        oauth = OAuth(app)
        oauth.register(
            name='google',
            client_id=GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=GOOGLE_OAUTH2_CLIENT_SECRET,
            api_base_url=GOOGLE_API_BASE_URL,
            access_token_url=GOOGLE_ACCESS_TOKEN_URL,
            authorize_url=GOOGLE_AUTHORIZE_URL,
            server_metadata_url=GOOGLE_SERVER_METADATA_URL,
            client_kwargs={'scope': GOOGLE_SCOPE},
        )
    except Exception:
        logger.exception('Google OAuth failed to initialize; refusing to start')

    register_icon_helper(app)
    register_blueprints(app)
    register_favicon_routes(app)
    register_healthcheck(app)
    register_context_processors(app)
    register_error_handlers(app)
    register_cli(app)

    return app


def register_healthcheck(app: Flask) -> None:
    @app.route('/healthz')
    def healthz() -> ResponseReturnValue:
        if database.engine is None:
            return jsonify(status='error', database='uninitialised'), 503
        try:
            with database.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
        except Exception as exc:
            logger.warning('Healthcheck database probe failed: %s', exc)
            return jsonify(status='error', database='unreachable'), 503
        return jsonify(status='ok', database='ok'), 200


def register_favicon_routes(app: Flask) -> None:
    favicon_dir = os.path.join(app.root_path, 'static', 'favicon')

    def send(filename: str, mimetype: str) -> ResponseReturnValue:
        return send_from_directory(favicon_dir, filename, mimetype=mimetype)

    for url, (filename, mimetype) in _FAVICON_ROUTES.items():
        app.add_url_rule(
            url,
            endpoint='favicon_' + filename.replace('.', '_'),
            view_func=partial(send, filename, mimetype),
        )

    manifest = partial(send, 'manifest.json', 'application/json')
    for url in ('/manifest.json', '/site.webmanifest'):
        app.add_url_rule(url, endpoint='manifest', view_func=manifest)


def register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_pending_requests_count() -> dict[str, int]:
        """Badge on the admin sidebar."""
        from app.services.loans import service as loan_service

        user = session.get('user')
        if not (user and user.get('is_librarian')):
            return {'pending_requests_count': 0}
        try:
            return {'pending_requests_count': loan_service.count_requests()}
        except Exception:
            logger.exception('Could not count pending requests')
            return {'pending_requests_count': 0}


def register_blueprints(app: Flask) -> None:
    from app.services.admin.routes import admin_bp
    from app.services.auth.routes import auth_bp
    from app.services.images.routes import images_bp
    from app.services.items.routes import items_bp
    from app.services.loans.routes import loans_bp
    from app.services.settings.routes import settings_bp
    from app.services.users.routes import users_bp

    for blueprint in (
        auth_bp,
        items_bp,
        loans_bp,
        images_bp,
        users_bp,
        settings_bp,
        admin_bp,
    ):
        app.register_blueprint(blueprint)


def register_error_handlers(app: Flask) -> None:
    def handler(code: int, message: str) -> Callable[[Exception], ResponseReturnValue]:
        def render(error: Exception) -> ResponseReturnValue:
            wants_json = request.path.startswith('/admin/api/') or (
                request.accept_mimetypes.accept_json
                and not request.accept_mimetypes.accept_html
            )
            if wants_json:
                return {'error': message}, code
            return render_template(f'{code}.html', user=session.get('user')), code

        return render

    for code, message in _ERROR_PAGES.items():
        app.register_error_handler(code, handler(code, message))
