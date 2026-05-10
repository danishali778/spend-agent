from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


if not settings.database_url:
    # The backend can still be scaffolded and imported for contract work,
    # but runtime DB access requires SUPABASE_DB_URL / DATABASE_URL.
    engine = None
    SessionLocal = None
else:
    engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def get_db_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database URL is not configured. Set SUPABASE_DB_URL or DATABASE_URL.")
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
