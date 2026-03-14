from backend.app.database.firebase import get_firestore_client


def get_db():
    return get_firestore_client()
