"""Add a test system to verify monitoring works"""

from datetime import date, time
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel, SLADefinitionModel

def add_test_system():
    """Add a simple test system for verification"""
    init_db()
    
    print("Adding Test System")
    print("=" * 50)
    
    test_system = {
        "id": "TEST001",
        "name": "Test System 1",
        "directory_path": "C:\\data\\test1",
        "is_active": True,
        "sla": {
            "expected_arrival_time": time(12, 0, 0),  # 12:00 PM
            "window_minutes": 120,  # ±2 hours (flexible for testing)
            "minimum_files_per_day": 1,
        }
    }
    
    with get_db_session() as session:
        # Check if exists
        existing = session.query(SourceSystemModel).filter_by(
            id=test_system["id"]
        ).first()
        
        if existing:
            print(f"⚠️  System {test_system['id']} already exists")
            print("   Deleting and recreating...")
            session.delete(existing)
            session.commit()
        
        # Create source system
        system = SourceSystemModel(
            id=test_system["id"],
            name=test_system["name"],
            directory_path=test_system["directory_path"],
            is_active=test_system["is_active"],
        )
        session.add(system)
        
        # Create SLA definition
        sla = SLADefinitionModel(
            source_system_id=test_system["id"],
            expected_arrival_time=test_system["sla"]["expected_arrival_time"],
            expected_arrival_window_minutes=test_system["sla"]["window_minutes"],
            minimum_files_per_day=test_system["sla"]["minimum_files_per_day"],
            weight=1.0,
            effective_from=date(2026, 1, 1),
            effective_to=None,
        )
        session.add(sla)
        
        session.commit()
        
        print(f"✅ Added test system: {test_system['id']}")
        print(f"   Name: {test_system['name']}")
        print(f"   Path: {test_system['directory_path']}")
        print(f"   SLA: {test_system['sla']['expected_arrival_time']} ±{test_system['sla']['window_minutes']}min")
    
    print("\n" + "=" * 50)
    print("✅ Test system configured!")
    print("\nNext steps:")
    print("  1. Start monitoring: python start_monitoring.py")
    print("  2. Create a test file: echo test > C:\\data\\test1\\testfile.txt")
    print("  3. Check if detected: python check_test_system.py")

if __name__ == "__main__":
    add_test_system()
