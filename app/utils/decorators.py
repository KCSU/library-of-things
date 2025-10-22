"""Authentication and authorization decorators"""

from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from app.services.user_service import UserService

def login_required(f):
    """Decorator to ensure user is authenticated"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get('user')
        if user is None:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # Add admin status to user, if applicable
        crsid = user['email'].split('@')[0]
        user['is_admin'] = UserService.is_admin(crsid)
        
        return f(user, *args, **kwargs)
    return wrapper

def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get('user')
        if user is None:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        crsid = user['email'].split('@')[0]
        if not UserService.is_admin(crsid):
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('main.index'))
        
        user['is_admin'] = True
        return f(user, *args, **kwargs)
    return wrapper
