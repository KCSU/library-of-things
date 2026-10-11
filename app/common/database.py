"""Database connection and session management."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.config import (
    DATABASE_MAX_OVERFLOW,
    DATABASE_POOL_PRE_PING,
    DATABASE_POOL_RECYCLE_SEC,
    DATABASE_POOL_SIZE,
    DATABASE_POOL_TIMEOUT_SEC,
)

engine: Engine | None = None
session_factory: scoped_session[Session] | None = None


def init_database(database_url: str | URL) -> Engine:
    global engine, session_factory

    new_engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=DATABASE_POOL_PRE_PING,
        pool_recycle=DATABASE_POOL_RECYCLE_SEC,
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_timeout=DATABASE_POOL_TIMEOUT_SEC,
    )

    with new_engine.connect() as conn:
        conn.execute(text('SELECT 1'))

    engine = new_engine
    session_factory = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    return engine


def get_db_session() -> Session:
    if session_factory is None:
        raise RuntimeError('Database not initialized. Call init_database() first.')
    return session_factory()


@contextmanager
def db_session() -> Iterator[Session]:
    """Session that commits on success and rolls back on any exception."""
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
