from app.utils.decorators import login_required
from flask import (Blueprint, current_app, redirect, render_template, request, session,
                   url_for)
from app.services.settings_service import SettingsService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@login_required
def index(user):
    # Get category from query parameters for sidebar highlighting
    category = request.args.get('category', None)
    announcement = SettingsService.get_announcement()
    return render_template('index.html', user=user, category=category, announcement=announcement)

@auth_bp.route('/login')
def login():
    if session.get('user') is None:
        return render_template('login.html')
    else:
        return redirect(url_for('auth.index'))
        
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# OAuth2 redirect
@auth_bp.route('/oauth2')
def oauth2():
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    if oauth:
        redirect_uri = url_for('auth.authorized', _external=True)
        return oauth.google.authorize_redirect(redirect_uri)
    return redirect(url_for('auth.login'))

# OAuth2 callback
@auth_bp.route('/authorized')
def authorized():
    from app.services.user_service import UserService
    
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    if oauth:
        token = oauth.google.authorize_access_token()
        if token:
            userinfo = token['userinfo']
            email = userinfo.get('email', '')
            
            if '@cam.ac.uk' in email:
                crsid = email.split('@')[0]
                
                # Check if user exists in database
                if UserService.user_exists(crsid):
                    session['user'] = userinfo
                    session['user']['crsid'] = crsid
                    return redirect(url_for('auth.index'))

            # User not authorized
            session.clear()
            return render_template('login.html', 
                error='You are not authorized to access this website. If you are from King\'s College, Cambridge, and believe you should have access, please contact the KCSU.'
            )
    
    return redirect(url_for('auth.login'))