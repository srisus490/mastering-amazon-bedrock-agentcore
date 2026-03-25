# Migration Checklist

## On Current Laptop (Before Migration)

### 1. Backup Your Work
- [ ] Run backup script: `python backup_for_migration.py`
- [ ] Verify backup ZIP file was created successfully
- [ ] Check backup includes `data/` folder (contains database)
- [ ] Backup file size looks reasonable (should be several MB)

### 2. Secure Sensitive Files
- [ ] Backup `.env` file separately (contains AWS credentials)
- [ ] Store `.env` in secure location (password manager, encrypted drive)
- [ ] Document any custom AWS configurations
- [ ] Note down any API keys or secrets not in `.env`

### 3. Document Custom Settings
- [ ] List monitored directory paths (from `add_systems.py`)
- [ ] Note any custom Kiro hooks or automations
- [ ] Document any special configurations
- [ ] Export any custom scripts you created

### 4. Transfer Files
- [ ] Copy backup ZIP to external drive or cloud storage
- [ ] Copy `.env` file separately (secure method)
- [ ] Copy any additional custom files
- [ ] Verify all files copied successfully

---

## On New Laptop (After Migration)

### 1. Install Prerequisites
- [ ] Install Python 3.10 or higher
- [ ] Verify Python installation: `python --version`
- [ ] Install pip (usually comes with Python)
- [ ] (Optional) Install uv: `pip install uv`

### 2. Install Kiro
- [ ] Download and install Kiro IDE
- [ ] Launch Kiro and verify it works
- [ ] Configure Kiro settings if needed

### 3. Restore Project Files
- [ ] Copy backup ZIP to new laptop
- [ ] Extract ZIP to desired location
- [ ] Navigate to project directory in terminal
- [ ] Verify all files extracted correctly

### 4. Setup Python Environment
```bash
# Create virtual environment
- [ ] python -m venv .venv

# Activate virtual environment (Windows)
- [ ] .venv\Scripts\activate

# Activate virtual environment (Mac/Linux)
- [ ] source .venv/bin/activate

# Install dependencies
- [ ] pip install -e ".[dev]"

# Verify installation
- [ ] pip list
```

### 5. Configure Environment
- [ ] Copy `.env` file to project root
- [ ] Open `.env` and verify all values
- [ ] Update `DATABASE_PATH` if needed
- [ ] Verify AWS credentials are correct
- [ ] Update `BEDROCK_REGION` if needed
- [ ] Check all other configuration values

### 6. Update Directory Paths
- [ ] Open `add_systems.py`
- [ ] Update all `directory_path` values for new laptop
- [ ] Create monitored directories if they don't exist
- [ ] Run: `python create_directories.py`
- [ ] Run: `python add_systems.py`

### 7. Verify Database
```bash
- [ ] python check_database.py
- [ ] Verify database file exists: data/file_monitoring.db
- [ ] Check database has your data
```

If database is missing or corrupted:
```bash
- [ ] python scripts/init_database.py
- [ ] python setup_test_data.py  # Optional
```

### 8. Test Everything
```bash
# Run tests
- [ ] pytest
- [ ] All tests should pass

# Test API
- [ ] python run_api.py
- [ ] Visit http://localhost:8000/docs
- [ ] Test a few API endpoints

# Test API programmatically
- [ ] python test_api.py
```

### 9. Test AI Features (If Using Bedrock)
```bash
- [ ] python test_ai_foundation.py
- [ ] Verify AWS credentials work
- [ ] Test AI insights generation
```

### 10. Verify Web Dashboard
- [ ] Open web dashboard in browser
- [ ] Check all pages load correctly
- [ ] Verify data displays properly
- [ ] Test AI insights features

### 11. Start Monitoring
```bash
- [ ] python start_monitoring.py
- [ ] Verify file monitoring is working
- [ ] Test by creating a file in monitored directory
- [ ] Check file appears in dashboard
```

---

## Verification Checklist

### Core Functionality
- [ ] API server starts without errors
- [ ] Database queries work
- [ ] File monitoring detects new files
- [ ] SLA tracking calculates correctly
- [ ] Trend analysis generates data

### AI Features (If Enabled)
- [ ] AWS Bedrock connection works
- [ ] AI insights generate successfully
- [ ] Forecasts are created
- [ ] Root cause analysis works

### Web Dashboard
- [ ] Dashboard loads in browser
- [ ] All pages accessible
- [ ] Data displays correctly
- [ ] Charts and graphs render
- [ ] AI features work (if enabled)

### Data Integrity
- [ ] Historical data preserved
- [ ] SLA configurations intact
- [ ] System configurations correct
- [ ] Trend data available

---

## Common Issues & Solutions

### Issue: Dependencies won't install
**Solution:**
```bash
# Update pip
python -m pip install --upgrade pip

# Try installing again
pip install -e ".[dev]"

# If still fails, install individually
pip install fastapi uvicorn sqlalchemy watchdog boto3
```

### Issue: Database not found
**Solution:**
```bash
# Check if data folder exists
ls data/

# If missing, initialize new database
python scripts/init_database.py

# Add test data
python setup_test_data.py
```

### Issue: AWS Bedrock not working
**Solution:**
```bash
# Verify credentials in .env
cat .env | grep AWS

# Test connection
python test_ai_foundation.py

# Check region setting
# Make sure BEDROCK_REGION matches your AWS setup
```

### Issue: Port 8000 already in use
**Solution:**
```bash
# Edit .env file
# Change API_PORT=8000 to API_PORT=8001

# Or kill process using port 8000
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -ti:8000 | xargs kill
```

### Issue: Directory paths don't exist
**Solution:**
```bash
# Edit add_systems.py with correct paths
# Then create directories
python create_directories.py

# Update database
python add_systems.py
```

---

## Quick Command Reference

```bash
# Backup (old laptop)
python backup_for_migration.py

# Setup (new laptop)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your values

# Verify
python check_database.py
pytest
python run_api.py

# Update paths
# Edit add_systems.py
python create_directories.py
python add_systems.py
```

---

## Success Criteria

You've successfully migrated when:
- [ ] All tests pass (`pytest`)
- [ ] API server runs without errors
- [ ] Web dashboard loads and displays data
- [ ] File monitoring detects new files
- [ ] AI features work (if enabled)
- [ ] Historical data is accessible
- [ ] No error messages in logs

---

## Need Help?

1. Check error messages in terminal
2. Review logs in application
3. Verify all prerequisites installed
4. Ensure AWS credentials valid
5. Check file paths are correct
6. Read MIGRATION_BACKUP_GUIDE.md for detailed instructions
7. Review TROUBLESHOOTING.md if available

---

## Post-Migration Tasks

- [ ] Test with real data for a few days
- [ ] Monitor for any errors or issues
- [ ] Verify SLA tracking accuracy
- [ ] Check AI insights quality
- [ ] Update any documentation with new paths
- [ ] Create new backup on new laptop
- [ ] Securely delete old laptop data (when ready)

---

**Estimated Migration Time:** 30-60 minutes

**Difficulty Level:** Moderate (requires basic command line knowledge)

**Prerequisites:** Python 3.10+, Kiro IDE, AWS credentials (if using AI features)
