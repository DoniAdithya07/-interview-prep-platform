from datetime import datetime
from typing import Any


def serialize_firestore_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: serialize_firestore_value(item) for key, item in value.items()}

    if isinstance(value, list):
        return [serialize_firestore_value(item) for item in value]

    return value
