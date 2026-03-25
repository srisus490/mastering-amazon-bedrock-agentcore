# Getting Started - Your Test System is Ready!

You've created `C:\data\test1` - let's test the file monitoring system!

## 🚀 Quick Start (2 Commands)

```bash
# 1. Add test system to database
python add_test_system.py

# 2. Run automated test workflow
python test_workflow.py
```

That's it! The workflow will guide you through everything.

---

## What Happens Next?

The test workflow will:

1. ✅ Configure TEST001 system monitoring `C:\data\test1`
2. ✅ Verify your setup is correct
3. ✅ Guide you to start monitoring service
4. ✅ Create test files automatically
5. ✅ Verify files are detected within 30 seconds
6. ✅ Test API endpoints
7. ✅ Show you the results

**Total time: 5 minutes**

---

## Manual Testing (If You Prefer)

### Step 1: Add Test System
```bash
python add_test_system.py
```

### Step 2: Start Monitoring (Terminal 1)
```bash
python start_monitoring.py
```

### Step 3: Create Test File (Terminal 2)
```bash
echo test > C:\data\test1\testfile.txt
```

### Step 4: Check Detection (Wait 30 seconds)
```bash
python check_test_system.py
```

### Step 5: Start API (Terminal 3)
```bash
python run_api.py
```

Visit: http://localhost:8000/docs

---

## Expected Results

After testing, you should see:

✅ **Monitoring Service**
```
Starting File Monitoring Service...
Found 1 active systems:
  - TEST001: Test System 1
✅ Monitoring started: TEST001
```

✅ **File Detection**
```
📁 Files detected (last 24 hours): 1

Recent files:
  1. testfile.txt
     Time: 2026-02-15 15:05:23
     Size: 6 bytes
```

✅ **API Response**
```json
{
  "systems": [
    {
      "id": "TEST001",
      "name": "Test System 1",
      "directory_path": "C:\\data\\test1",
      "is_active": true
    }
  ]
}
```

---

## What If Something Goes Wrong?

### No files detected?

1. Check monitoring is running (Terminal 1)
2. Verify directory: `dir C:\data\test1`
3. Create another test file
4. Wait 30 seconds and check again

### API not working?

1. Check API is running (Terminal 3)
2. Visit: http://localhost:8000/docs
3. Try the `/health` endpoint first

### Need help?

Check these guides:
- `TEST_SYSTEM_GUIDE.md` - Complete testing guide
- `CONFIGURATION_GUIDE.md` - Configuration help
- `SETUP_CHECKLIST.md` - Full setup process

---

## After Successful Test

Once your test passes:

1. **Stop test services** (Ctrl+C in terminals)

2. **Configure your 20 production systems**
   - Open `add_systems.py`
   - Update with your actual directories
   - Run `python add_systems.py`

3. **Start production monitoring**
   - `python start_monitoring.py`
   - `python run_api.py`

4. **Enjoy $0/month infrastructure costs!** 🎉

---

## Quick Commands

```bash
# Test system
python add_test_system.py          # Add test system
python check_test_system.py        # Check status
python test_workflow.py            # Full automated test

# Production setup
python add_systems.py              # Add 20 systems
python create_directories.py       # Create directories
python verify_configuration.py     # Verify setup

# Run services
python start_monitoring.py         # Start monitoring
python run_api.py                  # Start API

# Maintenance
python daily_check.py              # Daily health check
python backup_database.py          # Backup database
```

---

## Your System Capabilities

Once configured, your system will:

- 🔍 Monitor 20 source systems in real-time
- ⚡ Detect files within 30 seconds
- 📊 Track SLA compliance automatically
- 📈 Analyze trends with moving averages
- 🤖 Provide AI-powered insights (optional)
- 💰 Cost: $0/month infrastructure

**Annual savings: $2,160-$7,200 vs original design**

---

## Ready to Start?

Run this now:

```bash
python test_workflow.py
```

The automated workflow will guide you through everything!

---

## Documentation

- **This Guide**: Quick start with test system
- **TEST_SYSTEM_GUIDE.md**: Detailed testing guide
- **CONFIGURATION_GUIDE.md**: Configure 20 systems
- **SETUP_CHECKLIST.md**: Complete setup checklist
- **QUICK_START.md**: 5-minute production setup
- **DEPLOYMENT_GUIDE.md**: Production deployment
- **AI_IMPLEMENTATION_GUIDE.md**: AI features

---

Good luck! Your test directory `C:\data\test1` is ready to go! 🚀
