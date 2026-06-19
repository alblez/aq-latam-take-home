"""Owner-id header parsing and validation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.errors import ApiError
from app.owners import get_owner_id, parse_owner_id


def test_parse_owner_id_accepts_valid_uuid() -> None:
    owner = uuid4()
    assert parse_owner_id(str(owner)) == owner


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_parse_owner_id_rejects_missing(raw: str | None) -> None:
    with pytest.raises(ApiError) as exc:
        parse_owner_id(raw)
    assert exc.value.code == "invalid_owner_id"
    assert exc.value.status_code == 400


def test_parse_owner_id_rejects_malformed() -> None:
    with pytest.raises(ApiError) as exc:
        parse_owner_id("not-a-uuid")
    assert exc.value.code == "invalid_owner_id"


@pytest.mark.asyncio
async def test_get_owner_id_dependency_returns_uuid() -> None:
    owner = uuid4()
    assert await get_owner_id(str(owner)) == owner
