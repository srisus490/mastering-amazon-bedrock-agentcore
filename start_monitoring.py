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
            print("\nPlease add systems first:")
            print("  1. Edit add_systems.py with your directories")
            print("  2. Run: python add_systems.py")
            return
        
        print(f"Found {len(systems)} active system(s):\n")
        for sys in systems:
            _ = (sys.id, sys.name, sys.directory_path)
            session.expunge(sys)
            print(f"  📁 {sys.id}: {sys.name}")
            print(f"     Path: {sys.directory_path}")
    
    # Create database writer
    db_writer = DatabaseWriter()
    
    # Start monitoring each system
    watchers = []
    print("\nStarting watchers...")
    for sys in systems:
        # Ensure directory exists
        path = Path(sys.directory_path)
        if not path.exists():
            print(f"⚠️  Creating directory: {path}")
            path.mkdir(parents=True, exist_ok=True)
        
        # Create watcher
        watcher = DirectoryWatcher(
            source_system_id=sys.id,
            directory_path=sys.directory_path,
            database_writer=db_writer,
        )
        
        watcher.start_monitoring()
        watchers.append(watcher)
        print(f"✅ Monitoring: {sys.id}")
    
    print("\n" + "=" * 50)
    print("🔍 File monitoring is running...")
    print("\nMonitoring directories:")
    for sys in systems:
        print(f"  - {sys.directory_path}")
    print("\nPress Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 50)
        print("Stopping monitoring...")
        for watcher in watchers:
            watcher.stop_monitoring()
        print("✅ Monitoring stopped")
        print("=" * 50)

if __name__ == "__main__":
    start_monitoring()
