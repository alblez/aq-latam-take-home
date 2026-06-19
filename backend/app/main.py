from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from app.config import Settings, build_cors_origin_regex
from app.db import make_engine, make_session_factory
from app.engine.gateway import OpenRouterGateway
from app.errors import ApiError, api_error_handler, validation_error_handler
from app.logging import configure_logging
from app.routes import history_router, jobs_router, sessions_router

configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    try:
        settings = Settings()  # pyright: ignore[reportCallIssue] -- BaseSettings reads env vars.
    except ValidationError as exc:
        invalid_vars = [
            str(error["loc"][0])
            for error in exc.errors()
            if error["type"] in {"missing", "string_too_short"}
        ]
        logger.error("missing_required_env_vars", vars=invalid_vars)
        sys.exit(1)

    app.state.settings = settings

    # Wire DB session factory for per-request dependency injection
    engine = make_engine(settings.database_url)
    app.state.session_factory = make_session_factory(engine)

    # Wire model gateway for per-request dependency injection (D-20)
    app.state.gateway = OpenRouterGateway(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_llm_model,
    )

    yield

    # Cleanup
    if hasattr(app.state.gateway, "close"):
        app.state.gateway.close()
    engine.dispose()


class HealthResponse(BaseModel):
    status: str


app = FastAPI(
    title="AI Interviewer Platform API",
    version="0.1.0",
    openapi_version="3.1.0",
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=build_cors_origin_regex(os.environ.get("CORS_ALLOWED_ORIGINS", ""))
    or "^https?://localhost(:\\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(jobs_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
