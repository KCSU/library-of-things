from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, firestore
from cachetools.func import ttl_cache

app = Flask(__name__)

# Initialize Firestore DB
def initialize_firestore():
    cred = credentials.Certificate('service_account_key.json')
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firestore()

# Query all items from the database
@ttl_cache(maxsize=1, ttl=3000) # TODO(lucas): remove
def get_all_items():
    docs = db.collection('items').stream()
    items = [doc.to_dict() for doc in docs]
    return items

# Index route
@app.route('/')
def index():
    return render_template('index.html')

# Server-side rendering of item cards
@app.route('/_ssr/cards')
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
    
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8765)
