"""Database connection and session management."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.config import (
    MYSQL_MAX_OVERFLOW,
    MYSQL_POOL_PRE_PING,
    MYSQL_POOL_RECYCLE_SEC,
    MYSQL_POOL_SIZE,
    MYSQL_POOL_TIMEOUT_SEC,
)

engine: Engine | None = None
session_factory: scoped_session[Session] | None = None


def init_database(database_url: str) -> Engine:
    global engine, session_factory

    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=MYSQL_POOL_PRE_PING,
        pool_recycle=MYSQL_POOL_RECYCLE_SEC,
        pool_size=MYSQL_POOL_SIZE,
        max_overflow=MYSQL_MAX_OVERFLOW,
        pool_timeout=MYSQL_POOL_TIMEOUT_SEC,
    )
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
