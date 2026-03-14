from fastapi import HTTPException, Request, status

from backend.app.core.security import verify_firebase_token


def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token in Authorization header",
        )

    return verify_firebase_token(auth_header.removeprefix("Bearer ").strip())
