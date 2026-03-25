# Test System Guide

Quick guide to test your file monitoring system with the `C:\data\test1` directory.

## Quick Test (5 minutes)

### Option 1: Automated Test Workflow

Run the complete automated test:

```bash
python test_workflow.py
```

This will guide you through all steps automatically.

### Option 2: Manual Step-by-Step

#### Step 1: Add Test System (30 seconds)

```bash
python add_test_system.py
```

This creates a test system monitoring `C:\data\test1`.

#### Step 2: Start Monitoring (Terminal 1)

```bash
python start_monitoring.py
```

Keep this terminal open. You should see:
```
Starting File Monitoring Service...
Found 1 active systems:
  - TEST001: Test System 1
    Path: C:\data\test1
✅ Monitoring started: TEST001
```

#### Step 3: Create Test File (Terminal 2)

```bash
echo test > C:\data\test1\testfile.txt
```

Or create any file in `C:\data\test1\`.

#### Step 4: Check Detection (30 seconds later)

```bash
python check_test_system.py
```

You should see:
```
📁 Files detected (last 24 hours): 1

Recent files:
  1. testfile.txt
     Time: 2026-02-15 15:05:23
     Size: 6 bytes
```

#### Step 5: Test API (Terminal 3)

```bash
python run_api.py
```

Visit: http://localhost:8000/docs

Try these endpoints:
- `GET /api/v1/source-systems` - Should show TEST001
- `GET /api/v1/file-arrivals?days=1` - Should show your test file
- `GET /api/v1/file-arrivals/count` - Should show count > 0

---

## Test Scenarios

### Scenario 1: Single File Detection

```bash
# Create one file
echo "Test 1" > C:\data\test1\file1.txt

# Wait 5 seconds
timeout /t 5

# Check detection
python check_test_system.py
```

### Scenario 2: Multiple Files

```bash
# Create multiple files
for /L %i in (1,1,5) do echo Test %i > C:\data\test1\file%i.txt

# Wait 10 seconds
timeout /t 10

# Check detection
python check_test_system.py
```

### Scenario 3: Different File Types

```bash
# Create different file types
echo CSV data > C:\data\test1\data.csv
echo JSON data > C:\data\test1\data.json
echo XML data > C:\data\test1\data.xml

# Check detection
python check_test_system.py
```

### Scenario 4: Large File

```bash
# Create a larger file (1MB)
fsutil file createnew C:\data\test1\largefile.dat 1048576

# Check detection
python check_test_system.py
```

---

## Verification Checklist

After running tests, verify:

- [ ] Test system appears in database
  ```bash
  # Should show TEST001
  curl http://localhost:8000/api/v1/source-systems
  ```

- [ ] Files are detected within 30 seconds
  ```bash
  # Create file and check
  echo test > C:\data\test1\test.txt
  # Wait 30 seconds
  python check_test_system.py
  ```

- [ ] File metadata is captured correctly
  - Filename
  - Timestamp (millisecond precision)
  - File size
  - Source system ID

- [ ] API endpoints return correct data
  - `/api/v1/source-systems` shows TEST001
  - `/api/v1/file-arrivals` shows detected files
  - `/api/v1/file-arrivals/count` shows correct count

- [ ] SLA tracking works
  ```bash
  curl "http://localhost:8000/api/v1/sla/scores/TEST001?days=7"
  ```

---

## Troubleshooting

### Issue: No files detected

**Check 1: Is monitoring running?**
```bash
# You should see monitoring service running in Terminal 1
# Look for: "✅ Monitoring started: TEST001"
```

**Check 2: Is directory correct?**
```bash
dir C:\data\test1
# Should show your test files
```

**Check 3: Is system active?**
```bash
python verify_configuration.py
# Should show TEST001 as active
```

### Issue: "System not found"

**Solution:** Add the test system first
```bash
python add_test_system.py
```

### Issue: API not responding

**Check:** Is API server running?
```bash
# Terminal 3 should show:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Solution:** Start API server
```bash
python run_api.py
```

### Issue: Files detected but not in API

**Solution:** Restart API server to refresh data
```bash
# Stop API (Ctrl+C)
# Start again
python run_api.py
```

---

## Clean Up Test Data

After testing, you can clean up:

### Option 1: Remove Test Files Only

```bash
# Delete test files
del C:\data\test1\*.txt
del C:\data\test1\*.dat
```

### Option 2: Remove Test System from Database

```python
# In Python console
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel

init_db()

with get_db_session() as session:
    system = session.query(SourceSystemModel).filter_by(id="TEST001").first()
    if system:
        session.delete(system)
        session.commit()
        print("Deleted TEST001")
```

### Option 3: Keep for Future Testing

Leave TEST001 configured for quick testing anytime:
```bash
# Just create new test files
echo test > C:\data\test1\newtest.txt
```

---

## Success Criteria

Your test is successful when:

✅ Test system (TEST001) is in database  
✅ Monitoring service detects files within 30 seconds  
✅ File metadata is captured correctly  
✅ API endpoints return test system data  
✅ API endpoints return file arrival data  
✅ SLA scores are calculated  

---

## Next Steps After Successful Test

1. **Stop test services**
   - Stop monitoring (Ctrl+C in Terminal 1)
   - Stop API (Ctrl+C in Terminal 3)

2. **Configure production systems**
   - Edit `add_systems.py` with your 20 actual systems
   - Run `python add_systems.py`

3. **Start production monitoring**
   - Run `python start_monitoring.py`
   - Run `python run_api.py`

4. **Set up production features**
   - Daily health checks
   - Database backups
   - AI features (optional)

---

## Quick Commands Reference

```bash
# Add test system
python add_test_system.py

# Check test system status
python check_test_system.py

# Verify configuration
python verify_configuration.py

# Start monitoring
python start_monitoring.py

# Start API
python run_api.py

# Create test file
echo test > C:\data\test1\testfile.txt

# Run complete test workflow
python test_workflow.py
```

---

## Test System Configuration

The test system is configured with:

- **ID**: TEST001
- **Name**: Test System 1
- **Path**: C:\data\test1
- **Active**: Yes
- **SLA Time**: 12:00 PM ±2 hours (flexible for testing)
- **Min Files/Day**: 1

This configuration is intentionally flexible to make testing easy.

---

Your test environment is ready! 🎉

Run `python test_workflow.py` to start testing.
