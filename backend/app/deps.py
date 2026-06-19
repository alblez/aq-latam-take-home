from __future__ import annotations

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import Settings
from app.engine.gateway import ModelGateway
from app.owners import get_owner_id

OwnerId = Annotated[UUID, Depends(get_owner_id)]


def get_db_session(request: Request) -> Generator[Session]:
    """Yield a per-request SQLAlchemy session from app.state.session_factory."""
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db_session)]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


AppSettings = Annotated[Settings, Depends(get_settings)]


def get_gateway(request: Request) -> ModelGateway:
    """Return the app-level ModelGateway instance from app.state per D-21."""
    return request.app.state.gateway


GatewayDep = Annotated[ModelGateway, Depends(get_gateway)]
