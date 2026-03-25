# Migration Backup Guide

## Overview
This guide helps you backup your Intelligent File Monitoring System and restore it on a new laptop.

## What Gets Backed Up

### Essential Files (Must Backup)
1. **Source Code**: All Python files, configuration, and scripts
2. **Database**: SQLite database with all your monitoring data
3. **Configuration**: Environment variables and settings
4. **Documentation**: All markdown files and guides
5. **Kiro Settings**: .kiro folder with specs and configurations

### Files NOT Backed Up (Auto-generated)
- Virtual environment (.venv/)
- Python cache (__pycache__/)
- Test coverage reports (htmlcov/, .coverage)
- Git history (.git/)
- IDE settings (.vscode/)
- Temporary files (.hypothesis/, .pytest_cache/)

## Backup Methods

### Method 1: Automated Backup Script (Recommended)
```bash
python backup_for_migration.py
```

This creates a timestamped ZIP file containing:
- All source code
- Database files
- Configuration files
- Documentation
- Kiro settings

### Method 2: Git Repository (If Using Git)
```bash
# Commit all changes
git add .
git commit -m "Pre-migration backup"

# Push to remote repository
git push origin main

# On new laptop, simply clone
git clone <your-repo-url>
```

### Method 3: Manual Backup
Copy these folders/files to external drive or cloud storage:
- `src/` - Source code
- `config/` - Configuration files
- `scripts/` - Utility scripts
- `tests/` - Test suite
- `data/` - Database files (IMPORTANT!)
- `.kiro/` - Kiro settings
- `web-dashboard/` - Frontend code
- `.env` - Environment variables (contains AWS credentials!)
- `pyproject.toml` - Dependencies
- `README.md` and all documentation files

## Restoration on New Laptop

### Step 1: Install Prerequisites
```bash
# Install Python 3.10 or higher
python --version  # Verify installation

# Install uv (Python package manager) - Optional but recommended
pip install uv
```

### Step 2: Install Kiro
Follow Kiro installation instructions for your new laptop.

### Step 3: Restore Project Files

#### If using automated backup:
```bash
# Extract the backup ZIP file
unzip intelligent-file-monitoring-backup-YYYYMMDD-HHMMSS.zip -d /path/to/new/location
cd /path/to/new/location
```

#### If using Git:
```bash
git clone <your-repo-url>
cd intelligent-file-monitoring
```

### Step 4: Setup Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### Step 5: Configure Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
# IMPORTANT: Update these values:
# - AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# - Database path (if different)
# - API configuration
```

### Step 6: Verify Database
```bash
# Check database integrity
python check_database.py

# If database is missing or corrupted, initialize fresh:
python scripts/init_database.py
python setup_test_data.py  # Optional: add test data
```

### Step 7: Test Everything
```bash
# Run tests
pytest

# Start API server
python run_api.py

# Test API endpoints
python test_api.py

# Visit http://localhost:8000/docs to verify API is working
```

### Step 8: Update Directory Paths
If your monitored directories have different paths on the new laptop:
```bash
# Edit add_systems.py with new paths
# Then update database:
python add_systems.py
```

## Important Notes

### AWS Credentials
Your `.env` file contains AWS credentials for Bedrock AI. Make sure to:
1. Backup `.env` securely (don't commit to public repos!)
2. Verify AWS credentials work on new laptop
3. Update region if needed

### Database Location
The SQLite database is in `data/file_monitoring.db`. This file contains:
- All file arrival records
- SLA tracking data
- Trend analysis history
- System configurations

**CRITICAL**: Always backup this file!

### Monitored Directories
Update directory paths in `add_systems.py` if they differ on new laptop:
```python
{
    "directory_path": "C:\\data\\sales",  # Update this path
}
```

### Kiro Configuration
The `.kiro/` folder contains:
- Specs for features built with Kiro
- Custom agent configurations
- Hooks and automation rules

This folder should be backed up to preserve your Kiro workflows.

## Troubleshooting

### Database Issues
```bash
# Check database
python check_database.py

# Reinitialize if needed
python scripts/init_database.py
```

### Missing Dependencies
```bash
# Reinstall all dependencies
pip install -e ".[dev]"
```

### API Not Starting
```bash
# Check port availability
# Update API_PORT in .env if 8000 is taken

# Check logs
python run_api.py  # Look for error messages
```

### AWS Bedrock Not Working
```bash
# Verify credentials
python test_ai_foundation.py

# Check region setting in .env
BEDROCK_REGION=us-east-1
```

## Backup Checklist

- [ ] Run backup script or commit to Git
- [ ] Verify backup contains `data/` folder with database
- [ ] Backup `.env` file separately (secure location!)
- [ ] Export any custom Kiro configurations
- [ ] Document any custom directory paths
- [ ] Note any special AWS configurations
- [ ] Save any custom scripts you created

## Restoration Checklist

- [ ] Install Python 3.10+
- [ ] Install Kiro
- [ ] Extract/clone project files
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Configure `.env` file
- [ ] Verify database exists and is valid
- [ ] Update directory paths if needed
- [ ] Run tests
- [ ] Start API server
- [ ] Verify web dashboard works

## Support

If you encounter issues during migration:
1. Check error messages in terminal
2. Review logs in the application
3. Verify all prerequisites are installed
4. Ensure AWS credentials are valid
5. Check that all file paths are correct for new laptop

## Quick Reference Commands

```bash
# Backup
python backup_for_migration.py

# Restore and setup
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your values
python check_database.py
pytest
python run_api.py

# Update paths
# Edit add_systems.py
python add_systems.py
```
