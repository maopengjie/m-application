from typing import Any

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


class AuthRepository:
    def find_user_by_username(self, username: str) -> dict[str, Any] | None:
        return next((user for user in MOCK_USERS if user["username"] == username), None)

    def find_user_by_credentials(self, username: str, password: str) -> dict[str, Any] | None:
        return next(
            (
                user
                for user in MOCK_USERS
                if user["username"] == username and user["password"] == password
            ),
            None,
        )

    def get_access_codes(self, username: str) -> list[str]:
        return MOCK_CODES.get(username, [])
