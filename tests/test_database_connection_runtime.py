"""Unit tests for runtime database_connection module.

Tests the database connection functionality for the AgentCore Runtime environment.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime', 'file_monitoring_agent'))
import database_connection


@pytest.fixture(autouse=True)
def reset_db_state():
    """Reset database state before each test."""
    database_connection._engine = None
    database_connection._session_factory = None
    yield
    # Cleanup after test
    if database_connection._engine is not None:
        database_connection.close_db()


def test_init_db_with_explicit_url():
    """Test database initialization with explicit URL."""
    engine = database_connection.init_db("sqlite:///:memory:")
    
    assert engine is not None
    assert database_connection._engine is not None
    assert database_connection._session_factory is not None


def test_init_db_from_environment():
    """Test database initialization from DATABASE_URL environment variable."""
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
        engine = database_connection.init_db()
        
        assert engine is not None
        assert database_connection._engine is not None


def test_init_db_missing_env_var():
    """Test that init_db raises ValueError when DATABASE_URL not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="DATABASE_URL environment variable not set"):
            database_connection.init_db()


def test_init_db_already_initialized():
    """Test that calling init_db twice returns existing engine."""
    engine1 = database_connection.init_db("sqlite:///:memory:")
    engine2 = database_connection.init_db("sqlite:///:memory:")
    
    assert engine1 is engine2


def test_init_db_connection_verification():
    """Test that init_db verifies database connectivity."""
    # This should succeed for in-memory SQLite
    engine = database_connection.init_db("sqlite:///:memory:")
    assert engine is not None


def test_init_db_invalid_url():
    """Test that init_db raises RuntimeError for invalid database URL."""
    with pytest.raises(RuntimeError, match="Database connection initialization failed"):
        database_connection.init_db("invalid://database/url")


def test_get_engine_before_init():
    """Test that get_engine raises RuntimeError before initialization."""
    with pytest.raises(RuntimeError, match="Database not initialized"):
        database_connection.get_engine()


def test_get_engine_after_init():
    """Test that get_engine returns engine after initialization."""
    database_connection.init_db("sqlite:///:memory:")
    engine = database_connection.get_engine()
    
    assert engine is not None
    assert engine is database_connection._engine


def test_get_session_factory_before_init():
    """Test that get_session_factory raises RuntimeError before initialization."""
    with pytest.raises(RuntimeError, match="Database not initialized"):
        database_connection.get_session_factory()


def test_get_session_factory_after_init():
    """Test that get_session_factory returns factory after initialization."""
    database_connection.init_db("sqlite:///:memory:")
    factory = database_connection.get_session_factory()
    
    assert factory is not None
    assert factory is database_connection._session_factory


def test_get_db_session_context_manager():
    """Test that get_db_session works as context manager."""
    database_connection.init_db("sqlite:///:memory:")
    
    with database_connection.get_db_session() as session:
        assert session is not None
        # Execute a simple query
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_get_db_session_commit_on_success():
    """Test that get_db_session commits on successful execution."""
    database_connection.init_db("sqlite:///:memory:")
    
    # Create a test table
    with database_connection.get_db_session() as session:
        session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)"))
        session.execute(text("INSERT INTO test (value) VALUES ('test')"))
    
    # Verify data was committed
    with database_connection.get_db_session() as session:
        result = session.execute(text("SELECT value FROM test")).scalar()
        assert result == "test"


def test_get_db_session_rollback_on_error():
    """Test that get_db_session rolls back on error."""
    database_connection.init_db("sqlite:///:memory:")
    
    # Create a test table
    with database_connection.get_db_session() as session:
        session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT NOT NULL)"))
    
    # Try to insert invalid data (should rollback)
    try:
        with database_connection.get_db_session() as session:
            session.execute(text("INSERT INTO test (value) VALUES ('valid')"))
            # This should fail due to NOT NULL constraint
            session.execute(text("INSERT INTO test (value) VALUES (NULL)"))
    except Exception:
        pass
    
    # Verify no data was committed
    with database_connection.get_db_session() as session:
        count = session.execute(text("SELECT COUNT(*) FROM test")).scalar()
        assert count == 0


def test_close_db():
    """Test that close_db properly disposes of engine."""
    database_connection.init_db("sqlite:///:memory:")
    assert database_connection._engine is not None
    
    database_connection.close_db()
    
    assert database_connection._engine is None
    assert database_connection._session_factory is None


def test_verify_connection_success():
    """Test verify_connection returns True for valid connection."""
    database_connection.init_db("sqlite:///:memory:")
    
    result = database_connection.verify_connection()
    assert result is True


def test_verify_connection_failure():
    """Test verify_connection returns False when not initialized."""
    result = database_connection.verify_connection()
    assert result is False


def test_sqlite_pragma_settings():
    """Test that SQLite pragma settings are applied."""
    database_connection.init_db("sqlite:///:memory:")
    
    with database_connection.get_db_session() as session:
        # Check foreign keys are enabled
        fk_result = session.execute(text("PRAGMA foreign_keys")).scalar()
        assert fk_result == 1
        
        # Check journal mode (in-memory databases use MEMORY mode, not WAL)
        journal_result = session.execute(text("PRAGMA journal_mode")).scalar()
        assert journal_result.upper() in ("WAL", "MEMORY")


def test_connection_pooling_for_postgresql():
    """Test that PostgreSQL connections use proper pooling settings."""
    # Mock create_engine to verify pooling parameters
    with patch('database_connection.create_engine') as mock_create_engine:
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock()
        mock_engine.connect.return_value.__exit__ = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        database_connection.init_db("postgresql://user:pass@localhost/db")
        
        # Verify create_engine was called with pooling parameters
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs['pool_pre_ping'] is True
        assert call_kwargs['pool_size'] == 10
        assert call_kwargs['max_overflow'] == 20
        assert call_kwargs['pool_recycle'] == 3600
