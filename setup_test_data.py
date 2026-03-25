"""Setup test data for API testing"""

from datetime import date, datetime, time

from src.database.connection import get_db_session, init_db
from src.database.models import Base, FileArrivalModel, SLADefinitionModel, SourceSystemModel

def setup_test_data():
    """Create test data in the database"""
    print("Setting up test data...")
    
    # Initialize database
    init_db()
    
    with get_db_session() as session:
        # Check if data already exists
        existing = session.query(SourceSystemModel).count()
        if existing > 0:
            print(f"Database already has {existing} source systems. Skipping setup.")
            return
        
        # Create source systems
        systems = [
            SourceSystemModel(
                id="SYS001",
                name="Production System 1",
                directory_path="/data/prod1",
                is_active=True,
            ),
            SourceSystemModel(
                id="SYS002",
                name="Production System 2",
                directory_path="/data/prod2",
                is_active=True,
            ),
            SourceSystemModel(
                id="SYS003",
                name="Test System",
                directory_path="/data/test",
                is_active=False,
            ),
        ]
        
        for sys in systems:
            session.add(sys)
        
        # Create SLA definitions
        sla_defs = [
            SLADefinitionModel(
                source_system_id="SYS001",
                expected_arrival_time=time(9, 0, 0),
                expected_arrival_window_minutes=30,
                minimum_files_per_day=10,
                weight=1.0,
                effective_from=date(2024, 1, 1),
                effective_to=None,
            ),
            SLADefinitionModel(
                source_system_id="SYS002",
                expected_arrival_time=time(10, 0, 0),
                expected_arrival_window_minutes=60,
                minimum_files_per_day=5,
                weight=1.0,
                effective_from=date(2024, 1, 1),
                effective_to=None,
            ),
        ]
        
        for sla in sla_defs:
            session.add(sla)
        
        # Create some file arrivals
        arrivals = [
            FileArrivalModel(
                source_system_id="SYS001",
                file_path="/data/prod1/file1.txt",
                filename="file1.txt",
                arrival_timestamp=datetime(2026, 2, 15, 9, 15, 0),
                file_size_bytes=1024,
                checksum="abc123",
            ),
            FileArrivalModel(
                source_system_id="SYS001",
                file_path="/data/prod1/file2.txt",
                filename="file2.txt",
                arrival_timestamp=datetime(2026, 2, 15, 9, 30, 0),
                file_size_bytes=2048,
                checksum="def456",
            ),
            FileArrivalModel(
                source_system_id="SYS002",
                file_path="/data/prod2/data.csv",
                filename="data.csv",
                arrival_timestamp=datetime(2026, 2, 15, 10, 5, 0),
                file_size_bytes=4096,
                checksum="ghi789",
            ),
        ]
        
        for arrival in arrivals:
            session.add(arrival)
        
        session.commit()
        
        print(f"Created {len(systems)} source systems")
        print(f"Created {len(sla_defs)} SLA definitions")
        print(f"Created {len(arrivals)} file arrivals")
        print("Test data setup complete!")

if __name__ == "__main__":
    setup_test_data()
