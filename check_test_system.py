"""Check if test system is detecting files"""

from datetime import datetime, timedelta
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel, FileArrivalModel

def check_test_system():
    """Check test system status and file detections"""
    
    print("Checking Test System Status")
    print("=" * 60)
    
    init_db()
    
    with get_db_session() as session:
        # Get test system
        system = session.query(SourceSystemModel).filter_by(
            id="TEST001"
        ).first()
        
        if not system:
            print("❌ Test system not found!")
            print("   Run: python add_test_system.py")
            return
        
        # Load attributes
        _ = (system.id, system.name, system.directory_path, system.is_active)
        session.expunge(system)
        
        print(f"\nSystem: {system.id}")
        print(f"  Name: {system.name}")
        print(f"  Path: {system.directory_path}")
        print(f"  Active: {'✅ Yes' if system.is_active else '❌ No'}")
        
        # Check for file arrivals in last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        
        files = session.query(FileArrivalModel).filter(
            FileArrivalModel.source_system_id == "TEST001",
            FileArrivalModel.arrival_timestamp >= yesterday
        ).order_by(FileArrivalModel.arrival_timestamp.desc()).all()
        
        print(f"\n📁 Files detected (last 24 hours): {len(files)}")
        
        if files:
            print("\nRecent files:")
            for i, file in enumerate(files[:10], 1):  # Show last 10
                _ = (file.filename, file.arrival_timestamp, file.file_size_bytes)
                session.expunge(file)
                
                print(f"  {i}. {file.filename}")
                print(f"     Time: {file.arrival_timestamp}")
                print(f"     Size: {file.file_size_bytes} bytes")
        else:
            print("\n⚠️  No files detected yet")
            print("\nTo test file detection:")
            print("  1. Make sure monitoring is running: python start_monitoring.py")
            print("  2. Create a test file:")
            print("     echo test > C:\\data\\test1\\testfile.txt")
            print("  3. Wait a few seconds")
            print("  4. Run this script again: python check_test_system.py")
        
        # Check all files ever detected
        all_files = session.query(FileArrivalModel).filter(
            FileArrivalModel.source_system_id == "TEST001"
        ).count()
        
        print(f"\n📊 Total files detected (all time): {all_files}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_test_system()
