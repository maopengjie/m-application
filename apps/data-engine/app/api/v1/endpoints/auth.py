from fastapi import APIRouter, Cookie, Header, Response, status, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.auth import LoginPayload
from app.services.auth_service import AuthService
from app.utils.responses import response_error, response_success
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
auth_service = AuthService()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_key,
        value=refresh_token,
        httponly=True,
        max_age=settings.refresh_token_expire_seconds,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        path=settings.cookie_path,
        domain=settings.cookie_domain,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_key,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        path=settings.cookie_path,
        domain=settings.cookie_domain,
    )


@router.post("/login")
async def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    auth_result = auth_service.login(db, payload.username, payload.password)
    if not auth_result:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Username or password is incorrect or account is locked.")

    set_refresh_cookie(response, auth_result["refresh_token"])
    return response_success(
        {
            **auth_result["user"],
            "accessToken": auth_result["access_token"],
        }
    )


@router.post("/refresh")
async def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    jwt_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_key),
):
    if not jwt_cookie:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden Exception")

    clear_refresh_cookie(response)
    tokens = auth_service.refresh_access_token(db, jwt_cookie)
    if not tokens:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden Exception")

    set_refresh_cookie(response, tokens["refresh_token"])
    return response_success({"accessToken": tokens["access_token"]})


@router.post("/logout")
async def logout(
    response: Response,
    jwt_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_key),
):
    if jwt_cookie:
        clear_refresh_cookie(response)
    return response_success("")


@router.get("/codes")
async def get_access_codes(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return response_success(auth_service.get_access_codes(db, user["username"]))
