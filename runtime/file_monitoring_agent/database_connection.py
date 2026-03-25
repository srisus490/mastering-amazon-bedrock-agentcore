"""Database connection management for AgentCore Runtime environment.

This module provides database connection functionality for the File Monitoring Agent
running in AWS Bedrock AgentCore Runtime. It reads configuration from environment
variables and provides session management for database operations.

Validates Requirements: 6.1, 6.2, 6.3, 6.5, 6.7, 6.8
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Configure logging
logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def init_db(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Initialize database connection and create engine.
    
    Reads DATABASE_URL from environment variables if not provided.
    Configures SQLAlchemy engine with connection pooling appropriate for the database type.
    Verifies database connectivity on initialization.
    
    Args:
        database_url: Database connection URL (reads from DATABASE_URL env var if not provided)
        echo: Whether to echo SQL statements (default: False)
        
    Returns:
        SQLAlchemy engine
        
    Raises:
        ValueError: If DATABASE_URL is not set and database_url not provided
        RuntimeError: If database connection verification fails
        
    Validates: Requirements 6.1, 6.2, 6.3, 6.5
    """
    global _engine, _session_factory
    
    if _engine is not None:
        logger.warning("Database already initialized, returning existing engine")
        return _engine
    
    # Read DATABASE_URL from environment if not provided
    if database_url is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Please configure DATABASE_URL in the runtime environment."
            )
    
    logger.info(f"Initializing database connection: {database_url.split('://')[0]}://...")
    
    # Determine database type
    is_sqlite = database_url.startswith("sqlite")
    
    try:
        if is_sqlite:
            # SQLite-specific configuration
            db_path = database_url.replace("sqlite:///", "")
            
            # Create data directory if needed (not for in-memory)
            if db_path != ":memory:":
                db_dir = os.path.dirname(db_path)
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
                    logger.info(f"Ensured database directory exists: {db_dir}")
            
            _engine = create_engine(
                database_url,
                echo=echo,
                connect_args={"check_same_thread": False},  # Allow multi-threading
                poolclass=StaticPool,  # Use static pool for SQLite
            )
            
            # Enable foreign keys and WAL mode for SQLite
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                cursor.close()
                
        else:
            # PostgreSQL or other database configuration with connection pooling
            _engine = create_engine(
                database_url,
                echo=echo,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=10,  # Connection pool size
                max_overflow=20,  # Max overflow connections
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
        
        # Verify database connectivity
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection verified successfully")
        
        # Create session factory
        _session_factory = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
        )
        
        logger.info("Database connection initialized successfully")
        return _engine
        
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {str(e)}")
        _engine = None
        _session_factory = None
        raise RuntimeError(f"Database connection initialization failed: {str(e)}") from e


def get_engine() -> Engine:
    """
    Get the database engine.
    
    Returns:
        SQLAlchemy engine
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _engine is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first or ensure "
            "DATABASE_URL environment variable is set."
        )
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
        raise RuntimeError(
            "Database not initialized. Call init_db() first or ensure "
            "DATABASE_URL environment variable is set."
        )
    return _session_factory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.
    
    Provides automatic session management with commit/rollback handling.
    Sessions are properly closed after use to prevent connection leaks.
    
    Usage:
        with get_db_session() as session:
            # Use session for queries
            results = session.query(Model).all()
            # Session automatically commits on success
    
    Yields:
        Database session
        
    Raises:
        RuntimeError: If database not initialized
        Exception: Any database operation errors (session will be rolled back)
        
    Validates: Requirements 6.7, 6.8
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        session.commit()
        logger.debug("Database session committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error, rolled back: {str(e)}")
        raise
    finally:
        session.close()
        logger.debug("Database session closed")


def close_db() -> None:
    """
    Close database connection and cleanup resources.
    
    Should be called when shutting down the application to properly
    dispose of connection pools and release resources.
    """
    global _engine, _session_factory
    
    if _engine is not None:
        logger.info("Closing database connection")
        _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connection closed successfully")


def verify_connection() -> bool:
    """
    Verify database connection is working.
    
    Returns:
        True if connection is working, False otherwise
        
    Validates: Requirement 6.5
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verification successful")
        return True
    except Exception as e:
        logger.error(f"Database connection verification failed: {str(e)}")
        return False
