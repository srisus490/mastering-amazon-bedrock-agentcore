# Quick Start Guide - 5 Minutes to Running System

Get the Intelligent File Monitoring System running in 5 minutes!

## Step 1: Install (2 minutes)

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies (if not already done)
pip install -e ".[dev]"

# Initialize database
python scripts/init_database.py
```

**Expected Output:**
```
Database initialized successfully
Created 3 sample source systems
```

## Step 2: Add Test Data (30 seconds)

```bash
python setup_test_data.py
```

**Expected Output:**
```
Created 3 source systems
Created 2 SLA definitions
Created 3 file arrivals
Test data setup complete!
```

## Step 3: Start API Server (30 seconds)

```bash
python run_api.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Test the System (1 minute)

Open your browser and visit:

### 📚 API Documentation
http://localhost:8000/docs

Try these endpoints in the Swagger UI:
1. **GET /health** - Check system health
2. **GET /api/v1/source-systems** - See configured systems
3. **GET /api/v1/file-arrivals/count** - Count detected files
4. **GET /api/v1/sla/scores/SYS001?days=7** - View SLA scores

### 🧪 Run Tests

Open a **new terminal** (keep API running):

```bash
# Test API endpoints
python test_api.py

# Test SLA tracking
python test_sla_tracking.py

# Run all unit tests
pytest
```

## Step 5: Configure Your Systems (1 minute)

### Edit `add_systems.py`:

```python
systems = [
    {
        "id": "YOUR_SYSTEM_1",
        "name": "Your System Name",
        "directory_path": "C:\\your\\data\\path",  # Change this!
        "is_active": True,
        "sla": {
            "expected_arrival_time": time(9, 0, 0),  # 9:00 AM
            "window_minutes": 30,  # ±30 minutes
            "minimum_files_per_day": 5,
        }
    },
]
```

### Add to database:

```bash
python add_systems.py
```

### Start monitoring:

```bash
python start_monitoring.py
```

---

## What You Get

✅ **REST API** running on http://localhost:8000  
✅ **Interactive API Docs** at http://localhost:8000/docs  
✅ **File Monitoring** detecting files in real-time  
✅ **SLA Tracking** calculating compliance scores  
✅ **Trend Analysis** with moving averages  
✅ **Zero Cost** - no cloud services needed  

---

## Common Commands

```bash
# Start API server
python run_api.py

# Start file monitoring
python start_monitoring.py

# Run daily health check
python daily_check.py

# Backup database
python backup_database.py

# Run all tests
pytest

# Test specific component
python test_sla_tracking.py
python test_trends.py
```

---

## API Quick Reference

### Get Source Systems
```bash
curl http://localhost:8000/api/v1/source-systems
```

### Get File Arrivals (last 7 days)
```bash
curl "http://localhost:8000/api/v1/file-arrivals?days=7"
```

### Get SLA Scores
```bash
curl "http://localhost:8000/api/v1/sla/scores/SYS001?days=30"
```

### Get Trend Analysis
```bash
curl "http://localhost:8000/api/v1/trends/moving-average/SYS001?days=30"
```

### Get Violations
```bash
curl "http://localhost:8000/api/v1/sla/violations?source_system_id=SYS001"
```

---

## Next Steps

1. ✅ **Configure your actual directories** in `add_systems.py`
2. ✅ **Start monitoring** with `python start_monitoring.py`
3. ✅ **Set up daily checks** (schedule `daily_check.py`)
4. ✅ **Set up backups** (schedule `backup_database.py`)
5. 📊 **Build a dashboard** (optional - use the API)
6. 🔔 **Add alerting** (optional - email/Slack notifications)

---

## Troubleshooting

### API won't start - Port 8000 in use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <process_id>

# Linux
lsof -ti:8000 | xargs kill -9
```

### No files detected
- Check directory paths in database
- Verify directories exist
- Ensure system is marked as active
- Check file permissions

### Tests failing
```bash
# Reinstall dependencies
pip install -e ".[dev]"

# Clear pytest cache
pytest --cache-clear
```

---

## Support

- **Full Documentation**: See DEPLOYMENT_GUIDE.md
- **Testing Guide**: See TESTING_GUIDE.md
- **Implementation Details**: See IMPLEMENTATION_COMPLETE.md
- **API Docs**: http://localhost:8000/docs (when running)

---

## Success! 🎉

You now have a fully functional file monitoring system with:
- Real-time file detection
- SLA tracking and scoring
- REST API with comprehensive endpoints
- Zero infrastructure costs
- Production-ready deployment

**Total setup time: 5 minutes**  
**Monthly cost: $0**  
**Annual savings: $2,160-$7,200**
