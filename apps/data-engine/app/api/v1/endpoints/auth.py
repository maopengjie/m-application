from fastapi import APIRouter, Cookie, Header, Response, status

from app.core.config import get_settings
from app.schemas.auth import LoginPayload
from app.services.auth_service import AuthService
from app.utils.responses import response_error, response_success

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
auth_service = AuthService()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_key,
        value=refresh_token,
        httponly=True,
        max_age=settings.refresh_token_expire_seconds,
        samesite="lax",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_key,
        httponly=True,
        samesite="lax",
    )


def unauthorized_response(response: Response) -> dict:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return response_error("Unauthorized Exception", "Unauthorized Exception")


def forbidden_response(response: Response, message: str = "Forbidden Exception") -> dict:
    response.status_code = status.HTTP_403_FORBIDDEN
    return response_error(message, message)


@router.post("/login")
async def login(payload: LoginPayload, response: Response):
    auth_result = auth_service.login(payload.username, payload.password)
    if not auth_result:
        clear_refresh_cookie(response)
        return forbidden_response(response, "Username or password is incorrect.")

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
    jwt_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_key),
):
    if not jwt_cookie:
        return forbidden_response(response)

    clear_refresh_cookie(response)
    access_token = auth_service.refresh_access_token(jwt_cookie)
    if not access_token:
        return forbidden_response(response)

    set_refresh_cookie(response, jwt_cookie)
    return access_token


@router.post("/logout")
async def logout(
    response: Response,
    jwt_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_key),
):
    if jwt_cookie:
        clear_refresh_cookie(response)
    return response_success("")


@router.get("/codes")
async def get_access_codes(response: Response, authorization: str | None = Header(default=None)):
    user = auth_service.get_user_from_access_token(authorization)
    if not user:
        return unauthorized_response(response)
    return response_success(auth_service.get_access_codes(user["username"]))
