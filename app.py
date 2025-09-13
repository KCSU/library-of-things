from flask import Flask, jsonify, session, render_template, url_for, redirect
import firebase_admin
from firebase_admin import credentials, firestore
from cachetools.func import ttl_cache
from flask_oauthlib.client import OAuth
import dotenv
import os

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Raven OAuth2 configuration
oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=os.getenv('GOOGLE_OAUTH2_CLIENT_ID'),
    consumer_secret=os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET'),
    request_token_params={
        'scope': 'profile email openid',
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth?hd=cam.ac.uk',
)

# Initialize Firestore DB
def initialize_firestore():
    cred = credentials.Certificate('service_account_key.json')
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firestore()

# Query all items from the database
@ttl_cache(maxsize=1, ttl=60) # TODO(lucas): remove
def get_all_items():
    docs = db.collection('items').stream()
    items = [doc.to_dict() for doc in docs]
    return items

# Decorator to ensure user is authorized
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'google_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/login')
def login():
    if 'google_token' in session:
        return redirect(url_for('index'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/oauth')
def oauth():
    return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/authorized')
def authorized():
    response = google.authorized_response()
    if response is None or response.get('access_token') is None:
        # TODO(lucas): handle error separately with error page?
        return redirect(url_for('login'))

    session['google_token'] = (response['access_token'], '')
    return redirect(url_for('index'))

# Index route
@app.route('/')
@login_required
def index():
    me = google.get('userinfo')
    return render_template('index.html', user=me.data)

# Server-side rendering of item cards
@app.route('/_ssr/cards')
@login_required
def ssr_cards():
    items = get_all_items()
    return render_template('cards.html', items=items)

# Healthcheck endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'}), 200
    
# Favicon route
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon/favicon.ico')

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')
    
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8765)
