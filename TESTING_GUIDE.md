# Testing Guide - Intelligent File Monitoring System

This guide walks you through testing all components of the file monitoring system.

## Prerequisites

```bash
# Ensure you're in the project directory
cd mastering-amazon-bedrock-agentcore

# Activate virtual environment (if not already active)
.venv\Scripts\activate

# Verify installation
python -c "import src; print('Installation OK')"
```

## Test 1: Unit Tests (Automated)

### Run All Tests
```bash
pytest
```

**Expected Output:**
- All tests should pass
- Coverage report generated
- No errors

### Run Specific Test Suites
```bash
# Test SLA services
pytest tests/test_sla_simplified.py -v

# Test database writer
pytest tests/test_database_writer.py -v

# Test trend analyzer
pytest tests/test_trend_analyzer.py -v

# Test with coverage
pytest --cov=src --cov-report=html
```

**Success Criteria:**
- ✅ 15/15 SLA tests passing
- ✅ All database tests passing
- ✅ Coverage > 70%

---

## Test 2: Database Setup

### Initialize Database
```bash
python scripts/init_database.py
```

**Expected Output:**
```
Database initialized successfully
Created 3 sample source systems
```

### Add Test Data
```bash
python setup_test_data.py
```

**Expected Output:**
```
Setting up test data...
Created 3 source systems
Created 2 SLA definitions
Created 3 file arrivals
Test data setup complete!
```

### Verify Database
```bash
python -c "from src.database.connection import init_db, get_db_session; from src.database.models import SourceSystemModel; init_db(); session = get_db_session().__enter__(); print(f'Source systems: {session.query(SourceSystemModel).count()}'); session.close()"
```

**Expected Output:**
```
Source systems: 3
```

**Success Criteria:**
- ✅ Database file created at `data/file_monitoring.db`
- ✅ 3 source systems in database
- ✅ No errors

---

## Test 3: REST API

### Step 1: Start API Server

**Terminal 1:**
```bash
python run_api.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
Starting up API server
Initializing database connection
Database connection initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Test API Endpoints

**Terminal 2 (keep server running in Terminal 1):**

#### Test Health Check
```bash
python -c "import requests; r = requests.get('http://localhost:8000/health'); print(f'Status: {r.status_code}'); print(r.json())"
```

**Expected Output:**
```
Status: 200
{'status': 'healthy', 'timestamp': '2026-02-15T...', 'service': 'file-monitoring-api'}
```

#### Test Source Systems
```bash
python -c "import requests; r = requests.get('http://localhost:8000/api/v1/source-systems'); print(f'Found {len(r.json())} systems'); print(r.json()[0] if r.json() else 'No systems')"
```

**Expected Output:**
```
Found 3 systems
{'id': 'SYS001', 'name': 'Production System 1', 'directory_path': '/data/prod1', 'is_active': True}
```

#### Test File Arrivals
```bash
python -c "import requests; r = requests.get('http://localhost:8000/api/v1/file-arrivals/count'); print(r.json())"
```

**Expected Output:**
```
{'count': 3}
```

#### Test SLA Scores
```bash
python -c "import requests; r = requests.get('http://localhost:8000/api/v1/sla/scores/SYS001?days=7'); print(f'Scores: {len(r.json())} days'); print(r.json()[0] if r.json() else 'No scores')"
```

**Expected Output:**
```
Scores: 7 days
{'date': '2026-02-15', 'score': 100.0}
```

### Step 3: Use Comprehensive Test Script
```bash
python test_api.py
```

**Expected Output:**
```
Testing API endpoints...
==================================================

1. Health check:
   Status: 200
   Response: {'status': 'healthy', ...}

2. Root endpoint:
   Status: 200
   Response: {'message': 'Intelligent File Monitoring API', ...}

3. Source systems:
   Status: 200
   Count: 3
   First system: {'id': 'SYS001', ...}

4. File arrivals count:
   Status: 200
   Response: {'count': 3}

5. Trends summary:
   Status: 200
   Systems: 3

==================================================
API tests completed!
```

### Step 4: Test with Browser

Open your browser and visit:

1. **API Documentation**: http://localhost:8000/docs
   - Interactive Swagger UI
   - Try out endpoints directly
   - See request/response schemas

2. **Health Check**: http://localhost:8000/health
   - Should show JSON response

3. **Source Systems**: http://localhost:8000/api/v1/source-systems
   - Should show array of systems

**Success Criteria:**
- ✅ All endpoints return 200 status
- ✅ Data matches expected format
- ✅ Swagger UI loads correctly
- ✅ No 500 errors

---

## Test 4: File Monitoring (End-to-End)

### Step 1: Create Test Directory
```bash
mkdir test_monitoring
```

### Step 2: Create Monitoring Script

Create `test_file_monitor.py`:
```python
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
```

### Step 3: Run File Monitoring Test
```bash
python test_file_monitor.py
```

**Expected Output:**
```
Created test source system: TEST001
Monitoring directory: C:\...\test_monitoring
Creating test files...
  Created: test_file_0.txt
  Created: test_file_1.txt
  Created: test_file_2.txt

Results:
  Files created: 3
  Files in database: 3
  ✅ File monitoring working!
    - test_file_0.txt at 2026-02-15 12:00:00
    - test_file_1.txt at 2026-02-15 12:00:01
    - test_file_2.txt at 2026-02-15 12:00:02

Test complete!
```

**Success Criteria:**
- ✅ Files created successfully
- ✅ Files detected and recorded in database
- ✅ Timestamps captured correctly

---

## Test 5: SLA Tracking

### Create SLA Test Script

Create `test_sla_tracking.py`:
```python
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
```

### Run SLA Test
```bash
python test_sla_tracking.py
```

**Expected Output:**
```
Testing SLA Tracking...
==================================================
✅ Found system: Production System 1
✅ Found SLA: Expected at 09:00:00 ±30 min

1. Testing SLA Evaluator...
   ✅ SLA definition retrieved
   ✅ Window check: True
   ✅ Lateness: 15.0 minutes

2. Testing Score Calculator...
   ✅ Daily score: 100.0/100
   ✅ Score stored in database
   ✅ Score retrieved: 100.0/100

3. Testing Violation Tracker...
   ✅ Violation recorded: ID 1
   ✅ Total violations: 1
   ✅ By severity: {'critical': 0, 'high': 0, 'medium': 0, 'low': 1}

==================================================
SLA tracking tests complete!
```

**Success Criteria:**
- ✅ SLA definitions retrieved
- ✅ Compliance checks working
- ✅ Scores calculated and stored
- ✅ Violations tracked

---

## Test 6: Trend Analysis

### Create Trend Test Script

Create `test_trends.py`:
```python
"""Test trend analysis functionality"""

from datetime import date, timedelta

from src.analytics.trend_analyzer import TrendAnalyzer
from src.database.connection import init_db

def test_trends():
    """Test trend analysis"""
    
    init_db()
    
    print("Testing Trend Analysis...")
    print("=" * 50)
    
    analyzer = TrendAnalyzer()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    # Test daily counts
    print("\n1. Testing Daily Counts...")
    counts = analyzer.get_daily_counts("SYS001", start_date, end_date)
    print(f"   ✅ Retrieved {len(counts)} days of data")
    if counts:
        print(f"   Latest: {counts[-1].date} - {counts[-1].count} files")
    
    # Test moving averages
    print("\n2. Testing Moving Averages...")
    ma_points = analyzer.calculate_moving_average("SYS001", start_date, end_date)
    print(f"   ✅ Retrieved {len(ma_points)} data points")
    if ma_points:
        latest = ma_points[-1]
        print(f"   Latest: 7-day avg = {latest.moving_avg_7d:.2f}, 30-day avg = {latest.moving_avg_30d:.2f}")
    
    # Test hourly patterns
    print("\n3. Testing Hourly Patterns...")
    patterns = analyzer.get_hourly_patterns("SYS001", start_date, end_date)
    print(f"   ✅ Retrieved {len(patterns)} hourly patterns")
    if patterns:
        print(f"   Sample: Day {patterns[0].day_of_week}, Hour {patterns[0].hour} - Avg {patterns[0].avg_count:.2f} files")
    
    # Test all systems summary
    print("\n4. Testing All Systems Summary...")
    summary = analyzer.get_all_systems_summary()
    print(f"   ✅ Retrieved summary for {len(summary)} systems")
    if summary:
        print(f"   First system: {summary[0]}")
    
    print("\n" + "=" * 50)
    print("Trend analysis tests complete!")

if __name__ == "__main__":
    test_trends()
```

### Run Trend Test
```bash
python test_trends.py
```

**Expected Output:**
```
Testing Trend Analysis...
==================================================

1. Testing Daily Counts...
   ✅ Retrieved 7 days of data
   Latest: 2026-02-15 - 3 files

2. Testing Moving Averages...
   ✅ Retrieved 7 data points
   Latest: 7-day avg = 0.43, 30-day avg = 0.10

3. Testing Hourly Patterns...
   ✅ Retrieved 168 hourly patterns
   Sample: Day 6, Hour 9 - Avg 1.00 files

4. Testing All Systems Summary...
   ✅ Retrieved summary for 3 systems
   First system: {'source_system_id': 'SYS001', 'count': 3, ...}

==================================================
Trend analysis tests complete!
```

**Success Criteria:**
- ✅ Daily counts calculated
- ✅ Moving averages computed
- ✅ Hourly patterns analyzed
- ✅ Multi-system summary generated

---

## Test 7: Performance Test

### Create Performance Test

Create `test_performance.py`:
```python
"""Performance testing"""

import time
from datetime import datetime
from pathlib import Path

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
```

### Run Performance Test
```bash
python test_performance.py
```

**Expected Output:**
```
Performance Testing...
==================================================

1. Testing Database Write Performance...
   ✅ Inserted 100 records in 0.234s
   ✅ Average: 2.34ms per record

2. Testing Query Performance...
   ✅ Counted 103 records in 0.012s

3. Testing API Response Time...
   ✅ API response in 45.23ms

==================================================
Performance tests complete!
```

**Success Criteria:**
- ✅ Database writes < 10ms per record
- ✅ Queries < 100ms
- ✅ API responses < 200ms

---

## Troubleshooting

### Issue: API won't start
```bash
# Check if port is in use
netstat -ano | findstr :8000

# Kill process
taskkill /F /PID <process_id>
```

### Issue: Database locked
```bash
# Close all connections
# Restart Python
# SQLite WAL mode should prevent this
```

### Issue: Import errors
```bash
# Reinstall
pip install -e ".[dev]"
```

### Issue: Tests failing
```bash
# Clean and reinstall
pip uninstall intelligent-file-monitoring
pip install -e ".[dev]"

# Clear pytest cache
pytest --cache-clear
```

---

## Success Checklist

- [ ] All unit tests passing (pytest)
- [ ] Database initialized with test data
- [ ] API server starts without errors
- [ ] All API endpoints return 200
- [ ] Swagger UI accessible at /docs
- [ ] File monitoring detects new files
- [ ] SLA tracking calculates scores
- [ ] Trend analysis generates reports
- [ ] Performance meets targets

---

## Next Steps

1. **Production Deployment**: Deploy to server/cloud
2. **Monitoring**: Add logging and metrics
3. **Backup**: Set up database backups
4. **Dashboard**: Build frontend UI
5. **Alerts**: Configure SLA violation notifications

---

## Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review logs in console output
3. Check `data/file_monitoring.db` exists
4. Verify all dependencies installed
5. Open a GitHub issue with error details
