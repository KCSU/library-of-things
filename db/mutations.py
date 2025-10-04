from .base import clear_item_cache, db
from firebase_admin import firestore
import datetime
from zoneinfo import ZoneInfo

def create_item(data):
    doc_ref = db.collection('items').add(data)
    clear_item_cache()
    return doc_ref[1].id

def update_item(id, data):
    db.collection('items').document(id).update(data)
    clear_item_cache()

def delete_item(id):
    db.collection('items').document(id).delete()
    clear_item_cache()

def return_item(id, location):
    db.collection('items').document(id).update({
        'borrowed_by': firestore.DELETE_FIELD,
        'due_date': firestore.DELETE_FIELD,
        'location': location,
        'occupied': False
    })
    clear_item_cache()

def loan_item(id, email):
    # query the item to check its borrow length
    item_doc = db.collection('items').document(id).get()
    if not item_doc.exists:
        raise ValueError('Item not found')
    
    item_data = item_doc.to_dict()
    borrow_length = item_data.get('borrow_length', 'short')

    if borrow_length == 'permanent':
        # TODO(lucas): fix permanent loans
        delete_item(id)
    else:
        # Calculate due date based on borrow_length
        now = datetime.datetime.now(ZoneInfo("Europe/London"))
        if borrow_length == 'short':
            due_date = now + datetime.timedelta(weeks=1)
        elif borrow_length == 'long':
            # assume end of academic year is 1st July
            due_date = datetime.datetime(now.year + 1, 7, 1, tzinfo=ZoneInfo("Europe/London"))
        
        crsid = email.split('@')[0]
        new_data = {
            'borrowed_by': crsid,
            'due_date': due_date,
            'occupied': True,
            'location': firestore.DELETE_FIELD,
            'requested_by': firestore.DELETE_FIELD,
            'request_time': firestore.DELETE_FIELD
        }
        db.collection('items').document(id).update(new_data)

    clear_item_cache()

def request_item(id, email):
    now = datetime.datetime.now(ZoneInfo("Europe/London"))
    crsid = email.split('@')[0]
    db.collection('items').document(id).update({
        'requested_by': crsid,
        'request_time': now,
        'occupied': True
    })
    clear_item_cache()

def refuse_request(id, reason):
    db.collection('items').document(id).update({
        'requested_by': firestore.DELETE_FIELD,
        'request_time': firestore.DELETE_FIELD,
        'occupied': False
    })
    clear_item_cache()
