"""Tests for simplified SLA services with SQLite"""

from datetime import date, datetime, time, timedelta

import pytest

from src.database.connection import create_test_engine, init_db
from src.database.models import Base, SourceSystemModel, SLADefinitionModel, SLAViolationModel
from src.sla.calculator import ScoreCalculator
from src.sla.evaluator import SLAEvaluator
from src.sla.tracker import ViolationTracker


@pytest.fixture
def test_db_with_sla():
    """Create a test database with SLA definitions"""
    # Create engine and tables
    engine = create_test_engine()
    Base.metadata.create_all(bind=engine)
    
    # Initialize database connection
    init_db(database_url="sqlite:///:memory:")
    
    # Recreate tables on the initialized connection
    from src.database.connection import get_engine, get_db_session
    Base.metadata.create_all(bind=get_engine())
    
    # Create test source systems and SLA definitions
    with get_db_session() as session:
        source_system = SourceSystemModel(
            id="SYS001",
            name="Test System 1",
            directory_path="/test/path1",
            is_active=True,
        )
        session.add(source_system)
        
        sla_def = SLADefinitionModel(
            source_system_id="SYS001",
            expected_arrival_time=time(9, 0, 0),  # 9:00 AM
            expected_arrival_window_minutes=30,  # ±30 minutes
            minimum_files_per_day=5,
            weight=1.0,
            effective_from=date(2024, 1, 1),
            effective_to=None,
        )
        session.add(sla_def)
        session.commit()
    
    yield engine
    
    # Cleanup
    from src.database.connection import close_db
    close_db()


class TestSLAEvaluator:
    """Tests for SLAEvaluator"""
    
    def test_create_evaluator(self):
        """Test creating an SLA evaluator"""
        evaluator = SLAEvaluator()
        assert evaluator is not None
    
    def test_get_sla_definition(self, test_db_with_sla):
        """Test getting SLA definition"""
        evaluator = SLAEvaluator()
        
        sla = evaluator.get_sla_definition("SYS001", date(2024, 1, 15))
        assert sla is not None
        assert sla.source_system_id == "SYS001"
        assert sla.expected_arrival_time == time(9, 0, 0)
        assert sla.expected_arrival_window_minutes == 30
    
    def test_is_within_sla_window(self, test_db_with_sla):
        """Test checking if arrival is within SLA window"""
        evaluator = SLAEvaluator()
        
        sla = evaluator.get_sla_definition("SYS001", date(2024, 1, 15))
        
        # Within window (9:00 AM ± 30 min)
        arrival_on_time = datetime(2024, 1, 15, 9, 0, 0)
        assert evaluator.is_within_sla_window(arrival_on_time, sla) is True
        
        arrival_early = datetime(2024, 1, 15, 8, 45, 0)
        assert evaluator.is_within_sla_window(arrival_early, sla) is True
        
        arrival_late = datetime(2024, 1, 15, 9, 25, 0)
        assert evaluator.is_within_sla_window(arrival_late, sla) is True
        
        # Outside window
        arrival_too_early = datetime(2024, 1, 15, 8, 0, 0)
        assert evaluator.is_within_sla_window(arrival_too_early, sla) is False
        
        arrival_too_late = datetime(2024, 1, 15, 10, 0, 0)
        assert evaluator.is_within_sla_window(arrival_too_late, sla) is False
    
    def test_calculate_lateness(self, test_db_with_sla):
        """Test calculating lateness"""
        evaluator = SLAEvaluator()
        
        sla = evaluator.get_sla_definition("SYS001", date(2024, 1, 15))
        
        # On time
        arrival_on_time = datetime(2024, 1, 15, 9, 0, 0)
        lateness = evaluator.calculate_lateness_minutes(arrival_on_time, sla)
        assert lateness == 0.0
        
        # 15 minutes late
        arrival_late = datetime(2024, 1, 15, 9, 15, 0)
        lateness = evaluator.calculate_lateness_minutes(arrival_late, sla)
        assert lateness == 15.0
        
        # 30 minutes early
        arrival_early = datetime(2024, 1, 15, 8, 30, 0)
        lateness = evaluator.calculate_lateness_minutes(arrival_early, sla)
        assert lateness == -30.0
    
    def test_get_violation_severity(self, test_db_with_sla):
        """Test determining violation severity"""
        evaluator = SLAEvaluator()
        
        sla = evaluator.get_sla_definition("SYS001", date(2024, 1, 15))
        
        # Within window - low severity
        assert evaluator.get_violation_severity(15.0, sla) == "low"
        
        # Just outside window - low severity
        assert evaluator.get_violation_severity(40.0, sla) == "low"
        
        # Medium severity
        assert evaluator.get_violation_severity(60.0, sla) == "medium"
        
        # High severity
        assert evaluator.get_violation_severity(90.0, sla) == "high"
        
        # Critical severity
        assert evaluator.get_violation_severity(150.0, sla) == "critical"


class TestScoreCalculator:
    """Tests for ScoreCalculator"""
    
    def test_create_calculator(self):
        """Test creating a score calculator"""
        calculator = ScoreCalculator()
        assert calculator is not None
    
    def test_calculate_daily_score_no_violations(self, test_db_with_sla):
        """Test calculating daily score with no violations"""
        calculator = ScoreCalculator()
        
        score = calculator.calculate_daily_score("SYS001", date(2024, 1, 15))
        assert score == 100.0
    
    def test_calculate_daily_score_with_violations(self, test_db_with_sla):
        """Test calculating daily score with violations"""
        # Add a violation
        tracker = ViolationTracker()
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 15),
            violation_type="late",
            severity="medium",
        )
        
        calculator = ScoreCalculator()
        score = calculator.calculate_daily_score("SYS001", date(2024, 1, 15))
        
        # Score should be reduced (100 - 10 per violation)
        assert score == 90.0
    
    def test_store_and_retrieve_score(self, test_db_with_sla):
        """Test storing and retrieving scores"""
        calculator = ScoreCalculator()
        
        # Store a score
        calculator.store_daily_score(
            source_system_id="SYS001",
            target_date=date(2024, 1, 15),
            score=95.0,
            total_checks=1,
            passed_checks=1,
        )
        
        # Retrieve it
        stored_score = calculator.get_stored_score("SYS001", date(2024, 1, 15))
        assert stored_score == 95.0
    
    def test_calculate_score_range(self, test_db_with_sla):
        """Test calculating scores for a date range"""
        calculator = ScoreCalculator()
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        
        scores = calculator.calculate_score_range("SYS001", start_date, end_date)
        
        assert len(scores) == 5
        for score_dict in scores:
            assert "date" in score_dict
            assert "score" in score_dict
            assert 0 <= score_dict["score"] <= 100


class TestViolationTracker:
    """Tests for ViolationTracker"""
    
    def test_create_tracker(self):
        """Test creating a violation tracker"""
        tracker = ViolationTracker()
        assert tracker is not None
    
    def test_record_violation(self, test_db_with_sla):
        """Test recording a violation"""
        tracker = ViolationTracker()
        
        violation_id = tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 15),
            violation_type="late",
            expected_value="09:00",
            actual_value="10:00",
            severity="high",
        )
        
        assert violation_id > 0
    
    def test_get_violations(self, test_db_with_sla):
        """Test retrieving violations"""
        tracker = ViolationTracker()
        
        # Record some violations
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 15),
            violation_type="late",
            severity="high",
        )
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 16),
            violation_type="early",
            severity="low",
        )
        
        # Get all violations
        violations = tracker.get_violations(source_system_id="SYS001")
        assert len(violations) == 2
    
    def test_get_violation_count(self, test_db_with_sla):
        """Test getting violation count"""
        tracker = ViolationTracker()
        
        # Record violations
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 15),
            violation_type="late",
            severity="medium",
        )
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 16),
            violation_type="late",
            severity="high",
        )
        
        count = tracker.get_violation_count("SYS001")
        assert count == 2
    
    def test_get_violations_by_severity(self, test_db_with_sla):
        """Test getting violations grouped by severity"""
        tracker = ViolationTracker()
        
        # Record violations with different severities
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 15),
            violation_type="late",
            severity="critical",
        )
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 16),
            violation_type="late",
            severity="high",
        )
        tracker.record_violation(
            source_system_id="SYS001",
            violation_date=date(2024, 1, 17),
            violation_type="late",
            severity="high",
        )
        
        severity_counts = tracker.get_violations_by_severity("SYS001")
        
        assert severity_counts["critical"] == 1
        assert severity_counts["high"] == 2
        assert severity_counts["medium"] == 0
        assert severity_counts["low"] == 0
