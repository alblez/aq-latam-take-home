"""Error envelope construction and validation-error sanitization."""

from __future__ import annotations

import json

from app.errors import (
    ApiError,
    ErrorPayload,
    ErrorResponse,
    _sanitize_validation_errors,
    error_response,
)


def test_api_error_carries_fields() -> None:
    err = ApiError(
        status_code=404,
        code="job_not_found",
        message="No such job.",
        details={"jobId": "x"},
    )
    assert err.status_code == 404
    assert err.code == "job_not_found"
    assert err.message == "No such job."
    assert err.details == {"jobId": "x"}


def test_api_error_defaults_details_to_empty_dict() -> None:
    err = ApiError(status_code=400, code="validation_error", message="bad")
    assert err.details == {}


def test_error_response_serializes_envelope() -> None:
    response = error_response(
        status_code=400,
        code="invalid_owner_id",
        message="Valid X-Owner-Id header is required.",
    )
    assert response.status_code == 400
    body = json.loads(bytes(response.body))
    assert body["error"]["code"] == "invalid_owner_id"
    assert body["error"]["message"] == "Valid X-Owner-Id header is required."
    assert body["error"]["details"] == {}


def test_error_models_round_trip() -> None:
    payload = ErrorPayload(code="model_unavailable", message="down")
    envelope = ErrorResponse(error=payload)
    assert envelope.error.code == "model_unavailable"
    assert envelope.error.details == {}


def test_sanitize_validation_errors_stringifies_ctx() -> None:
    raw = [{"type": "value_error", "loc": ("body", "x"), "ctx": {"error": ValueError("boom")}}]
    cleaned = _sanitize_validation_errors(raw)
    assert cleaned[0]["ctx"]["error"] == "boom"
