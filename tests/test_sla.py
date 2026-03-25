"""Tests for SLA calculator service"""

from datetime import date, datetime, time, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.models import FileArrivalEvent, SLADefinition
from src.sla.calculator import ScoreCalculator
from src.sla.evaluator import SLAEvaluator
from src.sla.tracker import ViolationTracker


@pytest.fixture
def sample_sla():
    """Create a sample SLA definition"""
    return SLADefinition(
        source_system_id="SYS001",
        expected_arrival_time=time(10, 0, 0),  # 10:00 AM
        tolerance_minutes=30,
        expected_frequency_hours=24,
        violation_weight=1.0,
        is_active=True,
    )


@pytest.fixture
def sample_event_on_time():
    """Create a file arrival event that's on time"""
    return FileArrivalEvent(
        source_system_id="SYS001",
        filename="data.csv",
        file_path="/data/data.csv",
        arrival_timestamp=datetime(2024, 1, 15, 10, 15, 0),  # 10:15 AM (within tolerance)
        file_size_bytes=1024,
        checksum="abc123",
    )


@pytest.fixture
def sample_event_late():
    """Create a file arrival event that's late"""
    return FileArrivalEvent(
        source_system_id="SYS001",
        filename="data.csv",
        file_path="/data/data.csv",
        arrival_timestamp=datetime(2024, 1, 15, 11, 0, 0),  # 11:00 AM (60 min late)
        file_size_bytes=1024,
        checksum="abc123",
    )


class TestSLAEvaluator:
    """Test SLAEvaluator class"""

    def test_create_evaluator(self):
        """Test creating SLA evaluator"""
        evaluator = SLAEvaluator()
        assert evaluator is not None
        assert len(evaluator._sla_cache) == 0

    def test_is_within_sla_compliant(self, sample_event_on_time, sample_sla):
        """Test checking if event is within SLA (compliant case)"""
        evaluator = SLAEvaluator()
        
        is_compliant = evaluator.is_within_sla(sample_event_on_time, sample_sla)
        
        assert is_compliant is True

    def test_is_within_sla_violation(self, sample_event_late, sample_sla):
        """Test checking if event is within SLA (violation case)"""
        evaluator = SLAEvaluator()
        
        is_compliant = evaluator.is_within_sla(sample_event_late, sample_sla)
        
        assert is_compliant is False

    def test_calculate_lateness_on_time(self, sample_event_on_time, sample_sla):
        """Test calculating lateness for on-time event"""
        evaluator = SLAEvaluator()
        
        lateness = evaluator.calculate_lateness_minutes(sample_event_on_time, sample_sla)
        
        assert lateness == 15.0  # 15 minutes late (but within tolerance)

    def test_calculate_lateness_late(self, sample_event_late, sample_sla):
        """Test calculating lateness for late event"""
        evaluator = SLAEvaluator()
        
        lateness = evaluator.calculate_lateness_minutes(sample_event_late, sample_sla)
        
        assert lateness == 60.0  # 60 minutes late

    def test_get_violation_type_compliant(self, sample_event_on_time, sample_sla):
        """Test getting violation type for compliant event"""
        evaluator = SLAEvaluator()
        
        violation_type = evaluator.get_violation_type(sample_event_on_time, sample_sla)
        
        assert violation_type == "compliant"

    def test_get_violation_type_late(self, sample_event_late, sample_sla):
        """Test getting violation type for late event"""
        evaluator = SLAEvaluator()
        
        violation_type = evaluator.get_violation_type(sample_event_late, sample_sla)
        
        assert violation_type == "late"

    def test_get_violation_type_early(self, sample_sla):
        """Test getting violation type for early event"""
        evaluator = SLAEvaluator()
        
        # Event arrives 2 hours early (outside tolerance)
        early_event = FileArrivalEvent(
            source_system_id="SYS001",
            filename="data.csv",
            file_path="/data/data.csv",
            arrival_timestamp=datetime(2024, 1, 15, 8, 0, 0),  # 8:00 AM
            file_size_bytes=1024,
            checksum="abc123",
        )
        
        violation_type = evaluator.get_violation_type(early_event, sample_sla)
        
        assert violation_type == "early"

    def test_get_violation_severity_none(self, sample_event_on_time, sample_sla):
        """Test getting severity for compliant event"""
        evaluator = SLAEvaluator()
        
        severity = evaluator.get_violation_severity(sample_event_on_time, sample_sla)
        
        assert severity == "none"

    def test_get_violation_severity_low(self, sample_sla):
        """Test getting severity for low violation"""
        evaluator = SLAEvaluator()
        
        # 45 minutes late (15 min outside tolerance)
        event = FileArrivalEvent(
            source_system_id="SYS001",
            filename="data.csv",
            file_path="/data/data.csv",
            arrival_timestamp=datetime(2024, 1, 15, 10, 45, 0),
            file_size_bytes=1024,
            checksum="abc123",
        )
        
        severity = evaluator.get_violation_severity(event, sample_sla)
        
        assert severity == "low"

    def test_get_violation_severity_critical(self, sample_sla):
        """Test getting severity for critical violation"""
        evaluator = SLAEvaluator()
        
        # 3 hours late (way outside tolerance)
        event = FileArrivalEvent(
            source_system_id="SYS001",
            filename="data.csv",
            file_path="/data/data.csv",
            arrival_timestamp=datetime(2024, 1, 15, 13, 0, 0),
            file_size_bytes=1024,
            checksum="abc123",
        )
        
        severity = evaluator.get_violation_severity(event, sample_sla)
        
        assert severity == "critical"


class TestScoreCalculator:
    """Test ScoreCalculator class"""

    def test_create_calculator(self):
        """Test creating score calculator"""
        calculator = ScoreCalculator()
        assert calculator is not None

    @patch('src.sla.calculator.get_db_session')
    def test_calculate_daily_score_no_violations(self, mock_session):
        """Test calculating daily score with no violations"""
        # Mock database session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        
        calculator = ScoreCalculator()
        score = calculator.calculate_daily_score("SYS001", date(2024, 1, 15))
        
        assert score.score == 100.0
        assert score.total_checks == 1
        assert score.passed_checks == 1

    @patch('src.sla.calculator.get_db_session')
    def test_calculate_daily_score_with_violations(self, mock_session):
        """Test calculating daily score with violations"""
        # Mock database session with violations
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        
        # Create mock violations
        mock_violation = MagicMock()
        mock_violation.violation_weight = 1.0
        mock_session_instance.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_violation]
        
        calculator = ScoreCalculator()
        score = calculator.calculate_daily_score("SYS001", date(2024, 1, 15))
        
        # Score should be 0 (1 violation with weight 1.0, 1 total check)
        assert score.score == 0.0
        assert score.total_checks == 1
        assert score.passed_checks == 0

    @patch('src.sla.calculator.ScoreCalculator.calculate_daily_score')
    def test_calculate_monthly_score(self, mock_daily_score):
        """Test calculating monthly score"""
        # Mock daily scores
        from src.models import SLAScore
        
        mock_daily_score.return_value = SLAScore(
            source_system_id="SYS001",
            score_date=date(2024, 1, 1),
            score=95.0,
            total_checks=1,
            passed_checks=1,
        )
        
        calculator = ScoreCalculator()
        monthly_score = calculator.calculate_monthly_score("SYS001", 2024, 1)
        
        assert monthly_score.score > 0
        assert monthly_score.score <= 100
        assert monthly_score.source_system_id == "SYS001"

    @patch('src.sla.calculator.ScoreCalculator.calculate_daily_score')
    def test_calculate_score_range(self, mock_daily_score):
        """Test calculating scores for date range"""
        from src.models import SLAScore
        
        mock_daily_score.return_value = SLAScore(
            source_system_id="SYS001",
            score_date=date(2024, 1, 1),
            score=100.0,
            total_checks=1,
            passed_checks=1,
        )
        
        calculator = ScoreCalculator()
        scores = calculator.calculate_score_range(
            "SYS001",
            date(2024, 1, 1),
            date(2024, 1, 5),
        )
        
        assert len(scores) == 5  # 5 days
        assert all(s.score == 100.0 for s in scores)


class TestViolationTracker:
    """Test ViolationTracker class"""

    def test_create_tracker(self):
        """Test creating violation tracker"""
        tracker = ViolationTracker()
        assert tracker is not None

    @patch('src.sla.tracker.get_db_session')
    def test_record_violation(self, mock_session, sample_event_late, sample_sla):
        """Test recording a violation"""
        # Mock database session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        
        tracker = ViolationTracker()
        violation = tracker.record_violation(
            event=sample_event_late,
            sla=sample_sla,
            violation_type="late",
            severity="high",
            lateness_minutes=60.0,
        )
        
        assert violation.source_system_id == "SYS001"
        assert violation.violation_type == "late"
        assert violation.severity == "high"
        assert violation.lateness_minutes == 60.0
        
        # Verify database add was called
        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()

    @patch('src.sla.tracker.get_db_session')
    def test_get_violations(self, mock_session):
        """Test querying violations"""
        # Mock database session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        
        # Create mock violation
        mock_violation = MagicMock()
        mock_violation.source_system_id = "SYS001"
        mock_violation.violation_timestamp = datetime(2024, 1, 15, 11, 0, 0)
        mock_violation.violation_type = "late"
        mock_violation.severity = "high"
        mock_violation.expected_time = datetime(2024, 1, 15, 10, 0, 0)
        mock_violation.actual_time = datetime(2024, 1, 15, 11, 0, 0)
        mock_violation.lateness_minutes = 60.0
        mock_violation.violation_weight = 1.0
        
        mock_session_instance.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_violation]
        
        tracker = ViolationTracker()
        violations = tracker.get_violations(source_system_id="SYS001")
        
        assert len(violations) == 1
        assert violations[0].source_system_id == "SYS001"
        assert violations[0].violation_type == "late"

    @patch('src.sla.tracker.get_db_session')
    def test_get_violation_count(self, mock_session):
        """Test getting violation count"""
        # Mock database session
        mock_session_instance = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter_by.return_value.count.return_value = 5
        
        tracker = ViolationTracker()
        count = tracker.get_violation_count("SYS001")
        
        assert count == 5

    @patch('src.sla.tracker.ViolationTracker.get_violations')
    def test_get_violations_by_severity(self, mock_get_violations):
        """Test getting violations grouped by severity"""
        from src.models import SLAViolation
        
        # Mock violations with different severities
        mock_get_violations.return_value = [
            SLAViolation(
                source_system_id="SYS001",
                violation_timestamp=datetime(2024, 1, 15, 11, 0, 0),
                violation_type="late",
                severity="critical",
                expected_time=datetime(2024, 1, 15, 10, 0, 0),
                actual_time=datetime(2024, 1, 15, 11, 0, 0),
                lateness_minutes=60.0,
                violation_weight=1.0,
            ),
            SLAViolation(
                source_system_id="SYS001",
                violation_timestamp=datetime(2024, 1, 15, 10, 45, 0),
                violation_type="late",
                severity="low",
                expected_time=datetime(2024, 1, 15, 10, 0, 0),
                actual_time=datetime(2024, 1, 15, 10, 45, 0),
                lateness_minutes=45.0,
                violation_weight=1.0,
            ),
        ]
        
        tracker = ViolationTracker()
        severity_counts = tracker.get_violations_by_severity("SYS001")
        
        assert severity_counts["critical"] == 1
        assert severity_counts["low"] == 1
        assert severity_counts["high"] == 0
        assert severity_counts["medium"] == 0
