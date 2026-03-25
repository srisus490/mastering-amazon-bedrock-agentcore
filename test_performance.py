"""Performance testing"""

import time
from datetime import datetime

from src.database.connection import init_db, get_db_session
from src.database.models import FileArrivalModel

def test_performance():
    """Test system performance"""
    
    init_db()
    
    print("Performance Testing...")
    print("=" * 50)
    
    # Test 1: Database write performance
    print("\n1. Testing Database Write Performance...")
    start = time.time()
    
    with get_db_session() as session:
        for i in range(100):
            arrival = FileArrivalModel(
                source_system_id="SYS001",
                filename=f"perf_test_{i}.txt",
                file_path=f"/test/perf_test_{i}.txt",
                arrival_timestamp=datetime.now(),
                file_size_bytes=1024,
            )
            session.add(arrival)
        session.commit()
    
    elapsed = time.time() - start
    print(f"   ✅ Inserted 100 records in {elapsed:.3f}s")
    print(f"   ✅ Average: {elapsed/100*1000:.2f}ms per record")
    
    # Test 2: Query performance
    print("\n2. Testing Query Performance...")
    start = time.time()
    
    with get_db_session() as session:
        count = session.query(FileArrivalModel).filter_by(
            source_system_id="SYS001"
        ).count()
    
    elapsed = time.time() - start
    print(f"   ✅ Counted {count} records in {elapsed:.3f}s")
    
    # Test 3: API response time
    print("\n3. Testing API Response Time...")
    try:
        import requests
        start = time.time()
        r = requests.get("http://localhost:8000/api/v1/source-systems")
        elapsed = time.time() - start
        
        if r.status_code == 200:
            print(f"   ✅ API response in {elapsed*1000:.2f}ms")
        else:
            print(f"   ❌ API returned status {r.status_code}")
    except:
        print("   ⚠️  API server not running (start with: python run_api.py)")
    
    print("\n" + "=" * 50)
    print("Performance tests complete!")

if __name__ == "__main__":
    test_performance()
