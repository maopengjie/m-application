import time
from typing import Any
import bcrypt
from jose import JWTError, jwt

# Password hashing using bcrypt directly
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Convert to bytes if they are strings
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


import uuid

def sign_token(user: dict[str, Any], secret: str, expires_in: int, token_type: str = "access") -> str:
    now = int(time.time())
    payload = {
        "jti": uuid.uuid4().hex,
        "token_type": token_type,
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
