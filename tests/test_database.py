"""Tests for database functionality"""

from datetime import date, datetime, time

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.connection import create_test_engine, get_db_session
from src.database.models import Base, SourceSystemModel, SLADefinitionModel, FileArrivalModel
from src.database.utils import (
    create_tables,
    drop_tables,
    get_all_source_systems,
    get_source_system,
    save_file_arrival,
    save_source_system,
)
from src.models import FileArrivalEvent, SourceSystem


@pytest.fixture
def test_engine():
    """Create a test database engine"""
    engine = create_test_engine()
    create_tables(engine)
    yield engine
    drop_tables(engine)
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    """Create a test database session"""
    from sqlalchemy.orm import Session
    
    session = Session(bind=test_engine)
    yield session
    session.close()


class TestDatabaseConnection:
    """Test database connection management"""

    def test_create_tables(self, test_engine):
        """Test creating database tables"""
        from sqlalchemy import inspect
        
        # Tables should already be created by fixture
        inspector = inspect(test_engine)
        table_names = inspector.get_table_names()
        
        assert "source_systems" in table_names
        assert "sla_definitions" in table_names
        assert "sla_violations" in table_names
        assert "file_arrivals" in table_names
        assert "configuration_audit" in table_names


class TestSourceSystemModel:
    """Test SourceSystem ORM model"""

    def test_create_source_system(self, test_session):
        """Test creating a source system in database"""
        system = SourceSystemModel(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
            is_active=True,
        )
        test_session.add(system)
        test_session.commit()
        
        # Query it back
        retrieved = test_session.query(SourceSystemModel).filter_by(id="SYS001").first()
        assert retrieved is not None
        assert retrieved.name == "Test System"
        assert retrieved.is_active is True

    def test_source_system_unique_id(self, test_session):
        """Test that source system ID must be unique"""
        system1 = SourceSystemModel(
            id="SYS001",
            name="System 1",
            directory_path="/data/test1",
        )
        system2 = SourceSystemModel(
            id="SYS001",
            name="System 2",
            directory_path="/data/test2",
        )
        
        test_session.add(system1)
        test_session.commit()
        
        test_session.add(system2)
        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_source_system_relationships(self, test_session):
        """Test source system relationships"""
        system = SourceSystemModel(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        test_session.add(system)
        test_session.commit()
        
        # Add SLA definition
        sla = SLADefinitionModel(
            source_system_id="SYS001",
            expected_arrival_time=time(9, 0, 0),
            expected_arrival_window_minutes=30,
            minimum_files_per_day=5,
            effective_from=date(2024, 1, 1),
        )
        test_session.add(sla)
        test_session.commit()
        
        # Check relationship
        retrieved = test_session.query(SourceSystemModel).filter_by(id="SYS001").first()
        assert len(retrieved.sla_definitions) == 1
        assert retrieved.sla_definitions[0].minimum_files_per_day == 5


class TestSLADefinitionModel:
    """Test SLADefinition ORM model"""

    def test_create_sla_definition(self, test_session):
        """Test creating an SLA definition"""
        # First create source system
        system = SourceSystemModel(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        test_session.add(system)
        test_session.commit()
        
        # Create SLA definition
        sla = SLADefinitionModel(
            source_system_id="SYS001",
            expected_arrival_time=time(9, 0, 0),
            expected_arrival_window_minutes=30,
            minimum_files_per_day=5,
            weight=0.8,
            effective_from=date(2024, 1, 1),
        )
        test_session.add(sla)
        test_session.commit()
        
        # Query it back
        retrieved = test_session.query(SLADefinitionModel).first()
        assert retrieved is not None
        assert retrieved.source_system_id == "SYS001"
        assert float(retrieved.weight) == 0.8

    def test_sla_definition_constraints(self, test_session):
        """Test SLA definition constraints"""
        # First create source system
        system = SourceSystemModel(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        test_session.add(system)
        test_session.commit()
        
        # Try to create SLA with invalid weight
        sla = SLADefinitionModel(
            source_system_id="SYS001",
            expected_arrival_time=time(9, 0, 0),
            expected_arrival_window_minutes=30,
            minimum_files_per_day=5,
            weight=1.5,  # Invalid: > 1.0
            effective_from=date(2024, 1, 1),
        )
        test_session.add(sla)
        
        with pytest.raises(IntegrityError):
            test_session.commit()


class TestFileArrivalModel:
    """Test FileArrival ORM model"""

    def test_create_file_arrival(self, test_session):
        """Test creating a file arrival record"""
        # First create source system
        system = SourceSystemModel(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        test_session.add(system)
        test_session.commit()
        
        # Create file arrival
        arrival = FileArrivalModel(
            source_system_id="SYS001",
            filename="test.txt",
            file_path="/data/test/test.txt",
            arrival_timestamp=datetime(2024, 1, 1, 12, 0, 0),
            file_size_bytes=1024,
            checksum="abc123",
        )
        test_session.add(arrival)
        test_session.commit()
        
        # Query it back
        retrieved = test_session.query(FileArrivalModel).first()
        assert retrieved is not None
        assert retrieved.filename == "test.txt"
        assert retrieved.file_size_bytes == 1024

    def test_file_arrival_negative_size_constraint(self, test_session):
        """Test file arrival negative size constraint"""
        # First create source system
        system = SourceSystemModel(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        test_session.add(system)
        test_session.commit()
        
        # Try to create file arrival with negative size
        arrival = FileArrivalModel(
            source_system_id="SYS001",
            filename="test.txt",
            file_path="/data/test/test.txt",
            arrival_timestamp=datetime.now(),
            file_size_bytes=-100,  # Invalid
            checksum="abc123",
        )
        test_session.add(arrival)
        
        with pytest.raises(IntegrityError):
            test_session.commit()


class TestDatabaseUtils:
    """Test database utility functions"""

    def test_save_and_get_source_system(self, test_session):
        """Test saving and retrieving source system"""
        source_system = SourceSystem(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        
        # Save
        save_source_system(test_session, source_system)
        test_session.commit()
        
        # Retrieve
        retrieved = get_source_system(test_session, "SYS001")
        assert retrieved is not None
        assert retrieved.id == "SYS001"
        assert retrieved.name == "Test System"

    def test_get_all_source_systems(self, test_session):
        """Test getting all source systems"""
        # Create multiple systems
        systems = [
            SourceSystem(id="SYS001", name="System 1", directory_path="/data/1"),
            SourceSystem(id="SYS002", name="System 2", directory_path="/data/2", is_active=False),
            SourceSystem(id="SYS003", name="System 3", directory_path="/data/3"),
        ]
        
        for system in systems:
            save_source_system(test_session, system)
        test_session.commit()
        
        # Get all
        all_systems = get_all_source_systems(test_session)
        assert len(all_systems) == 3
        
        # Get active only
        active_systems = get_all_source_systems(test_session, active_only=True)
        assert len(active_systems) == 2

    def test_save_file_arrival(self, test_session):
        """Test saving file arrival event"""
        # First create source system
        source_system = SourceSystem(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        save_source_system(test_session, source_system)
        test_session.commit()
        
        # Create and save file arrival event
        event = FileArrivalEvent(
            source_system_id="SYS001",
            filename="test.txt",
            file_path="/data/test/test.txt",
            arrival_timestamp=datetime(2024, 1, 1, 12, 0, 0),
            file_size_bytes=1024,
            checksum="abc123",
        )
        
        save_file_arrival(test_session, event)
        test_session.commit()
        
        # Verify
        arrival = test_session.query(FileArrivalModel).first()
        assert arrival is not None
        assert arrival.filename == "test.txt"
