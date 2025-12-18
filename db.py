import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import g
import os

# Use serviceAccountKey.json for credentials
CRED_PATH = "serviceAccountKey.json"

def get_db():
    if 'db' not in g:
        # Check if already initialized to avoid "app already exists" error
        if not firebase_admin._apps:
            cred = credentials.Certificate(CRED_PATH)
            firebase_admin.initialize_app(cred)
        
        g.db = firestore.client()
    
    return g.db

def close_db(e=None):
    # Firestore client usually doesn't need explicit closing per request like SQLite
    g.pop('db', None)
