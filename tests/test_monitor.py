"""Tests for file monitoring service"""

import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.models import FileArrivalEvent, SourceSystem
from src.monitor.config_manager import ConfigurationManager
from src.monitor.watcher import DirectoryWatcher, FileMonitorService


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_callback():
    """Create a mock callback function"""
    return MagicMock()


class TestDirectoryWatcher:
    """Test DirectoryWatcher class"""

    def test_create_watcher(self, temp_directory):
        """Test creating a directory watcher"""
        watcher = DirectoryWatcher(
            directory_path=temp_directory,
            source_system_id="SYS001",
        )
        
        assert watcher.source_system_id == "SYS001"
        assert watcher.directory_path == Path(temp_directory)
        assert not watcher.is_monitoring

    def test_watcher_invalid_directory(self):
        """Test watcher with invalid directory"""
        with pytest.raises(ValueError, match="does not exist"):
            DirectoryWatcher(
                directory_path="/nonexistent/directory",
                source_system_id="SYS001",
            )

    def test_watcher_not_a_directory(self, temp_directory):
        """Test watcher with file instead of directory"""
        # Create a file
        file_path = Path(temp_directory) / "test.txt"
        file_path.write_text("test")
        
        with pytest.raises(ValueError, match="not a directory"):
            DirectoryWatcher(
                directory_path=str(file_path),
                source_system_id="SYS001",
            )

    def test_start_stop_monitoring(self, temp_directory):
        """Test starting and stopping monitoring"""
        watcher = DirectoryWatcher(
            directory_path=temp_directory,
            source_system_id="SYS001",
        )
        
        # Start monitoring
        watcher.start_monitoring()
        assert watcher.is_monitoring
        
        # Stop monitoring
        watcher.stop_monitoring()
        assert not watcher.is_monitoring

    def test_file_detection(self, temp_directory, mock_callback):
        """Test file detection when a file is created"""
        watcher = DirectoryWatcher(
            directory_path=temp_directory,
            source_system_id="SYS001",
            on_file_created=mock_callback,
        )
        
        watcher.start_monitoring()
        
        # Create a file
        test_file = Path(temp_directory) / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Wait for file system event to be processed
        time.sleep(0.5)
        
        # Check callback was called
        assert mock_callback.called
        
        # Get the event that was passed to callback
        event = mock_callback.call_args[0][0]
        assert isinstance(event, FileArrivalEvent)
        assert event.source_system_id == "SYS001"
        assert event.filename == "test.txt"
        assert event.file_size_bytes > 0
        
        watcher.stop_monitoring()

    def test_create_file_arrival_event(self, temp_directory):
        """Test creating FileArrivalEvent from file"""
        watcher = DirectoryWatcher(
            directory_path=temp_directory,
            source_system_id="SYS001",
        )
        
        # Create a test file
        test_file = Path(temp_directory) / "test.txt"
        test_content = "Test content"
        test_file.write_text(test_content)
        
        # Create event
        event = watcher._create_file_arrival_event(str(test_file))
        
        assert event.source_system_id == "SYS001"
        assert event.filename == "test.txt"
        assert event.file_size_bytes == len(test_content)
        assert event.checksum != "unknown"
        assert isinstance(event.arrival_timestamp, datetime)

    def test_calculate_checksum(self, temp_directory):
        """Test checksum calculation"""
        watcher = DirectoryWatcher(
            directory_path=temp_directory,
            source_system_id="SYS001",
        )
        
        # Create a test file
        test_file = Path(temp_directory) / "test.txt"
        test_file.write_text("Test content")
        
        # Calculate checksum
        checksum = watcher._calculate_checksum(str(test_file))
        
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
        assert checksum != "unknown"
        
        # Same content should produce same checksum
        checksum2 = watcher._calculate_checksum(str(test_file))
        assert checksum == checksum2


class TestFileMonitorService:
    """Test FileMonitorService class"""

    def test_create_service(self):
        """Test creating file monitor service"""
        service = FileMonitorService()
        assert len(service.watchers) == 0

    def test_add_watcher(self, temp_directory):
        """Test adding a watcher"""
        service = FileMonitorService()
        
        watcher = service.add_watcher(
            source_system_id="SYS001",
            directory_path=temp_directory,
        )
        
        assert watcher.source_system_id == "SYS001"
        assert "SYS001" in service.watchers

    def test_add_duplicate_watcher(self, temp_directory):
        """Test adding duplicate watcher raises error"""
        service = FileMonitorService()
        
        service.add_watcher(
            source_system_id="SYS001",
            directory_path=temp_directory,
        )
        
        with pytest.raises(ValueError, match="already exists"):
            service.add_watcher(
                source_system_id="SYS001",
                directory_path=temp_directory,
            )

    def test_remove_watcher(self, temp_directory):
        """Test removing a watcher"""
        service = FileMonitorService()
        
        service.add_watcher(
            source_system_id="SYS001",
            directory_path=temp_directory,
        )
        
        assert "SYS001" in service.watchers
        
        service.remove_watcher("SYS001")
        
        assert "SYS001" not in service.watchers

    def test_start_stop_all(self, temp_directory):
        """Test starting and stopping all watchers"""
        service = FileMonitorService()
        
        # Add multiple watchers
        service.add_watcher("SYS001", temp_directory)
        
        # Start all
        service.start_all()
        
        # Check all are monitoring
        for watcher in service.watchers.values():
            assert watcher.is_monitoring
        
        # Stop all
        service.stop_all()
        
        # Check all stopped
        for watcher in service.watchers.values():
            assert not watcher.is_monitoring

    def test_get_watcher(self, temp_directory):
        """Test getting a watcher by ID"""
        service = FileMonitorService()
        
        service.add_watcher("SYS001", temp_directory)
        
        watcher = service.get_watcher("SYS001")
        assert watcher is not None
        assert watcher.source_system_id == "SYS001"
        
        # Non-existent watcher
        assert service.get_watcher("SYS999") is None

    def test_get_active_watchers(self, temp_directory):
        """Test getting active watchers"""
        service = FileMonitorService()
        
        service.add_watcher("SYS001", temp_directory)
        
        # No active watchers initially
        assert len(service.get_active_watchers()) == 0
        
        # Start monitoring
        service.start_all()
        
        # Now should have active watchers
        active = service.get_active_watchers()
        assert len(active) == 1
        assert "SYS001" in active


class TestConfigurationManager:
    """Test ConfigurationManager class"""

    def test_create_manager(self):
        """Test creating configuration manager"""
        manager = ConfigurationManager()
        assert manager.source_system_count == 0

    def test_load_from_dict(self):
        """Test loading configuration from dictionary"""
        manager = ConfigurationManager()
        
        config = {
            "/data/sys1": "SYS001",
            "/data/sys2": "SYS002",
        }
        
        manager.load_from_dict(config)
        
        assert manager.source_system_count == 2
        assert manager.get_source_system_id("/data/sys1") == "SYS001"
        assert manager.get_source_system_id("/data/sys2") == "SYS002"

    def test_get_source_system_id(self):
        """Test getting source system ID by directory"""
        manager = ConfigurationManager()
        
        config = {"/data/sys1": "SYS001"}
        manager.load_from_dict(config)
        
        assert manager.get_source_system_id("/data/sys1") == "SYS001"
        assert manager.get_source_system_id("/data/unknown") is None

    def test_get_source_system(self):
        """Test getting source system by ID"""
        manager = ConfigurationManager()
        
        config = {"/data/sys1": "SYS001"}
        manager.load_from_dict(config)
        
        system = manager.get_source_system("SYS001")
        assert system is not None
        assert system.id == "SYS001"
        
        assert manager.get_source_system("SYS999") is None

    def test_get_all_directories(self):
        """Test getting all directories"""
        manager = ConfigurationManager()
        
        config = {
            "/data/sys1": "SYS001",
            "/data/sys2": "SYS002",
        }
        manager.load_from_dict(config)
        
        directories = manager.get_all_directories()
        assert len(directories) == 2
        assert "/data/sys1" in directories
        assert "/data/sys2" in directories

    def test_get_all_source_systems(self):
        """Test getting all source systems"""
        manager = ConfigurationManager()
        
        config = {
            "/data/sys1": "SYS001",
            "/data/sys2": "SYS002",
        }
        manager.load_from_dict(config)
        
        systems = manager.get_all_source_systems()
        assert len(systems) == 2
        assert all(isinstance(s, SourceSystem) for s in systems)

    def test_validate_directory(self, temp_directory):
        """Test directory validation"""
        manager = ConfigurationManager()
        
        # Valid directory
        assert manager.validate_directory(temp_directory) is True
        
        # Invalid directory
        assert manager.validate_directory("/nonexistent/directory") is False

    def test_validate_all_directories(self, temp_directory):
        """Test validating all directories"""
        manager = ConfigurationManager()
        
        config = {
            temp_directory: "SYS001",
            "/nonexistent": "SYS002",
        }
        manager.load_from_dict(config)
        
        results = manager.validate_all_directories()
        
        assert results[temp_directory] is True
        assert results["/nonexistent"] is False

    def test_add_remove_source_system(self):
        """Test adding and removing source systems"""
        manager = ConfigurationManager()
        
        system = SourceSystem(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        
        # Add
        manager.add_source_system(system)
        assert manager.source_system_count == 1
        assert manager.get_source_system("SYS001") is not None
        
        # Remove
        manager.remove_source_system("SYS001")
        assert manager.source_system_count == 0
        assert manager.get_source_system("SYS001") is None

    @given(
        system_count=st.integers(min_value=1, max_value=20),
    )
    def test_property_source_system_count(self, system_count: int):
        """Property test: Source system count should match added systems"""
        manager = ConfigurationManager()
        
        # Add systems
        for i in range(system_count):
            system = SourceSystem(
                id=f"SYS{i:03d}",
                name=f"System {i}",
                directory_path=f"/data/sys{i}",
            )
            manager.add_source_system(system)
        
        assert manager.source_system_count == system_count
        assert len(manager.get_all_source_systems()) == system_count
