# Deployment & Implementation Guide

Complete guide to implement the Intelligent File Monitoring System in your environment.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Starting the System](#starting-the-system)
5. [Production Deployment](#production-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Windows, Linux, or macOS
- **Python**: 3.10 or higher
- **Disk Space**: 500MB minimum (grows with data)
- **RAM**: 512MB minimum
- **Network**: Port 8000 available for API

### Check Python Version
```bash
python --version
# Should show Python 3.10.x or higher
```

---

## Installation

### Step 1: Clone/Download Project
```bash
# If using Git
git clone <repository-url>
cd intelligent-file-monitoring

# Or download and extract ZIP file
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install all dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import src; print('✅ Installation successful')"
```

### Step 4: Initialize Database
```bash
# Create database with schema
python scripts/init_database.py

# Verify database created
dir data\file_monitoring.db  # Windows
ls -lh data/file_monitoring.db  # Linux/Mac
```

**Expected Output:**
```
Database initialized successfully
Created 3 sample source systems
```

---

## Configuration

### Step 1: Configure Source Systems

Edit `config/monitoring_config.json`:

```json
{
  "source_systems": [
    {
      "id": "PROD_SALES",
      "name": "Production Sales System",
      "directory_path": "C:\\data\\sales",
      "is_active": true,
      "file_pattern": "*.csv",
      "sla": {
        "expected_arrival_time": "09:00:00",
        "window_minutes": 30,
        "minimum_files_per_day": 5
      }
    },
    {
      "id": "PROD_INVENTORY",
      "name": "Production Inventory System",
      "directory_path": "C:\\data\\inventory",
      "is_active": true,
      "file_pattern": "*.xlsx",
      "sla": {
        "expected_arrival_time": "10:00:00",
        "window_minutes": 60,
        "minimum_files_per_day": 3
      }
    }
  ]
}
```

### Step 2: Add Systems to Database

Create `add_systems.py`:

```python
"""Add your source systems to database"""

from datetime import date, time
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel, SLADefinitionModel

def add_systems():
    init_db()
    
    systems = [
        {
            "id": "PROD_SALES",
            "name": "Production Sales System",
            "directory_path": "C:\\data\\sales",
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(9, 0, 0),
                "window_minutes": 30,
                "minimum_files_per_day": 5,
            }
        },
        {
            "id": "PROD_INVENTORY",
            "name": "Production Inventory System",
            "directory_path": "C:\\data\\inventory",
            "is_active": True,
            "sla": {
                "expected_arrival_time": time(10, 0, 0),
                "window_minutes": 60,
                "minimum_files_per_day": 3,
            }
        },
    ]
    
    with get_db_session() as session:
        for sys_config in systems:
            # Check if exists
            existing = session.query(SourceSystemModel).filter_by(
                id=sys_config["id"]
            ).first()
            
            if existing:
                print(f"⚠️  System {sys_config['id']} already exists")
                continue
            
            # Create source system
            system = SourceSystemModel(
                id=sys_config["id"],
                name=sys_config["name"],
                directory_path=sys_config["directory_path"],
                is_active=sys_config["is_active"],
            )
            session.add(system)
            
            # Create SLA definition
            sla = SLADefinitionModel(
                source_system_id=sys_config["id"],
                expected_arrival_time=sys_config["sla"]["expected_arrival_time"],
                expected_arrival_window_minutes=sys_config["sla"]["window_minutes"],
                minimum_files_per_day=sys_config["sla"]["minimum_files_per_day"],
                weight=1.0,
                effective_from=date(2026, 1, 1),
                effective_to=None,
            )
            session.add(sla)
            
            print(f"✅ Added system: {sys_config['id']}")
        
        session.commit()
    
    print("\n✅ All systems configured!")

if __name__ == "__main__":
    add_systems()
```

Run it:
```bash
python add_systems.py
```

### Step 3: Environment Variables (Optional)

Create `.env` file:
```bash
# Database
DATABASE_URL=sqlite:///data/file_monitoring.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

---

## Starting the System

### Option 1: Start API Only (Recommended for Testing)

```bash
# Start API server
python run_api.py
```

**Access:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Source Systems: http://localhost:8000/api/v1/source-systems

### Option 2: Start File Monitoring Only

Create `start_monitoring.py`:

```python
"""Start file monitoring service"""

import time
from pathlib import Path
from src.monitor.watcher import DirectoryWatcher
from src.monitor.database_writer import DatabaseWriter
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel

def start_monitoring():
    """Start monitoring all active source systems"""
    
    init_db()
    
    print("Starting File Monitoring Service...")
    print("=" * 50)
    
    # Get active source systems
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).filter_by(
            is_active=True
        ).all()
        
        if not systems:
            print("❌ No active source systems found!")
            print("   Run: python add_systems.py")
            return
        
        print(f"Found {len(systems)} active systems:")
        for sys in systems:
            _ = (sys.id, sys.name, sys.directory_path)
            session.expunge(sys)
            print(f"  - {sys.id}: {sys.name}")
            print(f"    Path: {sys.directory_path}")
    
    # Create database writer
    db_writer = DatabaseWriter()
    
    # Start monitoring each system
    watchers = []
    for sys in systems:
        # Ensure directory exists
        path = Path(sys.directory_path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Create watcher
        watcher = DirectoryWatcher(
            source_system_id=sys.id,
            directory_path=sys.directory_path,
            database_writer=db_writer,
        )
        
        watcher.start()
        watchers.append(watcher)
        print(f"✅ Monitoring started: {sys.id}")
    
    print("\n" + "=" * 50)
    print("File monitoring is running...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping monitoring...")
        for watcher in watchers:
            watcher.stop()
        print("✅ Monitoring stopped")

if __name__ == "__main__":
    start_monitoring()
```

Run it:
```bash
python start_monitoring.py
```

### Option 3: Start Both (Production Setup)

Create `start_all.py`:

```python
"""Start both API and file monitoring"""

import subprocess
import sys
import time

def start_all():
    """Start API and monitoring in separate processes"""
    
    print("Starting Intelligent File Monitoring System...")
    print("=" * 50)
    
    # Start API server
    print("\n1. Starting API server...")
    api_process = subprocess.Popen(
        [sys.executable, "run_api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)  # Wait for API to start
    print("   ✅ API server started (PID: {})".format(api_process.pid))
    print("   📍 API Docs: http://localhost:8000/docs")
    
    # Start file monitoring
    print("\n2. Starting file monitoring...")
    monitor_process = subprocess.Popen(
        [sys.executable, "start_monitoring.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)
    print("   ✅ File monitoring started (PID: {})".format(monitor_process.pid))
    
    print("\n" + "=" * 50)
    print("✅ System is running!")
    print("\nAccess:")
    print("  - API Documentation: http://localhost:8000/docs")
    print("  - Health Check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        # Keep running
        api_process.wait()
        monitor_process.wait()
    except KeyboardInterrupt:
        print("\n\nStopping all services...")
        api_process.terminate()
        monitor_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    start_all()
```

Run it:
```bash
python start_all.py
```

---

## Production Deployment

### Option A: Windows Service

Create `install_service.py`:

```python
"""Install as Windows service using NSSM"""

import subprocess
import sys
from pathlib import Path

def install_service():
    """Install as Windows service"""
    
    # Download NSSM first: https://nssm.cc/download
    nssm_path = "nssm.exe"  # Add to PATH or use full path
    
    project_dir = Path(__file__).parent.absolute()
    python_exe = sys.executable
    script_path = project_dir / "start_all.py"
    
    # Install API service
    subprocess.run([
        nssm_path, "install", "FileMonitoringAPI",
        python_exe, str(script_path)
    ])
    
    # Set service description
    subprocess.run([
        nssm_path, "set", "FileMonitoringAPI",
        "Description", "Intelligent File Monitoring System"
    ])
    
    # Set startup directory
    subprocess.run([
        nssm_path, "set", "FileMonitoringAPI",
        "AppDirectory", str(project_dir)
    ])
    
    print("✅ Service installed!")
    print("\nTo start:")
    print("  net start FileMonitoringAPI")
    print("\nTo stop:")
    print("  net stop FileMonitoringAPI")

if __name__ == "__main__":
    install_service()
```

### Option B: Linux Systemd Service

Create `/etc/systemd/system/file-monitoring.service`:

```ini
[Unit]
Description=Intelligent File Monitoring System
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/intelligent-file-monitoring
Environment="PATH=/path/to/intelligent-file-monitoring/.venv/bin"
ExecStart=/path/to/intelligent-file-monitoring/.venv/bin/python start_all.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable file-monitoring
sudo systemctl start file-monitoring
sudo systemctl status file-monitoring
```

### Option C: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e ".[dev]"

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data

# Initialize database
RUN python scripts/init_database.py

# Expose API port
EXPOSE 8000

# Start application
CMD ["python", "start_all.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  file-monitoring:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - /your/data/directory:/data/monitored
    restart: unless-stopped
    environment:
      - DATABASE_URL=sqlite:///data/file_monitoring.db
      - API_HOST=0.0.0.0
      - API_PORT=8000
```

Deploy:
```bash
docker-compose up -d
docker-compose logs -f
```

---

## Monitoring & Maintenance

### Daily Checks

Create `daily_check.py`:

```python
"""Daily health check script"""

from datetime import date, timedelta
from src.database.connection import init_db, get_db_session
from src.database.models import FileArrivalModel, SLAViolationModel
from src.sla.calculator import ScoreCalculator

def daily_check():
    """Run daily health check"""
    
    init_db()
    
    print("Daily Health Check")
    print("=" * 50)
    print(f"Date: {date.today()}")
    
    # Check file arrivals today
    with get_db_session() as session:
        today_start = date.today()
        count = session.query(FileArrivalModel).filter(
            FileArrivalModel.arrival_timestamp >= today_start
        ).count()
        print(f"\n✅ Files detected today: {count}")
    
    # Check SLA violations
    with get_db_session() as session:
        violations = session.query(SLAViolationModel).filter(
            SLAViolationModel.violation_date == date.today()
        ).count()
        
        if violations > 0:
            print(f"⚠️  SLA violations today: {violations}")
        else:
            print(f"✅ No SLA violations today")
    
    # Check SLA scores
    calculator = ScoreCalculator()
    with get_db_session() as session:
        from src.database.models import SourceSystemModel
        systems = session.query(SourceSystemModel).filter_by(
            is_active=True
        ).all()
        
        print(f"\n📊 SLA Scores:")
        for sys in systems:
            _ = (sys.id, sys.name)
            session.expunge(sys)
            
            score = calculator.calculate_daily_score(sys.id, date.today())
            status = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
            print(f"  {status} {sys.id}: {score:.1f}/100")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    daily_check()
```

Schedule it:
```bash
# Windows Task Scheduler
# Linux cron: 0 8 * * * /path/to/.venv/bin/python /path/to/daily_check.py
```

### Database Backup

Create `backup_database.py`:

```python
"""Backup SQLite database"""

import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    """Create database backup"""
    
    db_file = Path("data/file_monitoring.db")
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"file_monitoring_{timestamp}.db"
    
    shutil.copy2(db_file, backup_file)
    
    print(f"✅ Database backed up to: {backup_file}")
    print(f"   Size: {backup_file.stat().st_size / 1024:.2f} KB")
    
    # Keep only last 7 backups
    backups = sorted(backup_dir.glob("*.db"), key=lambda p: p.stat().st_mtime)
    if len(backups) > 7:
        for old_backup in backups[:-7]:
            old_backup.unlink()
            print(f"   Deleted old backup: {old_backup.name}")

if __name__ == "__main__":
    backup_database()
```

Schedule daily:
```bash
# Run at 2 AM daily
# Windows: Task Scheduler
# Linux cron: 0 2 * * * /path/to/.venv/bin/python /path/to/backup_database.py
```

### Log Rotation

Logs are written to console. To save to file:

```bash
# Redirect output to log file
python start_all.py > logs/app.log 2>&1

# Or use logrotate on Linux
```

---

## Troubleshooting

### Issue: API won't start - Port in use
```bash
# Windows: Find process using port 8000
netstat -ano | findstr :8000

# Kill it
taskkill /F /PID <process_id>

# Linux: Find and kill
lsof -ti:8000 | xargs kill -9
```

### Issue: Database locked
```bash
# Check for stale connections
# Restart the application
# SQLite WAL mode should prevent this
```

### Issue: Files not being detected
```bash
# Check directory permissions
# Verify directory path in database
# Check if system is active
python -c "from src.database.connection import init_db, get_db_session; from src.database.models import SourceSystemModel; init_db(); s = get_db_session().__enter__(); sys = s.query(SourceSystemModel).all(); [print(f'{x.id}: {x.directory_path} (active={x.is_active})') for x in sys]"
```

### Issue: High memory usage
```bash
# Check database size
dir data\file_monitoring.db  # Windows
ls -lh data/file_monitoring.db  # Linux

# Vacuum database if large
python -c "from src.database.connection import init_db, get_engine; init_db(); get_engine().execute('VACUUM')"
```

---

## Next Steps

1. ✅ **Test the system** with sample data
2. ✅ **Configure your source systems**
3. ✅ **Start monitoring**
4. ✅ **Access API documentation** at http://localhost:8000/docs
5. ✅ **Set up daily health checks**
6. ✅ **Configure database backups**
7. 📊 **Build custom dashboard** (optional)
8. 🔔 **Add alerting** (optional)

---

## Support & Resources

- **Documentation**: See README.md and IMPLEMENTATION_COMPLETE.md
- **API Docs**: http://localhost:8000/docs (when running)
- **Testing Guide**: TESTING_GUIDE.md
- **GitHub Issues**: Report bugs and request features

---

## Summary

You now have a complete, production-ready file monitoring system with:
- ✅ Real-time file detection
- ✅ SLA tracking and scoring
- ✅ REST API with comprehensive endpoints
- ✅ Zero infrastructure costs
- ✅ Easy deployment options
- ✅ Automated monitoring and backups

The system is ready to monitor your 20 source systems with thousands of files per day!
