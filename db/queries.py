from cachetools.func import ttl_cache
from .base import db
from firebase_admin.firestore import FieldFilter

def get_all_requested_items():
    docs = db.collection('items').order_by('requested_by').stream()
    pending_items = []
    for doc in docs:
        item = doc.to_dict()
        item['id'] = doc.id  # Firestore document ID
        person_doc = db.collection('users').document(item['requested_by']).get()
        if person_doc.exists:
            person = person_doc.to_dict()
            item['requested_by_name'] = person.get('name', '(???)')
        pending_items.append(item)

    return pending_items

@ttl_cache(maxsize=1, ttl=600)
def get_all_users():
    docs = db.collection('users').stream()
    users = []
    for doc in docs:
        user = doc.to_dict()
        user['crsid'] = doc.id  # Firestore document ID
        users.append(user)
    return users

@ttl_cache(maxsize=1, ttl=3600)
def get_all_admins():
    docs = db.collection('users').where(filter=FieldFilter('admin', '==', True)).stream()
    users = []
    for doc in docs:
        user = doc.to_dict()
        user['crsid'] = doc.id  # Firestore document ID
        users.append(user)
    return users

def query_user_by_crsid(id):
    doc = db.collection('users').document(id).get()
    if doc.exists:
        user = doc.to_dict()
        user['crsid'] = doc.id
        return user
    return None