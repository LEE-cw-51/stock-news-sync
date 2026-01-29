import os
import json
import firebase_admin
from firebase_admin import credentials, db

class DBService:
    def __init__(self):
        if not firebase_admin._apps:
            firebase_json = os.environ.get('FIREBASE_CONFIG')
            if firebase_json:
                cred = credentials.Certificate(json.loads(firebase_json))
            else:
                cred = credentials.Certificate("serviceAccount.json")
            
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://stock-news-sync-default-rtdb.firebaseio.com/'
            })

    def update_market_indices(self, path, updates):
        db.reference(path).update(updates)

    def save_final_feed(self, data):
        db.reference('sync_feed').set(data)