"""Database connection and session management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# Global engine and session factory
engine = None
SessionLocal = None

def init_database(database_url: str):
    """Initialize database connection"""
    global engine, SessionLocal
    
    engine = create_engine(
        database_url, 
        echo=False,
        pool_pre_ping=True,  # Test connections before using them
        pool_recycle=3600,   # Recycle connections after 1 hour
        pool_size=10,        # Number of connections to maintain
        max_overflow=20      # Max additional connections when pool is full
    )
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    
    return engine

def get_db_session():
    """Get database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return SessionLocal()

@contextmanager
def db_session():
    """Context manager for database sessions"""
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def close_db_session():
    """Close database session"""
    if SessionLocal:
        SessionLocal.remove()