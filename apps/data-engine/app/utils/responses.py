from typing import Any
from fastapi.encoders import jsonable_encoder


def response_success(data: Any, message: str = "ok") -> dict[str, Any]:
    return {
        "code": 0,
        "data": jsonable_encoder(data),
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
