from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, cast

from asgi_correlation_id import correlation_id
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

ErrorCode = Literal[
    "invalid_owner_id",
    "job_not_found",
    "session_not_found",
    "session_not_in_progress",
    "session_in_progress",
    "turn_already_submitted",
    "validation_error",
    "model_unavailable",
    "catalog_setup_error",
]


class ErrorPayload(BaseModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    requestId: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorPayload


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code: int = status_code
        self.code: ErrorCode = code
        self.message: str = message
        self.details: dict[str, Any] = details or {}


def error_response(
    *,
    status_code: int,
    code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorPayload(
            code=code,
            message=message,
            details=details or {},
            requestId=correlation_id.get(),
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


async def api_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ApiError):
        raise exc
    return error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


def _sanitize_validation_errors(errors: Sequence[Any]) -> list[dict[str, Any]]:
    """Stringify unserializable ctx values so model_dump(mode='json') won't crash."""
    sanitized: list[dict[str, Any]] = []
    for err in errors:
        clean = dict(err)
        if "ctx" in clean and isinstance(clean["ctx"], dict):
            clean["ctx"] = {k: str(v) for k, v in clean["ctx"].items()}
        sanitized.append(clean)
    return sanitized


async def validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code=cast(ErrorCode, "validation_error"),
        message="Request validation failed.",
        details={"errors": _sanitize_validation_errors(exc.errors())},
    )
