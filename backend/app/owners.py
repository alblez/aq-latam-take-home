from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Header, status

from app.errors import ApiError


def parse_owner_id(raw_owner_id: str | None) -> UUID:
    if raw_owner_id is None or raw_owner_id.strip() == "":
        raise ApiError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_owner_id",
            message="Valid X-Owner-Id header is required.",
        )
    try:
        return UUID(raw_owner_id)
    except ValueError as exc:
        raise ApiError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_owner_id",
            message="Valid X-Owner-Id header is required.",
        ) from exc


async def get_owner_id(
    x_owner_id: Annotated[str | None, Header(alias="X-Owner-Id")] = None,
) -> UUID:
    return parse_owner_id(x_owner_id)
