"""Create test files in all active source systems"""

import time
from datetime import datetime
from pathlib import Path
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel

def create_test_files():
    """Create test files in all active source systems"""
    
    print("Creating Test Files in All Source Systems")
    print("=" * 70)
    
    init_db()
    
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).filter_by(
            is_active=True
        ).all()
        
        if not systems:
            print("❌ No active source systems found!")
            return
        
        print(f"\nFound {len(systems)} active system(s)\n")
        
        created = []
        failed = []
        
        for sys in systems:
            # Load attributes
            _ = (sys.id, sys.name, sys.directory_path)
            session.expunge(sys)
            
            print(f"📁 {sys.id}: {sys.name}")
            print(f"   Path: {sys.directory_path}")
            
            try:
                # Ensure directory exists
                path = Path(sys.directory_path)
                if not path.exists():
                    print(f"   ⚠️  Directory doesn't exist, creating...")
                    path.mkdir(parents=True, exist_ok=True)
                
                # Create test file with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"test_file_{timestamp}.txt"
                filepath = path / filename
                
                # Write test content
                content = f"""Test File for {sys.name}
System ID: {sys.id}
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Purpose: Demo file monitoring system
"""
                
                with open(filepath, 'w') as f:
                    f.write(content)
                
                print(f"   ✅ Created: {filename}")
                created.append(sys.id)
                
                # Small delay between files
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed.append((sys.id, str(e)))
            
            print()
    
    # Summary
    print("=" * 70)
    print("\nSummary:")
    print(f"  ✅ Files created: {len(created)}")
    print(f"  ❌ Failed: {len(failed)}")
    
    if created:
        print(f"\n✅ Successfully created test files in:")
        for sys_id in created:
            print(f"  - {sys_id}")
    
    if failed:
        print(f"\n❌ Failed to create files in:")
        for sys_id, error in failed:
            print(f"  - {sys_id}: {error}")
    
    print("\n⏱️  Waiting 10 seconds for file detection...")
    for i in range(10, 0, -1):
        print(f"   {i} seconds remaining...", end="\r")
        time.sleep(1)
    print("\n")
    
    print("✅ Files should now be detected!")
    print("\nNext steps:")
    print("  1. Check API: GET /api/v1/file-arrivals?days=1")
    print("  2. Check count: GET /api/v1/file-arrivals/count")
    print("  3. View in browser: http://localhost:8000/docs")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    create_test_files()
