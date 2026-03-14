from backend.app.core.config import settings


def get_firestore_client():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:  # noqa: BLE001
        raise RuntimeError(
            "firebase_admin is not installed. Install it or set AI_PROVIDER=local and disable Firestore features."
        ) from exc

    if not firebase_admin._apps:
        if not settings.firebase_credentials_path:
            raise RuntimeError("FIREBASE_CREDENTIALS_PATH is not configured.")

        try:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            firebase_admin.initialize_app(cred)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Failed to initialize Firebase Admin. "
                "Check FIREBASE_CREDENTIALS_PATH and service account permissions."
            ) from exc

    return firestore.client()
