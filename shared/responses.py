from typing import Any

from fastapi import HTTPException


def ok(data: Any = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": data, "meta": meta}


def fail(code: str, message: str, status_code: int = 400, details: Any | None = None):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message, "details": details}},
    )

