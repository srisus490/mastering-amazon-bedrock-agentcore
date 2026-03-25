# Setup Checklist - Configure Your 20 Source Systems

Follow this checklist to get your file monitoring system up and running.

## ✅ Phase 0: Quick Test (Optional but Recommended, 5 minutes)

- [ ] **0.1** Test directory already created: `C:\data\test1` ✅

- [ ] **0.2** Run automated test workflow
  ```bash
  python test_workflow.py
  ```

- [ ] **0.3** OR run manual test:
  ```bash
  python add_test_system.py
  python start_monitoring.py  # Terminal 1
  echo test > C:\data\test1\testfile.txt
  python check_test_system.py
  ```

- [ ] **0.4** Verify test passed (file detected within 30 seconds)

- [ ] **0.5** Review `TEST_SYSTEM_GUIDE.md` for detailed testing

**Why test first?** Validates your setup works before configuring 20 systems.

---

## ✅ Phase 1: Initial Setup (5 minutes)

- [ ] **1.1** Virtual environment activated
  ```bash
  .venv\Scripts\activate  # Windows
  # source .venv/bin/activate  # Linux/Mac
  ```

- [ ] **1.2** Dependencies installed
  ```bash
  pip install -e ".[dev]"
  ```

- [ ] **1.3** Database initialized
  ```bash
  python scripts/init_database.py
  ```

## ✅ Phase 2: Configure Your Systems (15-30 minutes)

- [ ] **2.1** Open `add_systems.py` in your editor

- [ ] **2.2** Update all 20 systems with your actual information:
  - [ ] System IDs (e.g., PROD_SALES, PROD_INVENTORY)
  - [ ] System names (human-readable)
  - [ ] Directory paths (where files arrive)
  - [ ] Expected arrival times
  - [ ] SLA windows (tolerance in minutes)
  - [ ] Minimum files per day

- [ ] **2.3** Review `CONFIGURATION_GUIDE.md` for examples and best practices

## ✅ Phase 3: Create Directories (2 minutes)

- [ ] **3.1** Run directory creation script
  ```bash
  python create_directories.py
  ```

- [ ] **3.2** Verify all directories were created successfully

## ✅ Phase 4: Add Systems to Database (1 minute)

- [ ] **4.1** Run configuration script
  ```bash
  python add_systems.py
  ```

- [ ] **4.2** Verify output shows all 20 systems added

## ✅ Phase 5: Verify Configuration (2 minutes)

- [ ] **5.1** Run verification script
  ```bash
  python verify_configuration.py
  ```

- [ ] **5.2** Fix any issues reported:
  - [ ] Missing directories
  - [ ] Permission problems
  - [ ] Missing SLA definitions

- [ ] **5.3** Re-run verification until all checks pass

## ✅ Phase 6: Start Services (2 minutes)

- [ ] **6.1** Start API server (Terminal 1)
  ```bash
  python run_api.py
  ```

- [ ] **6.2** Start file monitoring (Terminal 2)
  ```bash
  python start_monitoring.py
  ```

- [ ] **6.3** Verify both services are running without errors

## ✅ Phase 7: Test the System (5 minutes)

- [ ] **7.1** Open API documentation
  - Visit: http://localhost:8000/docs

- [ ] **7.2** Test basic endpoints:
  - [ ] GET `/health` - System health check
  - [ ] GET `/api/v1/source-systems` - List all 20 systems
  - [ ] GET `/api/v1/file-arrivals/count` - Count detected files

- [ ] **7.3** Create a test file in one of your monitored directories

- [ ] **7.4** Verify file was detected:
  - [ ] Check API: GET `/api/v1/file-arrivals?days=1`
  - [ ] Check monitoring service logs

## ✅ Phase 8: Configure AI Features (Optional, 10 minutes)

- [ ] **8.1** Set up AWS credentials
  ```bash
  aws configure
  ```

- [ ] **8.2** Enable Bedrock models in AWS Console
  - [ ] Anthropic Claude 3 Sonnet
  - [ ] Anthropic Claude 3 Haiku (optional)

- [ ] **8.3** Test AI features
  ```bash
  python test_ai.py
  ```

- [ ] **8.4** Try AI endpoints in API docs:
  - [ ] POST `/api/v1/ai/analyze-anomalies/{system_id}`
  - [ ] POST `/api/v1/ai/predict/{system_id}`
  - [ ] POST `/api/v1/ai/recommend-sla/{system_id}`

## ✅ Phase 9: Production Setup (15 minutes)

- [ ] **9.1** Set up daily health checks
  - [ ] Schedule `daily_check.py` to run at 8 AM daily
  - [ ] Windows: Task Scheduler
  - [ ] Linux: cron job

- [ ] **9.2** Set up database backups
  - [ ] Schedule `backup_database.py` to run at 2 AM daily
  - [ ] Verify backup directory exists

- [ ] **9.3** Configure as system service (optional)
  - [ ] Windows: Use NSSM (see DEPLOYMENT_GUIDE.md)
  - [ ] Linux: Create systemd service (see DEPLOYMENT_GUIDE.md)

- [ ] **9.4** Set up monitoring/alerting (optional)
  - [ ] Email notifications for SLA violations
  - [ ] Slack/Teams integration
  - [ ] Dashboard for visualization

## ✅ Phase 10: Documentation & Training (10 minutes)

- [ ] **10.1** Document your configuration
  - [ ] List all 20 systems and their purposes
  - [ ] Note any special SLA requirements
  - [ ] Document maintenance windows

- [ ] **10.2** Train team members
  - [ ] Show them the API documentation
  - [ ] Explain SLA scores and violations
  - [ ] Demonstrate AI features

- [ ] **10.3** Create runbook for common issues
  - [ ] What to do if monitoring stops
  - [ ] How to add/remove systems
  - [ ] How to adjust SLA settings

---

## Quick Reference Commands

### Daily Operations
```bash
# Start everything
python start_all.py

# Check system health
python daily_check.py

# Backup database
python backup_database.py

# View logs
# (Check terminal output or redirect to log files)
```

### Configuration Changes
```bash
# Add new systems
python add_systems.py

# Verify configuration
python verify_configuration.py

# Create missing directories
python create_directories.py
```

### Testing
```bash
# Test API endpoints
python test_api.py

# Test SLA tracking
python test_sla_tracking.py

# Test AI features
python test_ai.py

# Run all unit tests
pytest
```

### Troubleshooting
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -ti:8000  # Linux/Mac

# Verify database
dir data\file_monitoring.db  # Windows
ls -lh data/file_monitoring.db  # Linux/Mac

# Check Python version
python --version  # Should be 3.10+
```

---

## Success Criteria

Your system is ready when:

✅ All 20 source systems are configured in database  
✅ All directories exist and are writable  
✅ API server is running on http://localhost:8000  
✅ File monitoring service is running  
✅ Test files are detected within 30 seconds  
✅ SLA scores are calculated correctly  
✅ API endpoints return expected data  
✅ (Optional) AI features are working  

---

## Cost Summary

**Infrastructure Costs:**
- Database: $0 (SQLite)
- Message Queue: $0 (removed)
- Cache: $0 (removed)
- Time-series DB: $0 (removed)
- **Total Infrastructure: $0/month**

**AI Costs (Optional):**
- Amazon Bedrock: ~$30-60/month (100 queries/day)
- **Total with AI: $30-60/month**

**Savings vs Original Design:**
- Original: $180-600/month
- Current: $0-60/month
- **Savings: $120-600/month (90-95% reduction)**
- **Annual Savings: $1,440-7,200/year**

---

## Support Resources

- **Quick Start**: `QUICK_START.md`
- **Configuration**: `CONFIGURATION_GUIDE.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **AI Features**: `AI_IMPLEMENTATION_GUIDE.md`
- **API Docs**: http://localhost:8000/docs (when running)
- **Testing**: `TESTING_GUIDE.md`

---

## Next Steps After Setup

1. **Monitor for 1 week** - Let the system collect data
2. **Review SLA scores** - Check if thresholds are appropriate
3. **Use AI recommendations** - Optimize SLA settings after 30 days
4. **Build dashboard** (optional) - Create custom visualizations
5. **Set up alerts** (optional) - Email/Slack notifications

---

## Congratulations! 🎉

You now have a production-ready file monitoring system that:
- Monitors 20 source systems in real-time
- Tracks SLA compliance automatically
- Provides AI-powered insights
- Costs $0-60/month (vs $180-600/month)
- Saves $1,440-7,200/year

**Your system is ready to go!**
