from firebase_admin import credentials, firestore, initialize_app
from firebase_admin.firestore import FieldFilter
from cachetools.func import ttl_cache

# Initialize Firestore DB
def initialize_firestore():
    cred = credentials.Certificate('service_account_key.json')
    initialize_app(cred)
    return firestore.client()

db = initialize_firestore()

@ttl_cache(maxsize=1, ttl=600)
def get_all_items():
    docs = db.collection('items').order_by('display_id').stream()
    items = []
    for doc in docs:
        item = doc.to_dict()
        item['id'] = doc.id  # Firestore document ID
        items.append(item)
    return items

@ttl_cache(maxsize=1, ttl=600)
def get_all_available_items():
    docs = db.collection('items').where(filter=FieldFilter('occupied', '==', False)).order_by('display_id').stream()
    available_items = []
    for doc in docs:
        item = doc.to_dict()
        item['id'] = doc.id  # Firestore document ID
        available_items.append(item)
    return available_items

def clear_item_cache():
    get_all_items.cache_clear()
    get_all_available_items.cache_clear()