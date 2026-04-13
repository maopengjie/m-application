import time
from typing import Any

import pandas as pd
from fastapi import Cookie, FastAPI, Header, Response, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel

app = FastAPI(title="Vben Data Engine (Python)")

ACCESS_TOKEN_SECRET = "access_token_secret"
REFRESH_TOKEN_SECRET = "refresh_token_secret"
ACCESS_TOKEN_EXPIRE_SECONDS = 7 * 24 * 60 * 60
REFRESH_TOKEN_EXPIRE_SECONDS = 30 * 24 * 60 * 60
REFRESH_COOKIE_KEY = "jwt"

MOCK_USERS = [
    {
        "id": 0,
        "username": "vben",
        "password": "123456",
        "realName": "Vben",
        "roles": ["super"],
        "homePath": "/dashboard",
    },
    {
        "id": 1,
        "username": "admin",
        "password": "123456",
        "realName": "Admin",
        "roles": ["admin"],
        "homePath": "/workspace",
    },
    {
        "id": 2,
        "username": "jack",
        "password": "123456",
        "realName": "Jack",
        "roles": ["user"],
        "homePath": "/analytics",
    },
]

MOCK_CODES = {
    "vben": ["AC_100100", "AC_100110", "AC_100120", "AC_100010"],
    "admin": ["AC_100010", "AC_100020", "AC_100030"],
    "jack": ["AC_1000001", "AC_1000002"],
}


class LoginPayload(BaseModel):
    username: str
    password: str


def response_success(data: Any, message: str = "ok") -> dict[str, Any]:
    return {
        "code": 0,
        "data": data,
        "error": None,
        "message": message,
    }


def response_error(message: str, error: Any = None) -> dict[str, Any]:
    return {
        "code": -1,
        "data": None,
        "error": error,
        "message": message,
    }


def sign_token(user: dict[str, Any], secret: str, expires_in: int) -> str:
    now = int(time.time())
    payload = {
        "username": user["username"],
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in user.items() if key != "password"}


def find_user_by_username(username: str) -> dict[str, Any] | None:
    return next((user for user in MOCK_USERS if user["username"] == username), None)


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        return None

    username = payload.get("username")
    if not username:
        return None

    user = find_user_by_username(username)
    if not user:
        return None

    return public_user(user)


def verify_access_token(authorization: str | None) -> dict[str, Any] | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    return verify_token(token, ACCESS_TOKEN_SECRET)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_KEY,
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_SECONDS,
        samesite="lax",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_KEY,
        httponly=True,
        samesite="lax",
    )


def unauthorized_response(response: Response) -> dict[str, Any]:
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return response_error("Unauthorized Exception", "Unauthorized Exception")


def forbidden_response(response: Response, message: str = "Forbidden Exception") -> dict[str, Any]:
    response.status_code = status.HTTP_403_FORBIDDEN
    return response_error(message, message)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5777", "http://127.0.0.1:5777"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Vben Data Engine (Python) is running"}


@app.get("/api/status")
async def get_status():
    return response_success(
        {
            "status": "online",
            "engine": "FastAPI",
            "task_count": 0,
        }
    )


@app.post("/api/auth/login")
async def login(payload: LoginPayload, response: Response):
    user = next(
        (
            item
            for item in MOCK_USERS
            if item["username"] == payload.username and item["password"] == payload.password
        ),
        None,
    )
    if not user:
        clear_refresh_cookie(response)
        return forbidden_response(response, "Username or password is incorrect.")

    access_token = sign_token(user, ACCESS_TOKEN_SECRET, ACCESS_TOKEN_EXPIRE_SECONDS)
    refresh_token = sign_token(user, REFRESH_TOKEN_SECRET, REFRESH_TOKEN_EXPIRE_SECONDS)
    set_refresh_cookie(response, refresh_token)

    return response_success(
        {
            **public_user(user),
            "accessToken": access_token,
        }
    )


@app.post("/api/auth/refresh")
async def refresh_token(response: Response, jwt_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE_KEY)):
    if not jwt_cookie:
        return forbidden_response(response)

    clear_refresh_cookie(response)
    user = verify_token(jwt_cookie, REFRESH_TOKEN_SECRET)
    if not user:
        return forbidden_response(response)

    raw_user = find_user_by_username(user["username"])
    if not raw_user:
        return forbidden_response(response)

    set_refresh_cookie(response, jwt_cookie)
    access_token = sign_token(raw_user, ACCESS_TOKEN_SECRET, ACCESS_TOKEN_EXPIRE_SECONDS)
    return access_token


@app.post("/api/auth/logout")
async def logout(response: Response, jwt_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE_KEY)):
    if jwt_cookie:
        clear_refresh_cookie(response)
    return response_success("")


@app.get("/api/auth/codes")
async def get_access_codes(response: Response, authorization: str | None = Header(default=None)):
    user = verify_access_token(authorization)
    if not user:
        return unauthorized_response(response)

    return response_success(MOCK_CODES.get(user["username"], []))


@app.get("/api/user/info")
async def get_user_info(response: Response, authorization: str | None = Header(default=None)):
    user = verify_access_token(authorization)
    if not user:
        return unauthorized_response(response)

    return response_success(user)


@app.post("/api/crawler/start")
async def start_crawler(target_url: str):
    print(f"Starting crawler for: {target_url}")
    return response_success({"job_id": f"job_{int(time.time())}"}, "Crawler task started")


@app.get("/api/analysis/summary")
async def get_analysis():
    data = {
        "City": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"],
        "Sales": [100, 150, 120, 200],
    }
    df = pd.DataFrame(data)
    summary = df.describe().to_dict()
    return response_success(
        {
            "summary": summary,
            "chart_data": data,
        },
        "Analysis completed",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
