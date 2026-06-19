"""Shared fixtures for the fast (non-DB) test suite.

These fixtures exercise the application through an in-process ASGI transport and
provide non-secret runtime environment values so app construction succeeds.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx2 import ASGITransport, AsyncClient

from app.main import app

TEST_DATABASE_URL = "postgresql+psycopg://test:test@localhost:5432/test"
TEST_OPENROUTER_API_KEY = "sk-test-not-a-real-key"
TEST_OPENROUTER_LLM_MODEL = "test-provider/test-model"


@pytest.fixture(autouse=True)
def backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Supply non-secret runtime env so the app lifespan can build Settings."""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("OPENROUTER_API_KEY", TEST_OPENROUTER_API_KEY)
    monkeypatch.setenv("OPENROUTER_LLM_MODEL", TEST_OPENROUTER_LLM_MODEL)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """In-process ASGI client (does not run lifespan; routes needing DB are excluded)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
