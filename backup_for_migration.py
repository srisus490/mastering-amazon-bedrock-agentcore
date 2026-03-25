#!/usr/bin/env python3
"""
Backup script for migrating to a new laptop.
Creates a comprehensive backup ZIP file with all essential project files.
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path
import shutil

# Directories and files to include in backup
INCLUDE_DIRS = [
    "src",
    "tests",
    "scripts",
    "config",
    "data",  # CRITICAL: Contains SQLite database
    "web-dashboard",
    "alembic",
    "capstone_project",
    "docker",
    "kb-documents",
    "runtime",
    ".kiro",  # Kiro configurations
]

INCLUDE_FILES = [
    # Configuration
    ".env",  # IMPORTANT: Contains AWS credentials
    ".env.example",
    ".gitignore",
    ".python-version",
    "pyproject.toml",
    "uv.lock",
    "alembic.ini",
    "Makefile",
    
    # Documentation
    "README.md",
    "LICENSE",
    "GETTING_STARTED.md",
    "SETUP_GUIDE.md",
    "CONFIGURATION_GUIDE.md",
    "DEPLOYMENT_GUIDE.md",
    "TESTING_GUIDE.md",
    "MIGRATION_GUIDE.md",
    "MIGRATION_BACKUP_GUIDE.md",
    "PERMISSIONS_GUIDE.md",
    "TEST_SYSTEM_GUIDE.md",
    "SETUP_CHECKLIST.md",
    "QUICK_START.md",
    "BEDROCK_AGENT_SETUP.md",
    
    # Implementation docs
    "AI_BACKEND_COMPLETE.md",
    "AI_FRONTEND_COMPLETE.md",
    "AI_IMPLEMENTATION_GUIDE.md",
    "AI_INSIGHTS_FIXED.md",
    "AI_TROUBLESHOOTING.md",
    "IMPLEMENTATION_COMPLETE.md",
    "KB_INTEGRATION_COMPLETE.md",
    "NEW_FEATURES.md",
    "COST_REDUCTION_SUMMARY.md",
    "FINAL_COST_SAVINGS.md",
    
    # Scripts
    "run_api.py",
    "setup.sh",
    "add_systems.py",
    "add_test_system.py",
    "backup_database.py",
    "check_database.py",
    "check_endpoints.py",
    "check_models.py",
    "check_test_system.py",
    "complete_agent_setup.py",
    "create_directories.py",
    "create_test_files.py",
    "daily_check.py",
    "fix_permissions.py",
    "setup_bedrock_agent.py",
    "setup_test_data.py",
    "simple_agent_setup.py",
    "start_monitoring.py",
    "verify_configuration.py",
    "verify_setup.py",
    
    # Test files
    "test_agent.py",
    "test_ai_api.py",
    "test_ai_foundation.py",
    "test_ai_generation.py",
    "test_ai.py",
    "test_api.py",
    "test_date_format.py",
    "test_file_monitor.py",
    "test_forecast_debug.py",
    "test_forecast_direct.py",
    "test_frontend_api.py",
    "test_insights_service.py",
    "test_performance.py",
    "test_sla_tracking.py",
    "test_summary_api.py",
    "test_trend_analyzer.py",
    "test_trends_api.py",
    "test_trends.py",
    "test_workflow.py",
]

# Directories to exclude (auto-generated or not needed)
EXCLUDE_DIRS = [
    ".venv",
    "venv",
    "ENV",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".hypothesis",
    "htmlcov",
    ".git",
    ".vscode",
    ".idea",
    "node_modules",
    "dist",
    "build",
    "*.egg-info",
]

# File patterns to exclude
EXCLUDE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".coverage",
    "*.log",
    "*.swp",
    "*.swo",
    ".DS_Store",
    "Thumbs.db",
]


def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded from backup."""
    path_str = str(path)
    
    # Check if any parent directory is in exclude list
    for exclude_dir in EXCLUDE_DIRS:
        if f"/{exclude_dir}/" in path_str or f"\\{exclude_dir}\\" in path_str:
            return True
        if path.name == exclude_dir:
            return True
    
    # Check file patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*."):
            ext = pattern[1:]
            if path_str.endswith(ext):
                return True
        elif path.name == pattern:
            return True
    
    return False


def create_backup():
    """Create a comprehensive backup ZIP file."""
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f"intelligent-file-monitoring-backup-{timestamp}.zip"
    
    print(f"Creating backup: {backup_filename}")
    print("=" * 60)
    
    # Track statistics
    files_added = 0
    dirs_added = 0
    total_size = 0
    
    with zipfile.ZipFile(backup_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual files
        print("\nBacking up configuration and documentation files...")
        for file_path in INCLUDE_FILES:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                zipf.write(file_path)
                files_added += 1
                total_size += file_size
                print(f"  ✓ {file_path} ({file_size:,} bytes)")
            else:
                print(f"  ⚠ Skipped (not found): {file_path}")
        
        # Add directories
        print("\nBacking up directories...")
        for dir_name in INCLUDE_DIRS:
            if os.path.exists(dir_name):
                dir_path = Path(dir_name)
                print(f"\n  Processing: {dir_name}/")
                
                # Walk through directory
                for root, dirs, files in os.walk(dir_path):
                    root_path = Path(root)
                    
                    # Skip excluded directories
                    if should_exclude(root_path):
                        continue
                    
                    # Filter out excluded subdirectories
                    dirs[:] = [d for d in dirs if not should_exclude(root_path / d)]
                    
                    # Add files
                    for file in files:
                        file_path = root_path / file
                        
                        if should_exclude(file_path):
                            continue
                        
                        try:
                            file_size = file_path.stat().st_size
                            zipf.write(file_path)
                            files_added += 1
                            total_size += file_size
                            print(f"    ✓ {file_path} ({file_size:,} bytes)")
                        except Exception as e:
                            print(f"    ✗ Error adding {file_path}: {e}")
                
                dirs_added += 1
            else:
                print(f"  ⚠ Skipped (not found): {dir_name}/")
    
    # Print summary
    print("\n" + "=" * 60)
    print("BACKUP COMPLETE!")
    print("=" * 60)
    print(f"Backup file: {backup_filename}")
    print(f"Total files: {files_added}")
    print(f"Directories: {dirs_added}")
    print(f"Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    print(f"Compressed: {os.path.getsize(backup_filename):,} bytes "
          f"({os.path.getsize(backup_filename) / 1024 / 1024:.2f} MB)")
    
    # Important reminders
    print("\n" + "=" * 60)
    print("IMPORTANT REMINDERS:")
    print("=" * 60)
    print("1. ✓ Database backed up (data/ folder)")
    print("2. ✓ Environment variables backed up (.env file)")
    print("3. ✓ Kiro configurations backed up (.kiro/ folder)")
    print("4. ⚠ Keep .env file secure (contains AWS credentials!)")
    print("5. ⚠ Update directory paths in add_systems.py on new laptop")
    print("6. ⚠ Verify AWS credentials work on new laptop")
    print("\nNext steps:")
    print("1. Copy this ZIP file to your new laptop")
    print("2. Extract it to your desired location")
    print("3. Follow MIGRATION_BACKUP_GUIDE.md for restoration steps")
    print("=" * 60)
    
    return backup_filename


if __name__ == "__main__":
    try:
        backup_file = create_backup()
        print(f"\n✓ Backup successful: {backup_file}")
        print("\nRead MIGRATION_BACKUP_GUIDE.md for restoration instructions.")
    except Exception as e:
        print(f"\n✗ Backup failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
