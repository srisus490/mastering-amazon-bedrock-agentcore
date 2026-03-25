"""Create directories for all configured source systems"""

from pathlib import Path
from src.database.connection import init_db, get_db_session
from src.database.models import SourceSystemModel

def create_directories():
    """Create all directories needed for monitoring"""
    
    print("Creating Directories for Source Systems")
    print("=" * 60)
    
    init_db()
    
    with get_db_session() as session:
        systems = session.query(SourceSystemModel).all()
        
        if not systems:
            print("❌ No systems configured!")
            print("   Run: python add_systems.py first")
            return
        
        print(f"\nFound {len(systems)} configured systems\n")
        
        created = []
        existed = []
        failed = []
        
        for sys in systems:
            # Load attributes before expunging
            _ = (sys.id, sys.name, sys.directory_path)
            session.expunge(sys)
            
            path = Path(sys.directory_path)
            
            try:
                if path.exists():
                    print(f"✓ {sys.id}: Directory already exists")
                    print(f"  {sys.directory_path}")
                    existed.append(sys.id)
                else:
                    # Create directory with parents
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"✅ {sys.id}: Created directory")
                    print(f"  {sys.directory_path}")
                    created.append(sys.id)
            except Exception as e:
                print(f"❌ {sys.id}: Failed to create directory")
                print(f"  {sys.directory_path}")
                print(f"  Error: {e}")
                failed.append((sys.id, str(e)))
            
            print()
    
    # Summary
    print("=" * 60)
    print("\nSummary:")
    print(f"  Created: {len(created)} directories")
    print(f"  Already existed: {len(existed)} directories")
    print(f"  Failed: {len(failed)} directories")
    
    if created:
        print(f"\n✅ Created directories for:")
        for sys_id in created:
            print(f"  - {sys_id}")
    
    if failed:
        print(f"\n❌ Failed to create directories for:")
        for sys_id, error in failed:
            print(f"  - {sys_id}: {error}")
        print("\nTroubleshooting:")
        print("  - Check if you have write permissions")
        print("  - Verify the path is valid for your OS")
        print("  - Try running as administrator (Windows) or with sudo (Linux/Mac)")
    
    if not failed:
        print("\n✅ All directories ready!")
        print("\nNext steps:")
        print("  1. Verify configuration: python verify_configuration.py")
        print("  2. Start monitoring: python start_monitoring.py")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    create_directories()
