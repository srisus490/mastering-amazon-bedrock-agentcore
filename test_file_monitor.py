"""Test file monitoring end-to-end"""

import time
from pathlib import Path
from datetime import datetime

from src.monitor.watcher import DirectoryWatcher
from src.database.connection import init_db, get_db_session
from src.database.models import FileArrivalModel, SourceSystemModel

def test_file_monitoring():
    """Test complete file monitoring flow"""
    
    # Initialize database
    init_db()
    
    # Create test source system
    test_dir = Path("test_monitoring")
    test_dir.mkdir(exist_ok=True)
    
    with get_db_session() as session:
        # Check if test system exists
        existing = session.query(SourceSystemModel).filter_by(id="TEST001").first()
        if not existing:
            test_system = SourceSystemModel(
                id="TEST001",
                name="Test System",
                directory_path=str(test_dir.absolute()),
                is_active=True,
            )
            session.add(test_system)
            session.commit()
            print(f"Created test source system: TEST001")
    
    # Start monitoring
    print(f"Monitoring directory: {test_dir.absolute()}")
    print("Creating test files...")
    
    # Create test files
    for i in range(3):
        test_file = test_dir / f"test_file_{i}.txt"
        test_file.write_text(f"Test content {i} - {datetime.now()}")
        print(f"  Created: {test_file.name}")
        time.sleep(0.5)
    
    # Wait for processing
    time.sleep(2)
    
    # Check database
    with get_db_session() as session:
        count = session.query(FileArrivalModel).filter_by(
            source_system_id="TEST001"
        ).count()
        
        print(f"\nResults:")
        print(f"  Files created: 3")
        print(f"  Files in database: {count}")
        
        if count >= 3:
            print("  ✅ File monitoring working!")
            
            # Show details
            arrivals = session.query(FileArrivalModel).filter_by(
                source_system_id="TEST001"
            ).all()
            
            for arrival in arrivals:
                _ = (arrival.id, arrival.filename, arrival.arrival_timestamp)
                session.expunge(arrival)
                print(f"    - {arrival.filename} at {arrival.arrival_timestamp}")
        else:
            print("  ❌ Some files not detected")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_file_monitoring()
