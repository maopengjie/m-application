from typing import Any


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
