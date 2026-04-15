import time
from typing import Any

from jose import JWTError, jwt


def sign_token(user: dict[str, Any], secret: str, expires_in: int) -> str:
    now = int(time.time())
    payload = {
        "username": user["username"],
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        return None
