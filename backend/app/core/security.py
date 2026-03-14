import logging

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth

from backend.app.database.firebase import get_firestore_client

logger = logging.getLogger(__name__)


def verify_firebase_token(id_token: str) -> dict:
    try:
        get_firestore_client()
        decoded_token = firebase_auth.verify_id_token(id_token)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firebase token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        ) from exc

    return {
        "id": decoded_token["uid"],
        "email": decoded_token.get("email", ""),
    }
