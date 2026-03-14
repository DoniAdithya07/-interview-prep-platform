import firebase_admin
from firebase_admin import credentials, firestore

from backend.app.core.config import settings


def get_firestore_client():
    if not firebase_admin._apps:
        if not settings.firebase_credentials_path:
            raise RuntimeError("FIREBASE_CREDENTIALS_PATH is not configured.")

        if not credentials:
            raise RuntimeError("firebase-admin credentials module is unavailable.")

        try:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            firebase_admin.initialize_app(cred)
        except Exception as exc:
            raise RuntimeError(
                "Failed to initialize Firebase Admin. "
                "Check FIREBASE_CREDENTIALS_PATH and service account permissions."
            ) from exc

    return firestore.client()
