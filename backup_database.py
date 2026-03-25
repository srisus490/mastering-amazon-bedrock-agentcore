"""Backup SQLite database"""

import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    """Create database backup"""
    
    print("\n" + "=" * 60)
    print("💾 DATABASE BACKUP")
    print("=" * 60)
    
    db_file = Path("data/file_monitoring.db")
    
    if not db_file.exists():
        print("❌ Database file not found!")
        print(f"   Expected: {db_file.absolute()}")
        return
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"file_monitoring_{timestamp}.db"
    
    print(f"\nBacking up database...")
    print(f"  Source: {db_file}")
    print(f"  Destination: {backup_file}")
    
    # Copy database
    shutil.copy2(db_file, backup_file)
    
    size_kb = backup_file.stat().st_size / 1024
    print(f"\n✅ Backup created successfully!")
    print(f"   Size: {size_kb:.2f} KB")
    print(f"   Location: {backup_file.absolute()}")
    
    # Keep only last 7 backups
    print(f"\nCleaning old backups (keeping last 7)...")
    backups = sorted(backup_dir.glob("file_monitoring_*.db"), 
                    key=lambda p: p.stat().st_mtime, 
                    reverse=True)
    
    if len(backups) > 7:
        for old_backup in backups[7:]:
            old_backup.unlink()
            print(f"  🗑️  Deleted: {old_backup.name}")
    
    print(f"\nTotal backups: {min(len(backups), 7)}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    backup_database()
