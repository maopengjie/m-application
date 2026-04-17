from typing import Any
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import sign_token, verify_token, verify_password
from app.repositories.auth_repository import AuthRepository
from app.models.user import User

import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, repository: AuthRepository | None = None):
        self.repository = repository or AuthRepository()

    @staticmethod
    def public_user(user: User) -> dict[str, Any]:
        return {
            "id": user.id,
            "username": user.username,
            "realName": user.real_name,
            "roles": user.roles,
            "homePath": user.home_path,
        }

    def login(self, db: Session, username: str, password: str) -> dict[str, Any] | None:
        user = self.repository.find_user_by_username(db, username)
        
        if not user:
            return None
            
        if user.is_locked or not user.is_active:
            # Here we could return a specific error code for locked/inactive accounts
            return None

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Login failed: Incorrect password for user '{username}'")
            self.repository.increment_failed_attempts(db, username)
            return None

        logger.info(f"User logged in successfully: '{username}'")
        self.repository.update_last_login(db, user.id)

        user_dict = self.public_user(user)
        access_token = sign_token(
            user_dict,
            settings.access_token_secret,
            settings.access_token_expire_seconds,
            token_type="access",
        )
        refresh_token = sign_token(
            user_dict,
            settings.refresh_token_secret,
            settings.refresh_token_expire_seconds,
            token_type="refresh",
        )
        return {
            "user": user_dict,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def refresh_access_token(self, db: Session, refresh_token: str) -> dict[str, str] | None:
        payload = verify_token(refresh_token, settings.refresh_token_secret)
        if not payload or payload.get("token_type") != "refresh":
            return None

        user = self.repository.find_user_by_username(db, payload.get("username", ""))
        if not user or not user.is_active or user.is_locked:
            return None

        user_dict = self.public_user(user)
        new_access_token = sign_token(
            user_dict,
            settings.access_token_secret,
            settings.access_token_expire_seconds,
            token_type="access",
        )
        new_refresh_token = sign_token(
            user_dict,
            settings.refresh_token_secret,
            settings.refresh_token_expire_seconds,
            token_type="refresh",
        )
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }

    def get_user_from_access_token(self, db: Session, authorization: str | None) -> dict[str, Any] | None:
        if not authorization or not authorization.startswith("Bearer "):
            return None

        token = authorization.split(" ", 1)[1].strip()
        if not token:
            return None

        payload = verify_token(token, settings.access_token_secret)
        if not payload or payload.get("token_type") != "access":
            return None

        user = self.repository.find_user_by_username(db, payload.get("username", ""))
        if not user or not user.is_active or user.is_locked:
            return None

        return self.public_user(user)

    def get_access_codes(self, db: Session, username: str) -> list[str]:
        return self.repository.get_access_codes(db, username)
