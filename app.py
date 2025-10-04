from flask import Flask, jsonify, session, render_template, url_for, redirect, request
from authlib.integrations.flask_client import OAuth
import dotenv
import os
import datetime
from zoneinfo import ZoneInfo
import db

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Raven OAuth2 configuration
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_OAUTH2_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET'),
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth?hd=cam.ac.uk',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'profile email openid',
    }
)

# Decorator to ensure user is authorized
def login_required(f):
    def wrapper(*args, **kwargs):
        user = session.get('user')
        if user is None:
            return redirect(url_for('login'))

        crsid, _, _ = user['email'].partition('@')
        admin_crsids = [admin['crsid'] for admin in db.get_all_admins()]
        user['is_admin'] = crsid in admin_crsids
        return f(user, *args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def admin_required(f):
    def wrapper(*args, **kwargs):
        user = session.get('user')
        if user is None:
            return redirect(url_for('login'))

        crsid, _, _ = user['email'].partition('@')
        admin_crsids = [admin['crsid'] for admin in db.get_all_admins()]
        if crsid in admin_crsids:
            user['is_admin'] = True
            return f(user, *args, **kwargs)
        else:
            return jsonify({'error': 'Access denied'}), 403
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/login')
def login():
    if session.get('user') is None:
        return render_template('login.html')
    else:
        return redirect(url_for('index'))
        
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/oauth2')
def oauth2():
    redirect_uri = url_for('authorized', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorized')
def authorized():
    token = oauth.google.authorize_access_token()
    if token is None:
        # TODO(lucas): handle error separately with error page?
        return redirect(url_for('login'))

    session['user'] = token['userinfo']
    return redirect(url_for('index'))

# Index route
@app.route('/')
@login_required
def index(user):
    return render_template('index.html', user=user)

@app.route('/user')
@login_required
def user(user):
    return jsonify(user)

# Server-side rendering of item cards
@app.route('/ssr/cards')
@login_required
def ssr_cards(user):
    items = db.get_all_available_items()
    return render_template('cards.html', items=items)

# Healthcheck endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'}), 200

@app.route('/admin/directory')
@admin_required
def directory(user):
    return render_template('admin/directory.html', users=db.get_all_users(), user=user)

@app.route('/admin/inventory')
@admin_required
def inventory(user):
    items = db.get_all_items()
    return render_template('admin/inventory.html', items=items, user=user)

@app.route('/admin/list')
@admin_required
def permissions(user):
    return render_template('admin/directory.html', users=db.get_all_admins(), user=user)

@app.route('/admin/requests')
@admin_required
def requests(user):
    items = db.get_all_requested_items()
    return render_template('admin/requests.html', items=items, user=user)

@app.context_processor
def inject_datetime_now():
    now = datetime.datetime.now(ZoneInfo("Europe/London"))
    return {
        'datetime_now': now,
        'datetime_now_str': now.strftime("%Y-%m-%d %H:%M:%S")
    }

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon/favicon.ico')

@app.route('/api/edit_item', methods=['POST'])
@admin_required
def api_edit_item(user):
    payload = request.get_json()
    doc_id = payload.get('id')
    data = payload.get('data')
    if not doc_id or not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        print(data)
        db.update_item(doc_id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/new_item', methods=['POST'])
@admin_required
def api_new_item(user):
    payload = request.get_json()
    data = payload.get('data')
    
    try:
        item_id = db.create_item({ **data, 'occupied': False })
        return jsonify({'success': True, 'id': item_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_item', methods=['POST'])
@admin_required
def api_delete_item(user):
    payload = request.get_json()
    doc_id = payload.get('id')
    if not doc_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        db.delete_item(doc_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/return_item', methods=['POST'])
@admin_required
def api_return_item(user):
    payload = request.get_json()
    doc_id = payload.get('id')
    location = payload.get('location')
    if not doc_id or not location:
        return jsonify({'error': 'Invalid request'}), 400
    try:
        db.return_item(doc_id, location)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/loan_item', methods=['POST'])
@admin_required
def api_manually_loan_item(user):
    payload = request.get_json()
    doc_id = payload.get('id')
    email = payload.get('email')
    
    if not doc_id or not email:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        db.loan_item(doc_id, email)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/request_item', methods=['POST'])
@login_required
def api_request_item(user):
    payload = request.get_json()
    doc_id = payload.get('id')
    email = user['email']

    if not doc_id or not email:
        return jsonify({'error': 'Invalid request'}), 400

    try:
        db.request_item(doc_id, email)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refuse_request', methods=['POST'])
@admin_required
def api_refuse_request(user):
    payload = request.get_json()
    doc_id = payload.get('id')
    reason = payload.get('reason')
    if not doc_id or not reason:
        return jsonify({'error': 'Invalid request'}), 400
    try:
        db.refuse_request(doc_id, reason)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items')
def list_items():
    items = db.get_all_items()
    return jsonify(items)
    
# @app.route('/api/rebuild_lookup', methods=['GET', 'POST'])
# @login_required
# def api_rebuild_lookup(user):
#     if user['email'] != 'khm39@cam.ac.uk':
#         return jsonify({'error': 'Access denied'}), 403

#     try:
#         # Delete all existing users
#         db.delete_all_users()

#         # Download CSV of group
#         df = pd.read_csv("downloads/KINGSUG.csv")
#         users = df.to_dict(orient='records')

#         # Update Firestore with the new user data
#         for user in users:
#             # if not user['email']: continue
#             crsid = user['person_identifier']
#             db.create_user(crsid, user.get('display_name', ''), 'KINGSUG')

#         return jsonify({'success': True})
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8765)
