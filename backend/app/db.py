from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def normalize_postgres_url(url: str) -> str:
    """Rewrite postgresql:// to postgresql+psycopg:// for psycopg v3.

    Neon/Railway provide postgresql:// URLs which default to psycopg2.
    We use psycopg v3 — rewrite scheme to postgresql+psycopg://.
    """
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def make_engine(database_url: str) -> Engine:
    """Create a sync SQLAlchemy engine for explicit setup/deploy/runtime use."""
    return create_engine(normalize_postgres_url(database_url), pool_pre_ping=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a bound sessionmaker for per-request DB sessions."""
    return sessionmaker(bind=engine)
