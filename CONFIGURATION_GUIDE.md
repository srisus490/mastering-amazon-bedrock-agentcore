# Source Systems Configuration Guide

This guide helps you configure your 20 source systems for monitoring.

## Quick Start

1. **Edit `add_systems.py`** - Update the systems list with your actual directories
2. **Run the script** - `python add_systems.py`
3. **Start monitoring** - `python start_monitoring.py`

---

## Configuration Parameters

### System Identification

**`id`** (required)
- Unique identifier for the system
- Use uppercase letters, numbers, and underscores only
- Examples: `PROD_SALES`, `DEV_INVENTORY`, `TEST_CUSTOMER`

**`name`** (required)
- Human-readable name displayed in dashboard
- Can contain spaces and special characters
- Examples: "Production Sales System", "Customer Data Feed"

**`directory_path`** (required)
- Full path to the directory to monitor
- **Windows**: Use double backslashes `C:\\data\\sales` or raw strings `r"C:\data\sales"`
- **Linux/Mac**: Use forward slashes `/data/sales`
- The directory must exist before starting monitoring

**`is_active`** (required)
- `True`: System is actively monitored
- `False`: System is configured but not monitored (useful for testing)

### SLA Configuration

**`expected_arrival_time`** (required)
- Time when files typically arrive
- Format: `time(hour, minute, second)` in 24-hour format
- Examples:
  - `time(9, 0, 0)` = 9:00 AM
  - `time(14, 30, 0)` = 2:30 PM
  - `time(23, 45, 0)` = 11:45 PM

**`window_minutes`** (required)
- Tolerance window in minutes (±)
- Files arriving within this window are considered on-time
- Examples:
  - `30` = ±30 minutes (8:30 AM - 9:30 AM for 9:00 AM expected time)
  - `60` = ±1 hour
  - `15` = ±15 minutes (strict timing)

**`minimum_files_per_day`** (required)
- Minimum number of files expected per day
- Used to detect missing data
- Set to `1` if you expect at least one file daily
- Set to `0` if files are optional

---

## Example Configurations

### High-Frequency System (Many Files, Strict Timing)
```python
{
    "id": "PROD_TRANSACTIONS",
    "name": "Production Transaction System",
    "directory_path": "C:\\data\\transactions",
    "is_active": True,
    "sla": {
        "expected_arrival_time": time(8, 0, 0),  # 8:00 AM
        "window_minutes": 15,  # Strict: 7:45 AM - 8:15 AM
        "minimum_files_per_day": 50,  # Expect many files
    }
}
```

### Low-Frequency System (Few Files, Flexible Timing)
```python
{
    "id": "PROD_MONTHLY_REPORT",
    "name": "Monthly Report System",
    "directory_path": "C:\\data\\monthly",
    "is_active": True,
    "sla": {
        "expected_arrival_time": time(23, 0, 0),  # 11:00 PM
        "window_minutes": 180,  # Flexible: 8:00 PM - 2:00 AM
        "minimum_files_per_day": 1,  # Just one file expected
    }
}
```

### Overnight Batch System
```python
{
    "id": "PROD_BATCH",
    "name": "Overnight Batch Processing",
    "directory_path": "C:\\data\\batch",
    "is_active": True,
    "sla": {
        "expected_arrival_time": time(2, 0, 0),  # 2:00 AM
        "window_minutes": 60,  # 1:00 AM - 3:00 AM
        "minimum_files_per_day": 10,
    }
}
```

### Development/Test System (Inactive)
```python
{
    "id": "DEV_TEST",
    "name": "Development Test System",
    "directory_path": "C:\\data\\dev_test",
    "is_active": False,  # Not monitored yet
    "sla": {
        "expected_arrival_time": time(12, 0, 0),
        "window_minutes": 120,
        "minimum_files_per_day": 1,
    }
}
```

---

## Step-by-Step Configuration

### Step 1: Identify Your Systems

List all 20 source systems you need to monitor:

1. What is the system name?
2. Where does it write files? (directory path)
3. When do files typically arrive? (time of day)
4. How many files per day?
5. How strict is the timing?

### Step 2: Create Directory Structure

Before running the script, ensure all directories exist:

**Windows:**
```cmd
mkdir C:\data\sales
mkdir C:\data\inventory
mkdir C:\data\customer
REM ... create all 20 directories
```

**Linux/Mac:**
```bash
mkdir -p /data/sales
mkdir -p /data/inventory
mkdir -p /data/customer
# ... create all 20 directories
```

### Step 3: Edit add_systems.py

Open `add_systems.py` and update each system:

1. Change `directory_path` to your actual path
2. Adjust `expected_arrival_time` based on your schedule
3. Set appropriate `window_minutes` for tolerance
4. Set `minimum_files_per_day` based on expected volume
5. Set `is_active` to `False` for systems you want to configure but not monitor yet

### Step 4: Run the Configuration Script

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run the script
python add_systems.py
```

**Expected Output:**
```
Adding source systems to database...
==================================================
✅ Added system: PROD_SALES
   Name: Production Sales System
   Path: C:\data\sales
   SLA: 09:00:00 ±30min
✅ Added system: PROD_INVENTORY
   Name: Production Inventory System
   Path: C:\data\inventory
   SLA: 10:00:00 ±60min
...
==================================================
✅ All systems configured!

Next steps:
  1. Verify directories exist
  2. Start monitoring: python start_monitoring.py
  3. Start API: python run_api.py
```

### Step 5: Verify Configuration

Check that systems were added:

```bash
# Start API server
python run_api.py

# In browser, visit:
# http://localhost:8000/docs

# Try endpoint: GET /api/v1/source-systems
```

You should see all 20 systems listed.

---

## Common Scenarios

### Scenario 1: System Sends Files Multiple Times Per Day

If a system sends files at different times (e.g., 9 AM and 3 PM), choose the most critical time for SLA monitoring:

```python
{
    "id": "PROD_MULTI_TIME",
    "name": "Multi-Time System",
    "directory_path": "C:\\data\\multi",
    "is_active": True,
    "sla": {
        "expected_arrival_time": time(9, 0, 0),  # Monitor morning batch
        "window_minutes": 30,
        "minimum_files_per_day": 10,  # Total for entire day
    }
}
```

### Scenario 2: Weekend vs Weekday Schedules

Currently, the system uses the same SLA for all days. If you need different schedules:

1. Set SLA for the most common schedule (weekdays)
2. Use AI anomaly detection to identify weekend patterns
3. Manually review weekend violations

### Scenario 3: System is Down for Maintenance

Temporarily disable monitoring:

```python
{
    "id": "PROD_MAINTENANCE",
    "name": "System Under Maintenance",
    "directory_path": "C:\\data\\maintenance",
    "is_active": False,  # Disabled during maintenance
    "sla": {
        "expected_arrival_time": time(10, 0, 0),
        "window_minutes": 30,
        "minimum_files_per_day": 5,
    }
}
```

Re-enable by changing `is_active` to `True` and restarting the monitoring service.

### Scenario 4: Testing New System

Add with `is_active: False`, then enable once ready:

```python
{
    "id": "NEW_SYSTEM",
    "name": "New System (Testing)",
    "directory_path": "C:\\data\\new_system",
    "is_active": False,  # Test first
    "sla": {
        "expected_arrival_time": time(12, 0, 0),
        "window_minutes": 60,
        "minimum_files_per_day": 1,
    }
}
```

---

## Updating Existing Systems

If you need to modify a system after it's been added:

### Option 1: Update via Database (Recommended)

Use the API to update:

```bash
# Update SLA via API
curl -X PUT "http://localhost:8000/api/v1/source-systems/PROD_SALES" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "C:\\new\\path",
    "is_active": true
  }'
```

### Option 2: Delete and Re-add

```python
# In Python console or script
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel, SLADefinitionModel

init_db()

with get_db_session() as session:
    # Delete existing system
    system = session.query(SourceSystemModel).filter_by(id="PROD_SALES").first()
    if system:
        session.delete(system)
        session.commit()
        print("Deleted PROD_SALES")

# Then run add_systems.py again
```

---

## Troubleshooting

### Issue: "System already exists - skipping"

**Cause:** System with that ID is already in the database.

**Solution:**
1. Check if you want to update (see "Updating Existing Systems" above)
2. Or use a different ID for the new system

### Issue: "Directory not found" when starting monitoring

**Cause:** The directory path doesn't exist.

**Solution:**
```bash
# Create the directory
mkdir C:\data\your_directory  # Windows
mkdir -p /data/your_directory  # Linux/Mac
```

### Issue: Files detected but no SLA violations shown

**Cause:** Files are arriving within the SLA window.

**Solution:** This is good! Your systems are compliant. Check:
```bash
# View SLA scores
curl "http://localhost:8000/api/v1/sla/scores/PROD_SALES?days=7"
```

### Issue: Too many SLA violations

**Cause:** SLA parameters are too strict for actual file arrival patterns.

**Solution:** Use AI to optimize:
```bash
# Get AI recommendations
curl -X POST "http://localhost:8000/api/v1/ai/recommend-sla/PROD_SALES?days=90"
```

---

## Best Practices

1. **Start with Flexible SLAs**: Use wider windows initially, then tighten based on actual patterns
2. **Use AI Recommendations**: After 30-90 days of data, use AI to optimize SLA settings
3. **Monitor Gradually**: Enable 5 systems at a time to ensure stability
4. **Document Changes**: Keep notes on why you set specific SLA parameters
5. **Review Weekly**: Check SLA scores and violations weekly to identify issues early

---

## Next Steps

After configuring your systems:

1. ✅ **Start Monitoring**: `python start_monitoring.py`
2. ✅ **Start API**: `python run_api.py`
3. ✅ **View Dashboard**: http://localhost:8000/docs
4. ✅ **Test AI Features**: `python test_ai.py`
5. ✅ **Set Up Daily Checks**: Schedule `daily_check.py`
6. ✅ **Configure Backups**: Schedule `backup_database.py`

---

## Support

For issues or questions:
- Check `QUICK_START.md` for basic setup
- Check `DEPLOYMENT_GUIDE.md` for production deployment
- Check `AI_IMPLEMENTATION_GUIDE.md` for AI features
- Review API docs at http://localhost:8000/docs

Your system is ready to monitor 20 source systems with $0 infrastructure costs! 🎉
