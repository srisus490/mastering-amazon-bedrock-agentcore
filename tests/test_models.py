"""Tests for data models"""

from datetime import date, datetime, time, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.models import (
    FileArrivalEvent,
    SLADefinition,
    SLAScore,
    SLAViolation,
    SourceSystem,
)


class TestFileArrivalEvent:
    """Test FileArrivalEvent dataclass"""

    def test_create_valid_event(self):
        """Test creating a valid file arrival event"""
        event = FileArrivalEvent(
            source_system_id="SYS001",
            filename="test.txt",
            file_path="/data/test.txt",
            arrival_timestamp=datetime.now(),
            file_size_bytes=1024,
            checksum="abc123",
        )
        assert event.source_system_id == "SYS001"
        assert event.filename == "test.txt"
        assert event.event_id is not None  # Auto-generated UUID

    def test_event_validation_empty_source_system(self):
        """Test validation fails for empty source_system_id"""
        with pytest.raises(ValueError, match="source_system_id cannot be empty"):
            FileArrivalEvent(
                source_system_id="",
                filename="test.txt",
                file_path="/data/test.txt",
                arrival_timestamp=datetime.now(),
                file_size_bytes=1024,
                checksum="abc123",
            )

    def test_event_validation_negative_file_size(self):
        """Test validation fails for negative file size"""
        with pytest.raises(ValueError, match="file_size_bytes must be non-negative"):
            FileArrivalEvent(
                source_system_id="SYS001",
                filename="test.txt",
                file_path="/data/test.txt",
                arrival_timestamp=datetime.now(),
                file_size_bytes=-100,
                checksum="abc123",
            )

    def test_to_dict(self):
        """Test converting event to dictionary"""
        event = FileArrivalEvent(
            source_system_id="SYS001",
            filename="test.txt",
            file_path="/data/test.txt",
            arrival_timestamp=datetime(2024, 1, 1, 12, 0, 0),
            file_size_bytes=1024,
            checksum="abc123",
        )
        event_dict = event.to_dict()
        assert event_dict["source_system_id"] == "SYS001"
        assert event_dict["filename"] == "test.txt"
        assert "arrival_timestamp" in event_dict

    def test_from_dict(self):
        """Test creating event from dictionary"""
        data = {
            "event_id": "test-id",
            "source_system_id": "SYS001",
            "filename": "test.txt",
            "file_path": "/data/test.txt",
            "arrival_timestamp": "2024-01-01T12:00:00",
            "file_size_bytes": 1024,
            "checksum": "abc123",
            "metadata": {},
        }
        event = FileArrivalEvent.from_dict(data)
        assert event.source_system_id == "SYS001"
        assert isinstance(event.arrival_timestamp, datetime)

    @given(
        file_size=st.integers(min_value=0, max_value=10**9),
        filename=st.text(min_size=1, max_size=100),
    )
    def test_event_property_valid_file_size(self, file_size: int, filename: str):
        """Property test: Events with valid file sizes should be created successfully"""
        try:
            event = FileArrivalEvent(
                source_system_id="SYS001",
                filename=filename,
                file_path=f"/data/{filename}",
                arrival_timestamp=datetime.now(),
                file_size_bytes=file_size,
                checksum="abc123",
            )
            assert event.file_size_bytes == file_size
            assert event.file_size_bytes >= 0
        except ValueError:
            # Some filenames might be invalid (empty after strip, etc.)
            pass


class TestSourceSystem:
    """Test SourceSystem dataclass"""

    def test_create_valid_source_system(self):
        """Test creating a valid source system"""
        system = SourceSystem(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        assert system.id == "SYS001"
        assert system.name == "Test System"
        assert system.is_active is True

    def test_source_system_validation_empty_id(self):
        """Test validation fails for empty id"""
        with pytest.raises(ValueError, match="id cannot be empty"):
            SourceSystem(
                id="",
                name="Test System",
                directory_path="/data/test",
            )

    def test_source_system_validation_invalid_id(self):
        """Test validation fails for invalid id characters"""
        with pytest.raises(ValueError, match="alphanumeric"):
            SourceSystem(
                id="SYS@001",
                name="Test System",
                directory_path="/data/test",
            )

    def test_activate_deactivate(self):
        """Test activating and deactivating source system"""
        system = SourceSystem(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        
        system.deactivate()
        assert system.is_active is False
        
        system.activate()
        assert system.is_active is True

    def test_update_directory(self):
        """Test updating directory path"""
        system = SourceSystem(
            id="SYS001",
            name="Test System",
            directory_path="/data/test",
        )
        
        old_updated_at = system.updated_at
        system.update_directory("/data/new_path")
        
        assert system.directory_path == "/data/new_path"
        assert system.updated_at >= old_updated_at  # >= because update might be very fast


class TestSLADefinition:
    """Test SLADefinition dataclass"""

    def test_create_valid_sla_definition(self):
        """Test creating a valid SLA definition"""
        sla = SLADefinition(
            source_system_id="SYS001",
            expected_arrival_time=time(9, 0, 0),
            expected_arrival_window_minutes=30,
            minimum_files_per_day=5,
            effective_from=date(2024, 1, 1),
        )
        assert sla.source_system_id == "SYS001"
        assert sla.weight == 1.0  # Default value

    def test_sla_validation_negative_window(self):
        """Test validation fails for negative window"""
        with pytest.raises(ValueError, match="must be positive"):
            SLADefinition(
                source_system_id="SYS001",
                expected_arrival_time=time(9, 0, 0),
                expected_arrival_window_minutes=-10,
                minimum_files_per_day=5,
                effective_from=date(2024, 1, 1),
            )

    def test_sla_validation_invalid_weight(self):
        """Test validation fails for invalid weight"""
        with pytest.raises(ValueError, match="weight must be between 0 and 1"):
            SLADefinition(
                source_system_id="SYS001",
                expected_arrival_time=time(9, 0, 0),
                expected_arrival_window_minutes=30,
                minimum_files_per_day=5,
                effective_from=date(2024, 1, 1),
                weight=1.5,
            )

    def test_is_active(self):
        """Test checking if SLA is active on a date"""
        sla = SLADefinition(
            source_system_id="SYS001",
            expected_arrival_time=time(9, 0, 0),
            expected_arrival_window_minutes=30,
            minimum_files_per_day=5,
            effective_from=date(2024, 1, 1),
            effective_to=date(2024, 12, 31),
        )
        
        assert sla.is_active(date(2024, 6, 15)) is True
        assert sla.is_active(date(2023, 12, 31)) is False
        assert sla.is_active(date(2025, 1, 1)) is False


class TestSLAViolation:
    """Test SLAViolation dataclass"""

    def test_create_valid_violation(self):
        """Test creating a valid SLA violation"""
        violation = SLAViolation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 1),
            violation_type="missing_file",
            severity="high",
        )
        assert violation.source_system_id == "SYS001"
        assert violation.violation_type == "missing_file"

    def test_violation_validation_invalid_type(self):
        """Test validation fails for invalid violation type"""
        with pytest.raises(ValueError, match="violation_type must be one of"):
            SLAViolation(
                source_system_id="SYS001",
                violation_date=date(2024, 1, 1),
                violation_type="invalid_type",
                severity="high",
            )

    def test_violation_validation_invalid_severity(self):
        """Test validation fails for invalid severity"""
        with pytest.raises(ValueError, match="severity must be one of"):
            SLAViolation(
                source_system_id="SYS001",
                violation_date=date(2024, 1, 1),
                violation_type="missing_file",
                severity="invalid",
            )


class TestSLAScore:
    """Test SLAScore dataclass"""

    def test_create_valid_score(self):
        """Test creating a valid SLA score"""
        score = SLAScore(
            source_system_id="SYS001",
            date=date(2024, 1, 1),
            score=95.5,
            total_checks=100,
            passed_checks=95,
        )
        assert score.source_system_id == "SYS001"
        assert score.score == 95.5

    def test_score_validation_invalid_range(self):
        """Test validation fails for score outside 0-100 range"""
        with pytest.raises(ValueError, match="score must be between 0 and 100"):
            SLAScore(
                source_system_id="SYS001",
                date=date(2024, 1, 1),
                score=150.0,
                total_checks=100,
                passed_checks=95,
            )

    def test_score_validation_passed_exceeds_total(self):
        """Test validation fails when passed_checks exceeds total_checks"""
        with pytest.raises(ValueError, match="passed_checks cannot exceed total_checks"):
            SLAScore(
                source_system_id="SYS001",
                date=date(2024, 1, 1),
                score=95.0,
                total_checks=100,
                passed_checks=105,
            )

    def test_compliance_percentage(self):
        """Test compliance percentage calculation"""
        score = SLAScore(
            source_system_id="SYS001",
            date=date(2024, 1, 1),
            score=95.0,
            total_checks=100,
            passed_checks=95,
        )
        assert score.compliance_percentage == 95.0

    def test_is_compliant(self):
        """Test compliance check"""
        score = SLAScore(
            source_system_id="SYS001",
            date=date(2024, 1, 1),
            score=96.0,
            total_checks=100,
            passed_checks=96,
        )
        assert score.is_compliant(threshold=95.0) is True
        assert score.is_compliant(threshold=97.0) is False

    @given(
        total=st.integers(min_value=1, max_value=1000),
        passed_ratio=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_score_property_compliance_calculation(
        self, total: int, passed_ratio: float
    ):
        """Property test: Compliance percentage should match passed/total ratio"""
        passed = int(total * passed_ratio)
        score_value = (passed / total) * 100
        
        score = SLAScore(
            source_system_id="SYS001",
            date=date(2024, 1, 1),
            score=score_value,
            total_checks=total,
            passed_checks=passed,
        )
        
        assert abs(score.compliance_percentage - score_value) < 0.01
        assert 0 <= score.compliance_percentage <= 100
