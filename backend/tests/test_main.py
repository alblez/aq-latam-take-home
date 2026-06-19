"""Application wiring: health endpoint, OpenAPI document, and lifespan."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx2 import AsyncClient

from app.main import app, lifespan


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_openapi_document_is_3_1(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"] == "3.1.0"
    assert "/health" in schema["paths"]


def test_app_metadata() -> None:
    assert app.title == "AI Interviewer Platform API"
    assert app.version == "0.1.0"


@pytest.mark.asyncio
async def test_lifespan_wires_app_state() -> None:
    async with lifespan(app):
        assert app.state.settings is not None
        assert app.state.session_factory is not None
        assert app.state.gateway is not None


@pytest.mark.asyncio
async def test_lifespan_exits_on_missing_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_LLM_MODEL", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        async with lifespan(app):
            pass
