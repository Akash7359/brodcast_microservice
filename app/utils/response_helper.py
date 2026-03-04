from datetime import datetime, timezone
from typing import Any, Optional
from fastapi.responses import JSONResponse
from app.core.config import settings


def success_response(message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    body = {
        "success": True,
        "message": message,
        "version": settings.APP_VERSION,
    }
    if data is not None:
        body["data"] = data
    return JSONResponse(content=body, status_code=status_code)


def error_response(
    message: str,
    errors: Optional[Any] = None,
    status_code: int = 400,
) -> JSONResponse:
    body = {
        "success": False,
        "message": message,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(content=body, status_code=status_code)
