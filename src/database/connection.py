"""Database connection management"""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def init_db(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Initialize database connection and create engine.
    
    Args:
        database_url: Database connection URL (uses config if not provided)
        echo: Whether to echo SQL statements
        
    Returns:
        SQLAlchemy engine
    """
    global _engine, _session_factory
    
    if _engine is not None:
        logger.warning("Database already initialized, returning existing engine")
        return _engine
    
    # Get database URL from config if not provided
    if database_url is None:
        settings = get_settings()
        database_url = settings.database.url
    
    logger.info("Initializing database connection", database_url=database_url)
    
    # SQLite-specific configuration
    is_sqlite = database_url.startswith("sqlite")
    
    if is_sqlite:
        # SQLite configuration
        import os
        # Create data directory if it doesn't exist
        db_path = database_url.replace("sqlite:///", "")
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        
        _engine = create_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},  # Allow multi-threading
            poolclass=StaticPool,  # Use static pool for SQLite
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
            cursor.execute("PRAGMA cache_size=-32000")  # 32MB page cache
            cursor.execute("PRAGMA temp_store=MEMORY")  # Temp tables in memory
            cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes, still safe with WAL
            cursor.close()
    else:
        # PostgreSQL or other database configuration
        _engine = create_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    
    # Create session factory
    _session_factory = sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False,
    )
    
    logger.info("Database connection initialized successfully")
    return _engine


def get_engine() -> Engine:
    """
    Get the database engine.
    
    Returns:
        SQLAlchemy engine
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get the session factory.
    
    Returns:
        SQLAlchemy session factory
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.
    
    Usage:
        with get_db_session() as session:
            # Use session
            session.query(...)
    
    Yields:
        Database session
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Database session error", error=str(e))
        raise
    finally:
        session.close()


def close_db() -> None:
    """Close database connection and cleanup resources"""
    global _engine, _session_factory
    
    if _engine is not None:
        logger.info("Closing database connection")
        _engine.dispose()
        _engine = None
        _session_factory = None


def create_test_engine(database_url: str = "sqlite:///:memory:") -> Engine:
    """
    Create a test database engine (in-memory SQLite).
    
    Args:
        database_url: Test database URL
        
    Returns:
        SQLAlchemy engine for testing
    """
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    return engine
