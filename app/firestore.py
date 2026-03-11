import os

import firebase_admin
from firebase_admin import credentials, firestore

key_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_key.json")
cred = credentials.Certificate(key_path)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
