from app.config import config
from app.utils.database import init_database
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(config_name='development'):
    app = Flask(__name__)
    Talisman(app, content_security_policy=None)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config_obj = config[config_name]()

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Initialize database
    try:
        init_database(config_obj.DATABASE_URL)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
    
    # Initialize OAuth
    oauth = OAuth(app)
    oauth.register(
        name='google',
        client_id=config_obj.GOOGLE_OAUTH2_CLIENT_ID,
        client_secret=config_obj.GOOGLE_OAUTH2_CLIENT_SECRET,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        access_token_url='https://oauth2.googleapis.com/token',
        authorize_url='https://accounts.google.com/o/oauth2/v2/auth?hd=cam.ac.uk',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'profile email openid'}
    )
    
    # Register blueprints
    register_blueprints(app)
    
    # Register favicon routes
    register_favicon_routes(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_favicon_routes(app):
    """Register routes for favicon files"""
    import os

    from flask import request, send_from_directory
    
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'favicon'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    
    @app.route('/site.webmanifest')
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'favicon'),
            'manifest.json',
            mimetype='application/json'
        )
    
    @app.route('/browserconfig.xml')
    def browserconfig():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'favicon'),
            'browserconfig.xml',
            mimetype='application/xml'
        )
    
    @app.route('/apple-touch-icon.png')
    @app.route('/android-chrome-192x192.png')
    @app.route('/android-chrome-512x512.png')
    @app.route('/favicon-16x16.png')
    @app.route('/favicon-32x32.png')
    def favicon_png():
        filename = os.path.basename(request.path)
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'favicon'),
            filename,
            mimetype='image/png'
        )

def register_context_processors(app):
    """Register template context processors"""
    @app.context_processor
    def inject_pending_requests_count():
        """Inject pending requests count for admin users"""
        from app.services.loan_service import LoanService
        from flask import session
        
        user = session.get('user')
        pending_requests_count = 0
        
        # Only calculate for admin users
        if user and user.get('is_admin'):
            try:
                requests = LoanService.get_all_requests()
                pending_requests_count = len(requests)
            except Exception:
                # If there's an error, just set to 0
                pending_requests_count = 0
        
        return {'pending_requests_count': pending_requests_count}

def register_blueprints(app):
    """Register Flask blueprints"""
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.user import user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template, request, session
    
    @app.errorhandler(400)
    def bad_request(error):
        # Check if the request wants JSON (API request)
        if request.path.startswith('/api/') or request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': 'Bad request'}, 400
        
        # Otherwise, render the 400 page
        user = session.get('user')
        return render_template('400.html', user=user), 400
    
    @app.errorhandler(404)
    def not_found(error):
        # Check if the request wants JSON (API request)
        if request.path.startswith('/api/') or request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return {'error': 'Not found'}, 404
        
        # Otherwise, render the 404 page
        user = session.get('user')
        return render_template('404.html', user=user), 404