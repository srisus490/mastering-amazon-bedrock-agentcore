"""Test SLA tracking functionality"""

from datetime import date, datetime, time

from src.database.connection import init_db, get_db_session
from src.database.models import SLADefinitionModel, SourceSystemModel
from src.sla.calculator import ScoreCalculator
from src.sla.evaluator import SLAEvaluator
from src.sla.tracker import ViolationTracker

def test_sla_tracking():
    """Test SLA evaluation and scoring"""
    
    init_db()
    
    print("Testing SLA Tracking...")
    print("=" * 50)
    
    # Create test system with SLA
    with get_db_session() as session:
        system = session.query(SourceSystemModel).filter_by(id="SYS001").first()
        if system:
            print(f"✅ Found system: {system.name}")
        
        sla = session.query(SLADefinitionModel).filter_by(
            source_system_id="SYS001"
        ).first()
        
        if sla:
            _ = (sla.id, sla.expected_arrival_time, sla.expected_arrival_window_minutes)
            session.expunge(sla)
            print(f"✅ Found SLA: Expected at {sla.expected_arrival_time} ±{sla.expected_arrival_window_minutes} min")
    
    # Test SLA Evaluator
    print("\n1. Testing SLA Evaluator...")
    evaluator = SLAEvaluator()
    
    sla_def = evaluator.get_sla_definition("SYS001", date.today())
    if sla_def:
        print(f"   ✅ SLA definition retrieved")
        
        # Test time window check
        test_time = datetime.combine(date.today(), time(9, 15, 0))
        is_compliant = evaluator.is_within_sla_window(test_time, sla_def)
        print(f"   ✅ Window check: {is_compliant}")
        
        # Test lateness calculation
        lateness = evaluator.calculate_lateness_minutes(test_time, sla_def)
        print(f"   ✅ Lateness: {lateness} minutes")
    
    # Test Score Calculator
    print("\n2. Testing Score Calculator...")
    calculator = ScoreCalculator()
    
    score = calculator.calculate_daily_score("SYS001", date.today())
    print(f"   ✅ Daily score: {score}/100")
    
    # Store score
    calculator.store_daily_score("SYS001", date.today(), score, 1, 1)
    print(f"   ✅ Score stored in database")
    
    # Retrieve score
    stored = calculator.get_stored_score("SYS001", date.today())
    print(f"   ✅ Score retrieved: {stored}/100")
    
    # Test Violation Tracker
    print("\n3. Testing Violation Tracker...")
    tracker = ViolationTracker()
    
    # Record test violation
    violation_id = tracker.record_violation(
        source_system_id="SYS001",
        violation_date=date.today(),
        violation_type="test",
        severity="low",
    )
    print(f"   ✅ Violation recorded: ID {violation_id}")
    
    # Get violations
    violations = tracker.get_violations(source_system_id="SYS001")
    print(f"   ✅ Total violations: {len(violations)}")
    
    # Get by severity
    severity_counts = tracker.get_violations_by_severity("SYS001")
    print(f"   ✅ By severity: {severity_counts}")
    
    print("\n" + "=" * 50)
    print("SLA tracking tests complete!")

if __name__ == "__main__":
    test_sla_tracking()
