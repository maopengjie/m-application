from typing import Any

from app.core.config import get_settings
from app.core.security import sign_token, verify_token
from app.repositories.auth_repository import AuthRepository

settings = get_settings()


class AuthService:
    def __init__(self, repository: AuthRepository | None = None):
        self.repository = repository or AuthRepository()

    @staticmethod
    def public_user(user: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in user.items() if key != "password"}

    def login(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.repository.find_user_by_credentials(username, password)
        if not user:
            return None

        access_token = sign_token(
            user,
            settings.access_token_secret,
            settings.access_token_expire_seconds,
        )
        refresh_token = sign_token(
            user,
            settings.refresh_token_secret,
            settings.refresh_token_expire_seconds,
        )
        return {
            "user": self.public_user(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def refresh_access_token(self, refresh_token: str) -> str | None:
        payload = verify_token(refresh_token, settings.refresh_token_secret)
        if not payload:
            return None

        user = self.repository.find_user_by_username(payload.get("username", ""))
        if not user:
            return None

        return sign_token(
            user,
            settings.access_token_secret,
            settings.access_token_expire_seconds,
        )

    def get_user_from_access_token(self, authorization: str | None) -> dict[str, Any] | None:
        if not authorization or not authorization.startswith("Bearer "):
            return None

        token = authorization.split(" ", 1)[1].strip()
        if not token:
            return None

        payload = verify_token(token, settings.access_token_secret)
        if not payload:
            return None

        user = self.repository.find_user_by_username(payload.get("username", ""))
        if not user:
            return None

        return self.public_user(user)

    def get_access_codes(self, username: str) -> list[str]:
        return self.repository.get_access_codes(username)
