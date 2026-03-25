"""Integration tests for file monitoring with database writes"""

import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.database.connection import create_test_engine, init_db
from src.database.models import Base, FileArrivalModel, SourceSystemModel
from src.monitor.database_writer import DatabaseWriter
from src.monitor.watcher import DirectoryWatcher, FileMonitorService


@pytest.fixture
def test_db():
    """Create a test database with source systems"""
    # Create engine and tables
    engine = create_test_engine()
    Base.metadata.create_all(bind=engine)
    
    # Initialize database connection
    init_db(database_url="sqlite:///:memory:")
    
    # Recreate tables on the initialized connection
    from src.database.connection import get_engine, get_db_session
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
        ]
        session.add_all(source_systems)
        session.commit()
    
    yield engine
    
    # Cleanup
    from src.database.connection import close_db
    close_db()


class TestFileMonitoringIntegration:
    """Integration tests for complete file monitoring flow"""
    
    def test_file_detection_and_database_write(self, test_db):
        """Test that file detection triggers database write"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create watcher with database writer
            writer = DatabaseWriter()
            watcher = DirectoryWatcher(
                directory_path=tmpdir,
                source_system_id="SYS001",
                database_writer=writer,
            )
            
            # Start monitoring
            watcher.start_monitoring()
            
            try:
                # Create a test file
                test_file = Path(tmpdir) / "test_file.txt"
                test_file.write_text("test content")
                
                # Wait for file system event to be processed
                time.sleep(0.5)
                
                # Verify file was written to database
                from src.database.connection import get_db_session
                with get_db_session() as session:
                    arrivals = session.query(FileArrivalModel).all()
                    assert len(arrivals) == 1
                    
                    arrival = arrivals[0]
                    assert arrival.source_system_id == "SYS001"
                    assert arrival.filename == "test_file.txt"
                    assert arrival.file_size_bytes > 0
                    assert arrival.checksum is not None
                    
            finally:
                watcher.stop_monitoring()
    
    def test_multiple_files_detection(self, test_db):
        """Test monitoring multiple file arrivals"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file monitor service
            service = FileMonitorService()
            service.add_watcher(
                source_system_id="SYS001",
                directory_path=tmpdir,
            )
            
            # Start monitoring
            service.start_all()
            
            try:
                # Create multiple test files
                for i in range(3):
                    test_file = Path(tmpdir) / f"file_{i}.txt"
                    test_file.write_text(f"content {i}")
                    time.sleep(0.2)  # Small delay between files
                
                # Wait for all events to be processed
                time.sleep(0.5)
                
                # Verify all files were written to database
                from src.database.connection import get_db_session
                with get_db_session() as session:
                    arrivals = session.query(FileArrivalModel).order_by(
                        FileArrivalModel.filename
                    ).all()
                    assert len(arrivals) == 3
                    
                    for i, arrival in enumerate(arrivals):
                        assert arrival.source_system_id == "SYS001"
                        assert arrival.filename == f"file_{i}.txt"
                        
            finally:
                service.stop_all()
    
    def test_file_monitoring_with_callback(self, test_db):
        """Test file monitoring with custom callback"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Track callback invocations
            callback_events = []
            
            def on_file_created(event):
                callback_events.append(event)
            
            # Create watcher with callback
            writer = DatabaseWriter()
            watcher = DirectoryWatcher(
                directory_path=tmpdir,
                source_system_id="SYS001",
                on_file_created=on_file_created,
                database_writer=writer,
            )
            
            # Start monitoring
            watcher.start_monitoring()
            
            try:
                # Create a test file
                test_file = Path(tmpdir) / "callback_test.txt"
                test_file.write_text("callback test content")
                
                # Wait for processing
                time.sleep(0.5)
                
                # Verify callback was invoked
                assert len(callback_events) == 1
                assert callback_events[0].filename == "callback_test.txt"
                
                # Verify database write also happened
                from src.database.connection import get_db_session
                with get_db_session() as session:
                    arrivals = session.query(FileArrivalModel).all()
                    assert len(arrivals) == 1
                    
            finally:
                watcher.stop_monitoring()
