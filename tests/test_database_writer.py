"""Tests for database writer"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.database.connection import create_test_engine, init_db
from src.database.models import Base, FileArrivalModel
from src.database.utils import create_tables
from src.models import FileArrivalEvent
from src.monitor.database_writer import DatabaseWriter


@pytest.fixture
def test_db():
    """Create a test database with source systems"""
    # Create engine and tables
    engine = create_test_engine()
    Base.metadata.create_all(bind=engine)
    
    # Initialize database connection with the same in-memory database
    init_db(database_url="sqlite:///:memory:")
    
    # Recreate tables on the initialized connection
    from src.database.connection import get_engine, get_db_session
    from src.database.models import SourceSystemModel
    Base.metadata.create_all(bind=get_engine())
    
    # Create test source systems
    with get_db_session() as session:
        source_systems = [
            SourceSystemModel(
                id="SYS001",
                name="Test System 1",
                directory_path="/test/path1",
                is_active=True,
            ),
            SourceSystemModel(
                id="SYS002",
                name="Test System 2",
                directory_path="/test/path2",
                is_active=True,
            ),
        ]
        session.add_all(source_systems)
        session.commit()
    
    yield engine
    
    # Cleanup
    from src.database.connection import close_db
    close_db()


@pytest.fixture
def sample_event():
    """Create a sample file arrival event"""
    return FileArrivalEvent(
        source_system_id="SYS001",
        filename="test_file.txt",
        file_path="/path/to/test_file.txt",
        arrival_timestamp=datetime(2024, 1, 15, 10, 30, 0),
        file_size_bytes=1024,
        checksum="abc123def456",
    )


class TestDatabaseWriter:
    """Tests for DatabaseWriter class"""
    
    def test_create_writer(self):
        """Test creating a database writer"""
        writer = DatabaseWriter()
        assert writer is not None
        assert writer.max_retries == 3
    
    def test_create_writer_custom_retries(self):
        """Test creating a database writer with custom retries"""
        writer = DatabaseWriter(max_retries=5)
        assert writer.max_retries == 5
    
    def test_write_file_arrival(self, test_db, sample_event):
        """Test writing a file arrival event"""
        writer = DatabaseWriter()
        
        # Write event
        success = writer.write_file_arrival(sample_event)
        assert success is True
        
        # Verify it was written
        from src.database.connection import get_db_session
        with get_db_session() as session:
            arrivals = session.query(FileArrivalModel).all()
            assert len(arrivals) == 1
            
            arrival = arrivals[0]
            assert arrival.source_system_id == "SYS001"
            assert arrival.filename == "test_file.txt"
            assert arrival.file_size_bytes == 1024
            assert arrival.checksum == "abc123def456"
    
    def test_write_multiple_events(self, test_db):
        """Test writing multiple file arrival events"""
        writer = DatabaseWriter()
        
        # Create multiple events
        events = [
            FileArrivalEvent(
                source_system_id="SYS001",
                filename=f"file_{i}.txt",
                file_path=f"/path/to/file_{i}.txt",
                arrival_timestamp=datetime(2024, 1, 15, 10, 30, i),
                file_size_bytes=1024 * i,
                checksum=f"checksum_{i}",
            )
            for i in range(1, 6)
        ]
        
        # Write all events
        for event in events:
            success = writer.write_file_arrival(event)
            assert success is True
        
        # Verify all were written
        from src.database.connection import get_db_session
        with get_db_session() as session:
            arrivals = session.query(FileArrivalModel).all()
            assert len(arrivals) == 5
    
    def test_write_batch(self, test_db):
        """Test batch writing of file arrival events"""
        writer = DatabaseWriter()
        
        # Create multiple events
        events = [
            FileArrivalEvent(
                source_system_id="SYS001",
                filename=f"file_{i}.txt",
                file_path=f"/path/to/file_{i}.txt",
                arrival_timestamp=datetime(2024, 1, 15, 10, 30, i),
                file_size_bytes=1024 * i,
                checksum=f"checksum_{i}",
            )
            for i in range(1, 11)
        ]
        
        # Write batch
        count = writer.write_batch(events)
        assert count == 10
        
        # Verify all were written
        from src.database.connection import get_db_session
        with get_db_session() as session:
            arrivals = session.query(FileArrivalModel).all()
            assert len(arrivals) == 10
    
    def test_write_batch_empty(self, test_db):
        """Test batch writing with empty list"""
        writer = DatabaseWriter()
        
        count = writer.write_batch([])
        assert count == 0
    
    def test_write_with_processed_timestamp(self, test_db, sample_event):
        """Test that processed_at timestamp is set automatically"""
        writer = DatabaseWriter()
        
        # Write event
        success = writer.write_file_arrival(sample_event)
        assert success is True
        
        # Verify processed_at is set
        from src.database.connection import get_db_session
        with get_db_session() as session:
            arrival = session.query(FileArrivalModel).first()
            assert arrival.processed_at is not None
            assert isinstance(arrival.processed_at, datetime)


class TestDatabaseWriterIntegration:
    """Integration tests for database writer with file watcher"""
    
    def test_watcher_with_database_writer(self, test_db):
        """Test that watcher can use database writer"""
        from src.monitor.watcher import DirectoryWatcher
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = DatabaseWriter()
            
            # Create watcher with database writer
            watcher = DirectoryWatcher(
                directory_path=tmpdir,
                source_system_id="SYS001",
                database_writer=writer,
            )
            
            assert watcher.database_writer is writer
            
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            # Manually trigger file creation event
            event = watcher._create_file_arrival_event(str(test_file))
            
            # Write to database
            success = writer.write_file_arrival(event)
            assert success is True
            
            # Verify it was written
            from src.database.connection import get_db_session
            with get_db_session() as session:
                arrivals = session.query(FileArrivalModel).all()
                assert len(arrivals) == 1
                assert arrivals[0].filename == "test.txt"
